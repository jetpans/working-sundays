# Working Sundays — Agent Guidelines & Codebase Overview

## Project Overview

**Working Sundays** is a job scheduling and store management optimization platform.

**Purpose**: Enable users to define store locations, configure Sunday work constraints per store, and run optimization algorithms to generate optimal weekly Sunday work schedules.

**High-level flow**:
1. User logs in with username, sets backend server (default `localhost:5000`).
2. User creates a job.
3. User configures the job via a tabbed wizard:
   - **Stores tab** (primary): Upload store data (JSON), optional clustering, define global constraints (YEAR, SUNDAYS, MAX_WORKS, MAX_DOESNT_WORK), set radius value formula and radius settings, edit per-store Sunday constraints.
   - **Settings tab**: Configure general settings (cluster distances) and genetic algorithm parameters (operators, populations, threads).
   - **Run tab**: Execute optimization, stream logs over websocket, allow termination.
   - **Results tab** (stub): Display optimization results and metrics.
4. Job data is saved to backend job directory.
5. Backend coordinates with Java algorithm backend for optimization.

---

## Tech Stack

- **Frontend**: Next.js 16.2.4 + React 19.2.4 + TypeScript + Tailwind CSS v4
- **Backend API**: Flask (Python)
- **Algorithm**: Java (separate backend service)
- **Map**: Leaflet + react-leaflet (dynamic import, no SSR)
- **UI Notifications**: Sonner (toast library)
- **State Management**: React Context API (AppContext for global `server` and `username`)
- **File I/O**: Job data stored as JSON in backend `RUNS_DIR/<username>/<jobid>/`
 - **File I/O**: Job data stored as JSON in backend `RUNS_DIR/<username>/<jobid>/` with results in `RUNS_DIR/<username>/<jobid>/results/`

---

## Key File Locations

### Frontend (Next.js, app/web)

- **Layout & Setup**
  - `src/app/layout.tsx` — Root layout, wires AppProvider, ToastProvider, AppHeader
  - `src/app/globals.css` — Global styles, Tailwind directives, Leaflet CSS import
  - `tailwind.config.ts` — Tailwind content configuration
  - `src/app/page.tsx` — Home page (welcome + link to Jobs)

- **Context & Providers**
  - `src/context/AppContext.tsx` — React Context for `server`, `username` global state
  - `src/app/providers/ToastProvider.tsx` — Sonner toast wrapper

- **Navigation & Header**
  - `src/app/components/AppHeader.tsx` — Header with server input, editable username, Jobs button

- **Jobs Management**
  - `src/app/jobs/page.tsx` — Jobs list page, fetch jobs, create job, delete job with toasts
  - `src/app/jobs/[id]/page.tsx` — Job details page, fetch job info, render tabbed wizard, pass initial data to StoresTab

- **Job Wizard Tabs**
  - `src/app/jobs/[id]/components/StoresTab.tsx` — **Primary tab**: file upload, map, list, constraints modal, save to backend
  - `src/app/jobs/[id]/components/StoreMap.tsx` — Leaflet map, CircleMarkers, cluster coloring, dynamically imported
  - `src/app/jobs/[id]/components/StoreList.tsx` — Sidebar list of stores, select/delete buttons
  - `src/app/jobs/[id]/components/ConstraintsEditorModal.tsx` — Modal to toggle Sunday work constraints per store
   - `src/app/jobs/[id]/components/SettingsTab.tsx` — General + GA settings editor
   - `src/app/jobs/[id]/components/RunTab.tsx`, `ResultsTab.tsx` — Tab stubs

- **Utilities**
  - `src/lib/constants.ts` — DEFAULT_SERVER, DEFAULT_USERNAME, API URL builder
  - `src/lib/jobUtils.ts` — Store types, clustering types, color generation, Sunday calculation, validation functions

### Backend API (Flask, app/api)

- **Main Files**
  - `run.py` — Flask app entry point, registers controllers
  - `app.py` — Flask app factory
  - `config.py` — AppConfig (RUNS_DIR, PYTHON_BIN, etc.)

- **Controllers**
  - `controllers/jobCreationController.py` — JobCreationHelper class:
    - `create_job(username, descriptor)` → create job directory + descriptor.job
    - `load_stores(username, jobid, stores)` → write data.json
    - `load_constraints(username, jobid, constraints)` → write constraints.json
    - `load_calc(username, jobid, calc_string)` → save calculator in descriptor
    - `job_init_finish(username, jobid)` → validate files, calculate store values, update status

  - `controllers/jobsController.py` — JobsController class:
    - `GET /api/jobs/<username>` → list job IDs
    - `GET /api/job/<username>/<jobid>` → fetch job info including data.json and constraints.json content if present
    - `DELETE /api/job/<username>/<jobid>` → delete job directory
      - POST `/api/job/<username>/<jobid>/run` → start Java run, stream logs via websocket
      - POST `/api/job/<username>/<jobid>/terminate` → terminate active run

