"""Le figure di struttura del libro 2: livelli, convergenza, swing e violazione.

Quattro capitoli della Parte IV arrivavano alla stampa senza una sola figura, e
sono quattro capitoli in cui il risultato e' un **confronto fra livelli o fra
mercati**: la specie di risultato che una colonna di cifre nasconde e un
disegno mostra intero. Nessuna di queste figure aggiunge un numero alle tavole;
tutte leggono da `dati/serie/` o da `dati/misure/`, e non contengono un solo
valore trascritto a mano.

Uscite:
  livelli_sovrapposizione   -> cap. 1, la scala che perde due gradini
  convergenza_per_livello   -> cap. 10, dove la comunanza fra mercati finisce
  swing_condizionato        -> cap. 7, la previsione della teoria, invertita
  violazione_contro_tenuta  -> cap. 8, un evento contro un non-evento
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import layout  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
SERIE = RADICE / "dati" / "serie"
MISURE = RADICE / "dati" / "misure"

#: I tre mercati, con il nome che i libri usano in pagina.
MERCATI = (("BTCUSDT_D", "Bitcoin"), ("ETHUSDT_D", "Ethereum"), ("SOLUSDT_D", "Solana"))

#: La soglia di sovrapposizione dichiarata nel capitolo 1: oltre questa quota di
#: minimi condivisi in **entrambe** le direzioni, due livelli sono lo stesso
#: livello con due nomi.
SOGLIA_SOVRAPPOSIZIONE = 80.0


def _serie(asset: str, percorso: str) -> dict:
    return json.loads((SERIE / asset / percorso).read_text(encoding="utf-8"))


def _misura(nome: str) -> dict:
    return json.loads((MISURE / f"{nome}.json").read_text(encoding="utf-8"))


def _tracce(dati: dict) -> dict:
    return dati["tracce"]


def livelli_sovrapposizione(schermo: bool = False) -> Path:
    """La sovrapposizione fra livelli adiacenti, contro la soglia dichiarata.

    E' la figura del verdetto del capitolo 1, e mostra in un colpo d'occhio
    perche' quel verdetto riguarda **un gradino solo** invece che la scala
    intera: la coppia T-T+1 sta sopra la soglia su tutti e tre i mercati, tutte
    le altre stanno fra un terzo e due terzi.

    La matrice del materiale e' simmetrica perche' riporta gia' la
    sovrapposizione **bidirezionale**, cioe' la piu' piccola delle due
    direzioni: e' la grandezza su cui il capitolo si pronuncia, e la sola che
    non valga il cento per cento per costruzione in una gerarchia sincronizzata.
    """
    layout.configura(schermo=schermo)
    fig, asse = layout.figura("normale")

    coppie_viste: list[str] = []
    per_mercato: dict[str, dict[str, float]] = {}

    for asset, nome in MERCATI:
        traccia = next(iter(_tracce(_serie(asset, "phantom/matrix.json")).values()))
        livelli = traccia["x"]
        matrice = traccia["z"]
        valori: dict[str, float] = {}
        for i in range(len(livelli) - 1):
            etichetta = f"{livelli[i]}–{livelli[i + 1]}"
            valori[etichetta] = matrice[i][i + 1] * 100
            if etichetta not in coppie_viste:
                coppie_viste.append(etichetta)
        per_mercato[nome] = valori

    posizioni = np.arange(len(coppie_viste), dtype=float)
    larghezza = 0.26
    for indice, (_, nome) in enumerate(MERCATI):
        altezze = [per_mercato[nome].get(c, np.nan) for c in coppie_viste]
        asse.bar(
            posizioni + (indice - 1) * larghezza,
            altezze,
            width=larghezza,
            label=nome,
            zorder=2,
            **layout.riempimento(indice, schermo),
        )

    asse.axhline(
        SOGLIA_SOVRAPPOSIZIONE,
        color=layout.GRIGI[0] if not (schermo or layout.STAMPA_A_COLORI) else "#333333",
        linestyle="--",
        linewidth=0.9,
        zorder=3,
    )
    asse.annotate(
        f"soglia dichiarata: {layout.numero(SOGLIA_SOVRAPPOSIZIONE, 0)}%",
        # Al centro, sopra le coppie basse: in fondo attraversava la barra al
        # cento per cento di Bitcoin a T+7–T+8.
        xy=((len(coppie_viste) - 1) / 2, SOGLIA_SOVRAPPOSIZIONE),
        xytext=(0, 4),
        textcoords="offset points",
        ha="center",
        va="bottom",
        fontsize=7,
    )

    asse.set_xticks(posizioni)
    asse.set_xticklabels(coppie_viste)
    asse.set_ylabel("minimi condivisi, entrambe le direzioni (%)")
    asse.set_xlabel("coppia di livelli adiacenti")
    asse.set_ylim(0, 108)
    layout.legenda(asse, ncols=3)
    return layout.salva(fig, "livelli_sovrapposizione", libro=2, schermo=schermo)


def convergenza_per_livello(schermo: bool = False) -> Path:
    """Dove la comunanza fra mercati funziona, e dove smette.

    Due pannelli con la stessa scala orizzontale. Sopra le tre durate mediane
    per livello, in scala logaritmica perche' coprono un fattore trenta; sotto
    il campo di variazione relativo, che e' la grandezza su cui il capitolo 10
    si pronuncia — e che sale di un ordine di grandezza fra T+3 e T+4.

    Il salto sta nel secondo pannello e non nel primo: nel primo i tre punti di
    T+4 e T+5 sembrano vicini perche' la scala logaritmica comprime, ed e'
    esattamente l'illusione che il secondo pannello toglie.
    """
    layout.configura(schermo=schermo)
    dati = _misura("listino-misura")
    convergenza = dati["convergenza"]
    livelli = [r["livello"] for r in convergenza]
    posizioni = np.arange(len(livelli), dtype=float)

    fig, assi = layout.figura("alta", nrows=2, sharex=True)

    for indice, (_, nome) in enumerate(MERCATI):
        assi[0].plot(
            posizioni,
            [r["mediane"][indice] for r in convergenza],
            marker="os^"[indice],
            markersize=4,
            label=nome,
            zorder=3,
            **layout.serie(indice, schermo),
        )
    assi[0].set_yscale("log")
    #: Tacche scelte a mano: le minori automatiche della scala logaritmica
    #: scrivono «4 x 10^2» dove basta «400», e in una figura di libro sono rumore.
    tacche = [10, 20, 50, 100, 200, 500]
    assi[0].set_yticks(tacche)
    assi[0].set_yticklabels([str(v) for v in tacche])
    assi[0].minorticks_off()
    assi[0].set_ylabel("durata mediana (barre)")

    campi = [r["campo_percentuale"] for r in convergenza]
    assi[1].bar(
        posizioni, campi, width=0.5, zorder=2, **layout.riempimento(2, schermo)
    )
    assi[1].set_ylabel("campo di variazione (%)")
    assi[1].set_xlabel("livello")
    assi[1].set_xticks(posizioni)
    assi[1].set_xticklabels(livelli)
    assi[1].set_ylim(0, max(campi) * 1.25)

    layout.legenda_figura(fig, assi[0], ncols=3)
    return layout.salva(fig, "convergenza_per_livello", libro=2, schermo=schermo)


def _per_livello(asset: str, percorso: str, traccia: str) -> dict[str, tuple[float, int]]:
    """Una traccia a barre del materiale, letta come livello -> (quota, campione).

    Le etichette del materiale portano la struttura fra parentesi — «T+3 (x2)» —
    e il numero di casi sta nel campo `text` nella forma «N=30». Qui si tiene il
    livello e il campione, che sono le due cose di cui la figura ha bisogno.
    """
    tracce = _tracce(_serie(asset, percorso))
    voce = tracce[traccia]
    valori: dict[str, tuple[float, int]] = {}
    for etichetta, quota, testo in zip(voce["x"], voce["y"], voce["text"]):
        livello = etichetta.split(" ")[0]
        valori[livello] = (float(quota), int(str(testo).split("=")[1]))
    return valori


def _livelli_ordinati(mappe: list[dict[str, tuple[float, int]]]) -> list[str]:
    ordine: list[str] = []
    for mappa in mappe:
        for livello in mappa:
            if livello not in ordine:
                ordine.append(livello)
    return sorted(ordine, key=lambda s: int(s[2:]) if len(s) > 1 else 0)


def _pannello_a_gruppi(
    asse,
    livelli: list[str],
    per_mercato: dict[str, dict[str, tuple[float, int]]],
    schermo: bool,
    campione_minimo: int = 0,
) -> int:
    """Barre raggruppate per livello, con il campione scritto sotto l'asse.

    Una cella senza casi si tace; una cella con casi e quota zero si scrive «0»
    sopra l'asse, altrimenti una barra alta zero si confonde con un vuoto
    (DIRETTIVE §4). Restituisce quanti zeri con campione ha scritto.
    """
    posizioni = np.arange(len(livelli), dtype=float)
    larghezza = 0.26
    zeri = 0
    for indice, (_, nome) in enumerate(MERCATI):
        mappa = per_mercato[nome]
        altezze = [mappa[l][0] if l in mappa and mappa[l][1] > 0 else np.nan
                   for l in livelli]
        x = posizioni + (indice - 1) * larghezza
        asse.bar(
            x,
            altezze,
            width=larghezza,
            label=nome,
            zorder=2,
            **layout.riempimento(indice, schermo),
        )
        for xx, altezza in zip(x, altezze):
            if altezza == 0:
                asse.text(xx, 1.5, "0", ha="center", va="bottom", fontsize=6.5, zorder=3)
                zeri += 1
    asse.set_xticks(posizioni)
    asse.set_xticklabels(livelli)
    asse.set_ylim(0, 108)
    asse.set_xlim(-0.6, len(livelli) - 0.4)
    if campione_minimo:
        asse.axhline(50.0, color="#808080", linestyle=":", linewidth=0.8, zorder=1)
    return zeri


def _etichette_col_campione(
    asse, livelli: list[str], per_mercato: dict[str, dict[str, tuple[float, int]]]
) -> None:
    """Sotto ogni gruppo, il livello e i casi **di quel pannello**.

    I due pannelli di queste figure condividono l'asse orizzontale ma non il
    campione: la violazione del massimo e la sua negazione contano eventi
    diversi, e lo swing condizionato e quello incondizionato pure. Scrivere una
    riga sola sotto la figura significa attribuire al pannello di sopra i casi
    del pannello di sotto, che e' un errore della stessa famiglia di quelli che
    questi libri raccontano. Ogni pannello porta quindi i propri.
    """
    asse.tick_params(labelbottom=True)
    etichette = []
    for livello in livelli:
        casi = [
            str(per_mercato[nome][livello][1]) if livello in per_mercato[nome] else "—"
            for _, nome in MERCATI
        ]
        etichette.append(livello + "\nn = " + "/".join(casi))
    asse.set_xticklabels(etichette)


def swing_condizionato(schermo: bool = False) -> Path:
    """I due swing alla stessa prova, livello per livello.

    Il corpus dichiara in anticipo quale dei due debba essere il piu'
    affidabile — l'incondizionato — e la figura conferma la previsione: il
    pannello di sopra e' pieno al cento per cento ovunque il campione esista,
    quello di sotto va da zero a cento, e i suoi due zeri (Ethereum a T+5 e a
    T+7) poggiano su due casi ciascuno.

    Quello che la tavola aggregata del capitolo non lascia vedere e' **da dove
    venga quel cento per cento**: dal dettaglio per livello si vede che sta su
    campioni da quattro a trenta casi nel pannello di sopra e da uno a sette in
    quello di sotto. Il numero di casi e' scritto sotto ogni gruppo perche'
    senza di esso una barra al cento per cento su un caso solo si legge come le
    altre, ed e' la ragione per cui il verdetto del capitolo dice «confermato
    **sul campione**» invece di «confermato».
    """
    layout.configura(schermo=schermo)
    fig, assi = layout.figura("alta", nrows=2)
    zeri = 0

    for riga, (traccia, titolo) in enumerate(
        (
            ("Incondizionato (2° 50%)", "swing incondizionato"),
            ("Condizionato (1° 50%)", "swing condizionato"),
        )
    ):
        per_mercato = {
            nome: _per_livello(asset, "swing/success_rate.json", traccia)
            for asset, nome in MERCATI
        }
        livelli = _livelli_ordinati(list(per_mercato.values()))
        zeri += _pannello_a_gruppi(assi[riga], livelli, per_mercato, schermo,
                                   campione_minimo=1)
        assi[riga].set_ylabel(f"{titolo}\nchiusure previste (%)")
        _etichette_col_campione(assi[riga], livelli, per_mercato)

    assi[1].set_xlabel(
        "livello, e casi disponibili per mercato (Bitcoin / Ethereum / Solana)"
    )
    layout.legenda_figura(fig, assi[0], ncols=3)
    return layout.salva(fig, "swing_condizionato", libro=2, schermo=schermo,
                        fatti={"zeri_con_campione": zeri})


def violazione_contro_tenuta(schermo: bool = False) -> Path:
    """Un evento contro un non-evento, alla stessa prova.

    Sopra la violazione del massimo precedente, sotto la sua negazione: il
    massimo che NON viene superato. Entrambi i pannelli disegnano la direzione
    che la regola dichiara — rialzista sopra, ribassista sotto — e il materiale
    le porta gia' cosi': `D>P -> Bull` e `Hold -> Bear`.

    **Non sono due misure**: la seconda e' la marginale della prima, e la figura
    serve a rendere visibile quanto poco aggiunga. La prima sta stabilmente sopra
    la meta' su tutti e tre i mercati, la seconda ci oscilla attorno.

    La riga tratteggiata e' il cinquanta per cento, cioe' il lancio della
    moneta, e non la base-rate del mercato: quella e' diversa per asset e sta
    nella tavola del capitolo. Serve un riferimento che non cambi fra i tre
    pannelli, altrimenti la figura confronta anche i riferimenti.
    """
    layout.configura(schermo=schermo)
    fig, assi = layout.figura("alta", nrows=2)

    for riga, (traccia, titolo) in enumerate(
        (
            ("D>P → Bull (%)", "violazione del massimo\n→ ciclo rialzista"),
            ("Hold → Bear (%)", "tenuta del massimo\n→ ciclo ribassista"),
        )
    ):
        per_mercato = {
            nome: _per_livello(asset, "top_violation/dp_rate.json", traccia)
            for asset, nome in MERCATI
        }
        livelli = _livelli_ordinati(list(per_mercato.values()))
        _pannello_a_gruppi(assi[riga], livelli, per_mercato, schermo, campione_minimo=1)
        assi[riga].set_ylabel(f"{titolo}\naccuratezza (%)")
        _etichette_col_campione(assi[riga], livelli, per_mercato)

    assi[1].set_xlabel(
        "livello, e casi disponibili per mercato (Bitcoin / Ethereum / Solana)"
    )
    layout.legenda_figura(fig, assi[0], ncols=3)
    return layout.salva(fig, "violazione_contro_tenuta", libro=2, schermo=schermo)


def sequenze_intervalli(schermo: bool = False) -> Path:
    """Perche' un verdetto resta sospeso, disegnato.

    Un campione insufficiente non produce un numero sbagliato: produce un
    numero il cui intervallo comprende tutto, e questa e' la sola figura dei due
    volumi in cui **cio' che conta e' la lunghezza delle barre d'errore**, non la
    posizione dei punti.

    Ogni riga e' la quota di strutture conformi con il proprio intervallo di
    confidenza esatto; la riga verticale e' la quota che una successione casuale
    produrrebbe, ed e' diversa per le due strutture perche' le sequenze ammesse
    sono in proporzione diversa sui due alfabeti. Ogni intervallo attraversa la
    riga: nessuno dei confronti distingue l'ipotesi dal caso.
    """
    layout.configura(schermo=schermo)
    dati = _misura("sequenze-intervalli")
    fig, assi = layout.figura("normale", ncols=2)

    for colonna, struttura in enumerate(("quattro", "tre")):
        asse = assi[colonna]
        righe = [r for r in dati["per_mercato"] if r["struttura"] == struttura]
        aggregato = dati["aggregati"][struttura]
        voci = [(r["asset"], r) for r in righe] + [("tutti e tre", aggregato)]

        posizioni = np.arange(len(voci), dtype=float)[::-1]
        quote = [v["quota"] * 100 for _, v in voci]
        basso = [q - v["intervallo_basso"] * 100 for q, (_, v) in zip(quote, voci)]
        alto = [v["intervallo_alto"] * 100 - q for q, (_, v) in zip(quote, voci)]

        asse.errorbar(
            quote,
            posizioni,
            xerr=[basso, alto],
            fmt="o",
            markersize=4,
            capsize=2.5,
            linewidth=0.9,
            color=layout.GRIGI[0] if not (schermo or layout.STAMPA_A_COLORI) else layout.COLORI_SCHERMO[0],
            zorder=3,
        )
        asse.axvline(
            aggregato["attesa_sotto_il_caso"] * 100,
            color=layout.GRIGI[1] if not (schermo or layout.STAMPA_A_COLORI) else "#a63603",
            linestyle="--",
            linewidth=0.9,
            zorder=2,
        )
        asse.set_yticks(posizioni)
        asse.set_yticklabels(
            [
                f"{nome}\nn = {v['strutture']}"
                for nome, v in voci
            ],
            fontsize=7,
        )
        asse.set_xlim(0, 100)
        asse.set_ylim(-0.7, len(voci) - 0.3)
        asse.set_xlabel("strutture conformi (%)")
        asse.set_title(
            f"strutture a {struttura} tempi\ncaso: "
            f"{layout.numero(aggregato['attesa_sotto_il_caso'] * 100, 0)}%",
            fontsize=8,
        )

    return layout.salva(fig, "sequenze_intervalli", libro=2, schermo=schermo)


FIGURE = (
    livelli_sovrapposizione,
    convergenza_per_livello,
    swing_condizionato,
    violazione_contro_tenuta,
    sequenze_intervalli,
)


if __name__ == "__main__":
    for funzione in FIGURE:
        for schermo in (False, True):
            print(funzione(schermo=schermo))
