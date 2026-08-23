import { useState, type FormEvent } from "react";
import { cerca, type Risultato } from "./api";
import "./App.css";

type Stato =
  | { fase: "inattivo" }
  | { fase: "in_corso" }
  | { fase: "errore"; messaggio: string }
  | { fase: "completo"; risultati: Risultato[] };

export default function App() {
  const [domanda, setDomanda] = useState("");
  const [stato, setStato] = useState<Stato>({ fase: "inattivo" });

  async function onSubmit(evento: FormEvent) {
    evento.preventDefault();
    const testo = domanda.trim();
    if (!testo) return;

    setStato({ fase: "in_corso" });
    try {
      const risultati = await cerca(testo, 5);
      setStato({ fase: "completo", risultati });
    } catch (errore) {
      setStato({
        fase: "errore",
        messaggio: errore instanceof Error ? errore.message : "Errore sconosciuto",
      });
    }
  }

  return (
    <main className="pagina">
      <h1>ateneo-search</h1>
      <p className="sottotitolo">
        Cerca nei tuoi materiali di corso. Ogni risultato è il testo reale del
        PDF, con file e pagina — nessuna risposta generata, nessuna citazione
        da verificare.
      </p>

      <form onSubmit={onSubmit} className="form-ricerca">
        <input
          type="text"
          value={domanda}
          onChange={(e) => setDomanda(e.target.value)}
          placeholder="Cosa vuoi sapere?"
          aria-label="Domanda"
        />
        <button type="submit" disabled={stato.fase === "in_corso"}>
          {stato.fase === "in_corso" ? "Cerco…" : "Cerca"}
        </button>
      </form>

      {stato.fase === "errore" && (
        <p className="errore" role="alert">
          {stato.messaggio}
        </p>
      )}

      {stato.fase === "completo" && stato.risultati.length === 0 && (
        <p className="vuoto">Nessun risultato.</p>
      )}

      {stato.fase === "completo" && (
        <ul className="risultati">
          {stato.risultati.map((r) => (
            <li key={r.id} className="risultato">
              <div className="citazione">
                {r.file} — p.{r.pagina_inizio}
                {r.pagina_fine !== r.pagina_inizio && `-${r.pagina_fine}`}
              </div>
              <p className="testo">{r.testo}</p>
            </li>
          ))}
        </ul>
      )}
    </main>
  );
}
