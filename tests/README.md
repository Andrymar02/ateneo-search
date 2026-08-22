# tests/

Test automatici (pytest) per `ingestione` e `retrieval`. Non scaricano
nessun modello: usano un tokenizer finto (per il chunking) e PDF
generati al volo con `fpdf2` (per l'estrazione), quindi girano in
meno di un secondo e non servono i pesi di sentence-transformers.

Setup e uso:
```bash
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m pytest tests/ -v
```

Percorso esplicito (`.venv/bin/python -m ...`) invece di `source
.venv/bin/activate` + comando nudo: se conda è installato e attivo
(`(base)` nel prompt), il suo hook di shell può reinserirsi davanti al
venv nel `PATH` anche dopo l'activate, facendo eseguire `pytest`/`pip`
di conda invece che quelli del venv — capita in silenzio, senza errore
di attivazione. Il percorso esplicito lo evita del tutto.
