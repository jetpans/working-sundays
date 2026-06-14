"use client";

import { useParams } from "next/navigation";
import { useState, useEffect } from "react";
import { toast } from "sonner";
import { useApp } from "@/context/AppContext";
import { useApiFetch } from "@/hooks/useApiFetch";
import StoresTab from "./components/StoresTab";
import SettingsTab from "./components/SettingsTab";
import RunTab from "./components/RunTab";
import ResultsTab from "./components/ResultsTab";
import { Store, StoreConstraints } from "@/lib/jobUtils";

type TabName = "stores" | "settings" | "run" | "results";

interface TabInfo {
  name: TabName;
  label: string;
  isValid?: boolean;
}

interface JobDescriptor {
  description?: string | null;
  settings?: Record<string, unknown>;
  value_for_radius_calculator?: string | null;
}

interface JobInfo {
  descriptor?: JobDescriptor;
  data?: Record<string, Store> | null;
  constraints?: Record<string, StoreConstraints> | null;
}

function hasCompleteStoresTab(jobInfo: JobInfo | null) {
  const constraints = jobInfo?.constraints;
  const radiusCalc = jobInfo?.descriptor?.value_for_radius_calculator;

  return (
    !!jobInfo?.data &&
    Object.keys(jobInfo.data).length > 0 &&
    !!constraints &&
    constraints.YEAR !== undefined &&
    constraints.SUNDAYS !== undefined &&
    constraints.MAX_WORKS !== undefined &&
    constraints.MAX_DOESNT_WORK !== undefined &&
    typeof radiusCalc === "string" &&
    radiusCalc.trim().length > 0
  );
}

function hasCompleteSettingsTab(jobInfo: JobInfo | null) {
  const settings = jobInfo?.descriptor?.settings;
  return !!settings?.general && !!settings?.ga;
}

function renderTabStatusIcon(tab: TabName, isValid?: boolean) {
  if (tab === "results") return null;
  if (isValid === false) {
    return (
      <span className="text-red-500" title="Incomplete">
        ★
      </span>
    );
  }
  if (isValid === true) {
    return (
      <span className="text-green-500" title="Complete">
        ✓
      </span>
    );
  }
  return null;
}

