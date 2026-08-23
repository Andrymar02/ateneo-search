// Punto unico da cui passa ogni chiamata all'API — stesso principio di
// retrieval/cerca.py lato backend: un solo posto che conosce la forma
// della risposta e l'URL del server.

export interface Risultato {
  id: number;
  file: string;
  pagina_inizio: number;
  pagina_fine: number;
  testo: string;
  distanza: number;
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function cerca(domanda: string, k = 5): Promise<Risultato[]> {
  const url = new URL("/cerca", API_URL);
  url.searchParams.set("domanda", domanda);
  url.searchParams.set("k", String(k));

  const risposta = await fetch(url);
  if (!risposta.ok) {
    const corpo = await risposta.json().catch(() => null);
    throw new Error(corpo?.detail ?? `Errore ${risposta.status} dal server`);
  }
  return risposta.json();
}
