"""Biglietti da visita Carola Castiglione: PSD a livelli, 300 DPI, con abbondanza."""
import os
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from psdwriter import write_psd

QUI = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(QUI, "fonts")

# ---- misure di stampa ----
# Il progetto e' disegnato in unita' a 300 DPI; alzando DPI tutto scala di conseguenza.
DPI = int(os.environ.get("CARD_DPI", "300"))
S = DPI / 300.0                      # fattore di scala rispetto al disegno base
PX_MM = DPI / 25.4
PT = DPI / 72.0                      # 1 punto tipografico in pixel


def u(px300):
    """Converte una misura pensata a 300 DPI nella risoluzione corrente."""
    return int(round(px300 * S))


TRIM_W, TRIM_H = u(1004), u(650)     # 85 x 55 mm
BLEED = u(35)                        # 3 mm di abbondanza per lato
W, H = TRIM_W + 2 * BLEED, TRIM_H + 2 * BLEED
SAFE = u(59)                         # 5 mm di margine di sicurezza dal taglio

TRIM_L, TRIM_T = BLEED, BLEED
TRIM_R, TRIM_B = BLEED + TRIM_W, BLEED + TRIM_H
CX = W // 2

# ---- colori del brand ----
VERDE    = (27, 38, 33)
LINO     = (244, 238, 225)
OSSO     = (237, 232, 219)
OSSO_2   = (169, 176, 160)
AMBRA    = (217, 163, 68)
NOCCIOLA = (110, 122, 98)


def font(nome, punti):
    return ImageFont.truetype(os.path.join(FONTS, nome), int(round(punti * PT)))


CG   = lambda pt: font("CabinetGrotesk-Extrabold.ttf", pt)
SAT  = lambda pt: font("Satoshi-Medium.ttf", pt)
SATB = lambda pt: font("Satoshi-Bold.ttf", pt)


def nuovo():
    return Image.new("RGBA", (W, H), (0, 0, 0, 0))


def larghezza(testo, ft, tracking=0.0):
    misura = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    tot = sum(misura.textlength(c, font=ft) for c in testo)
    if len(testo) > 1:
        tot += tracking * (len(testo) - 1)
    return tot


def scrivi(livello, testo, ft, colore, x, y_ink, tracking=0.0, centra=False):
    """Disegna il testo con crenatura allargata, ancorando il bordo superiore dell'inchiostro a y_ink."""
    d = ImageDraw.Draw(livello)
    larg = larghezza(testo, ft, tracking)
    if centra:
        x = x - larg / 2
    inchiostro = ft.getbbox(testo)          # (x0, y0, x1, y1) rispetto alla linea di base alta
    y = y_ink - inchiostro[1]
    for c in testo:
        d.text((x, y), c, font=ft, fill=colore)
        x += d.textlength(c, font=ft) + tracking
    return inchiostro[3] - inchiostro[1]    # altezza dell'inchiostro


def altezza_ink(testo, ft):
    b = ft.getbbox(testo)
    return b[3] - b[1]


GEOMETRIA = {}   # posizione e misura del monogramma, per il passaggio vettoriale in GIMP


