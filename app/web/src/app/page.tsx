import Link from "next/link";

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col gap-8 px-6 py-10">
      <section className="rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Overview
        </p>
        <h1 className="mt-3 text-3xl font-semibold text-slate-900">
          Welcome to Working Sundays
        </h1>
        <p className="mt-3 max-w-2xl text-sm text-slate-600">
          This dashboard helps you connect to the backend, manage your user
          session, and keep track of jobs. We will fill in the real content as
          the backend features land.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            className="rounded bg-slate-900 px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800"
            href="/jobs"
          >
            Go to jobs
          </Link>
          <button
            className="rounded border border-slate-200 px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
            type="button"
          >
            Create new job (soon)
          </button>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-700">Server</p>
          <p className="mt-2 text-xs text-slate-500">
            Use the header to set the server URL you want to connect to.
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-700">Username</p>
          <p className="mt-2 text-xs text-slate-500">
            Toggle the edit button to update the active username.
          </p>
        </div>
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <p className="text-sm font-medium text-slate-700">Jobs</p>
          <p className="mt-2 text-xs text-slate-500">
            View and create jobs in the jobs page once it is wired up.
          </p>
        </div>
      </section>

      <section className="rounded-2xl border border-dashed border-slate-200 bg-white p-6 text-sm text-slate-500">
        Recent activity will show here once job tracking is connected.
      </section>
    </main>
  );
}
