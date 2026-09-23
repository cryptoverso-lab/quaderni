"""Le due coordinate di un movimento — ampiezza e durata — e il ruolo del volume.

Un movimento si descrive con due numeri: quanto si e' spostato il prezzo e quanto
a lungo ci ha messo. Il volume e' la terza colonna che ogni piattaforma mostra, e
la domanda del capitolo 4 e' se sia una terza coordinata o il riflesso delle prime
due e del calendario.

Il nucleo di questo modulo viene dal lavoro svolto per *La matematica di chi perde*, dove
la stessa misura era presentata in forma divulgativa. Qui e' ripreso con la
notazione e i controlli che servono a un libro con le formule.

Nessuna funzione guarda avanti tranne la segmentazione, che per costruzione
riconosce un estremo solo dopo l'inversione: descrive movimenti conclusi, non
produce segnali.
"""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

import numpy as np

#: Soglia di inversione di riferimento. Le conclusioni vanno verificate su tutta
#: la fascia dichiarata nel capitolo, non su questo solo valore.
SOGLIA = 0.05

#: Finestra su cui si normalizza il volume, in barre. Serve a confrontare un
#: giorno del 2003 con uno del 2025 senza farsi ingannare dalla crescita del
#: mercato.
FINESTRA_VOLUME = 250


def movimenti(chiusure: np.ndarray, soglia: float = SOGLIA) -> list[tuple[int, int]]:
    """Segmenta la serie in movimenti alternati fra estremi successivi.

    Un estremo diventa definitivo quando il prezzo si e' allontanato di almeno
    `soglia` in logaritmo nella direzione opposta.
    """
    lp = np.log(np.asarray(chiusure, dtype=float))
    estremi = [0]
    direzione = 0
    alto_i = basso_i = 0
    alto = basso = lp[0]

    for i in range(1, len(lp)):
        x = lp[i]
        if x > alto:
            alto, alto_i = x, i
        if x < basso:
            basso, basso_i = x, i
        if direzione >= 0 and alto - x >= soglia:
            estremi.append(alto_i)
            direzione = -1
            k = int(np.argmin(lp[alto_i : i + 1])) + alto_i
            basso, basso_i = lp[k], k
            alto, alto_i = x, i
        elif direzione <= 0 and x - basso >= soglia:
            estremi.append(basso_i)
            direzione = +1
            k = int(np.argmax(lp[basso_i : i + 1])) + basso_i
            alto, alto_i = lp[k], k
            basso, basso_i = x, i

    estremi = sorted(set(estremi))
    return [(estremi[k], estremi[k + 1]) for k in range(len(estremi) - 1)]


def volume_relativo(volume: np.ndarray, finestra: int = FINESTRA_VOLUME) -> np.ndarray:
    """Volume diviso per la propria mediana delle barre precedenti. Causale."""
    v = np.asarray(volume, dtype=float)
    fuori = np.full(len(v), np.nan)
    for i in range(finestra, len(v)):
        mediana = np.median(v[i - finestra : i])
        if mediana > 0:
            fuori[i] = v[i] / mediana
    return fuori


@dataclass(frozen=True)
class Tavolo:
    """Un movimento per riga, tre colonne misurate sulla stessa finestra."""

    ampiezza: np.ndarray  # |variazione logaritmica| fra i due estremi
    durata: np.ndarray    # barre fra i due estremi
    prezzo: np.ndarray    # deviazione standard dei rendimenti del tratto
    volume: np.ndarray    # volume relativo medio del tratto
    inizio: np.ndarray    # indice di barra del primo estremo
    fine: np.ndarray      # indice di barra del secondo estremo

    def __len__(self) -> int:
        return len(self.ampiezza)