export default function JobDetailsPage() {
  const params = useParams();
  const { server, username } = useApp();
  const apiFetch = useApiFetch();
  const jobId = params.id as string;

  const [activeTab, setActiveTab] = useState<TabName>("stores");
  const [tabValidity, setTabValidity] = useState<Record<TabName, boolean>>({
    stores: false,
    settings: false,
    run: false,
    results: false,
  });
  const [jobInfo, setJobInfo] = useState<JobInfo | null>(null);
  const [description, setDescription] = useState("");
  const [isSavingDescription, setIsSavingDescription] = useState(false);

  // Load job descriptor and any existing files so tabs can preload edit state
  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await apiFetch(`/api/job/${username}/${jobId}`);
        if (!res.ok) return;
        const body = await res.json();
        if (body.success && mounted) {
          const nextJobInfo = body.data || null;
          setJobInfo(nextJobInfo);
          setDescription(body.data?.descriptor?.description || "");
          setTabValidity((prev) => ({
            ...prev,
            stores: hasCompleteStoresTab(nextJobInfo),
            settings: hasCompleteSettingsTab(nextJobInfo),
          }));
        }
      } catch {
        // ignore
      }
    };
    load();
    return () => {
      mounted = false;
    };
  }, [server, username, jobId]);

  const tabs: TabInfo[] = [
    { name: "stores", label: "Stores", isValid: tabValidity.stores },
    { name: "settings", label: "Settings", isValid: tabValidity.settings },
    { name: "run", label: "Run", isValid: tabValidity.run },
    { name: "results", label: "Results", isValid: tabValidity.results },
  ];

  const handleTabValidation = (tabName: TabName, isValid: boolean) => {
    setTabValidity((prev) => ({
      ...prev,
      [tabName]: isValid,
    }));
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case "stores":
        return (
          <StoresTab
            username={username}
            jobId={jobId}
            server={server}
            onValidationChange={(isValid) =>
              handleTabValidation("stores", isValid)
            }
          />
        );
      case "settings":
        return (
          <SettingsTab
            username={username}
            jobId={jobId}
            server={server}
            initialDescriptor={jobInfo || undefined}
            onSaved={({ general, ga }) => {
              setJobInfo((prev) => {
                if (!prev) return prev;
                const prevDescriptor = prev.descriptor || {};
                const prevSettings = prevDescriptor.settings || {};
                return {
                  ...prev,
                  descriptor: {
                    ...prevDescriptor,
                    settings: {
                      ...prevSettings,
                      general,
                      ga,
                    },
                  },
                };
              });
            }}
            onValidationChange={(isValid) =>
              handleTabValidation("settings", isValid)
            }
          />
        );
      case "run":
        return (
          <RunTab
            username={username}
            jobId={jobId}
            server={server}
            onStatusChange={(status) =>
              handleTabValidation("run", status === "Complete")
            }
          />
        );
      case "results":
        return <ResultsTab username={username} jobId={jobId} server={server} />;
      default:
        return null;
    }
  };

  return (
    <main className="mx-auto flex w-full max-w-full flex-1 flex-col gap-6 px-6 py-6">
      <div>
        <h1 className="text-3xl font-semibold">Job Configuration</h1>
        <p className="mt-1 text-sm text-slate-600">
          ID: {jobId.slice(0, 8)}...
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <label className="text-sm font-medium text-slate-600" htmlFor="job-description">
            Description
          </label>
          <input
            id="job-description"
            value={description}
            onChange={(event) => setDescription(event.target.value)}
            placeholder="Describe this job"
            className="min-w-[260px] flex-1 rounded border border-slate-200 bg-white px-3 py-2 text-sm shadow-sm focus:border-slate-400 focus:outline-none"
          />
          <button
            type="button"
            disabled={isSavingDescription}
            onClick={async () => {
              try {
                setIsSavingDescription(true);
                const res = await apiFetch(`/api/job/${username}/${jobId}/description`, {
                  method: "POST",
                  body: JSON.stringify({
                    description: description.trim() || null,
                  }),
                });
                if (!res.ok) {
                  throw new Error(`Failed to save description (${res.status})`);
                }
                const body = await res.json();
                if (!body.success) {
                  throw new Error(body.error || "Failed to save description");
                }
                setJobInfo((prev) => {
                  if (!prev) return prev;
                  return {
                    ...prev,
                    descriptor: {
                      ...prev.descriptor,
                      description: description.trim() || null,
                    },
                  };
                });
                toast.success("Description saved");
              } catch (error) {
                toast.error(
                  error instanceof Error
                    ? error.message
                    : "Failed to save description",
                );
              } finally {
                setIsSavingDescription(false);
              }
            }}
            className="rounded border border-slate-200 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-60"
          >
            {isSavingDescription ? "Saving..." : "Save"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-slate-200">
        <div className="flex gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.name}
              onClick={() => {
                if (activeTab === "stores" && tab.name !== "stores") {
                  if (!tabValidity.stores) {
                    toast.error(
                      "Save the Stores tab successfully before leaving it.",
                    );
                    return;
                  }
                }
                setActiveTab(tab.name);
              }}
              className={`flex items-center gap-2 border-b-2 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.name
                  ? "border-slate-900 text-slate-900"
                  : "border-transparent text-slate-600 hover:text-slate-900"
              }`}
            >
              {tab.label}
              {renderTabStatusIcon(tab.name, tab.isValid)}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Content */}
      <div>
        {activeTab === "stores" ? (
          jobInfo ? (
            <StoresTab
              username={username}
              jobId={jobId}
              server={server}
              initialStores={jobInfo.data || undefined}
              initialConstraints={jobInfo.constraints || undefined}
              initialRadiusCalc={
                jobInfo.descriptor?.value_for_radius_calculator || undefined
              }
              initialGeneralSettings={
                jobInfo.descriptor?.settings?.general || undefined
              }
              initialSettings={jobInfo.descriptor?.settings || undefined}
              onImportedJob={({ stores, constraints, radiusCalc, settings }) => {
                const importedJobInfo = {
                  ...jobInfo,
                  data: stores || jobInfo.data,
                  constraints: constraints || jobInfo.constraints,
                  descriptor: {
                    ...jobInfo.descriptor,
                    settings: settings || jobInfo.descriptor?.settings || {},
                    value_for_radius_calculator:
                      radiusCalc ||
                      jobInfo.descriptor?.value_for_radius_calculator,
                  },
                };

                setJobInfo(importedJobInfo);
                setTabValidity((prev) => ({
                  ...prev,
                  stores: hasCompleteStoresTab(importedJobInfo),
                  settings: hasCompleteSettingsTab(importedJobInfo),
                }));
              }}
              onValidationChange={(isValid) =>
                handleTabValidation("stores", isValid)
              }
            />
          ) : (
            <div className="rounded-lg border border-slate-200 bg-white p-6 text-sm text-slate-500">
              Loading saved stores...
            </div>
          )
        ) : (
          renderTabContent()
        )}
      </div>
    </main>
  );
}
