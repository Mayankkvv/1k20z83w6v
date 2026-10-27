# WindSight frontend

The React + Vite dashboard for WindSight. It only displays data: every number comes from the Python backend.

See the main [README](../README.md) for the full project description, how to run everything, and the architecture.

Quick start (from this folder):

```bash
npm install
npm run dev      # http://localhost:5173
npm test         # unit tests
npm run lint
npm run build
```

The backend address is set with `VITE_API_BASE_URL` (see `.env.example`). It defaults to `http://127.0.0.1:8000`.