# frontend/

Interfaccia di ricerca di ateneo-search (React + Vite + TypeScript).

- `src/api.ts` — chiamate tipate a `/cerca` e `/rispondi`
- `src/App.tsx` — form di domanda, risposta generata in evidenza,
  fonti grezze (file + pagina + testo) sempre visibili sotto per
  verificarla

Setup:
```bash
npm install
npm run dev
```

Richiede l'API già avviata (vedi il [README principale](../README.md))
per via del CORS: legge `VITE_API_URL` da `.env.local` (default
`http://localhost:8000`, vedi `.env.example`).
