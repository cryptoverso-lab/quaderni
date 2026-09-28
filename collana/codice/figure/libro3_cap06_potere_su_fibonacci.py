r"""La seconda figura del capitolo 6 del terzo volume — il metro avrebbe visto Fibonacci?

Il paragrafo chiede, prima di chiamare falsificata l'affermazione sul ritracciamento, se la
procedura avrebbe riconosciuto un addensamento vero. La figura porta il controllo di potenza:
serie costruite con una quota nota di cicli che chiude sul 61,8 per cento, passate per la stessa
procedura, cento prove per ogni quota. La curva piena conta le prove in cui la procedura
riconosce il rapporto impiantato; la tratteggiata quelle in cui conferma anche lo 0,786, che nelle
serie non c'e'. La riga orizzontale e' la soglia di potere dichiarata prima, la verticale la quota
minima perche' il rapporto serva come aspettativa.

Da `dati/misure/potenza-quaternario-fibonacci.json` (blocco `a46`).

    uv run python codice/figure/libro3_cap06_potere_su_fibonacci.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
#: La soglia di potere e la quota minima, dichiarate nel criterio della misura e riportate
#: nel testo del capitolo: ottanta prove su cento, un ciclo su cinque.
SOGLIA_DI_POTERE = 80
QUOTA_MINIMA = 0.2


def _dati() -> dict:
    percorso = RADICE / "dati" / "misure" / "potenza-quaternario-fibonacci.json"
    return json.loads(percorso.read_text(encoding="utf-8"))["a46"]


def disegna(schermo: bool = False) -> Path:
    layout.configura(schermo=schermo)
    dati = _dati()
    quote = sorted(dati["rilevazioni_per_intensita"], key=float)
    x = [float(q) for q in quote]
    riconosciuto = [dati["rilevazioni_per_intensita"][q] for q in quote]
    vicino = [dati["livello_adiacente_confermato"][q] for q in quote]

    fig, asse = layout.figura("normale")
    asse.axhline(SOGLIA_DI_POTERE, color=layout.GRIGI[2], linewidth=0.8, linestyle="-.", zorder=1,
                 label=f"potere richiesto, {SOGLIA_DI_POTERE} prove su 100")
    asse.axvline(QUOTA_MINIMA, color=layout.GRIGI[2], linewidth=0.8, linestyle=":", zorder=1,
                 label="quota minima perché il rapporto serva")
    asse.plot(x, riconosciuto, marker="o", markersize=4, label="0,618 riconosciuto (impiantato)",
              **layout.composito(schermo))
    asse.plot(x, vicino, marker="s", markersize=3.6, label="0,786 confermato (non impiantato)",
              **layout.componente(0, schermo))
    asse.set_xlim(-0.02, 0.52)
    asse.set_ylim(-3, 103)
    asse.set_xticks(x)
    asse.set_xlabel("quota di cicli impiantati sul 61,8 per cento", fontsize=8)
    asse.set_ylabel("prove su 100", fontsize=8)
    layout.cornice(asse)
    layout.legenda_figura(fig, asse, ncols=2, fontsize=6.6)

    return layout.salva(
        fig, "cap06_potere_su_fibonacci", libro=3, schermo=schermo,
        fatti={
            "prove_per_quota": dati["repliche_per_intensita"],
            "riconosciuto_per_quota": dict(zip(quote, riconosciuto)),
            "adiacente_per_quota": dict(zip(quote, vicino)),
            "soglia_di_potere": SOGLIA_DI_POTERE,
            "quota_minima": QUOTA_MINIMA,
            "livello_impiantato_per_cento": 61.8,
            "verdetto": dati["verdetto"],
            "file": "dati/misure/potenza-quaternario-fibonacci.json",
        },
    )


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for su_schermo in (False, True):
        print(disegna(schermo=su_schermo))