def tavolo(
    chiusure: np.ndarray,
    volume: np.ndarray,
    soglia: float = SOGLIA,
    durata_minima: int = 3,
    relativo: np.ndarray | None = None,
) -> Tavolo:
    """Costruisce il tavolo dei movimenti conclusi.

    Le tre colonne sono misurate sulla stessa finestra e con lo stesso
    trattamento: e' cio' che rende leale il confronto.

    `relativo` permette di sostituire il volume relativo con una versione gia'
    calcolata — serve al controllo di calendario, che usa il volume ripulito
    dagli effetti di giorno e di mese.
    """
    c = np.asarray(chiusure, dtype=float)
    r = np.diff(np.log(c), prepend=np.nan)
    vrel = volume_relativo(volume) if relativo is None else np.asarray(relativo, float)

    righe = []
    for a, b in movimenti(c, soglia):
        if a < FINESTRA_VOLUME + 10 or b - a < durata_minima:
            continue
        ampiezza = abs(math.log(c[b] / c[a]))
        sigma = float(np.std(r[a + 1 : b + 1], ddof=1))
        tratto = vrel[a + 1 : b + 1]
        tratto = tratto[np.isfinite(tratto)]
        medio = float(tratto.mean()) if len(tratto) else float("nan")
        if ampiezza > 0 and sigma > 0 and np.isfinite(medio) and medio > 0:
            righe.append((ampiezza, b - a, sigma, medio, a, b))

    dati = np.array(righe, dtype=float).reshape(-1, 6)
    return Tavolo(
        dati[:, 0], dati[:, 1], dati[:, 2], dati[:, 3],
        dati[:, 4].astype(int), dati[:, 5].astype(int),
    )


def r_quadro(y: np.ndarray, regressori: list[np.ndarray]) -> float:
    """R quadro di una regressione lineare con intercetta."""
    y = np.asarray(y, dtype=float)
    if not regressori:
        return 0.0
    X = np.column_stack([np.ones(len(y))] + [np.asarray(c, float) for c in regressori])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    residui = y - X @ beta
    scarto = y - y.mean()
    return float(1.0 - residui @ residui / (scarto @ scarto))


def shapley(y: np.ndarray, blocchi: dict[str, list[np.ndarray]]) -> dict[str, float]:
    """Ripartisce l'R quadro fra blocchi di variabili, su tutti gli ordini."""
    nomi = list(blocchi)
    k = len(nomi)
    memoria: dict[tuple[str, ...], float] = {}

    def R(sottoinsieme) -> float:
        chiave = tuple(sorted(sottoinsieme))
        if chiave not in memoria:
            colonne = [c for nome in chiave for c in blocchi[nome]]
            memoria[chiave] = r_quadro(y, colonne)
        return memoria[chiave]

    quote = {nome: 0.0 for nome in nomi}
    for nome in nomi:
        altri = [x for x in nomi if x != nome]
        for r in range(k):
            for combinazione in itertools.combinations(altri, r):
                peso = math.factorial(r) * math.factorial(k - r - 1) / math.factorial(k)
                quote[nome] += peso * (R(list(combinazione) + [nome]) - R(combinazione))
    return quote


def decomposizione(t: Tavolo) -> dict[str, float]:
    """Quanto spiegano prezzo, tempo e volume dell'ampiezza di un movimento."""
    y = np.log(t.ampiezza)
    prezzo, tempo, volume = np.log(t.prezzo), np.log(t.durata), np.log(t.volume)
    quote = shapley(y, {"prezzo": [prezzo], "tempo": [tempo], "volume": [volume]})
    con_volume = r_quadro(y, [prezzo, tempo, volume])
    senza_volume = r_quadro(y, [prezzo, tempo])
    return {
        "movimenti": len(t),
        "prezzo": quote["prezzo"],
        "tempo": quote["tempo"],
        "volume": quote["volume"],
        "totale": con_volume,
        "prezzo_e_tempo": senza_volume,
        "guadagno_volume": con_volume - senza_volume,
        "quota_prezzo_e_tempo": senza_volume / con_volume,
    }


