"""Serie sintetiche e rilevatore elementare, condivisi dalle verifiche.

Le tre verifiche aperte del capitolo 21 del libro 2 hanno bisogno delle
stesse due cose: un modo di costruire serie prive di struttura ciclica ma
con lo stesso contenuto spettrale, e un rilevatore di estremi cosi'
semplice da poter essere applicato identico ai dati veri e alle serie
sintetiche.

**Il rilevatore e' deliberatamente elementare.** Non e' quello del
protocollo del primo volume: non ha gerarchia, ne' criterio spettrale, ne'
conferma a finestra chiusa. E' la stessa regola usata nella Parte V — il
minimo e' il punto piu' basso in una finestra centrata di mezzo ciclo — ed
e' scelta cosi' perche' un confronto contro i surrogati e' leale solo se
la procedura non contiene nulla che i surrogati non possano soddisfare.

**I surrogati sono a fase randomizzata.** Si trasforma la serie, si
sostituiscono le fasi con valori casuali uniformi mantenendo i moduli, e
si antitrasforma. Il risultato ha lo **stesso spettro di potenza**
dell'originale — quindi la stessa volatilita' e lo stesso contenuto in
frequenza — e nessuna ragione di avere gli estremi negli stessi punti.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

RADICE = Path(__file__).resolve().parents[3]
SNAPSHOT = RADICE / "dati" / "snapshot"

#: I periodi nominali della scala, in barre giornaliere.
NOMINALI = {"T": 10, "T+1": 20, "T+2": 45, "T+3": 90, "T+4": 160, "T+5": 480}

NOMI = {"BTCUSDT": "Bitcoin", "ETHUSDT": "Ethereum", "SOLUSDT": "Solana"}


def chiusure(simbolo: str) -> np.ndarray:
    """Il logaritmo delle chiusure giornaliere dallo snapshot congelato."""
    percorso = SNAPSHOT / f"{simbolo}_D.csv"
    righe = percorso.read_text(encoding="utf-8").splitlines()[1:]
    valori = [float(r.split(",")[4]) for r in righe if r.strip()]
    return np.log(np.array(valori, dtype=float))


def chiusure_h4(simbolo: str) -> np.ndarray:
    """Il logaritmo delle chiusure a quattro ore dallo snapshot congelato.

    Stessa fonte e stesso taglio del giornaliero — `dati/snapshot/registro-h4.json`
    ne porta barre, impronta e mesi assenti — con sei barre per giornata invece
    di una. La colonna della chiusura e' la quinta anche qui, ma la prima e'
    l'istante e non la data.
    """
    percorso = SNAPSHOT / f"{simbolo}_H4.csv"
    righe = percorso.read_text(encoding="utf-8").splitlines()[1:]
    valori = [float(r.split(",")[4]) for r in righe if r.strip()]
    return np.log(np.array(valori, dtype=float))


def surrogato(serie: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Una replica con lo stesso spettro di potenza e le fasi randomizzate.

    La deriva viene tolta prima e rimessa dopo: randomizzare le fasi di una
    serie con una tendenza forte produrrebbe un artefatto ai bordi, e la
    tendenza non e' l'oggetto della verifica.
    """
    n = len(serie)
    passi = np.arange(n)
    coefficienti = np.polyfit(passi, serie, 1)
    deriva = np.polyval(coefficienti, passi)
    residuo = serie - deriva

    spettro = np.fft.rfft(residuo)
    fasi = rng.uniform(0, 2 * np.pi, len(spettro))
    fasi[0] = 0.0
    if n % 2 == 0:
        fasi[-1] = 0.0
    return np.fft.irfft(np.abs(spettro) * np.exp(1j * fasi), n=n) + deriva


