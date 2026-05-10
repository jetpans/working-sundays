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

type TabName = "stores" | "settings" | "run" | "results";

interface TabInfo {
  name: TabName;
  label: string;
  isValid?: boolean;
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
  const [jobInfo, setJobInfo] = useState<any | null>(null);

  // Load job descriptor and any existing files so tabs can preload edit state
  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const res = await apiFetch(`/api/job/${username}/${jobId}`);
        if (!res.ok) return;
        const body = await res.json();
        if (body.success && mounted) {
          setJobInfo(body.data || null);
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
