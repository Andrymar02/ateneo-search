# ateneo-search

Un sistema RAG (retrieval-augmented) che indicizza materiali universitari
(PDF, slide) e risponde a domande recuperando i passaggi più pertinenti,
**citando sempre file e pagina di origine**. Nessuna generazione di testo:
la risposta è il contenuto reale del PDF, non una riscrittura — la
citazione è quindi sempre verificabile, per costruzione.

Progetto personale per il mio portfolio (Ingegneria Informatica, AI e Data
Analytics, Politecnico di Torino). Gira interamente in locale: nessuna
chiave API, nessun servizio esterno.

## Stack

- **pdfplumber** — estrazione del testo dai PDF, pagina per pagina
- **sentence-transformers** (`intfloat/multilingual-e5-small`) — embedding, in locale
- **SQLite + sqlite-vec** — indice vettoriale, un file per configurazione testata
- **FastAPI** — API di ricerca
- **React** — interfaccia (ultimo pezzo, non ancora fatto)

## Struttura

```
ingestione/          estrazione PDF, chunking, indicizzazione
retrieval/            ricerca vettoriale (unico punto di verità, riusato da eval/ e api/)
api/                  API FastAPI (GET /cerca)
eval/                 domande con fonte attesa + script di misura del recall
tests/                test automatici (pytest) su chunking ed estrazione
data/                 PDF originali e indici generati — MAI versionati (vedi sotto)
```

## Setup

```bash
python3 -m venv .venv --upgrade-deps
source .venv/bin/activate
pip install -r requirements.txt          # pipeline
pip install -r requirements-dev.txt       # + test automatici
```

Richiede un Python il cui modulo `sqlite3` supporti il caricamento di
estensioni (`enable_load_extension`), necessario per sqlite-vec: il
Python di sistema di Apple (Command Line Tools) **non** lo supporta.

## Uso

```bash
# 1. metti i tuoi PDF in data/raw/ (cartella ignorata da git)

# 2. costruisci un indice (un file .db per ogni configurazione testata)
python -m ingestione.indicizzazione data/raw --chunk-size 300 --overlap 50

# 3. avvia l'API
cp .env.example .env   # personalizza INDICE_DB se serve
uvicorn api.main:app --reload

# 4. interroga
curl "http://127.0.0.1:8000/cerca?domanda=cosa+sono+le+liste+in+python&k=5"
```

## Valutazione

`eval/` è la parte centrale del progetto, non un extra: misura quante
volte il sistema recupera davvero la pagina giusta (recall@k), e
permette di confrontare configurazioni diverse con numeri, non a
sensazione.

```bash
python -m eval.valuta data/index/idx_cs300_ov50.db
python -m eval.valuta data/index/idx_cs150_ov30.db data/index/idx_cs500_ov100.db --k 3
```

Stato attuale: recall@5 tra 50% e 57% a seconda della configurazione,
su un set iniziale di 14 domande. Limiti misurati (non presunti) sono
documentati in [`eval/README.md`](eval/README.md), insieme ai prossimi
esperimenti candidati.

## Materiali e copyright

I PDF dei corsi sono materiale protetto da copyright e **non vengono
mai committati**: `data/` è nel `.gitignore` nella sua interezza, PDF
originali compresi indici generati. Chi clona questo repo deve
procurarsi (e indicizzare) i propri materiali.

## Licenza

MIT — vedi [`LICENSE`](LICENSE). Si applica al codice, non ai materiali
didattici eventualmente indicizzati in locale.
