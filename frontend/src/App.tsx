import { useState, type FormEvent } from "react";
import { rispondi, type Risultato } from "./api";
import "./App.css";

type Stato =
  | { fase: "inattivo" }
  | { fase: "in_corso" }
  | { fase: "errore"; messaggio: string }
  | { fase: "completo"; risposta: string; fonti: Risultato[] };

const DOMANDE_ESEMPIO = [
  "Cos'è un iteratore?",
  "Differenza tra training set e test set",
  "Come funziona il controllo di concorrenza in un DBMS?",
];

export default function App() {
  const [domanda, setDomanda] = useState("");
  const [stato, setStato] = useState<Stato>({ fase: "inattivo" });

  async function esegui(testoDomanda: string) {
    const testo = testoDomanda.trim();
    if (!testo) return;

    setStato({ fase: "in_corso" });
    try {
      const { risposta, fonti } = await rispondi(testo, 5);
      setStato({ fase: "completo", risposta, fonti });
    } catch (errore) {
      setStato({
        fase: "errore",
        messaggio: errore instanceof Error ? errore.message : "Errore sconosciuto",
      });
    }
  }

  function onSubmit(evento: FormEvent) {
    evento.preventDefault();
    esegui(domanda);
  }

  function onEsempio(testoEsempio: string) {
    setDomanda(testoEsempio);
    esegui(testoEsempio);
  }

  return (
    <main className="pagina">
      <header className="intestazione">
        <span className="badge">100% locale · nessuna API esterna</span>
        <h1>ateneo-search</h1>
        <p className="sottotitolo">
          Fai una domanda sui tuoi materiali di corso. Un LLM locale scrive la
          risposta leggendo solo i passaggi recuperati qui sotto — sempre
          visibili, per verificarla.
        </p>
      </header>

      <form onSubmit={onSubmit} className="form-ricerca">
        <input
          type="text"
          value={domanda}
          onChange={(e) => setDomanda(e.target.value)}
          placeholder="Cosa vuoi sapere?"
          aria-label="Domanda"
        />
        <button type="submit" disabled={stato.fase === "in_corso"}>
          {stato.fase === "in_corso" ? "Penso…" : "Chiedi"}
        </button>
      </form>

      {stato.fase === "inattivo" && (
        <div className="esempi">
          <span className="esempi-etichetta">Prova:</span>
          {DOMANDE_ESEMPIO.map((d) => (
            <button key={d} type="button" className="chip" onClick={() => onEsempio(d)}>
              {d}
            </button>
          ))}
        </div>
      )}

      {stato.fase === "errore" && (
        <p className="errore" role="alert">
          {stato.messaggio}
        </p>
      )}

      {stato.fase === "completo" && (
        <>
          <div className="risposta-generata">{stato.risposta}</div>

          {stato.fonti.length > 0 && (
            <>
              <h2 className="titolo-fonti">Fonti</h2>
              <ul className="risultati">
                {stato.fonti.map((r) => (
                  <li key={r.id} className="risultato">
                    <div className="citazione">
                      {r.file} — p.{r.pagina_inizio}
                      {r.pagina_fine !== r.pagina_inizio && `-${r.pagina_fine}`}
                    </div>
                    <p className="testo">{r.testo}</p>
                  </li>
                ))}
              </ul>
            </>
          )}
        </>
      )}

      <footer className="piede">
        <span className="chip-tech">bge-m3</span>
        <span className="chip-tech">llama3.1</span>
        <span className="chip-tech">sqlite-vec</span>
      </footer>
    </main>
  );
}
