# Working Sundays — Build & Development Guidelines

## Project Overview

**Working Sundays** is a job scheduling and store management optimization platform enabling users to define store locations, configure Sunday work constraints, and generate optimal weekly schedules via optimization algorithms.

**Tech Stack:**
- **Frontend**: Next.js 16.2.4 + React 19.2.4 + TypeScript + Tailwind CSS v4
- **Backend API**: Flask (Python)
- **Algorithm**: Java (separate backend service)
- **Documentation**: Flasgger (OpenAPI 2.0 via external swagger.yml)
- **Map**: Leaflet + react-leaflet
- **State Management**: React Context API
- **Notifications**: Sonner (toast library)

---

## API Documentation Setup

### Swagger/OpenAPI Configuration

**File**: `app/api/swagger.yml` (800+ lines)
- **Format**: OpenAPI 2.0 (Swagger 2.0)
- **Content**: All 30+ REST API endpoints with complete specifications
- **Security**: Bearer JWT token in Authorization header
- **Auto-rendered at**: `http://localhost:5000/api/docs` (Swagger UI)
- **Spec endpoint**: `http://localhost:5000/apispec.json`

### Frontend Link

**File**: `app/web/src/app/components/AppHeader.tsx`
- "API Docs" button links to `http://{server}/api/docs`
- Dynamically uses configured server from AppContext
- Opens in new tab

### Implementation Pattern (DO NOT use inline docstrings)

✅ **Correct**: Document in external `swagger.yml`
```yaml
paths:
  /api/jobs/{username}:
    get:
      tags:
        - Jobs
      summary: List all jobs for a user
      parameters:
        - in: path
          name: username
          type: string
          required: true
      responses:
        200:
          description: Job list
        500:
          description: Server error
```

❌ **Wrong**: Do NOT embed YAML docstrings in route functions
```python
@app.get("/api/jobs/<username>")
def get_jobs(username: str):
    """
    List all jobs
    ---
    tags:
      - Jobs
    ...
    """
```

---

## Build & Run Instructions

### Backend API

```bash
# Set up Python environment (if using venv)
cd app/api
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run Flask development server
python run.py
# API available at http://localhost:5000
# Swagger UI at http://localhost:5000/api/docs
```

### Frontend (Next.js)

```bash
cd app/web
npm install
npm run dev
# Frontend available at http://localhost:3000
```

### Validation

```bash
# Validate all Flask controllers compile
cd app/api/controllers
python -m py_compile authController.py jobCreationController.py jobsController.py jobResultController.py healthController.py

# Build Next.js frontend
cd app/web
npm run build
```

---

## Code Organization

### Backend Controllers

**Location**: `app/api/controllers/`

1. **authController.py** (3 endpoints)
   - POST `/api/auth/login` — User authentication
   - GET `/api/auth/me` — Current user info
   - POST `/api/auth/logout` — Client-side logout

2. **jobCreationController.py** (9 endpoints)
   - POST `/api/job/init` — Create new job
   - POST `/api/job/{username}/{jobid}/stores` — Save store data
   - POST `/api/job/{username}/{jobid}/constraints` — Save constraints
   - POST `/api/job/{username}/{jobid}/settings` — Save settings
   - POST `/api/job/{username}/{jobid}/calc` — Save calculator
   - POST `/api/job/{username}/{jobid}/export` — Export job snapshot
   - POST `/api/job/{username}/{jobid}/finish` — Validate & finalize

3. **jobsController.py** (13+ endpoints)
   - GET `/api/jobs/{username}` — List jobs
   - GET `/api/job/{username}/{jobid}` — Get job info with files
   - POST `/api/job/{username}/{jobid}/run` — Execute job (spawns Java subprocess)
   - POST `/api/job/{username}/{jobid}/terminate` — Kill running job
   - DELETE `/api/job/{username}/{jobid}` — Delete job
   - GET `/api/job/{username}/{jobid}/runlog` — Full run log
   - GET `/api/job/{username}/{jobid}/runlog/tail` — Incremental log
   - GET `/api/job/{username}/{jobid}/results` — List result files
   - GET `/api/job/{username}/{jobid}/results/file` — Read result JSON
   - GET `/api/job/{username}/{jobid}/results/stats` — Compute statistics

4. **healthController.py** (1 endpoint)
   - GET `/api/heartbeat` — Health check

5. **jobResultController.py** (4 stub endpoints)
   - GET `/api/job/{username}/{jobid}/result` — NotImplemented
   - GET `/api/job/{username}/{jobid}/metrics` — NotImplemented
   - GET `/api/job/{username}/{jobid}/visualization` — NotImplemented
   - GET `/api/job/{username}/{jobid}/logs` — NotImplemented

### Frontend Structure

**Location**: `app/web/src/`

- **app/layout.tsx** — Root layout with AppProvider, ToastProvider, AppHeader
- **app/page.tsx** — Home page
- **context/AppContext.tsx** — Global state for server, username
- **components/AppHeader.tsx** — Navigation header with API Docs link
- **jobs/page.tsx** — Jobs list (create, delete jobs)
- **jobs/[id]/page.tsx** — Job details with tabbed wizard
- **jobs/[id]/components/** — Tab components (StoresTab, SettingsTab, RunTab, ResultsTab)
- **lib/jobUtils.ts** — Utility types and functions
- **lib/constants.ts** — Configuration constants

---

## Code Style & Patterns

### TypeScript
- No `any` types (use proper interfaces)
- Define props interfaces for all components
- Use type guards and narrowing

### Python Flask
- Use `@api_user_required()` decorator for JWT-protected endpoints
- Always return `{"success": bool, "data": Any, "error": str}` format
- Wrap async operations in try-catch, show user feedback via toast/return error

### React Components
- Use "use client" at top of client components
- Dynamically import Leaflet to avoid SSR hydration issues
- Use `useEffect` for data fetching on mount
- Manage form state locally, save to backend on button click

### Tailwind CSS
- Use utility classes (no CSS modules)
- Add `content: ['./src/**/*.{js,ts,jsx,tsx,mdx}']` to tailwind.config.ts
- Use `@tailwind` directives in globals.css

