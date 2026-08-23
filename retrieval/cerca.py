"""Ricerca vettoriale su un indice SQLite + sqlite-vec.

Punto unico da cui passa ogni ricerca (usato da eval/valuta.py, api/ e
ingestione/indicizzazione.py): tiene la query SQL e le convenzioni di
prefisso specifiche di ciascun modello in un solo posto.
"""

import re
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

    Ogni risultato: {"id": int, "file": str, "pagina_inizio": int,
    "pagina_fine": int, "testo": str, "distanza": float} (distanza
    crescente = meno simile).
    """
    nome_modello = leggi_modello(conn)
    testo_query = prefisso(nome_modello, "query") + domanda
    vettore = modello.encode(testo_query, normalize_embeddings=True)
    righe = conn.execute(
        """
        select c.id, c.file, c.pagina_inizio, c.pagina_fine, c.testo, distance
        from chunk_vec
        join chunk c on c.id = chunk_vec.rowid
        where chunk_vec.embedding match ? and k = ?
        order by distance
        """,
        [sqlite_vec.serialize_float32(vettore.tolist()), k],
    ).fetchall()
    return [
        {"id": id_, "file": file, "pagina_inizio": p1, "pagina_fine": p2, "testo": testo, "distanza": dist}
        for id_, file, p1, p2, testo, dist in righe
    ]


def _query_fts5(domanda: str) -> str | None:
    """Costruisce una query FTS5 dalla domanda: un OR tra le sue parole,
    ognuna tra virgolette (così caratteri speciali FTS5 come "(" o "-"
    non spezzano la sintassi). None se la domanda non contiene nessuna
    parola indicizzabile (es. solo punteggiatura).
    """
    parole = re.findall(r"\w+", domanda, flags=re.UNICODE)
    if not parole:
        return None
    return " OR ".join(f'"{p}"' for p in parole)


def cerca_parole_chiave(conn: sqlite3.Connection, domanda: str, k: int = 5) -> list[dict]:
    """Ricerca per parole chiave (FTS5/BM25), stessa forma di risultato
    di cerca(). Richiede che l'indice sia stato costruito con la tabella
    chunk_fts (vedi ingestione/indicizzazione.py)."""
    query_fts = _query_fts5(domanda)
    if query_fts is None:
        return []
    righe = conn.execute(
        """
        select c.id, c.file, c.pagina_inizio, c.pagina_fine, c.testo, bm25(chunk_fts) as punteggio
        from chunk_fts
        join chunk c on c.id = chunk_fts.rowid
        where chunk_fts match ?
        order by punteggio
        limit ?
        """,
        [query_fts, k],
    ).fetchall()
    return [
        {"id": id_, "file": file, "pagina_inizio": p1, "pagina_fine": p2, "testo": testo, "distanza": punteggio}
        for id_, file, p1, p2, testo, punteggio in righe
    ]


def cerca_ibrida(
    conn: sqlite3.Connection,
    modello: SentenceTransformer,
    domanda: str,
    k: int = 5,
    k_candidati: int = 20,
    costante_rrf: int = 60,
) -> list[dict]:
    """Combina ricerca vettoriale e per parole chiave con Reciprocal Rank
    Fusion: ogni chunk riceve 1/(costante_rrf + posizione) da ciascuna
    classifica in cui compare, poi si sommano i contributi. Non serve
    confrontare punteggi di scale diverse (distanza vettoriale vs BM25),
    conta solo la posizione in ciascuna lista.

    Ogni risultato: come cerca(), ma con "punteggio_rrf" al posto di
    "distanza" (qui più alto = più rilevante, non più basso).
    """
    risultati_vettoriali = cerca(conn, modello, domanda, k_candidati)
    risultati_fts = cerca_parole_chiave(conn, domanda, k_candidati)

    punteggio_rrf: dict[int, float] = {}
    dettagli: dict[int, dict] = {}
    for lista in (risultati_vettoriali, risultati_fts):
        for posizione, r in enumerate(lista, start=1):
            punteggio_rrf[r["id"]] = punteggio_rrf.get(r["id"], 0.0) + 1 / (costante_rrf + posizione)
            dettagli[r["id"]] = r

    id_ordinati = sorted(punteggio_rrf, key=punteggio_rrf.get, reverse=True)[:k]
    return [
        {
            "id": id_,
            "file": dettagli[id_]["file"],
            "pagina_inizio": dettagli[id_]["pagina_inizio"],
            "pagina_fine": dettagli[id_]["pagina_fine"],
            "testo": dettagli[id_]["testo"],
            "punteggio_rrf": punteggio_rrf[id_],
        }
        for id_ in id_ordinati
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
