"""Il test di sovrapposizione e il rapporto fra le durate sono la stessa misura.

E' il conto di verifica nato da un'osservazione di Luigi sul motore: il criterio
dichiarato — sovrapposizione bidirezionale oltre l'ottanta per cento — marca
**T+1 su tutti e tre i mercati**, e il modulo `analysis_phantom.py` lo scrive
nella propria rettifica. La conclusione del capitolo 1 del libro 2, «T+1 esiste
ma non e' distinto da T», e' quindi confermata dal motore stesso. Questo conto
non la tocca: guarda **come ci si arriva**, e trova che le due strade che il
capitolo presenta come indipendenti sono una sola.

**Che cosa dice il capitolo 1.** Che il risultato su T+1 poggia su due misure:
il rapporto fra le durate mediane (1,19 su Bitcoin, ben sotto il due che una
gerarchia richiederebbe) e la sovrapposizione bidirezionale fra i minimi (86,3%,
sopra la soglia dell'80%). E che le due «concordano partendo da grandezze
diverse», cioe' che la seconda conferma la prima **per una via indipendente**.

**Che cosa questo conto verifica.** Il capitolo stesso, due paragrafi prima,
scrive la @eq-01-propri: in una gerarchia sincronizzata il figlio ha
`n_f (1 - P_f/P_p)` minimi propri. Letta al rovescio, quella formula dice che la
sovrapposizione attesa vale **`P_f/P_p`** — cioe' e' il rapporto fra le durate,
scritto in un altro modo. Se le due grandezze coincidono sui dati, non ci sono
due misure che concordano: ce n'e' una sola, riportata due volte, e la soglia
dell'80% sulla sovrapposizione **e' identica** alla soglia 1,25 sul rapporto
delle durate. Va detto, perche' due prove che concordano valgono piu' di una, e
qui non ce ne sono due.

**Il conto, in tre parti.**

1. *L'attesa contro il misurato.* Per ogni coppia di livelli adiacenti e ogni
   mercato: le durate mediane del bundle, l'attesa `P_f/P_p` che ne discende, e
   la sovrapposizione che il motore ha misurato e congelato in
   `dati/serie/*/phantom/matrix.json`. Se lo scarto e' piccolo su tutte e
   quindici le coppie, l'identita' e' stabilita sui dati e non per argomento.
2. *La soglia tradotta.* La soglia dell'80% sulla sovrapposizione corrisponde a
   un rapporto fra durate di **1,25**. Si riporta, per ogni coppia, da quale
   parte della soglia stia il rapporto e da quale parte la sovrapposizione: se
   le due classificazioni coincidono sempre, il criterio e' uno.
3. *La stessa misura con un rilevatore che non annida.* Il rilevatore del motore
   costruisce i livelli annidati; quello elementare della Parte V li trova
   indipendentemente uno dall'altro. Si riporta la sovrapposizione che ne esce,
   accanto a quella del motore, per mostrare quanto della coincidenza venga
   dalla costruzione. Accanto, per riferimento, la nube di **200 repliche a
   fase randomizzata** e **200 AAFT**.

**Un limite del nullo, dichiarato invece che nascosto.** La randomizzazione di
fase conserva lo spettro di potenza: una serie con un ciclo solo e una con due
cicli veri hanno spettri diversi, e le loro repliche li conservano. Il confronto
con le repliche non puo' quindi rispondere alla domanda «uno o due cicli?» — e
il controllo sintetico che ci ha provato non e' passato, il che e' il modo
giusto di accorgersene. Serve a rispondere a una domanda piu' stretta: *dato
questo spettro, la coincidenza fra i due livelli e' quella che il rilevatore
produce comunque?* La nube e' riportata per quello, ed e' **descrittiva**.

**Controlli sintetici, con la risposta nota prima dell'esecuzione.** Tre
gerarchie costruite a mano, in cui i minimi del padre sono per costruzione un
sotto-insieme di quelli del figlio, con rapporti 1,2 — 2 — 4. La
sovrapposizione bidirezionale misurata deve valere `1/rapporto` entro 0,05:
0,83, 0,50 e 0,25. E' il controllo della formula e del codice che la applica
insieme, ed e' l'unico che questo conto puo' passare in modo pulito.

**Determinismo.** Seme fisso `20260826 + indice del mercato` per le repliche a
fase randomizzata, `+ 100` per le AAFT. Due esecuzioni, stesso file byte per
byte.

Uscita: rapporto a schermo e `dati/misure/livelli-sovrapposizione.json`.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from acbook import surrogati as S  # noqa: E402

RADICE = Path(__file__).resolve().parents[2]
VERDETTI = RADICE / "dati" / "verdetti"
SERIE = RADICE / "dati" / "serie"
USCITA = RADICE / "dati" / "misure" / "livelli-sovrapposizione.json"

ASSET = ("BTCUSDT", "ETHUSDT", "SOLUSDT")
COPPIE = (("T", "T+1"), ("T+1", "T+2"), ("T+2", "T+3"), ("T+3", "T+4"),
          ("T+4", "T+5"))
N_REPLICHE = 200
SOGLIA_PHANTOM = 0.80
#: La stessa soglia, tradotta in rapporto fra durate: `1 / 0,80`.
SOGLIA_RAPPORTO = 1.0 / SOGLIA_PHANTOM
SEME = 20260826


def tolleranza(periodo_corto: int) -> int:
    """La tolleranza del motore: dieci per cento del periodo corto, minimo tre."""
    return max(3, int(periodo_corto * 0.10))


def sovrapposizione(a: np.ndarray, b: np.ndarray, tol: int) -> float:
    """La frazione di minimi di `a` che trovano un minimo di `b` entro `tol`."""
    if len(a) == 0 or len(b) == 0:
        return 0.0
    return float(sum(1 for t in a if np.min(np.abs(b - t)) <= tol) / len(a))


def bidirezionale_da_indici(a: np.ndarray, b: np.ndarray, tol: int) -> float:
    """La minore delle due direzioni: e' la grandezza che porta informazione."""
    return min(sovrapposizione(a, b, tol), sovrapposizione(b, a, tol))


