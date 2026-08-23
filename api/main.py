"""API di ricerca su ateneo-search.

Nessuna generazione di testo: ogni risultato è un chunk reale, con la
sua fonte esatta (file + intervallo di pagine). Niente da verificare
sul fatto che la risposta sia "inventata" — è testo del PDF originale.
"""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer

from retrieval.cerca import apri_connessione, cerca, leggi_modello

load_dotenv()

PERCORSO_INDICE = Path(os.getenv("INDICE_DB", "data/index/idx_bge-m3_cs300_ov50.db"))
ORIGINE_FRONTEND = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")

stato: dict = {}


@asynccontextmanager
async def ciclo_vita(app: FastAPI):
    if not PERCORSO_INDICE.exists():
        raise RuntimeError(
            f"Indice non trovato: {PERCORSO_INDICE}. "
            "Costruiscilo con: python -m ingestione.indicizzazione"
        )
    conn = apri_connessione(PERCORSO_INDICE)
    nome_modello = leggi_modello(conn)
    conn.close()
    stato["modello"] = SentenceTransformer(nome_modello)
    yield
    stato.clear()


app = FastAPI(title="ateneo-search", lifespan=ciclo_vita)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[ORIGINE_FRONTEND],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/cerca")
def endpoint_cerca(domanda: str, k: int = 5) -> list[dict]:
    if not domanda.strip():
        raise HTTPException(status_code=400, detail="domanda vuota")

    conn = apri_connessione(PERCORSO_INDICE)
    try:
        return cerca(conn, stato["modello"], domanda, k)
    finally:
        conn.close()