def surrogato_aaft(serie: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Come `surrogato`, ma conserva anche la distribuzione dei valori.

    La randomizzazione di fase pura ha un difetto noto: la somma di molte
    componenti con fasi indipendenti tende alla gaussiana, quindi le repliche
    perdono le code spesse e i grappoli di volatilita' dei mercati veri. Sono
    percio' **piu' pulite** dell'originale, e un confronto contro di esse
    puo' favorire il rumore.

    L'AAFT (*amplitude adjusted Fourier transform*) rimedia in tre passi:
    si mappa la serie su valori gaussiani conservando l'ordinamento, si
    randomizzano le fasi di quella, e si rimappano i valori risultanti sulla
    distribuzione empirica di partenza. Il risultato ha la distribuzione
    esatta dell'originale e lo spettro approssimato.
    """
    n = len(serie)
    passi = np.arange(n)
    coefficienti = np.polyfit(passi, serie, 1)
    deriva = np.polyval(coefficienti, passi)
    residuo = serie - deriva

    ranghi = np.argsort(np.argsort(residuo))
    gaussiana = np.sort(rng.standard_normal(n))[ranghi]
    randomizzata = surrogato(gaussiana, rng)
    ranghi_finali = np.argsort(np.argsort(randomizzata))
    return np.sort(residuo)[ranghi_finali] + deriva


def minimi(serie: np.ndarray, periodo: int) -> np.ndarray:
    """Gli indici dei minimi: punto piu' basso in una finestra centrata.

    La finestra vale mezzo periodo per lato, come nella Parte V. Un punto
    e' un minimo se nessun punto della sua finestra sta piu' in basso; a
    parita' di valore vince il primo, cosi' la regola resta deterministica.
    """
    mezza = max(1, periodo // 2)
    trovati = []
    ultimo = -(10**9)
    for i in range(mezza, len(serie) - mezza):
        finestra = serie[i - mezza : i + mezza + 1]
        if serie[i] <= finestra.min() and i - ultimo >= mezza:
            trovati.append(i)
            ultimo = i
    return np.array(trovati, dtype=int)


def minimi_veloci(serie: np.ndarray, periodo: int) -> np.ndarray:
    """Gli stessi indici di `minimi`, calcolati senza il ciclo sulle barre.

    Il confronto con la finestra e' un minimo mobile, e un minimo mobile si
    calcola in una passata invece che in una per barra. La seconda regola —
    la distanza minima fra minimi consecutivi — resta sequenziale, ma corre
    sui soli candidati, che sono pochi.

    Serve sulle serie a quattro ore, dove le barre sono sei volte quelle del
    giornaliero e i livelli lunghi hanno finestre da centinaia di barre: con
    il ciclo per barra una sola replica costerebbe piu' dell'intera verifica.
    L'identita' con `minimi` non e' affidata al ragionamento — la si verifica
    in codice, sulle serie vere, prima di usarla.
    """
    from scipy.ndimage import minimum_filter1d

    mezza = max(1, periodo // 2)
    if len(serie) <= 2 * mezza:
        return np.array([], dtype=int)
    fondo = minimum_filter1d(serie, size=2 * mezza + 1, mode="nearest")
    candidati = np.flatnonzero(serie <= fondo)
    candidati = candidati[(candidati >= mezza) & (candidati < len(serie) - mezza)]

    trovati = []
    ultimo = -(10**9)
    for i in candidati:
        if i - ultimo >= mezza:
            trovati.append(int(i))
            ultimo = int(i)
    return np.array(trovati, dtype=int)


def cicli(serie: np.ndarray, periodo: int) -> tuple[np.ndarray, np.ndarray]:
    """Durate e ampiezze dei cicli fra minimi consecutivi.

    L'ampiezza e' l'escursione dal minimo iniziale al massimo interno,
    misurata sui logaritmi — quindi e' gia' un'escursione relativa, ed e'
    la definizione dichiarata nella nota di apertura del libro 2.
    """
    indici = minimi(serie, periodo)
    if len(indici) < 2:
        return np.array([]), np.array([])
    durate, ampiezze = [], []
    for inizio, fine in zip(indici[:-1], indici[1:]):
        tratto = serie[inizio : fine + 1]
        durate.append(float(fine - inizio))
        ampiezze.append(float(tratto.max() - tratto[0]))
    return np.array(durate), np.array(ampiezze)


def spettro_di_potenza(serie: np.ndarray, periodi: np.ndarray) -> np.ndarray:
    """La potenza a ciascun periodo interrogato, con Goertzel.

    Si interroga un elenco di periodi invece di prendere le frequenze della
    trasformata: e' la stessa scelta del protocollo del primo volume, e
    serve perche' i periodi lunghi altrimenti sarebbero campionati troppo
    di rado per essere confrontati fra loro.
    """
    passi = np.arange(len(serie))
    coefficienti = np.polyfit(passi, serie, 1)
    residuo = serie - np.polyval(coefficienti, passi)
    residuo = residuo - residuo.mean()

    potenze = np.empty(len(periodi))
    for indice, periodo in enumerate(periodi):
        omega = 2.0 * np.pi / periodo
        coseno = np.cos(omega * passi)
        seno = np.sin(omega * passi)
        potenze[indice] = (residuo @ coseno) ** 2 + (residuo @ seno) ** 2
    return potenze / len(serie) ** 2


def sbianca(potenze: np.ndarray, finestra: int = 21) -> np.ndarray:
    """Lo spettro diviso per il proprio fondo, stimato con una mediana mobile.

    Lo spettro di una serie finanziaria decade fortemente con la frequenza:
    senza questo passaggio ogni massimo locale trovato starebbe ai periodi
    brevi, e il confronto fra picchi lontani sarebbe governato dal fondo
    invece che dalla struttura. La mediana mobile e' la stima di fondo piu'
    robusta e non risente dei picchi che si vogliono trovare.
    """
    n = len(potenze)
    mezza = max(1, finestra // 2)
    fondo = np.empty(n)
    for i in range(n):
        a, b = max(0, i - mezza), min(n, i + mezza + 1)
        fondo[i] = np.median(potenze[a:b])
    fondo[fondo <= 0] = np.finfo(float).tiny
    return potenze / fondo


def picchi_prominenti(
    periodi: np.ndarray, potenze: np.ndarray, prominenza: float = 1.0
) -> np.ndarray:
    """I periodi dei picchi dello spettro sbiancato, per prominenza topografica.

    La prominenza di un picco e' la sua altezza sopra la piu' alta delle due
    valli che lo separano da un picco piu' alto — la definizione topografica,
    non la differenza dal vicino immediato. E' cio' che distingue un picco
    vero da un'increspatura sul fianco di un altro, e senza di essa il
    criterio seleziona quasi ogni massimo locale.

    La soglia e' espressa in unita' del fondo: `prominenza = 1.0` significa
    che il picco deve superare le proprie valli di almeno una volta il fondo
    locale. Il criterio e' applicato identico ai dati veri e ai surrogati.
    """
    from scipy.signal import find_peaks

    sbiancate = sbianca(potenze)
    indici, _ = find_peaks(sbiancate, prominence=prominenza)
    return periodi[indici]