### Data & Config Files

- `data/` — Sample instance data (small_instance, two_sunday_instance, etc.)
  - `data.json` — Store locations and metadata
  - `clustering.json` — Pre-computed cluster assignments
  - `constraints.json` — Global and per-store constraints
- `app/web/package.json` — Dependencies: sonner, leaflet, react-leaflet, next, react, tailwind, etc.
- `app/api/requirements.txt` — Flask, python-dotenv, etc.

---

## Important Design Details & Guidelines

### State Management & Data Flow

1. **Global state** (App-wide username & server):
   - Stored in `AppContext`.
   - Updated via `useApp()` hook in any component.
   - Header allows user to edit these values.

2. **Job data** (Server-side state):
   - Always stored in backend job directory: `RUNS_DIR/<username>/<jobid>/`
   - Files: `descriptor.job`, `data.json`, `constraints.json`, `calc.py` (embedded in descriptor), optional `clustering.json`, `results/`.
   - Frontend fetches entire job info on page load and preloads StoresTab.

3. **Job wizard** (Frontend form state):
   - Each tab manages its own local state.
   - Stores tab holds: `stores`, `clustering`, `globalConstraints`, `constraintsMap`, `radiusCalculator`, `generalSettings`.
   - Preloaded from backend job info on mount.
   - Saved to backend endpoints on "Save" button click.

### UI/UX Patterns

1. **Modals**:
   - Use transparent backdrop (`bg-transparent`) + `backdrop-blur-sm` to keep background visible.
   - Set z-index high (`z-[9999]`) to sit above Leaflet map.
   - Disable map interactivity while modal is open (drag, zoom, keyboard all disabled).

2. **Toasts**:
   - Use Sonner for all success/error feedback.
   - Avoid modal alerts; always prefer toast notifications.

3. **Loading & Async**:
   - Fetch data on component mount using `useEffect`.
   - Show loading UI (spinners or disabled buttons) while async operations are in flight.
   - Always handle errors gracefully with toast messages.

4. **Map & List Sync**:
   - Selecting a marker on map highlights the same item in the list (via `selectedStoreId`).
   - Deleting a store removes it from both map and list.

### Code Style & Patterns

1. **Imports**:
   - Next.js components use `"use client"` at top.
   - Dynamically import Leaflet components to avoid SSR hydration issues.

2. **Validation**:
   - Stores data validation: check required fields (name, brand, formatted_address, coordinates).
   - Constraints validation: ensure global keys (YEAR, SUNDAYS, MAX_WORKS, MAX_DOESNT_WORK) and per-store format.
   - Always validate before saving.

3. **Tailwind**:
   - Use utility classes for styling (no CSS modules).
   - Use `@tailwind` directives in globals.css.
   - Add `content: ['./src/**/*.{js,ts,jsx,tsx,mdx}']` to tailwind.config.ts.

4. **Type Safety**:
   - Use TypeScript interfaces for all component props and data structures.
   - Define interfaces in `jobUtils.ts` for domain types (Store, Clustering, GlobalConstraints, etc.).

---

## Agent Instructions & Best Practices

### Before Making Changes

1. **Always read the relevant file first** before editing.
   - Use `read_file()` to check context and existing patterns.
   - If changing a component, verify its props and state management first.

2. **Ask about design choices** rather than assume.
   - If uncertain whether a feature should live in a component or a utility, ask the user.
   - If considering a new pattern (e.g., a new Context, a new controller endpoint), confirm with the user first.
   - Do not invent UI/UX decisions without user guidance.

3. **Check for existing patterns** before creating new ones.
   - Look for similar components, hooks, or utility functions.
   - Reuse existing patterns rather than creating parallel implementations.

### When Writing Code

1. **Write human-readable, concise code**.
   - Use clear variable and function names.
   - Keep functions small and focused (one responsibility per function).
   - Add comments only for non-obvious logic.
   - Avoid nested ternaries; use intermediate variables or early returns.

2. **Handle edge cases gracefully**.
   - Check for null/undefined before accessing properties.
   - Wrap async operations in try-catch; always show user feedback via toast.
   - Validate data before processing.

3. **Prefer composition over duplication**.
   - If two components share logic, extract it to a utility or a shared component.
   - Don't copy-paste code; refactor.

4. **Use TypeScript strictly**.
   - No `any` types unless absolutely necessary.
   - Define proper interfaces for all component props and data.
   - Use type guards and narrowing.

### Before Finishing a Task

1. **Verify the code works**.
   - If creating a new feature, test it locally first.
   - Provide test steps and expected behavior.
   - Do not assume something works; always confirm.

