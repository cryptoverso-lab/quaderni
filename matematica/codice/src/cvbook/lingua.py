"""Lingua attiva del progetto — supporto bilingue italiano/inglese.

Il libro e le sue figure restano italiani per default: nessuna variabile
d'ambiente impostata equivale a `it`, e l'output non cambia di un pixel
rispetto a prima. Chi clona la repository da fuori Italia puo' pero' chiedere
`CVBOOK_LANG=en` e vedere le stesse figure, calcolatori e quaderni con le
etichette in inglese — utile per una repo pubblica e internazionale.
"""

from __future__ import annotations

import os
from pathlib import Path

#: Valori ammessi. Qualunque altra cosa (typo, lingua non supportata, variabile
#: vuota) ricade silenziosamente su "it": una build non deve rompersi per una
#: variabile d'ambiente scritta male.
_LINGUE_AMMESSE = {"it", "en"}

#: Cartella del progetto Quarto inglese. Quarto esegue i pre-render con la directory
#: corrente uguale alla radice del progetto: se quella radice e' `en/`, la lingua **e'**
#: l'inglese, anche quando nessuno ha impostato la variabile. Senza questa deduzione un
#: `quarto render` lanciato dentro `en/` a mani nude avrebbe riscritto il colophon e la
#: pagina dei diritti **dell'edizione italiana**, in silenzio e con dentro i numeri
#: dell'inglese. La variabile d'ambiente resta e vince: serve a rendere le figure e a
#: forzare la lingua da fuori.
_CARTELLA_INGLESE = "en"


def _leggi_lingua() -> str:
    grezza = os.environ.get("CVBOOK_LANG", "").strip().lower()
    if grezza in _LINGUE_AMMESSE:
        return grezza
    try:
        if Path.cwd().name == _CARTELLA_INGLESE:
            return "en"
    except OSError:  # directory corrente sparita sotto i piedi: non e' un motivo per cadere
        pass
    return "it"


#: Letta una volta all'importazione del modulo. E' cosi' che la usano tutte le
#: figure e i calcolatori: cambiarla a runtime richiede reimportare il modulo,
#: che e' esattamente cio' che succede a ogni esecuzione di uno script o di una
#: cella di un notebook.
LINGUA = _leggi_lingua()


def t(it: str, en: str) -> str:
    """Restituisce `it` o `en` a seconda della lingua attiva.

    Il default resta l'italiano: se `CVBOOK_LANG` non e' impostata, `t()` si
    comporta come l'identita' su `it` e nessuna figura del libro cambia.
    """
    return en if LINGUA == "en" else it
