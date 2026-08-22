"""Costruisce un indice SQLite + sqlite-vec a partire dai PDF di una cartella.

Ogni chunk viene salvato con file di origine, intervallo di pagine e testo
(per la citazione verificabile) insieme al suo embedding (per la ricerca
vettoriale). La configurazione usata (modello, chunk_size, overlap) viene
scritta nella tabella meta dello stesso file .db, cosi' eval/ la legge
senza doverla dedurre dal nome del file.
"""

import argparse
import sqlite3
from pathlib import Path

import sqlite_vec
from sentence_transformers import SentenceTransformer

from ingestione.chunking import crea_chunk
from ingestione.estrazione_pdf import estrai_pagine

NOME_MODELLO = "intfloat/multilingual-e5-small"


def crea_schema(conn: sqlite3.Connection, dimensione_embedding: int) -> None:
    conn.execute("""
        create table if not exists chunk (
            id integer primary key,
            file text not null,
            pagina_inizio integer not null,
            pagina_fine integer not null,
            testo text not null,
            n_token integer not null
        )
    """)
    conn.execute(f"""
        create virtual table if not exists chunk_vec using vec0(
            embedding float[{dimensione_embedding}]
        )
    """)
    conn.execute("""
        create table if not exists meta (
            chiave text primary key,
            valore text not null
        )
    """)


def salva_meta(conn: sqlite3.Connection, nome_modello: str, chunk_size: int, overlap: int) -> None:
    valori = {
        "modello": nome_modello,
        "chunk_size": str(chunk_size),
        "overlap": str(overlap),
    }
    for chiave, valore in valori.items():
        conn.execute(
            "insert or replace into meta(chiave, valore) values (?, ?)",
            (chiave, valore),
        )


def apri_connessione(percorso_db: Path) -> sqlite3.Connection:
    percorso_db.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(percorso_db)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def indicizza_cartella(
    cartella_pdf: Path,
    percorso_db: Path,
    chunk_size: int,
    overlap: int,
    nome_modello: str = NOME_MODELLO,
) -> None:
    modello = SentenceTransformer(nome_modello)
    conn = apri_connessione(percorso_db)
    crea_schema(conn, modello.get_embedding_dimension())
    salva_meta(conn, nome_modello, chunk_size, overlap)

    pdf_trovati = sorted(cartella_pdf.glob("*.pdf"))
    if not pdf_trovati:
        print(f"nessun PDF trovato in {cartella_pdf}")
        return

    totale_chunk = 0
    for pdf in pdf_trovati:
        pagine = estrai_pagine(pdf)
        chunk = crea_chunk(pagine, modello.tokenizer, chunk_size, overlap)
        if not chunk:
            print(f"{pdf.name}: 0 chunk (nessun testo estratto)")
            continue

        testi_con_prefisso = [f"passage: {c['testo']}" for c in chunk]
        embedding = modello.encode(testi_con_prefisso, normalize_embeddings=True)

        for c, vettore in zip(chunk, embedding):
            cur = conn.execute(
                "insert into chunk(file, pagina_inizio, pagina_fine, testo, n_token) "
                "values (?, ?, ?, ?, ?)",
                (pdf.name, c["pagina_inizio"], c["pagina_fine"], c["testo"], c["n_token"]),
            )
            id_chunk = cur.lastrowid
            conn.execute(
                "insert into chunk_vec(rowid, embedding) values (?, ?)",
                (id_chunk, sqlite_vec.serialize_float32(vettore.tolist())),
            )

        print(f"{pdf.name}: {len(chunk)} chunk indicizzati")
        totale_chunk += len(chunk)

    conn.commit()
    conn.close()
    print(f"totale: {totale_chunk} chunk -> {percorso_db}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cartella_pdf", type=Path, nargs="?", default=Path("data/raw"))
    parser.add_argument("--chunk-size", type=int, default=300)
    parser.add_argument("--overlap", type=int, default=50)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--modello", default=NOME_MODELLO)
    args = parser.parse_args()

    output = args.output or (
        Path("data/index") / f"idx_cs{args.chunk_size}_ov{args.overlap}.db"
    )
    indicizza_cartella(args.cartella_pdf, output, args.chunk_size, args.overlap, args.modello)
