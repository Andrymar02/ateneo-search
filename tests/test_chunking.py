"""Test di ingestione.chunking.crea_chunk.

Usa un tokenizer finto (1 token per carattere della parola, non il
vero tokenizer del modello di embedding): la logica di chunking non
dipende dal tokenizer specifico, e un tokenizer finto rende i test
veloci e deterministici, senza scaricare nessun modello.
"""

import pytest

from ingestione.chunking import crea_chunk


class TokenizerFinto:
    """input_ids con un token per carattere: 'abc' -> 3 token."""

    def __call__(self, parole: list[str], add_special_tokens: bool = False) -> dict:
        return {"input_ids": [[0] * max(1, len(p)) for p in parole]}


def pagine_di_prova() -> list[dict]:
    return [
        {"pagina": 1, "testo": "aa bb cc dd ee"},
        {"pagina": 2, "testo": "ff gg hh ii jj"},
        {"pagina": 3, "testo": "kk ll mm nn oo"},
    ]


def test_rispetta_chunk_size():
    chunk = crea_chunk(pagine_di_prova(), TokenizerFinto(), chunk_size=10, overlap=2)
    assert all(c["n_token"] <= 10 for c in chunk)


def test_copre_tutte_le_parole_senza_buchi():
    pagine = pagine_di_prova()
    chunk = crea_chunk(pagine, TokenizerFinto(), chunk_size=10, overlap=2)
    # l'ultima parola dell'ultimo chunk deve essere l'ultima parola del testo
    ultima_parola_testo = pagine[-1]["testo"].split()[-1]
    assert chunk[-1]["testo"].split()[-1] == ultima_parola_testo


def test_overlap_condivide_parole_tra_chunk_consecutivi():
    chunk = crea_chunk(pagine_di_prova(), TokenizerFinto(), chunk_size=10, overlap=4)
    for precedente, successivo in zip(chunk, chunk[1:]):
        parole_precedente = precedente["testo"].split()
        parole_successivo = successivo["testo"].split()
        # almeno l'ultima parola del chunk precedente deve ricomparire
        # all'inizio del chunk successivo
        assert parole_precedente[-1] in parole_successivo[: len(parole_successivo) // 2 + 1]


def test_pagina_inizio_fine_coerenti():
    chunk = crea_chunk(pagine_di_prova(), TokenizerFinto(), chunk_size=6, overlap=1)
    for c in chunk:
        assert 1 <= c["pagina_inizio"] <= c["pagina_fine"] <= 3


def test_pagine_vuote_ritorna_lista_vuota():
    pagine = [{"pagina": 1, "testo": ""}, {"pagina": 2, "testo": "   "}]
    assert crea_chunk(pagine, TokenizerFinto(), chunk_size=10, overlap=2) == []


def test_lista_pagine_vuota():
    assert crea_chunk([], TokenizerFinto(), chunk_size=10, overlap=2) == []


def test_overlap_maggiore_uguale_chunk_size_solleva_errore():
    with pytest.raises(ValueError):
        crea_chunk(pagine_di_prova(), TokenizerFinto(), chunk_size=5, overlap=5)


def test_singola_parola_piu_grande_del_chunk_size_non_si_perde():
    # una parola di 20 caratteri -> 20 token con il tokenizer finto,
    # ben oltre chunk_size=5: deve comunque finire in un chunk da sola,
    # non essere spezzata o scartata.
    pagine = [{"pagina": 1, "testo": "parolamoltolungaventicaratt"}]
    chunk = crea_chunk(pagine, TokenizerFinto(), chunk_size=5, overlap=1)
    assert len(chunk) == 1
    assert chunk[0]["testo"] == "parolamoltolungaventicaratt"
    assert chunk[0]["n_token"] == len("parolamoltolungaventicaratt")


def test_chunk_size_piu_piccolo_produce_piu_chunk():
    grande = crea_chunk(pagine_di_prova(), TokenizerFinto(), chunk_size=10, overlap=2)
    piccolo = crea_chunk(pagine_di_prova(), TokenizerFinto(), chunk_size=4, overlap=1)
    assert len(piccolo) > len(grande)