def bidirezionale(serie: np.ndarray, corto: int, lungo: int) -> tuple[float, int, int]:
    """La sovrapposizione fra due livelli trovati indipendentemente sulla serie."""
    a = S.minimi_veloci(serie, corto)
    b = S.minimi_veloci(serie, lungo)
    return bidirezionale_da_indici(a, b, tolleranza(corto)), len(a), len(b)


def attesa_dal_rapporto(mediana_corta: float, mediana_lunga: float) -> float:
    """La sovrapposizione che una gerarchia sincronizzata produce da sola.

    E' la @eq-01-propri del capitolo 1 letta al rovescio: se il figlio ha
    `n_f (1 - P_f/P_p)` minimi propri, la frazione che condivide con il padre
    vale `P_f/P_p`. Non dipende dai dati, solo dalle due durate mediane.
    """
    return float(min(1.0, mediana_corta / mediana_lunga))


def mediane_del_motore(simbolo: str) -> dict[str, float]:
    """Le durate mediane del modulo dei confronti fra mercati, dal bundle."""
    percorso = VERDETTI / f"{simbolo}_D" / "cross_asset" / "data.json"
    per_asset = json.loads(percorso.read_text(encoding="utf-8"))["per_asset"]
    return {nome: float(voce["median"]) for nome, voce in per_asset[simbolo].items()
            if voce.get("median")}


def sovrapposizioni_del_motore(simbolo: str) -> dict[tuple[str, str], float]:
    """La matrice di sovrapposizione congelata, cella per cella."""
    percorso = SERIE / f"{simbolo}_D" / "phantom" / "matrix.json"
    traccia = list(
        json.loads(percorso.read_text(encoding="utf-8"))["tracce"].values()
    )[0]
    nomi, valori = traccia["x"], traccia["z"]
    return {
        (nomi[i], nomi[j]): float(valori[i][j])
        for i in range(len(nomi)) for j in range(len(nomi)) if i != j
    }


#: I tre controlli, con la risposta nota prima dell'esecuzione.
CONTROLLI = ({"rapporto": 1.2}, {"rapporto": 2.0}, {"rapporto": 4.0})
PERIODO_DI_LABORATORIO = 20
MINIMI_DI_LABORATORIO = 400
TOLLERANZA_DEL_CONTROLLO = 0.05


def controlli_sintetici() -> list[dict]:
    """Gerarchie costruite a mano: il padre e' un sotto-insieme del figlio.

    Se i minimi del padre sono uno ogni `k` del figlio, la sovrapposizione
    bidirezionale vale `1/k` per costruzione. E' il controllo della formula e
    del codice che la applica, con la risposta nota senza bisogno di dati.
    """
    righe = []
    for caso in CONTROLLI:
        rapporto = caso["rapporto"]
        figlio = np.arange(MINIMI_DI_LABORATORIO) * PERIODO_DI_LABORATORIO
        scelti = np.unique(
            np.round(np.arange(0, len(figlio) - 1, rapporto)).astype(int)
        )
        padre = figlio[scelti]
        misurata = bidirezionale_da_indici(
            figlio, padre, tolleranza(PERIODO_DI_LABORATORIO)
        )
        attesa = 1.0 / rapporto
        assert 0.0 <= misurata <= 1.0, "sovrapposizione fuori da [0, 1]"
        righe.append(
            {
                "rapporto": rapporto,
                "atteso": round(attesa, 4),
                "minimi_corti": int(len(figlio)),
                "minimi_lunghi": int(len(padre)),
                "sovrapposizione": round(misurata, 4),
                "superato": bool(abs(misurata - attesa) <= TOLLERANZA_DEL_CONTROLLO),
            }
        )
    return righe


