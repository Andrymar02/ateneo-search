"""Test di retrieval.cerca._query_fts5: la costruzione della query FTS5
dalla domanda è l'unica parte nuova con rischio di rompere la sintassi
SQL/FTS5 (parentesi, apostrofi, punteggiatura nelle domande reali)."""

from retrieval.cerca import _query_fts5


def test_estrae_ed_unisce_le_parole_con_or():
    assert _query_fts5("liste in python") == '"liste" OR "in" OR "python"'


def test_ignora_punteggiatura_e_parentesi():
    # non deve rompersi né includere "(" o ")" come token
    query = _query_fts5("Come si definisce la classificazione (classification)?")
    assert "(" not in query and ")" not in query
    assert '"classification"' in query


def test_apostrofo_non_finisce_nei_token():
    # "Cos'è" -> due parole ("Cos" e "è"), l'apostrofo stesso non deve
    # comparire in un token (romperebbe la sintassi FTS5 tra virgolette)
    query = _query_fts5("Cos'è un iteratore?")
    assert "'" not in query
    assert '"iteratore"' in query


def test_nessuna_parola_ritorna_none():
    assert _query_fts5("???") is None
    assert _query_fts5("") is None
