# tests/

Test automatici (pytest) per `ingestione` e `retrieval`. Non scaricano
nessun modello: usano un tokenizer finto (per il chunking) e PDF
generati al volo con `fpdf2` (per l'estrazione), quindi girano in
meno di un secondo e non servono i pesi di sentence-transformers.

Setup e uso:
```bash
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest tests/ -v
```
