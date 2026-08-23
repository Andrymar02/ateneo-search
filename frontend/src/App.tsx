import { useState, type FormEvent } from "react";
import { rispondi, type Risultato } from "./api";
import "./App.css";

type Stato =
  | { fase: "inattivo" }
  | { fase: "in_corso" }
  | { fase: "errore"; messaggio: string }
  | { fase: "completo"; risposta: string; fonti: Risultato[] };

export default function App() {
  const [domanda, setDomanda] = useState("");
  const [stato, setStato] = useState<Stato>({ fase: "inattivo" });

  async function onSubmit(evento: FormEvent) {
    evento.preventDefault();
    const testo = domanda.trim();
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

  return (
    <main className="pagina">
      <h1>ateneo-search</h1>
      <p className="sottotitolo">
        Fai una domanda sui tuoi materiali di corso. La risposta è scritta da
        un LLM locale che legge solo i passaggi recuperati qui sotto — sono
        sempre visibili, verifica sempre contro quelli.
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
          {stato.fase === "in_corso" ? "Penso…" : "Chiedi"}
        </button>
      </form>

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
    </main>
  );
}