def dispersioni(t: Tavolo) -> dict[str, float]:
    """Quanto varia ciascuna colonna, sulla scala su cui entra nella misura.

    Serve a rispondere alla domanda che il risultato solleva: una colonna pesa
    di piu' anche perche' nel campione varia di piu'.
    """
    return {
        "prezzo": float(np.std(np.log(t.prezzo), ddof=1)),
        "tempo": float(np.std(np.log(t.durata), ddof=1)),
        "volume": float(np.std(np.log(t.volume), ddof=1)),
    }


def elasticita(t: Tavolo) -> dict[str, float]:
    """Coefficienti della regressione di log-ampiezza sulle tre colonne.

    Sotto passeggiata casuale l'ampiezza attesa vale $\\sigma \\sqrt{D}$: gli
    esponenti da confrontare sono 1 per la volatilita' e 1/2 per la durata.
    """
    y = np.log(t.ampiezza)
    X = np.column_stack(
        [np.ones(len(y)), np.log(t.prezzo), np.log(t.durata), np.log(t.volume)]
    )
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    return {
        "costante": float(beta[0]),
        "prezzo": float(beta[1]),
        "tempo": float(beta[2]),
        "volume": float(beta[3]),
    }


def _matrice_calendario(date) -> list[np.ndarray]:
    """Indicatrici di giorno della settimana e di mese, con la prima omessa."""
    giorni = np.array([d.weekday() for d in date])
    mesi = np.array([d.month for d in date])
    colonne = [(giorni == g).astype(float) for g in range(1, 7)]
    colonne += [(mesi == m).astype(float) for m in range(2, 13)]
    return [c for c in colonne if c.any() and not c.all()]


def senza_calendario(
    chiusure: np.ndarray, volume: np.ndarray, date, soglia: float = SOGLIA
) -> dict[str, float]:
    """Che cosa resta del volume quando gli si toglie il calendario.

    Il volume relativo viene regredito su giorno della settimana e mese; il
    residuo prende il posto della colonna del volume e la decomposizione si
    ripete. Se il guadagno del volume era calendario, qui sparisce.
    """
    vrel = volume_relativo(volume)
    valido = np.isfinite(vrel) & (vrel > 0)
    y = np.log(vrel[valido])
    colonne = [c[valido] for c in _matrice_calendario(date)]
    X = np.column_stack([np.ones(len(y))] + colonne)
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)

    ripulito = np.full(len(vrel), np.nan)
    ripulito[valido] = np.exp(y - X @ beta)

    t = tavolo(chiusure, volume, soglia=soglia, relativo=ripulito)
    conto = decomposizione(t)
    return {
        "r_quadro_volume": r_quadro(y, colonne),
        "movimenti": conto["movimenti"],
        "guadagno_volume": conto["guadagno_volume"],
        "quota_prezzo_e_tempo": conto["quota_prezzo_e_tempo"],
    }


def surrogato_volume(t: Tavolo, ripetizioni: int, seme: int = 20260615) -> dict[str, float]:
    """Quanto vale il guadagno del volume quando il volume e' rimescolato.

    Ogni movimento tiene la propria ampiezza, durata e volatilita' e riceve il
    volume di un altro. E' il termine di paragone corretto: se il guadagno vero
    non si distingue da questo, il legame non c'e'.
    """
    generatore = np.random.default_rng(seme)
    y = np.log(t.ampiezza)
    prezzo, tempo = np.log(t.prezzo), np.log(t.durata)
    volume = np.log(t.volume)
    base = r_quadro(y, [prezzo, tempo])

    guadagni = np.empty(ripetizioni)
    for i in range(ripetizioni):
        mescolato = generatore.permutation(volume)
        guadagni[i] = r_quadro(y, [prezzo, tempo, mescolato]) - base

    return {
        "medio": float(guadagni.mean()),
        "p95": float(np.percentile(guadagni, 95)),
        "massimo": float(guadagni.max()),
    }
