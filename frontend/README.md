# Vue Frontend

This frontend aligns the demo with the thesis stack:

- Vue 3 + Vite
- Element Plus
- Axios
- ECharts graph visualization

Run locally:

```bash
npm install
npm run dev
```

The Vite dev server proxies `/api/*` to the Flask backend at
`http://127.0.0.1:5000`.

Build output is written to `web_app/static/vue` so Flask/Nginx can serve the
compiled assets in a deployment.
