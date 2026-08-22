"""Ricerca vettoriale su un indice SQLite + sqlite-vec.

Punto unico da cui passa ogni ricerca (usato da eval/valuta.py, api/ e
ingestione/indicizzazione.py): tiene la query SQL e le convenzioni di
prefisso specifiche di ciascun modello in un solo posto.
"""

import sqlite3
from pathlib import Path

import sqlite_vec
from sentence_transformers import SentenceTransformer

NOME_MODELLO = "BAAI/bge-m3"

# Alcuni modelli (es. la famiglia E5) richiedono un prefisso testuale
# diverso per query e passage/document; non è nei metadati del modello
# stesso (verificato: anche per e5 i "prompts" di sentence-transformers
# sono vuoti), è solo documentato nella scheda del modello. Lo teniamo
# esplicito qui invece di dimenticarcelo al prossimo modello nuovo.
# Default (bge-m3 compreso): nessun prefisso.
CONVENZIONI_PROMPT: dict[str, dict[str, str]] = {
    "intfloat/multilingual-e5-small": {"query": "query: ", "passage": "passage: "},
}


def prefisso(nome_modello: str, tipo: str) -> str:
    return CONVENZIONI_PROMPT.get(nome_modello, {}).get(tipo, "")


def apri_connessione(percorso_db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(percorso_db)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def leggi_modello(conn: sqlite3.Connection) -> str:
    """Legge il nome del modello di embedding con cui è stato costruito
    l'indice, dalla tabella meta — mai assumerlo fisso: un indice può
    essere stato costruito con un modello diverso da quello di default."""
    riga = conn.execute("select valore from meta where chiave = 'modello'").fetchone()
    if riga is None:
        raise ValueError("indice senza tabella meta: ricostruiscilo con la versione attuale di indicizzazione.py")
    return riga[0]


def cerca(
    conn: sqlite3.Connection,
    modello: SentenceTransformer,
    domanda: str,
    k: int = 5,
) -> list[dict]:
    """Ritorna i k chunk più simili alla domanda, con file e pagine per
    la citazione.

    Ogni risultato: {"file": str, "pagina_inizio": int, "pagina_fine": int,
    "testo": str, "distanza": float} (distanza crescente = meno simile).
    """
    nome_modello = leggi_modello(conn)
    testo_query = prefisso(nome_modello, "query") + domanda
    vettore = modello.encode(testo_query, normalize_embeddings=True)
    righe = conn.execute(
        """
        select c.file, c.pagina_inizio, c.pagina_fine, c.testo, distance
        from chunk_vec
        join chunk c on c.id = chunk_vec.rowid
        where chunk_vec.embedding match ? and k = ?
        order by distance
        """,
        [sqlite_vec.serialize_float32(vettore.tolist()), k],
    ).fetchall()
    return [
        {"file": file, "pagina_inizio": p1, "pagina_fine": p2, "testo": testo, "distanza": dist}
        for file, p1, p2, testo, dist in righe
    ]


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("indice", type=Path)
    parser.add_argument("domanda")
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    conn = apri_connessione(args.indice)
    modello = SentenceTransformer(leggi_modello(conn))
    for r in cerca(conn, modello, args.domanda, args.k):
        print(f"[{r['distanza']:.3f}] {r['file']} p.{r['pagina_inizio']}-{r['pagina_fine']}")
        print(f"  {r['testo'][:150]}")