def nubi_del_mercato(serie: np.ndarray, indice: int) -> dict:
    """La sovrapposizione misurata su duecento repliche per tipo, coppia per coppia."""
    nubi: dict = {}
    for etichetta, costruttore, scarto in (
        ("fase", S.surrogato, 0),
        ("aaft", S.surrogato_aaft, 100),
    ):
        rng = np.random.default_rng(SEME + indice + scarto)
        raccolta: dict = {coppia: [] for coppia in COPPIE}
        for _ in range(N_REPLICHE):
            replica = costruttore(serie, rng)
            for corto, lungo in COPPIE:
                raccolta[(corto, lungo)].append(
                    bidirezionale(replica, S.NOMINALI[corto], S.NOMINALI[lungo])[0]
                )
        for coppia, valori in raccolta.items():
            nubi.setdefault(coppia, {})[etichetta] = np.array(valori)
    return nubi


def controlla_dominio(voce: dict, dove: str) -> None:
    """Ogni quantita' nel suo intervallo ammesso, prima di essere stampata."""
    for chiave in ("sovrapposizione", "sovrapposizione_del_motore",
                   "attesa_dal_rapporto", "sovrapposizione_fase_mediana",
                   "sovrapposizione_aaft_mediana"):
        assert 0.0 <= voce[chiave] <= 1.0, f"{dove}: {chiave} fuori da [0, 1]"
    assert -1.0 <= voce["scarto_attesa_motore"] <= 1.0, (
        f"{dove}: scarto fuori da [-1, 1]"
    )
    assert voce["rapporto_delle_durate"] > 0, f"{dove}: rapporto non positivo"


def confronto() -> list[dict]:
    """Le tre parti del conto, coppia per coppia e mercato per mercato."""
    righe = []
    for indice, asset in enumerate(ASSET):
        serie = S.chiusure(asset)
        mediane = mediane_del_motore(asset)
        del_motore = sovrapposizioni_del_motore(asset)
        nubi = nubi_del_mercato(serie, indice)
        for corto, lungo in COPPIE:
            if corto not in mediane or lungo not in mediane:
                continue
            if (corto, lungo) not in del_motore:
                continue
            attesa = attesa_dal_rapporto(mediane[corto], mediane[lungo])
            misurata = del_motore[(corto, lungo)]
            elementare, na, nb = bidirezionale(
                serie, S.NOMINALI[corto], S.NOMINALI[lungo]
            )
            nube = nubi[(corto, lungo)]
            voce = {
                "asset": S.NOMI[asset],
                "coppia": f"{corto}-{lungo}",
                "mediana_corta": mediane[corto],
                "mediana_lunga": mediane[lungo],
                "rapporto_delle_durate": round(mediane[lungo] / mediane[corto], 3),
                "attesa_dal_rapporto": round(attesa, 4),
                "sovrapposizione_del_motore": round(misurata, 4),
                "scarto_attesa_motore": round(misurata - attesa, 4),
                "sovrapposizione": round(elementare, 4),
                "minimi_corti": int(na),
                "minimi_lunghi": int(nb),
                "sovrapposizione_fase_mediana": round(float(np.median(nube["fase"])), 4),
                "sovrapposizione_aaft_mediana": round(float(np.median(nube["aaft"])), 4),
                "repliche_fase": int(len(nube["fase"])),
                "repliche_aaft": int(len(nube["aaft"])),
            }
            voce["motore_sopra_la_soglia"] = bool(misurata > SOGLIA_PHANTOM)
            voce["rapporto_sotto_la_soglia"] = bool(
                voce["rapporto_delle_durate"] < SOGLIA_RAPPORTO
            )
            voce["le_due_soglie_concordano"] = bool(
                voce["motore_sopra_la_soglia"] == voce["rapporto_sotto_la_soglia"]
            )
            controlla_dominio(voce, f"{S.NOMI[asset]} {corto}-{lungo}")
            righe.append(voce)
    return righe