2. **Check for regressions**.
   - If modifying an existing component, verify other components that depend on it still work.
   - Test the full flow (e.g., create job → open job → load stores → edit constraints → save).

3. **Provide clear setup instructions**.
   - Include bash commands (copyable, one-per-line) for running the app.
   - Specify which folder to run commands from.
   - Mention dependencies that need to be installed.

4. **Use proper file linking** in responses.
   - Link to files with markdown syntax: `[filename.tsx](path/to/filename.tsx)`.
   - Include line numbers for specific sections: `[StoresTab.tsx](src/app/jobs/[id]/components/StoresTab.tsx#L100)`.

### Multi-Step Tasks

1. **Use `manage_todo_list()`** to track progress on complex tasks.
   - Break the task into actionable steps.
   - Mark steps as `in-progress` when starting, `completed` when done.
   - Update the list as you progress; do not batch completions.

2. **Provide progress updates** every 3–5 tool calls or after making > 3 file edits.
   - Summarize what's been done.
   - Explain what's next.

3. **Avoid hand-offs** — keep working until the user's request is fully resolved.
   - Do not stop and ask "does this look good?" unless genuinely blocked.
   - Infer intent and proceed proactively.

### Communication Style

1. **Skip filler acknowledgments** — avoid "Sounds good", "Okay, I will…", etc.
2. **Open with purpose** — start sentences with what you're about to do.
3. **Be concise** — answer directly, avoid unnecessary repetition.
4. **Use code blocks** for runnable commands, with proper language tags.
5. **Do not volunteer model name** unless explicitly asked.

---

## Common Pitfalls to Avoid

1. **Hydration mismatches**: Leaflet is dynamically imported to prevent SSR issues. Do not remove this.
2. **Black modals**: Use `bg-transparent` for overlays; avoid `bg-black` or dark opacity that hides the page.
3. **Map z-index conflicts**: Always set map container z-index to 0 when modals are open. Disable interactivity.
4. **Missing preload**: When opening a job page, always fetch job info and pass initial data to StoresTab immediately (no need to switch tabs first).
5. **Validation gaps**: Always validate user input before posting to backend. Provide clear error messages.
6. **Async state bugs**: Initialize state with callbacks (`useState(() => ...)`) when deriving from props. Use `useEffect` to sync prop changes to state.
7. **Broken dependencies**: Always add new npm packages to `package.json`. Run `npm install` after changes.
8. **Run status drift**: When starting/terminating a job, update `descriptor.job.run_info` and keep Run tab polling it.

---

## Run Tab Execution Notes

- The API launches the Java run with `JAVA_BIN` and `JAVA_JAR` and streams stdout/stderr over Socket.IO.
- One job corresponds to one run; new runs override the existing `results/` folder.
- Run status is stored in `descriptor.job.run_info` and surfaced on the Run tab.

## Cross-Stack Change Workflow (Settings + GA Operators)

Use this checklist when adding a new genetic operator or a new setting so the frontend, API, and Java stay in sync.

1. **Define the JSON contract first**
   - Update the expected shape under `descriptor.job.settings` (usually `settings.general` or `settings.ga`).
   - Decide default values and whether the setting should be user-visible.

2. **Frontend: add the control + validation**
   - Add the field to the appropriate tab (Stores for radius settings, Settings for GA/general).
   - Update defaults in [SettingsTab.tsx](app/web/src/app/jobs/[id]/components/SettingsTab.tsx) or [StoresTab.tsx](app/web/src/app/jobs/[id]/components/StoresTab.tsx).
   - Ensure save flow posts to `/settings` before any dependent API calls.

3. **Backend API: persist and consume settings**
   - `/settings` writes into `descriptor.job` via `jobCreationController`.
   - Any Python-side usage (e.g. radius calculation) should read from `descriptor.job.settings` and apply defaults.

4. **Java: load from descriptor.job**
   - Extend `Settings.fromDescriptorJson(...)` to map new fields.
   - If an operator type is added, add its constructor mapping and params parsing.
   - Apply general values to `Global` if they affect clustering or algorithm behavior.

5. **End-to-end sanity check**
   - Create a job → set new values → save → export descriptor → run Java with `CallableDispatcher` and verify behavior.

## Next Steps & Future Work

- **Run tab**: Implement WebSocket integration with Java backend to stream optimization logs.
- **Results tab**: Display optimization results (store assignments, Sunday schedules, cost metrics).
- **Settings tab**: Configuration options (algorithm parameters, timeout, etc.).
- **UX Polish**: Scroll-to-item when selecting on map, save indicators, better validation messages.
- **Clustering**: Visual toggle to color stores by cluster vs. brand.

---

End of AGENTS.md.
