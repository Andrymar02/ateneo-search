"""Estrazione del testo dai PDF, pagina per pagina.

Ogni pagina viene mantenuta separata (invece di concatenare tutto il
documento in un unico blocco) perche' e' da qui che nascera' la
citazione verificabile: file + numero di pagina per ogni risposta.
"""

from pathlib import Path

import pdfplumber


def estrai_pagine(percorso_pdf: Path, x_tolerance: float = 1.5) -> list[dict]:
    """Estrae il testo di un PDF, una pagina alla volta.

    Ritorna una lista di dict {"pagina": int, "testo": str}.
    Il numero di pagina e' 1-indicizzato e corrisponde alla posizione
    del foglio nel file PDF (non necessariamente al numero stampato
    sul foglio, se il documento ha frontespizi non numerati).

    x_tolerance=1.5 (invece del default 3 di pdfplumber) evita che
    parole adiacenti nelle slide LaTeX/Beamer vengano incollate senza
    spazio (es. "SandroCumani" invece di "Sandro Cumani"): verificato
    su piu' file reali senza effetti collaterali di segno opposto
    (parole spezzate a meta').

    Nota: pagine con formule matematiche possono comunque contenere
    glifi non mappati a Unicode (appaiono come "(cid:NN)") o ordine di
    apici/pedici alterato: e' un limite del font del PDF sorgente, non
    di questa funzione. La citazione (file + pagina) resta corretta.
    """
    pagine = []
    with pdfplumber.open(percorso_pdf) as pdf:
        for indice, pagina in enumerate(pdf.pages, start=1):
            testo = pagina.extract_text(x_tolerance=x_tolerance) or ""
            pagine.append({"pagina": indice, "testo": testo})
    return pagine


if __name__ == "__main__":
    import sys

    percorso = Path(sys.argv[1])
    for p in estrai_pagine(percorso):
        print(f"--- pagina {p['pagina']} ---")
        print(p["testo"])
        print()
