"""Genera una risposta in linguaggio naturale a partire dai chunk
recuperati da retrieval/cerca.py, usando un LLM locale via Ollama.

Principio non negoziabile del progetto: la citazione resta verificabile
anche con la generazione in mezzo. Il prompt istruisce il modello a
rispondere SOLO dal materiale fornito e a citare la fonte esatta; in
più, l'API (vedi api/main.py) restituisce sempre anche i chunk grezzi
usati, così la risposta generata resta sempre controllabile contro il
testo originale — non lo sostituisce.
"""

import ollama

NOME_MODELLO_LLM = "llama3.1:8b"

PROMPT_SISTEMA = """Sei un assistente che aiuta uno studente a ripassare i suoi materiali di corso.

Rispondi ESCLUSIVAMENTE usando le fonti fornite qui sotto, estratte dai suoi PDF di corso. Non usare conoscenza esterna, anche se la conosci: se le fonti non bastano a rispondere, dillo chiaramente ("Il materiale fornito non contiene questa informazione") invece di completare con conoscenza generale.

Quando usi un'informazione, indica tra parentesi quadre la fonte esatta, es. [FONTE 2]. Rispondi in italiano, in modo conciso e diretto."""


def _intervallo_pagine(risultato: dict) -> str:
    if risultato["pagina_inizio"] == risultato["pagina_fine"]:
        return f"p.{risultato['pagina_inizio']}"
    return f"p.{risultato['pagina_inizio']}-{risultato['pagina_fine']}"


def costruisci_contesto(risultati: list[dict]) -> str:
    blocchi = [
        f"[FONTE {i}: {r['file']}, {_intervallo_pagine(r)}]\n{r['testo']}"
        for i, r in enumerate(risultati, start=1)
    ]
    return "\n\n".join(blocchi)


def genera_risposta(domanda: str, risultati: list[dict]) -> str:
    """risultati: output di retrieval.cerca.cerca() o cerca_ibrida()."""
    if not risultati:
        return "Non ho trovato materiale pertinente a questa domanda nell'indice."

    contesto = costruisci_contesto(risultati)
    risposta = ollama.chat(
        model=NOME_MODELLO_LLM,
        messages=[
            {"role": "system", "content": PROMPT_SISTEMA},
            {"role": "user", "content": f"FONTI:\n\n{contesto}\n\nDOMANDA: {domanda}"},
        ],
    )
    return risposta["message"]["content"]


if __name__ == "__main__":
    import argparse
    from pathlib import Path

    from sentence_transformers import SentenceTransformer

    from retrieval.cerca import apri_connessione, cerca, leggi_modello

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("indice", type=Path)
    parser.add_argument("domanda")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    conn = apri_connessione(args.indice)
    modello = SentenceTransformer(leggi_modello(conn))
    risultati = cerca(conn, modello, args.domanda, args.k)

    print("--- fonti usate ---")
    for i, r in enumerate(risultati, start=1):
        print(f"[FONTE {i}] {r['file']} {_intervallo_pagine(r)}")

    print("\n--- risposta ---")
    print(genera_risposta(args.domanda, risultati))
