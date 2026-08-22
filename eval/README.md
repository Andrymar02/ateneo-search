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
python -m eval.valuta data/index/idx_cs300_ov50.db
python -m eval.valuta data/index/idx_cs150_ov30.db data/index/idx_cs500_ov100.db --k 3
```

## Risultati iniziali e limiti osservati

Con le 14 domande attuali, recall@5: 50% (chunk_size=300/overlap=50),
57% (150/30 e 500/100). Il chunk size da solo non spiega gli errori
residui: 3 domande falliscono in **tutte** le configurazioni provate.

Indagando quelle 3, emergono due fenomeni distinti (non ipotesi, dati
misurati riproducibili con `retrieval/cerca.py`):

1. **La lingua della domanda influenza fortemente la lingua dei
   risultati recuperati.** Stessa domanda sull'I/O in un DBMS, posta
   in italiano vs inglese: il set di file restituiti cambia lingua
   quasi per intero, anche se il file corretto è in inglese.
2. **Anche a parità di lingua, tra più file che coprono lo stesso
   argomento (es. più lezioni sugli interni di un DBMS), il modello
   non sempre isola quello giusto** — probabile quando il concetto
   cercato è menzionato di sfuggita in un file introduttivo, tra
   diversi che trattano argomenti adiacenti.

Non ancora testato, candidati per un prossimo esperimento (misurabile
con lo stesso `valuta.py`, confrontando i numeri prima/dopo):
- modello di embedding più capace (`bge-m3`, scartato all'inizio per
  peso/velocità, ma da riconsiderare se la qualità resta un collo di
  bottiglia);
- retrieval ibrido: combinare ricerca vettoriale con una ricerca per
  parole chiave (es. FTS5 di SQLite), che non soffrirebbe del bias
  linguistico dell'embedding.
