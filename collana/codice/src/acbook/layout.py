"""Gabbia tipografica e stile delle figure.

Un solo posto dove vivono le misure del blocco testo e i criteri di leggibilita'
in scala di grigi. I valori qui dentro e quelli in `_quarto.yml` devono restare
allineati: un test in `codice/testing` lo verifica a ogni giro.

Regole di stampa, imparate sul libro precedente e non negoziabili:
  - niente trasparenza: i servizi di stampa chiedono di appiattirla. Il colore
    c'e' dal 22/09/2026 (la stampa e' a colori, vedi `STAMPA_A_COLORI`), ma la
    figura deve reggere anche in scala di grigi;
  - le serie si distinguono per **stile di linea** e livello di grigio insieme,
    mai per il solo grigio;
  - le aree si riempiono con **grigi pieni** e mai con `alpha`. Il retino resta
    solo per le aree che si **sovrappongono** (`riempimento_retinato`): fra due
    aree che si toccano due retini diagonali vicini si saldano in un unico
    blocco rigato, ed e' il difetto che rendeva illeggibile la barra impilata
    del capitolo su prezzo e tempo;
  - i font sono di tipo 42, perche' i Type 3 sono la contestazione classica dei
    servizi di stampa.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt

from . import sidecar

# --- Gabbia (17 x 24 cm) ------------------------------------------------------
# Le stesse misure stanno in _quarto.yml sotto `geometry`.
PAGINA_MM = (170.0, 240.0)
MARGINE_INTERNO_MM = 22.0
MARGINE_ESTERNO_MM = 18.0
MARGINE_SUPERIORE_MM = 20.0
MARGINE_INFERIORE_MM = 22.0

MM_PER_POLLICE = 25.4
BLOCCO_MM = PAGINA_MM[0] - MARGINE_INTERNO_MM - MARGINE_ESTERNO_MM  # 130 mm
BLOCCO_IN = BLOCCO_MM / MM_PER_POLLICE  # 5.118 in

# Tre altezze standard: piu' di tre proporzioni in un libro sono disordine.
ALTEZZE = {
    "bassa": BLOCCO_IN * 0.42,
    "normale": BLOCCO_IN * 0.60,
    "alta": BLOCCO_IN * 0.80,
}

# --- Grigi e tratti -----------------------------------------------------------
# Quattro livelli distinguibili anche su carta crema, dal piu' scuro al piu'
# chiaro. Oltre il quarto livello si usa un secondo pannello, non un quinto grigio.
GRIGI = ("#1a1a1a", "#4d4d4d", "#808080", "#b3b3b3")
TRATTI = ("-", "--", "-.", ":")
# I tratti delle componenti di un modello: il continuo resta al composito.
TRATTI_COMPONENTI = ("--", ":", "-.", (0, (3, 1, 1, 1, 1, 1)))
RETINI = ("///", "\\\\\\", "xxx", "...")

# Sullo schermo (EPUB e notebook) le stesse figure possono usare il colore:
# stesso codice, uscita piu' leggibile.
COLORI_SCHERMO = ("#1f4e79", "#a63603", "#2d6a4f", "#6a4c93")

#: **La stampa e' a colori** (decisione di Luigi del 22/09/2026: «stamperemo libri
#: con grafici a colori»). Le uscite `stampa/` restano vettoriali, con la gabbia e
#: i tratti della stampa, ma prendono la tavolozza dello schermo. I tratti e i
#: retini restano: la figura deve leggersi anche in fotocopia. Rimettere False
#: riporta l'interno in grigi senza toccare nessun generatore.
STAMPA_A_COLORI = True


#: Il separatore decimale delle tacche numeriche. Il libro scrive la virgola; la
#: resa inglese (`codice/traduzione/genera_figure_en.py`) lo rimette al punto
#: prima di disegnare.
DECIMALE = ","


def _virgola_nelle_tacche() -> None:
    """Le tacche automatiche di matplotlib col separatore decimale del libro.

    Le figure scrivevano «0,80» nelle legende e «0.8» sull'asse accanto (B53,
    A21, A35): due convenzioni nella stessa cornice. Si aggancia il solo punto
    per cui passa ogni numero di `ScalarFormatter` — tacche e scostamento — e si
    lascia il resto com'e'. Dentro il mathtext la virgola va fra graffe, o il
    motore la tratta da punteggiatura e ci mette uno spazio dopo.
    """
    from matplotlib import ticker

    classe = ticker.ScalarFormatter
    if getattr(classe, "_acbook_decimale", False):
        return
    originale = classe._format_maybe_minus_and_locale

    def formatta(self, fmt, arg):
        testo = originale(self, fmt, arg)
        if DECIMALE == "." or self._useLocale:
            return testo
        return testo.replace(".", "{,}" if self._useMathText else DECIMALE)

    classe._format_maybe_minus_and_locale = formatta
    classe._acbook_decimale = True


def configura(schermo: bool = False) -> None:
    """Imposta matplotlib per la stampa (o per lo schermo)."""
    _virgola_nelle_tacche()
    ciclo = COLORI_SCHERMO if (schermo or STAMPA_A_COLORI) else GRIGI
    mpl.rcParams.update(
        {
            "figure.figsize": (BLOCCO_IN, ALTEZZE["normale"]),
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
            "font.family": "serif",
            "font.serif": ["Libertinus Serif", "Linux Libertine O", "DejaVu Serif"],
            "font.size": 8.5,
            "axes.titlesize": 9,
            "axes.labelsize": 8.5,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "legend.fontsize": 7.5,
            "axes.prop_cycle": mpl.cycler(color=ciclo),
            "axes.grid": True,
            "grid.color": "#d9d9d9",
            "grid.linewidth": 0.4,
            "axes.axisbelow": True,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.linewidth": 0.6,
            "lines.linewidth": 1.0,
            "legend.frameon": False,
            "figure.constrained_layout.use": True,
        }
    )


def tinta(indice: int, schermo: bool = False,
          grigio: int | None = None) -> str:
    """Il colore della n-esima serie di **dati**, nel modo corrente.

    Da usare ovunque una figura scelga il tono a mano invece di lasciarlo al
    ciclo di matplotlib. `layout.GRIGI[i]` scritto direttamente resta grigio
    anche nell'edizione a colori: e' il difetto che il 15/09/2026 lasciava
    quattro figure su 111 in bianco e nero dentro il volume a colori.

    **Solo per i dati.** Linee di riferimento, griglie, annotazioni e sfondi
    restano grigi in tutte e due le edizioni: colorare l'arredo toglie contrasto
    a cio' che porta l'informazione.

    `grigio` disaccoppia i due indici quando la composizione in grigi e' gia'
    tarata: due serie possono volere due colori distinti a schermo e lo stesso
    tono in stampa — per esempio il triangolo e il cerchio del repainting, che
    indicano lo stesso minimo letto in due modi.
    """
    if schermo or STAMPA_A_COLORI:
        return COLORI_SCHERMO[indice % len(COLORI_SCHERMO)]
    return GRIGI[(indice if grigio is None else grigio) % len(GRIGI)]


#: I tre toni di una scala ordinata — «sotto», «dentro», «sopra» — per le
#: figure a bande. In grigi la scala e' monotona; a schermo il centro e' quello
#: che si deve vedere, e i due estremi lo incorniciano.
BANDE_GRIGI = ("#e6e6e6", "#9c9c9c", "#4d4d4d")
BANDE_SCHERMO = ("#cfd8dc", "#2d6a4f", "#a63603")


def bande(schermo: bool = False) -> tuple[str, str, str]:
    """La scala a tre bande di `risoluzione_righello` e sorelle."""
    return BANDE_SCHERMO if (schermo or STAMPA_A_COLORI) else BANDE_GRIGI


def serie(indice: int, schermo: bool = False) -> dict:
    """Stile della n-esima serie: colore **e** tratto, mai uno solo dei due."""
    if schermo:
        return {"color": COLORI_SCHERMO[indice % len(COLORI_SCHERMO)], "linestyle": "-"}
    if STAMPA_A_COLORI:
        return {"color": COLORI_SCHERMO[indice % len(COLORI_SCHERMO)],
                "linestyle": TRATTI[indice % len(TRATTI)]}
    return {
        "color": GRIGI[indice % len(GRIGI)],
        "linestyle": TRATTI[indice % len(TRATTI)],
    }


def composito(schermo: bool = False) -> dict:
    """La curva risultante di un modello: nera, continua, pesante.

    In una figura sovrapposta — somma e componenti nella stessa cornice — il
    lettore deve capire in un colpo d'occhio quale curva e' il risultato e quali
    sono gli addendi. Il peso della linea fa questo lavoro meglio del tono, e lo
    fa anche in fotocopia.
    """
    return {"color": GRIGI[0], "linestyle": "-", "linewidth": 1.5, "zorder": 5}


def componente(indice: int, schermo: bool = False) -> dict:
    """Una componente del modello: tratto proprio, tono piu' chiaro, peso lieve.

    Tono e tratto avanzano con passi diversi — due grigi e quattro tratti — cosi'
    che le prime otto componenti siano coppie distinte. La regola della casa
    resta: **la distinzione sta nel tratto**, il tono la rinforza e non la
    sostituisce. Il nero e' riservato al composito; il grigio piu' chiaro resta
    fuori, perche' una linea sottile a quel tono in stampa sparisce.
    """
    if schermo or STAMPA_A_COLORI:
        return {
            "color": COLORI_SCHERMO[indice % len(COLORI_SCHERMO)],
            "linestyle": TRATTI_COMPONENTI[indice % len(TRATTI_COMPONENTI)],
            "linewidth": 0.9,
        }
    return {
        "color": GRIGI[1 + indice % 2],
        "linestyle": TRATTI_COMPONENTI[indice % len(TRATTI_COMPONENTI)],
        "linewidth": 0.9,
    }


def cornice(asse) -> None:
    """Riquadra l'area dati sui quattro lati e toglie la griglia di fondo.

    Le figure di modello hanno molte curve dentro una cornice sola: la griglia
    diventa rumore, il riquadro chiuso invece delimita il campo e rende contabile
    l'asse numerico.
    """
    for lato in asse.spines.values():
        lato.set_visible(True)
        lato.set_linewidth(0.6)
    asse.grid(False)


def etichetta_curva(asse, x: float, y: float, testo: str, **kwargs) -> None:
    """Nome della serie scritto accanto alla curva, su fondo bianco pieno.

    Una legenda dice quali serie ci sono; un'etichetta sulla curva dice **quale
    e' questa qui**. Le figure che si leggono senza tornare alla legenda hanno
    entrambe le cose.
    """
    scarto = kwargs.pop("scarto", (0.0, 6.0))
    asse.annotate(
        testo,
        (x, y),
        xytext=scarto,
        textcoords="offset points",
        fontsize=kwargs.pop("fontsize", 6.5),
        bbox={"facecolor": "white", "edgecolor": "none", "pad": 1.0},
        zorder=6,
        **kwargs,
    )


def riempimento(indice: int, schermo: bool = False) -> dict:
    """Stile di un'area: **grigio pieno**, mai trasparenza e mai retino.

    Era un retino su fondo bianco, ed era sbagliato per le aree che si toccano.
    Su una barra impilata due retini diagonali vicini — `///` e `\\\\\\` — si
    leggono come un unico blocco rigato e il confine fra i due segmenti sparisce:
    la figura del capitolo sul prezzo e il tempo era illeggibile in stampa
    esattamente per questo. Il grigio pieno separa al primo sguardo, si stampa
    senza trasparenze e senza inchiostri speciali, ed e' la stessa scelta di
    *La matematica di chi perde*, che questa collana prende come riferimento.

    Il bordo bianco sottile serve alle aree adiacenti: senza, due grigi vicini
    si saldano quando il retino non c'e' piu' a dividerli.
    """
    if schermo:
        return {
            "facecolor": COLORI_SCHERMO[indice % len(COLORI_SCHERMO)],
            "edgecolor": "none",
        }
    tavolozza = COLORI_SCHERMO if STAMPA_A_COLORI else GRIGI
    return {
        "facecolor": tavolozza[indice % len(tavolozza)],
        "edgecolor": "white",
        "linewidth": 0.6,
    }


def riempimento_retinato(indice: int, schermo: bool = False) -> dict:
    """Stile di un'area **sovrapposta** a un'altra: retino su fondo bianco.

    Resta per il solo caso in cui due aree si accavallano e sotto deve restare
    visibile: li' il grigio pieno coprirebbe, e la trasparenza e' vietata in
    stampa. Per le aree che si toccano senza sovrapporsi si usa `riempimento`.
    """
    if schermo:
        return {
            "facecolor": COLORI_SCHERMO[indice % len(COLORI_SCHERMO)],
            "edgecolor": "none",
        }
    tavolozza = COLORI_SCHERMO if STAMPA_A_COLORI else GRIGI
    return {
        "facecolor": "white",
        "edgecolor": tavolozza[indice % len(tavolozza)],
        "hatch": RETINI[indice % len(RETINI)],
        "linewidth": 0.6,
    }


def legenda(asse, ncols: int = 3, **kwargs):
    """Legenda **sopra** l'area dati: non puo' coprire ne' curve ne' punti.

    Una legenda dentro il riquadro va bene finche' i dati le lasciano spazio, e
    smette di andare bene appena la serie cambia. Metterla fuori una volta per
    tutte e' l'unico modo di non doverlo ricontrollare a ogni rigenerazione.
    """
    return asse.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.005),
        ncols=ncols,
        frameon=False,
        borderaxespad=0.0,
        **kwargs,
    )


def legenda_figura(fig, asse, ncols: int = 3, **kwargs):
    """Legenda **sopra tutti** i riquadri, per le figure a piu' pannelli.

    `legenda()` ancora la legenda al singolo riquadro: su una figura a tre
    pannelli quella legenda deborda oltre il bordo, e il ritaglio `tight`
    allarga la figura fino a sfondare la gabbia. Qui la legenda appartiene
    alla figura, e il `constrained_layout` le riserva la sua striscia.
    """
    voci, etichette = asse.get_legend_handles_labels()
    return fig.legend(
        voci,
        etichette,
        loc="outside upper center",
        ncols=ncols,
        frameon=False,
        **kwargs,
    )


def legenda_interna(asse, posizione: str = "upper left", **kwargs):
    """Legenda dentro il riquadro, su fondo bianco pieno.

    Il fondo opaco non e' trasparenza — che in stampa e' vietata — ma un
    rettangolo bianco: se la legenda finisse sopra una curva, la nasconde invece
    di intrecciarsi con essa.
    """
    return asse.legend(
        loc=posizione,
        frameon=True,
        facecolor="white",
        edgecolor="none",
        framealpha=1.0,
        **kwargs,
    )


def numero(valore: float, decimali: int = 2) -> str:
    """Un numero come lo scrive il libro: virgola decimale, e il mezzo si arrotonda in su.

    `f"{0.9295:.3f}"` da' 0.929 — il binario tiene 0,9295 un soffio sotto — mentre
    il testo, arrotondando a mano, scrive 0,930: figura e prosa stampavano due
    numeri diversi per lo stesso valore (finding A41). Si arrotonda sulla cifra
    scritta nel file congelato, come la arrotonda chi legge.
    """
    from decimal import ROUND_HALF_UP, Decimal

    quanto = Decimal(1).scaleb(-decimali)
    arrotondato = Decimal(repr(float(valore))).quantize(quanto, rounding=ROUND_HALF_UP)
    return f"{arrotondato:.{decimali}f}".replace(".", ",")


def figura(altezza: str = "normale", **kwargs):
    """Una figura larga quanto il blocco testo, con una delle tre altezze."""
    return plt.subplots(figsize=(BLOCCO_IN, ALTEZZE[altezza]), **kwargs)


def salva(fig, nome: str, libro: int, schermo: bool = False,
          fatti: dict | None = None) -> Path:
    """Salva in `figure/libro-N/`: PDF vettoriale per la stampa, PNG per lo schermo.

    Sulla stampa scrive anche il **sidecar** `figure/libro-N/meta/<nome>.meta.json`
    con i fatti del disegno (`acbook.sidecar`), che il presidio delle didascalie
    confronta con la frase del `.qmd`. `fatti` porta cio' che solo il generatore
    sa — conteggi, soglie, il file congelato da cui legge — e finisce sotto la
    chiave `dichiarati`.
    """
    progetto = Path(__file__).resolve().parents[3]
    cartella = progetto / "figure" / f"libro-{libro}" / ("schermo" if schermo else "stampa")
    cartella.mkdir(parents=True, exist_ok=True)
    percorso = cartella / f"{nome}.{'png' if schermo else 'pdf'}"
    fig.savefig(percorso)
    if not schermo:
        # Prima di `plt.close`: dopo, gli artisti non si interrogano piu'.
        sidecar.scrivi(fig, nome, libro, progetto, fatti)
    plt.close(fig)
    return percorso
