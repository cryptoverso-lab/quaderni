"""Tre famiglie di rilevatori, la stessa serie, tre risposte diverse.

Il capitolo 5 del libro 1 sostiene che un ciclo non e' un oggetto che sta nella
serie: e' **un'etichetta assegnata da una procedura**. La dimostrazione che il
capitolo porta cambia un parametro di un rilevatore solo. Questa misura fa la
cosa piu' severa: cambia **famiglia**, e confronta le tre che il capitolo
descrive, ciascuna al proprio meglio e sullo stesso periodo.

1. **a soglia** — la segmentazione per inversione percentuale (ZigZag, e la
   famiglia di Bry-Boschan): un estremo e' definitivo quando il prezzo si e'
   mosso in senso contrario di almeno una quota dichiarata;
2. **a finestra** — il punto piu' basso in una finestra centrata di mezzo
   periodo, che e' la regola usata dalla figura dell'anatomia del ciclo;
3. **a banda** — filtro passa-banda di Butterworth attorno al periodo
   interrogato, poi i minimi del segnale filtrato: e' l'impostazione del DSP.

Il filtro e' applicato in **avanti e indietro** (`filtfilt`), che e' la prassi
del DSP per non introdurre ritardo di fase. **Guarda il futuro**, e va detto: qui
serve a rappresentare la famiglia nel modo in cui la famiglia si presenta, non a
produrre un segnale operativo. Nessun numero di questa misura entra in una regola
che opera nel tempo.

Si contano i minimi che ciascuna produce e **quanti coincidono**: due minimi sono
lo stesso minimo se distano meno di un decimo del periodo interrogato.

**L'accordo si riporta nei due versi**, e non e' pedanteria. Il rilevatore a
soglia produce cinque volte i minimi di quello a finestra: chiedersi quanti
minimi a finestra abbiano un vicino fra quelli a soglia da' il cento per cento
per costruzione, ed e' una misura della **cardinalita'**, non dell'accordo. Il
verso opposto — quanti minimi a soglia trovino un vicino fra quelli a finestra —
racconta la storia vera, e i due numeri insieme dicono che cosa e' successo.

    uv run python codice/verifica/tre_rilevatori.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from scipy.signal import butter, filtfilt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook.movimenti import movimenti  # noqa: E402
from acbook.surrogati import NOMI, NOMINALI, chiusure, minimi  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
ESITO = RADICE / "dati" / "misure" / "tre-rilevatori.json"

#: Soglia di inversione del rilevatore a soglia, per livello: la quota che il
#: capitolo 4 usa (5%) scalata sulla radice del periodo, perche' un movimento di
#: un livello lungo e' piu' ampio di uno breve. Dichiarata prima della misura.
def _soglia_di(periodo: int) -> float:
    return 0.05 * float(np.sqrt(periodo / 45.0))

#: Ampiezza della banda del filtro, in ottave attorno al periodo. Mezza ottava
#: per lato e' la scelta di Ehlers per il roofing filter.
BANDA = 0.5

#: Due minimi sono lo stesso minimo entro questa frazione del periodo.
VICINANZA = 0.10


def _a_banda(serie: np.ndarray, periodo: int) -> np.ndarray:
    """Minimi del segnale filtrato attorno al periodo interrogato."""
    basso = 2.0 / (periodo * 2 ** BANDA)
    alto = min(0.95, 2.0 / (periodo / 2 ** BANDA))
    b, a = butter(2, (basso, alto), btype="bandpass")
    filtrato = filtfilt(b, a, serie - serie.mean())
    return minimi(filtrato, periodo)


def _accordo(uno: np.ndarray, due: np.ndarray, periodo: int) -> int:
    """Quanti minimi di `uno` hanno un minimo di `due` entro la vicinanza."""
    if len(uno) == 0 or len(due) == 0:
        return 0
    raggio = max(1, int(round(VICINANZA * periodo)))
    return int(sum(np.min(np.abs(due - i)) <= raggio for i in uno))


def misura(simbolo: str, livello: str, periodo: int) -> dict:
    serie = chiusure(simbolo)
    soglia = _soglia_di(periodo)
    estremi = movimenti(np.exp(serie), soglia=soglia)
    # I movimenti alternano salita e discesa: sono minimi solo gli inizi delle salite.
    a_soglia = np.array([a for a, b in estremi if serie[b] > serie[a]], dtype=int)
    a_finestra = minimi(serie, periodo)
    a_banda = _a_banda(serie, periodo)

    conteggi = {"a soglia": len(a_soglia), "a finestra": len(a_finestra),
                "a banda": len(a_banda)}
    coppie = {}
    for nome_a, dati_a in (("a soglia", a_soglia), ("a finestra", a_finestra),
                           ("a banda", a_banda)):
        for nome_b, dati_b in (("a soglia", a_soglia), ("a finestra", a_finestra),
                               ("a banda", a_banda)):
            if nome_a >= nome_b:
                continue
            coppie[f"{nome_a} / {nome_b}"] = {
                "comuni_dal_primo": _accordo(dati_a, dati_b, periodo),
                "comuni_dal_secondo": _accordo(dati_b, dati_a, periodo),
                "quota_sul_primo_pct": round(
                    _accordo(dati_a, dati_b, periodo) / max(len(dati_a), 1) * 100, 2),
                "quota_sul_secondo_pct": round(
                    _accordo(dati_b, dati_a, periodo) / max(len(dati_b), 1) * 100, 2),
            }
    return {"asset": NOMI[simbolo], "livello": livello, "periodo_barre": periodo,
            "soglia_inversione": round(soglia, 4), "conteggi": conteggi,
            "accordo": coppie}


def main() -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    righe = [misura(s, liv, per)
             for s in NOMI
             for liv, per in NOMINALI.items() if liv in ("T+1", "T+2", "T+3")]
    ESITO.write_text(json.dumps(
        {"snapshot": "2026-06-15", "vicinanza_frazione_periodo": VICINANZA,
         "banda_ottave": BANDA, "righe": righe},
        indent=2, ensure_ascii=False), encoding="utf-8")
    for r in righe:
        c = r["conteggi"]
        print(f"{r['asset']:10s} {r['livello']:4s} "
              f"soglia {c['a soglia']:4d}  finestra {c['a finestra']:4d}  "
              f"banda {c['a banda']:4d}   "
              + "  ".join(f"{k}: {v['quota_sul_primo_pct']:.0f}/"
                          f"{v['quota_sul_secondo_pct']:.0f}%"
                          for k, v in r["accordo"].items()))
    print(f"\nscritto {ESITO.relative_to(RADICE)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