def sintesi_da(righe: list[dict]) -> dict:
    """I tre numeri che riassumono il conto."""
    scarti = [abs(r["scarto_attesa_motore"]) for r in righe]
    prime = [r for r in righe if r["coppia"] == "T-T+1"]
    return {
        "coppie": len(righe),
        "scarto_assoluto_mediano": round(float(np.median(scarti)), 4),
        "scarto_assoluto_massimo": round(float(np.max(scarti)), 4),
        "coppie_in_cui_le_due_soglie_concordano": sum(
            1 for r in righe if r["le_due_soglie_concordano"]
        ),
        "coppie_marcate_dal_motore": sum(
            1 for r in righe if r["motore_sopra_la_soglia"]
        ),
        "coppie_t_t1": len(prime),
        "t_t1_marcate": sum(1 for r in prime if r["motore_sopra_la_soglia"]),
        "soglia_in_rapporto_di_durate": round(SOGLIA_RAPPORTO, 3),
    }


def main() -> None:
    controlli = controlli_sintetici()
    print("Controlli sintetici (risposta nota prima dell'esecuzione)")
    print()
    print(f"{'gerarchia costruita':32s} {'atteso':>8s} {'n corti':>8s} "
          f"{'n lunghi':>9s} {'misurato':>9s} {'esito':>10s}")
    for c in controlli:
        print(f"{'padre = un minimo ogni ' + format(c['rapporto'], '.1f'):32s} "
              f"{c['atteso']:8.3f} {c['minimi_corti']:8d} {c['minimi_lunghi']:9d} "
              f"{c['sovrapposizione']:9.3f} "
              f"{'superato' if c['superato'] else 'FALLITO':>10s}")
    if not all(c["superato"] for c in controlli):
        raise SystemExit(
            "\nLa formula non riproduce una gerarchia costruita a mano: e' "
            "sbagliata, e i dati veri non servono."
        )

    righe = confronto()
    sintesi = sintesi_da(righe)

    print()
    print("L'attesa dal solo rapporto fra le durate, contro cio' che il motore misura")
    print()
    print(f"{'asset':10s} {'coppia':10s} {'P corta':>8s} {'P lunga':>8s} "
          f"{'rapporto':>9s} {'attesa':>7s} {'motore':>7s} {'scarto':>7s} "
          f"{'soglie':>10s}")
    for r in righe:
        print(f"{r['asset']:10s} {r['coppia']:10s} {r['mediana_corta']:8.1f} "
              f"{r['mediana_lunga']:8.1f} {r['rapporto_delle_durate']:9.2f} "
              f"{r['attesa_dal_rapporto']:7.3f} "
              f"{r['sovrapposizione_del_motore']:7.3f} "
              f"{r['scarto_attesa_motore']:+7.3f} "
              f"{('concordi' if r['le_due_soglie_concordano'] else 'DISCORDI'):>10s}")

    print()
    print("La stessa coppia con un rilevatore che non annida i livelli")
    print()
    print(f"{'asset':10s} {'coppia':10s} {'motore':>7s} {'elementare':>11s} "
          f"{'n corti':>8s} {'n lunghi':>9s} {'fase':>7s} {'aaft':>7s}")
    for r in righe:
        print(f"{r['asset']:10s} {r['coppia']:10s} "
              f"{r['sovrapposizione_del_motore']:7.3f} {r['sovrapposizione']:11.3f} "
              f"{r['minimi_corti']:8d} {r['minimi_lunghi']:9d} "
              f"{r['sovrapposizione_fase_mediana']:7.3f} "
              f"{r['sovrapposizione_aaft_mediana']:7.3f}")

    print()
    print(f"Scarto fra attesa e misurato: mediano "
          f"{sintesi['scarto_assoluto_mediano']:.3f}, massimo "
          f"{sintesi['scarto_assoluto_massimo']:.3f} su {sintesi['coppie']} coppie.")
    print(f"Le due soglie — 80% sulla sovrapposizione e "
          f"{sintesi['soglia_in_rapporto_di_durate']:.2f} sul rapporto delle durate "
          f"— danno la stessa classificazione su "
          f"{sintesi['coppie_in_cui_le_due_soglie_concordano']} coppie su "
          f"{sintesi['coppie']}.")
    print(f"Coppie marcate dal motore: {sintesi['coppie_marcate_dal_motore']}, di cui "
          f"{sintesi['t_t1_marcate']} sono le tre T-T+1.")

    rapporto = {
        "snapshot": "2026-06-15",
        "seme": SEME,
        "repliche": N_REPLICHE,
        "soglia_phantom": SOGLIA_PHANTOM,
        "soglia_rapporto": round(SOGLIA_RAPPORTO, 3),
        "controlli_sintetici": controlli,
        "confronti": righe,
        "sintesi": sintesi,
        "deviazioni": [],
    }

    USCITA.parent.mkdir(parents=True, exist_ok=True)
    USCITA.write_text(
        json.dumps(rapporto, ensure_ascii=False, indent=1) + "\n", encoding="utf-8"
    )
    print()
    print(f"scritto {USCITA.relative_to(RADICE)}")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
