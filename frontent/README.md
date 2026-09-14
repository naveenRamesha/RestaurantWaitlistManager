# Verde Host frontend

Interactive React + TypeScript frontend for the Restaurant Waitlist Manager MVP.

```powershell
cd frontent
npm.cmd install
npm.cmd run dev
```

The UI uses `src/api.ts` as its only data boundary. It calls the FastAPI `/api/v1` endpoints and translates their API fields for the UI. By default it connects to `http://127.0.0.1:8000/api/v1`; set `VITE_API_BASE_URL` to use another server.

Validate a production bundle with:

```powershell
npm.cmd run build
```
