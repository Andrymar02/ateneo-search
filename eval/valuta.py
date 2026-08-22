"""Valuta la qualita' del retrieval su uno o piu' indici.

Per ogni domanda in eval/domande.jsonl, verifica se la pagina attesa
compare tra i primi k risultati restituiti dall'indice (recall@k): un
chunk conta come "trovato" se il suo file coincide con quello atteso e
la pagina attesa cade nel suo intervallo [pagina_inizio, pagina_fine].

Uso:
    python eval/valuta.py data/index/idx_cs300_ov50.db
    python eval/valuta.py data/index/idx_cs300_ov50.db data/index/idx_cs150_ov30.db --k 3
"""

import argparse
import json
import sqlite3
from pathlib import Path

import sqlite_vec
from sentence_transformers import SentenceTransformer

NOME_MODELLO = "intfloat/multilingual-e5-small"


def carica_domande(percorso: Path) -> list[dict]:
    domande = []
    with open(percorso, encoding="utf-8") as f:
        for riga in f:
            riga = riga.strip()
            if riga:
                domande.append(json.loads(riga))
    return domande


def apri_connessione(percorso_db: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(percorso_db)
    conn.enable_load_extension(True)
    sqlite_vec.load(conn)
    conn.enable_load_extension(False)
    return conn


def cerca(conn: sqlite3.Connection, modello: SentenceTransformer, domanda: str, k: int) -> list[tuple]:
    vettore = modello.encode(f"query: {domanda}", normalize_embeddings=True)
    return conn.execute(
        """
        select c.file, c.pagina_inizio, c.pagina_fine, distance
        from chunk_vec
        join chunk c on c.id = chunk_vec.rowid
        where chunk_vec.embedding match ? and k = ?
        order by distance
        """,
        [sqlite_vec.serialize_float32(vettore.tolist()), k],
    ).fetchall()


def valuta_indice(percorso_db: Path, domande: list[dict], modello: SentenceTransformer, k: int) -> dict:
    conn = apri_connessione(percorso_db)
    dettaglio = []
    for d in domande:
        righe = cerca(conn, modello, d["domanda"], k)
        posizione_trovata = None
        for posizione, (file, p1, p2, _dist) in enumerate(righe, start=1):
            if file == d["file_atteso"] and p1 <= d["pagina_attesa"] <= p2:
                posizione_trovata = posizione
                break
        dettaglio.append({**d, "trovata_in_posizione": posizione_trovata})
    conn.close()

    n_trovate = sum(1 for r in dettaglio if r["trovata_in_posizione"] is not None)
    return {
        "recall@k": n_trovate / len(domande) if domande else 0.0,
        "k": k,
        "n_domande": len(domande),
        "dettaglio": dettaglio,
    }


def stampa_report(percorso_db: Path, report: dict) -> None:
    print(f"\n=== {percorso_db} ===")
    print(f"recall@{report['k']}: {report['recall@k']:.0%}  ({report['n_domande']} domande)")
    for r in report["dettaglio"]:
        if r["trovata_in_posizione"] is not None:
            esito = f"OK  (posizione {r['trovata_in_posizione']})"
        else:
            esito = "MANCA"
        print(f"  [{esito}] {r['domanda']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("indici", type=Path, nargs="+", help="uno o piu' file .db da valutare/confrontare")
    parser.add_argument("--domande", type=Path, default=Path("eval/domande.jsonl"))
    parser.add_argument("--k", type=int, default=5)
    args = parser.parse_args()

    domande = carica_domande(args.domande)
    modello = SentenceTransformer(NOME_MODELLO)

    for percorso_db in args.indici:
        report = valuta_indice(percorso_db, domande, modello, args.k)
        stampa_report(percorso_db, report)
