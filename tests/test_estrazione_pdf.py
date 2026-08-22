"""Test di ingestione.estrazione_pdf.estrai_pagine.

Il PDF di prova viene generato al volo con fpdf2 in una cartella
temporanea (pytest tmp_path): niente binari committati nel repo, e il
fixture resta riproducibile per chiunque clona il progetto.
"""

from pathlib import Path

import pytest
from fpdf import FPDF

from ingestione.estrazione_pdf import estrai_pagine


@pytest.fixture
def pdf_di_prova(tmp_path: Path) -> Path:
    pdf = FPDF()
    for testo in ["Prima pagina di prova", "Seconda pagina di prova", "Terza pagina di prova"]:
        pdf.add_page()
        pdf.set_font("Helvetica", size=14)
        pdf.cell(0, 10, testo)

    percorso = tmp_path / "prova.pdf"
    pdf.output(str(percorso))
    return percorso


def test_numero_pagine(pdf_di_prova: Path):
    pagine = estrai_pagine(pdf_di_prova)
    assert len(pagine) == 3


def test_numerazione_pagine_1_indicizzata(pdf_di_prova: Path):
    pagine = estrai_pagine(pdf_di_prova)
    assert [p["pagina"] for p in pagine] == [1, 2, 3]


def test_testo_estratto_corretto_per_pagina(pdf_di_prova: Path):
    pagine = estrai_pagine(pdf_di_prova)
    assert "Prima pagina" in pagine[0]["testo"]
    assert "Seconda pagina" in pagine[1]["testo"]
    assert "Terza pagina" in pagine[2]["testo"]


def test_parole_non_incollate(pdf_di_prova: Path):
    # regressione sul fix di x_tolerance: le parole non devono essere
    # unite senza spazio (es. "Primapagina" invece di "Prima pagina")
    pagine = estrai_pagine(pdf_di_prova)
    assert "Primapagina" not in pagine[0]["testo"]