def monogramma(diametro, colore_c_est, colore_c_int, colore_orlo, alfa_orlo=0.24, ss=8):
    """Il piatto in filigrana con le due C che ne emergono. Ritorna un'immagine RGBA quadrata."""
    D = diametro * ss
    img = Image.new("RGBA", (D, D), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    c = D / 2

    def box(raggio_rel):
        r = raggio_rel * D
        return [c - r, c - r, c + r, c + r]

    orlo = colore_orlo + (int(round(255 * alfa_orlo)),)
    sp_orlo = max(1, int(round(0.015 * D)))
    d.ellipse(box(0.44), outline=orlo, width=sp_orlo)
    d.ellipse(box(0.27), outline=orlo, width=sp_orlo)

    def arco_capocchie(raggio_rel, gradi_apertura, colore, spessore_rel):
        """PIL disegna il tratto verso l'interno del riquadro: allargo di meta' spessore
        cosi' l'asse del tratto cade sul raggio nominale, come nell'SVG del sito."""
        import math
        r = raggio_rel * D
        sp = int(round(spessore_rel * D))
        est = r + sp / 2
        d.arc([c - est, c - est, c + est, c + est], gradi_apertura, 360 - gradi_apertura,
              fill=colore + (255,), width=sp)
        # estremita' arrotondate, come lo stroke-linecap del logo sul sito
        for ang in (gradi_apertura, -gradi_apertura):
            px = c + r * math.cos(math.radians(ang))
            py = c + r * math.sin(math.radians(ang))
            d.ellipse([px - sp / 2, py - sp / 2, px + sp / 2, py + sp / 2], fill=colore + (255,))

    arco_capocchie(0.44, 32, colore_c_est, 0.05)   # C esterna: orlo del piatto
    arco_capocchie(0.27, 45, colore_c_int, 0.045)  # C interna: fondo del piatto

    return img.resize((diametro, diametro), Image.LANCZOS)


def livello_guide():
    """Linee di taglio e area di sicurezza: livello nascosto, non va in stampa."""
    lv = nuovo()
    d = ImageDraw.Draw(lv)
    d.rectangle([TRIM_L, TRIM_T, TRIM_R - 1, TRIM_B - 1], outline=(255, 0, 128, 200), width=2)
    passo = u(18)
    for x in range(TRIM_L + SAFE, TRIM_R - SAFE, passo * 2):
        d.line([x, TRIM_T + SAFE, min(x + passo, TRIM_R - SAFE), TRIM_T + SAFE], fill=(0, 170, 255, 180), width=2)
        d.line([x, TRIM_B - SAFE, min(x + passo, TRIM_R - SAFE), TRIM_B - SAFE], fill=(0, 170, 255, 180), width=2)
    for y in range(TRIM_T + SAFE, TRIM_B - SAFE, passo * 2):
        d.line([TRIM_L + SAFE, y, TRIM_L + SAFE, min(y + passo, TRIM_B - SAFE)], fill=(0, 170, 255, 180), width=2)
        d.line([TRIM_R - SAFE, y, TRIM_R - SAFE, min(y + passo, TRIM_B - SAFE)], fill=(0, 170, 255, 180), width=2)
    return lv


def arr(img):
    return np.array(img, dtype=np.uint8)


# =====================  FRONTE  =====================
def fronte():
    NOME = "CAROLA CASTIGLIONE"
    RUOLO = "PRIVATE CHEF · ROMA"

    ft_nome = CG(14)
    tr_nome = 0.12 * ft_nome.size
    while larghezza(NOME, ft_nome, tr_nome) > TRIM_W - 2 * SAFE - u(40):
        ft_nome = CG(ft_nome.size / PT - 0.5)
        tr_nome = 0.12 * ft_nome.size

    ft_ruolo = SAT(7.5)
    tr_ruolo = 0.22 * ft_ruolo.size

    D_MONO = u(170)
    h_nome = altezza_ink(NOME, ft_nome)
    h_ruolo = altezza_ink(RUOLO, ft_ruolo)
    sp1, sp2, sp3 = u(54), u(32), u(28)          # respiro fra mono, nome, filetto, ruolo
    h_filetto = u(2)

    blocco = D_MONO + sp1 + h_nome + sp2 + h_filetto + sp3 + h_ruolo
    y = TRIM_T + (TRIM_H - blocco) / 2

    livelli = []

    fondo = Image.new("RGBA", (W, H), VERDE + (255,))
    livelli.append({"name": "Fondo", "image": arr(fondo)})

    lv = nuovo()
    pos = (int(CX - D_MONO / 2), int(y))
    lv.alpha_composite(monogramma(D_MONO, AMBRA, OSSO_2, OSSO), pos)
    livelli.append({"name": "Monogramma", "image": arr(lv)})
    GEOMETRIA["fronte"] = {"x": pos[0], "y": pos[1], "d": D_MONO}
    y += D_MONO + sp1

    lv = nuovo()
    scrivi(lv, NOME, ft_nome, OSSO + (255,), CX, y, tr_nome, centra=True)
    livelli.append({"name": "Nome", "image": arr(lv)})
    y += h_nome + sp2

    lv = nuovo()
    ImageDraw.Draw(lv).rectangle([CX - u(36), y, CX + u(36), y + h_filetto - 1], fill=AMBRA + (255,))
    livelli.append({"name": "Filetto", "image": arr(lv)})
    y += h_filetto + sp3

    lv = nuovo()
    scrivi(lv, RUOLO, ft_ruolo, OSSO_2 + (255,), CX, y, tr_ruolo, centra=True)
    livelli.append({"name": "Ruolo", "image": arr(lv)})

    livelli.append({"name": "Guide taglio (non stampare)", "image": arr(livello_guide()), "visible": False})
    return livelli


# =====================  RETRO  =====================
def retro():
    CLAIM = ["Cucina genuina,", "a casa vostra."]
    CONTATTI = ["carola@carolacastiglione.it", "+39 000 000 0000", "carolacastiglione.it"]

    ft_claim = CG(12)
    interlinea_claim = int(round(ft_claim.size * 1.22))
    ft_cont = SAT(8.5)
    interlinea_cont = int(round(ft_cont.size * 1.55))

    D_MONO = u(104)
    x = TRIM_L + u(100)

    h_claim_riga = altezza_ink("Hg", ft_claim)
    h_claim = h_claim_riga + interlinea_claim
    h_cont_riga = altezza_ink("Hg@", ft_cont)
    h_cont = h_cont_riga + 2 * interlinea_cont
    sp1, sp2 = u(46), u(42)
    h_filetto = u(2)

    blocco = h_claim + sp1 + h_filetto + sp2 + h_cont
    y = TRIM_T + (TRIM_H - blocco) / 2

    livelli = []

    fondo = Image.new("RGBA", (W, H), LINO + (255,))
    livelli.append({"name": "Fondo", "image": arr(fondo)})

    lv = nuovo()
    pos = (int(TRIM_R - u(100) - D_MONO), int(y))
    lv.alpha_composite(monogramma(D_MONO, AMBRA, NOCCIOLA, VERDE, alfa_orlo=0.22), pos)
    livelli.append({"name": "Monogramma", "image": arr(lv)})
    GEOMETRIA["retro"] = {"x": pos[0], "y": pos[1], "d": D_MONO}

    lv = nuovo()
    yy = y
    for riga in CLAIM:
        scrivi(lv, riga, ft_claim, VERDE + (255,), x, yy)
        yy += interlinea_claim
    livelli.append({"name": "Claim", "image": arr(lv)})

    y += h_claim + sp1
    lv = nuovo()
    ImageDraw.Draw(lv).rectangle([x, y, x + u(72), y + h_filetto - 1], fill=AMBRA + (255,))
    livelli.append({"name": "Filetto", "image": arr(lv)})
    y += h_filetto + sp2

    lv = nuovo()
    yy = y
    for riga in CONTATTI:
        scrivi(lv, riga, ft_cont, VERDE + (255,), x, yy)
        yy += interlinea_cont
    livelli.append({"name": "Contatti", "image": arr(lv)})

    livelli.append({"name": "Guide taglio (non stampare)", "image": arr(livello_guide()), "visible": False})
    return livelli


def esporta(nome, livelli, sfondo):
    psd = os.path.join(QUI, f"{nome}.psd")
    peso = write_psd(psd, W, H, livelli, dpi=DPI, background=sfondo)

    # anteprima appiattita, utile per controllo a schermo
    comp = Image.new("RGBA", (W, H), sfondo + (255,))
    for lv in livelli:
        if lv.get("visible", True):
            comp.alpha_composite(Image.fromarray(lv["image"], "RGBA"))
    comp.convert("RGB").save(os.path.join(QUI, f"{nome}.png"), dpi=(DPI, DPI))
    print(f"{nome}.psd  {W}x{H}px  {peso/1024/1024:.1f} MB  livelli: " +
          ", ".join(l["name"] for l in livelli))


if __name__ == "__main__":
    import json
    sfx = "" if DPI == 300 else f"-{DPI}dpi"
    esporta(f"carola-biglietto-fronte{sfx}", fronte(), VERDE)
    esporta(f"carola-biglietto-retro{sfx}", retro(), LINO)
    with open(os.path.join(QUI, f"geometria-monogramma{sfx}.json"), "w") as fh:
        json.dump(GEOMETRIA, fh, indent=2)
    print("geometria monogramma:", GEOMETRIA)
