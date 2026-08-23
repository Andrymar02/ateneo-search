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

export interface RispostaGenerata {
  risposta: string;
  fonti: Risultato[];
}

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function chiamaApi<T>(percorso: string, domanda: string, k: number): Promise<T> {
  const url = new URL(percorso, API_URL);
  url.searchParams.set("domanda", domanda);
  url.searchParams.set("k", String(k));

  const risposta = await fetch(url);
  if (!risposta.ok) {
    const corpo = await risposta.json().catch(() => null);
    throw new Error(corpo?.detail ?? `Errore ${risposta.status} dal server`);
  }
  return risposta.json();
}

export function cerca(domanda: string, k = 5): Promise<Risultato[]> {
  return chiamaApi<Risultato[]>("/cerca", domanda, k);
}

// Ricerca + risposta scritta da un LLM locale, che legge SOLO le fonti
// recuperate (vedi retrieval/genera.py). Le fonti tornano comunque
// intere: la risposta va verificata contro quelle, non presa per buona.
export function rispondi(domanda: string, k = 5): Promise<RispostaGenerata> {
  return chiamaApi<RispostaGenerata>("/rispondi", domanda, k);
}