### API Documentation
- All endpoints documented in `swagger.yml`
- NO inline YAML docstrings in route functions
- Use consistent tags, parameters, responses format
- Include `security: ["Bearer: []"]` for protected endpoints

---

## Critical Practices

### Before Making Changes

1. **Read relevant files first** — Check existing patterns before implementing
2. **Ask about design choices** — Clarify architecture decisions before coding
3. **Check for existing patterns** — Reuse instead of duplicating
4. **Validate input** — Always check for null/undefined before processing

### When Writing Code

1. **Readable code first** — Prefer clarity over cleverness
2. **Keep functions focused** — One responsibility per function
3. **Handle edge cases** — Check for null, manage errors gracefully
4. **Use TypeScript strictly** — Define proper interfaces, avoid `any`
5. **Compose over duplication** — Extract shared logic to utilities

### Before Finishing a Task

1. **Verify it works locally** — Test end-to-end before declaring done
2. **Check for regressions** — Ensure other components still work
3. **Validate syntax** — Run py_compile or npm build
4. **Provide setup instructions** — Clear, copyable bash commands

---

## Common Pitfalls

1. **Hydration mismatches** — Leaflet must be dynamically imported
2. **Black modals** — Use `bg-transparent` + `backdrop-blur-sm`, avoid dark overlays
3. **Map z-index conflicts** — Set map container z-index 0 when modals open
4. **Missing preload** — Always fetch job info before opening job page
5. **Validation gaps** — Always validate before posting to backend
6. **Async state bugs** — Initialize with callbacks, use useEffect for updates
7. **Broken dependencies** — Add packages to package.json, run npm install
8. **Inline Swagger docstrings** — Use external swagger.yml instead

---

## File Locations Reference

```
working-sundays/
├── AGENTS.md                          # Original agent guidelines (comprehensive)
├── BUILD_GUIDELINES.md                # This file
├── swagger.yml                        # API spec (not present in root; see below)
├── app/
│   ├── api/
│   │   ├── swagger.yml                # ← OpenAPI 2.0 specification (800+ lines)
│   │   ├── docs.py                    # Flasgger configuration
│   │   ├── app.py                     # Flask app factory
│   │   ├── run.py                     # Entry point
│   │   ├── config.py                  # Configuration
│   │   ├── security.py                # JWT & auth utilities
│   │   ├── controllers/
│   │   │   ├── authController.py
│   │   │   ├── jobCreationController.py
│   │   │   ├── jobsController.py
│   │   │   ├── jobResultController.py
│   │   │   ├── healthController.py
│   │   ├── requirements.txt
│   │
│   ├── web/
│   │   ├── package.json
│   │   ├── tsconfig.json
│   │   ├── tailwind.config.ts
│   │   ├── src/
│   │   │   ├── app/
│   │   │   │   ├── layout.tsx
│   │   │   │   ├── page.tsx
│   │   │   │   ├── components/AppHeader.tsx
│   │   │   │   ├── context/AppContext.tsx
│   │   │   │   ├── jobs/page.tsx
│   │   │   │   ├── jobs/[id]/page.tsx
│   │   │   │   ├── jobs/[id]/components/
│   │   │   ├── lib/
│   │   │   │   ├── jobUtils.ts
│   │   │   │   ├── constants.ts
│   │
├── data/                              # Sample instance data
│   ├── small_instance/
│   │   ├── data.json
│   │   ├── constraints.json
│   │   ├── clustering.json
```

---

## Validation Checklist

Before committing changes:

- [ ] All Python files compile: `python -m py_compile file.py`
- [ ] All controllers pass syntax check
- [ ] Next.js builds: `npm run build`
- [ ] No TypeScript errors: `npm run type-check` (if available)
- [ ] Swagger UI loads at `http://localhost:5000/api/docs`
- [ ] API Docs button in header points to correct server
- [ ] No `any` types in new TypeScript code
- [ ] No inline YAML docstrings in route functions
- [ ] All new endpoints documented in `swagger.yml`
- [ ] Error handling in place (try-catch + user feedback)

---

## Quick Reference: Adding a New Endpoint

### 1. Add to swagger.yml
```yaml
paths:
  /api/new-endpoint:
    post:
      tags:
        - Category
      summary: Brief description
      security:
        - Bearer: []
      parameters:
        - in: body
          name: body
          schema:
            type: object
            properties:
              key: { type: string }
      responses:
        200:
          description: Success message
        400:
          description: Error message
```

### 2. Add route in controller
```python
@self.app.post("/api/new-endpoint")
@api_user_required()
def new_endpoint():
    try:
        # Implementation
        return {"success": True, "data": result}, 200
    except Exception as e:
        return {"success": False, "error": str(e)}, 500
```

### 3. NO docstring (docs live in swagger.yml)

### 4. Validate
```bash
python -m py_compile controller.py
```

---

## References

- **AGENTS.md** — Comprehensive project guidelines
- **app/api/swagger.yml** — Complete OpenAPI specification
- **Flasgger**: https://github.com/flasgger/flasgger
- **Next.js**: https://nextjs.org
- **Tailwind CSS**: https://tailwindcss.com
- **OpenAPI 2.0**: https://swagger.io/specification/v2/

