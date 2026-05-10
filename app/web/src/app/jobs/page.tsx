"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useApp } from "@/context/AppContext";
import { useApiFetch } from "@/hooks/useApiFetch";
import { toast } from "sonner";

interface Job {
  id: string;
  created_at: string;
  status: string;
}

export default function JobsPage() {
  const { server, username } = useApp();
  const apiFetch = useApiFetch();
  const router = useRouter();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);

  const fetchJobs = async () => {
    try {
      setIsLoading(true);
      const response = await apiFetch(`/api/jobs/${username}`);
      if (!response.ok) {
        throw new Error(`Failed to fetch jobs (${response.status})`);
      }
      const data = await response.json();
      if (data.success && Array.isArray(data.data)) {
        // Fetch full job info for each job
        const jobsWithInfo = await Promise.all(
          data.data.map(async (jobId: string) => {
            try {
              const jobResponse = await apiFetch(
                `/api/job/${username}/${jobId}`,
              );
              if (jobResponse.ok) {
                const jobData = await jobResponse.json();
                if (jobData.success && jobData.data) {
                  return {
                    id: jobId,
                    created_at: jobData.data.run_info?.created_at || "N/A",
                    status: jobData.data.run_info?.status || "unknown",
                  };
                }
              }
            } catch {
              // Fallback if individual job fetch fails
            }
            return {
              id: jobId,
              created_at: "N/A",
              status: "unknown",
            };
          }),
        );
        setJobs(jobsWithInfo);
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to load jobs",
      );
    } finally {
      setIsLoading(false);
    }
  };

  const createJob = async () => {
    try {
      setIsCreating(true);
      const response = await apiFetch(`/api/job/init`, {
        method: "POST",
        body: JSON.stringify({ username }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create job (${response.status})`);
      }

      const data = await response.json();
      if (data.success) {
        toast.success("Job created successfully");
        fetchJobs();
      } else {
        throw new Error(data.error || "Failed to create job");
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to create job",
      );
    } finally {
      setIsCreating(false);
    }
  };

  const deleteJob = async (jobId: string) => {
    try {
      const response = await apiFetch(`/api/job/${username}/${jobId}`, {
        method: "DELETE",
      });

      if (!response.ok) {
        throw new Error(`Failed to delete job (${response.status})`);
      }

      const data = await response.json();
      if (data.success) {
        toast.success("Job deleted successfully");
        fetchJobs();
      } else {
        throw new Error(data.error || "Failed to delete job");
      }
    } catch (error) {
      toast.error(
        error instanceof Error ? error.message : "Failed to delete job",
      );
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [server, username]);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-6 px-6 py-10">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Jobs</h1>
        <button
          onClick={createJob}
          disabled={isCreating}
          className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:opacity-60"
        >
          {isCreating ? "Creating..." : "Create Job"}
        </button>
      </header>

      <section className="rounded-lg border border-slate-200 bg-white shadow-sm overflow-hidden">
        {isLoading ? (
          <div className="p-6 text-center text-slate-500">Loading jobs...</div>
        ) : jobs.length === 0 ? (
          <div className="p-6 text-center text-slate-500">
            No jobs yet. Click "Create Job" to get started.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="border-b border-slate-200 bg-slate-50">
                <tr>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
                    Job ID
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
                    Created
                  </th>
                  <th className="px-4 py-3 text-left text-sm font-semibold text-slate-700">
                    Status
                  </th>
                  <th className="px-4 py-3 text-right text-sm font-semibold text-slate-700">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200">
                {jobs.map((job) => (
                  <tr
                    key={job.id}
                    className="hover:bg-slate-50 cursor-pointer"
                    onClick={() => router.push(`/jobs/${job.id}`)}
                  >
                    <td className="px-4 py-3 text-sm font-mono text-slate-900">
                      {job.id.slice(0, 8)}...
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-600">
                      {new Date(job.created_at).toLocaleDateString()} at{" "}
                      {new Date(job.created_at).toLocaleTimeString()}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-medium text-slate-700">
                        {job.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          deleteJob(job.id);
                        }}
                        className="text-sm font-semibold text-red-600 hover:text-red-800"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </main>
  );
}
