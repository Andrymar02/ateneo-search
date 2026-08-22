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
