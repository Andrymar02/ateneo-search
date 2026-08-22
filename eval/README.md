# eval/

## domande.jsonl

Una domanda per riga (JSONL), con la fonte corretta attesa:

```json
{"domanda": "...", "file_atteso": "nome_file.pdf", "pagina_attesa": 22}
```

`pagina_attesa` è la pagina del PDF originale dove si trova davvero la
risposta (verificata leggendo il testo estratto, non con la ricerca).
Un chunk conta come "trovato" se il suo file coincide con `file_atteso`
e `pagina_attesa` cade nel suo intervallo `[pagina_inizio, pagina_fine]`
— i chunk possono coprire più pagine, vedi `ingestione/chunking.py`.

Le 14 domande attuali le ho scritte io leggendo direttamente alcune
pagine di 10 file diversi, solo per avere da subito un'infrastruttura
funzionante da testare. **Non sostituiscono le tue domande di ripasso
reali** — anzi, quelle contano di più: aggiungile con lo stesso
formato, una riga alla volta, mentre studi.

## valuta.py

Calcola recall@k: su quante domande la pagina attesa compare tra i
primi k risultati della ricerca vettoriale. Accetta uno o più indici,
utile per confrontare configurazioni diverse:

```bash
python -m eval.valuta data/index/idx_bge-m3_cs300_ov50.db
python -m eval.valuta data/index/idx_bge-m3_cs300_ov50.db data/index/idx_cs300_ov50.db --k 3
```

## Storia dei risultati (dalla diagnosi al fix)

Con le 14 domande attuali, punto di partenza: recall@5 = 50%
(`multilingual-e5-small`, chunk_size=300/overlap=50); 57% provando
chunk_size 150/30 e 500/100. Il chunk size da solo non spiegava gli
errori residui: 3 domande fallivano in **tutte** le configurazioni.

Indagando quelle 3, sono emersi due fenomeni distinti (misurati con
`retrieval/cerca.py`, non ipotizzati):

1. **La lingua della domanda influenzava fortemente la lingua dei
   risultati recuperati.** Stessa domanda sull'I/O in un DBMS, posta
   in italiano vs inglese: il set di file restituiti cambiava lingua
   quasi per intero, anche se il file corretto era in inglese.
2. **Anche a parità di lingua, tra più file che coprono lo stesso
   argomento** (es. più lezioni sugli interni di un DBMS), il modello
   non sempre isolava quello giusto.

**Esperimento 1 — modello più capace.** Passando a `bge-m3` (stesso
chunk_size/overlap): recall@5 50% → **86%**. Confermava che il bias
del punto 1 pesava più del chunk size.

**Bug trovato durante l'esperimento**: il codice applicava il prefisso
`"query: "`/`"passage: "` a ogni modello, ma è una convenzione
specifica di E5 (verificato: `bge-m3` dichiara prompt vuoti — vedi
`retrieval/cerca.py:CONVENZIONI_PROMPT`). Rimuovendolo per `bge-m3`:
recall@5 86% → **93%**.

Resta 1 domanda su 14 ("training set vs test set", terminologia ML
generica ripetuta in più file del corpus): non trovata in top 5, ma
presente in posizione 6 con k=15 — non un fallimento del retrieval,
un caso ambiguo per costruzione (la stessa definizione compare, quasi
identica, in almeno 3 corsi diversi).

Non ancora testato: retrieval ibrido (ricerca vettoriale + parole
chiave via FTS5 di SQLite), utile soprattutto quando la domanda cita
termini esatti del testo originale.
