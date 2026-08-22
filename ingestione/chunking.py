"""Suddivisione del testo estratto in chunk, con dimensione e overlap
espressi in token (non caratteri) del tokenizer del modello di embedding.

Le pagine di slide sono spesso troppo corte per raggiungere da sole una
chunk_size utile: un chunk puo' quindi nascere dall'unione di piu' pagine
consecutive. Per questo ogni chunk riporta pagina_inizio e pagina_fine
invece di un singolo numero di pagina: la citazione resta verificabile
anche quando il chunk copre un intervallo di pagine.
"""


def crea_chunk(pagine: list[dict], tokenizer, chunk_size: int, overlap: int) -> list[dict]:
    """Divide il testo di piu' pagine in chunk da circa chunk_size token,
    con overlap token condivisi tra un chunk e il successivo.

    pagine: output di estrai_pagine() -> [{"pagina": int, "testo": str}, ...]
    tokenizer: il tokenizer del modello di embedding (es. modello.tokenizer
        di un SentenceTransformer), usato solo per contare i token, non
        per ricostruire il testo.

    Ritorna una lista di dict:
    {"testo": str, "pagina_inizio": int, "pagina_fine": int, "n_token": int}
    """
    if overlap >= chunk_size:
        raise ValueError("overlap deve essere minore di chunk_size")

    parole: list[str] = []
    pagina_di: list[int] = []
    for p in pagine:
        for parola in p["testo"].split():
            parole.append(parola)
            pagina_di.append(p["pagina"])

    if not parole:
        return []

    # conteggio dei token per parola in un'unica chiamata batch (molto
    # piu' veloce che tokenizzare parola per parola su documenti lunghi)
    n_token_parola = [
        len(ids) for ids in tokenizer(parole, add_special_tokens=False)["input_ids"]
    ]
    prefisso = [0]
    for nt in n_token_parola:
        prefisso.append(prefisso[-1] + nt)

    chunk = []
    n = len(parole)
    inizio = 0
    while inizio < n:
        fine = inizio + 1
        while fine < n and prefisso[fine + 1] - prefisso[inizio] <= chunk_size:
            fine += 1
        chunk.append({
            "testo": " ".join(parole[inizio:fine]),
            "pagina_inizio": pagina_di[inizio],
            "pagina_fine": pagina_di[fine - 1],
            "n_token": prefisso[fine] - prefisso[inizio],
        })
        if fine >= n:
            break

        # il prossimo chunk riparte piu' indietro di 'overlap' token,
        # senza mai tornare prima di 'inizio' (garantisce progresso)
        nuovo_inizio = fine
        while nuovo_inizio > inizio + 1 and prefisso[fine] - prefisso[nuovo_inizio - 1] <= overlap:
            nuovo_inizio -= 1
        inizio = nuovo_inizio

    return chunk


if __name__ == "__main__":
    import sys
    from pathlib import Path

    from sentence_transformers import SentenceTransformer

    from ingestione.estrazione_pdf import estrai_pagine

    percorso = Path(sys.argv[1])
    chunk_size = int(sys.argv[2]) if len(sys.argv) > 2 else 200
    overlap = int(sys.argv[3]) if len(sys.argv) > 3 else 40

    modello = SentenceTransformer("intfloat/multilingual-e5-small")
    pagine = estrai_pagine(percorso)
    chunk = crea_chunk(pagine, modello.tokenizer, chunk_size, overlap)

    print(f"{len(pagine)} pagine -> {len(chunk)} chunk (chunk_size={chunk_size}, overlap={overlap})")
    for c in chunk[:5]:
        print(f"--- pagine {c['pagina_inizio']}-{c['pagina_fine']} ({c['n_token']} token) ---")
        print(c["testo"][:200])
        print()
