# -*- coding: utf-8 -*-
"""
uxkit.py — the shared module of the Chapter 32 labs (user experience and
explainability).

The chapter's thesis — *a correct answer that cannot be verified is not a usable
answer* — stays entirely visible offline.

What this module supplies:

  - attribution     : matches each block of an answer to its source fragment,
                      with a fidelity score (the "compass");
  - trust score     : aggregates the retrieval, generation, source count,
                      contradiction and freshness signals;
  - calibration     : the ECE, and a threshold below which the system abstains;
  - perceived latency: the effect of streaming and of progressive disclosure;
  - implicit signals : reading, copying, reformulating, abandoning.

A NOTE ON THE STOP WORDS BELOW. They feed the lexical overlap used by the
attribution, so they must be in the language of the corpus. Left in French
against an English corpus they filter nothing, every grammatical word counts as
content, and the fidelity scores drift.
"""

from __future__ import annotations

import html
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

import numpy as np

CORPUS = Path(__file__).resolve().parent / "corpus"


# ===========================================================================
#  0)  Outils optionnels
# ===========================================================================
def _a_sentence_transformers() -> bool:
    try:
        import sentence_transformers  # noqa: F401
        return True
    except Exception:
        return False


def bandeau(titre: str) -> None:
    emb = "sentence-transformers" if _a_sentence_transformers() else "TF-IDF"
    print("=" * 74)
    print(titre)
    print(f"  Embeddings: {emb}   |   HTML demos: standalone (no server)")
    print("=" * 74)


def normaliser(texte: str) -> str:
    texte = unicodedata.normalize("NFD", texte.lower())
    texte = "".join(c for c in texte if unicodedata.category(c) != "Mn")
    return re.sub(r"[^a-z0-9 ]", " ", texte)


def _mots(texte: str) -> set[str]:
    stop = {"the", "a", "an", "of", "to", "in", "on", "for", "and", "or",
            "at", "by", "with", "is", "are", "be", "was", "were", "it", "its",
            "this", "that", "these", "what", "which", "who", "how", "when",
            "not", "more", "must", "can", "you", "we", "your", "our",
            "from", "as", "then", "so", "any"}
    return {m for m in normaliser(texte).split() if len(m) > 1 and m not in stop}


def phrases(texte: str) -> list[str]:
    parts = re.split(r"(?<=[\.\!\?])\s+", texte.strip())
    return [p.strip() for p in parts if p.strip()]


# ===========================================================================
#  1)  Index vectoriel
# ===========================================================================
class Embedder:
    def __init__(self, textes: list[str]):
        self.textes = textes
        if _a_sentence_transformers():
            from sentence_transformers import SentenceTransformer
            self._modele = SentenceTransformer("all-MiniLM-L6-v2")
            self.matrice = self._modele.encode(textes, normalize_embeddings=True)
            self._dense = True
        else:
            from sklearn.feature_extraction.text import TfidfVectorizer
            self._vect = TfidfVectorizer(token_pattern=r"[a-zA-Z0-9]{2,}",
                                         lowercase=True)
            self.matrice = self._vect.fit_transform(textes).toarray()
            n = np.linalg.norm(self.matrice, axis=1, keepdims=True)
            self.matrice = self.matrice / np.clip(n, 1e-9, None)
            self._dense = False

    def encoder(self, texte: str) -> np.ndarray:
        if self._dense:
            return self._modele.encode([texte], normalize_embeddings=True)[0]
        v = self._vect.transform([texte]).toarray()[0]
        return v / max(np.linalg.norm(v), 1e-9)


class Search:
    def __init__(self, fragments: list[dict]):
        self.fragments = fragments
        self.emb = Embedder([f["texte"] for f in fragments])

    def chercher(self, requete: str, k: int = 5) -> list[dict]:
        q = self.emb.encoder(requete)
        scores = self.emb.matrice @ q
        ordre = np.argsort(scores)[::-1][:k]
        out = []
        for i in ordre:
            f = dict(self.fragments[i])
            f["score"] = float(scores[i])
            out.append(f)
        return out


# ===========================================================================
# 2) Citations : ancrer each sentence generated to son fragment source
# ===========================================================================
def _similarite_lexicale(a: str, b: str) -> float:
    ma, mb = _mots(a), _mots(b)
    if not ma or not mb:
        return 0.0
    return len(ma & mb) / len(ma | mb)


def ancrer_citations(reponse_blocs: list[str], fragments: list[dict],
                     threshold: float = 0.12) -> list[dict]:
    """Relie each bloc/sentence of the answer to son fragment the more probable.

 Return a list of {bloc, frag_id, frag_title, frag_texte, fidelite}.
 `fidelite` ∈ [0,1] = correspondance texte generated / fragment (boussole of
    the fidelity compass of Lab 32-1). Below the threshold, the block is marked
    "unsourced".
 """
    ancres = []
    for bloc in reponse_blocs:
        meilleur, score = None, 0.0
        for f in fragments:
            s = _similarite_lexicale(bloc, f["texte"])
            if s > score:
                meilleur, score = f, s
        if meilleur and score >= threshold:
            ancres.append({"bloc": bloc, "frag_id": meilleur["id"],
                           "frag_titre": meilleur.get("titre", ""),
                           "frag_texte": meilleur["texte"],
                           "page": meilleur.get("page"),
                           "document": meilleur.get("document"),
                           "fidelite": round(score, 3), "source": True})
        else:
            ancres.append({"bloc": bloc, "frag_id": None, "frag_titre": "",
                           "frag_texte": "", "page": None, "document": None,
                           "fidelite": round(score, 3), "source": False})
    return ancres


def provenance_narrative(ancres: list[dict]) -> str:
    """Summary in head of answer : on quels documents appuie the answer."""
    docs = []
    for a in ancres:
        if a["source"] and a["document"] and a["document"] not in docs:
            docs.append(a["document"])
    if not docs:
        return "This answer rests on no verifiable source."
    if len(docs) == 1:
        return f"This answer rests on: {docs[0]}."
    return ("This answer rests on: "
            + ", ".join(docs[:-1]) + f" et {docs[-1]}.")


def ancre_persistante(document: str, page: int | None, frag_id: str) -> str:
    """A stable anchor address that survives reindexing: document, page and
    fragment id, independent of the position in the vector index."""
    base = f"{document}#p={page}" if page else document
    return f"{base}&frag={frag_id}"


# ===========================================================================
# 3) Gestion of the incertitude : states, messages, calibration
# ===========================================================================
@dataclass
class ConfidenceThresholds:
    eleve: float = 0.45      # at the-dessus : trust high
    abstention: float = 0.18  # en dessous : abstention


def etat_confiance(score_retrieval: float, score_generation: float,
                   n_sources: int, contradiction: bool,
                   thresholds: ConfidenceThresholds | None = None) -> str:
    """Returns 'elevee' | 'low' | 'abstention'.
 Combine the score of retrieval, the coherence and the number of sources."""
    s = thresholds or ConfidenceThresholds()
    score = min(score_retrieval, score_generation)
    if score < s.abstention or n_sources == 0:
        return "abstention"
    if contradiction or score < s.eleve or n_sources < 2:
        return "faible"
    return "elevee"


def message_operationnel(etat: str, n_sources: int, fraicheur: str = "",
                         contradiction: bool = False) -> dict:
    """Traduit a state in LANGAGE CLAIR — never in pourcentage.
 Returns {bandeau, couleur, message, ton_reponse}."""
    if etat == "elevee":
        frais = f", {fraicheur}" if fraicheur else ""
        return {"bandeau": None, "couleur": "vert",
                "message": f"Official documentation found, consistent across "
                           f"{n_sources} source(s){frais}.",
                "ton_reponse": "affirmatif"}
    if etat == "faible":
        cause = "sources in disagreement" if contradiction else \
                "correspondance documentaire partielle"
        return {"bandeau": "To be checked", "couleur": "orange",
                "message": f"Answer to be confirmed ({cause}). "
                           f"Check the sources before acting.",
                "ton_reponse": "conditionnel"}
    return {"bandeau": "Information unavailable", "couleur": "rouge",
            "message": "No reliable source found. I prefer to abstain rather "
                       "than invent. Escalation to an expert is offered.",
            "ton_reponse": "abstention"}


def ece(confiances: list[float], justes: list[bool], n_bacs: int = 5) -> float:
    """Expected Calibration Error: the mean gap |trust - accuracy|, weighted by
    the size of the bins. 0 means perfectly calibrated."""
    confiances = np.asarray(confiances, float)
    justes = np.asarray(justes, float)
    erreur, n = 0.0, len(confiances)
    if n == 0:
        return 0.0
    bornes = np.linspace(0.0, 1.0, n_bacs + 1)
    for i in range(n_bacs):
        lo, hi = bornes[i], bornes[i + 1]
        masque = (confiances > lo) & (confiances <= hi) if i > 0 \
            else (confiances >= lo) & (confiances <= hi)
        if masque.sum() == 0:
            continue
        conf_moy = confiances[masque].mean()
        exact_moy = justes[masque].mean()
        erreur += (masque.sum() / n) * abs(conf_moy - exact_moy)
    return float(erreur)


def calibrer_seuils(scores: list[float], justes: list[bool]) -> dict:
    """Search for the abstention threshold that best aligns trust with reliability.
 Returns {threshold, ece_avant, ece_apres, precision_servie}."""
    scores = np.asarray(scores, float)
    justes = np.asarray(justes, bool)
    ece_avant = ece(list(scores), list(justes))
    meilleur = {"threshold": 0.0, "ece_apres": ece_avant, "precision_servie": 0.0}
    for threshold in np.linspace(0.0, 0.6, 25):
        servis = scores >= threshold
        if servis.sum() < 3:
            continue
        prec = justes[servis].mean()
        # The perceived trust of what is 'served'; we want high precision
        e = abs(prec - 1.0)  # ideally, whatever is served is correct
        if prec > meilleur["precision_servie"] or (
                prec == meilleur["precision_servie"] and threshold < meilleur["threshold"]):
            meilleur = {"threshold": float(threshold), "ece_apres": float(e),
                        "precision_servie": float(prec)}
    meilleur["ece_avant"] = float(ece_avant)
    return meilleur


# ===========================================================================
# 4) Perceived latency: classic against streaming and split-screen
# ===========================================================================
@dataclass
class LatencyProfile:
    t_retrieval: float       # seconds until reranking ends
    t_premier_token: float   # seconds until the first generated token
    n_tokens: int
    debit_tokens: float      # tokens per second while streaming


def mesurer_latence_percue(p: LatencyProfile) -> dict:
    """Compare three modes on PERCEIVED latency: the time before useful reading.

      - classic: the user waits for the whole generation before seeing anything
 regardless of the implementation;
      - streaming: reading starts at the first token;
      - split-screen: the sources appear as soon as the reranking ends, so there is
 enough material to start checking before the first token arrives.
 """
    t_total = p.t_premier_token + p.n_tokens / max(p.debit_tokens, 1e-9)
    return {
        "classique": {"premier_utile": round(t_total, 2),
                      "total": round(t_total, 2)},
        "streaming": {"premier_utile": round(p.t_premier_token, 2),
                      "total": round(t_total, 2)},
        "split_screen": {"premier_utile": round(p.t_retrieval, 2),
                         "total": round(t_total, 2)},
        "gain_percu_vs_classique": round(
            (t_total - p.t_retrieval) / max(t_total, 1e-9), 3),
    }


# ===========================================================================
#  5)  Feedback implicite : comportement -> signal
# ===========================================================================
def signal_implicite(evenement: dict) -> dict:
    """Translate an observed behaviour into a plus or minus signal, with no explicit click.

 `evenement` contient the type and ses parameters. Returns
 {signal: +1|-1|0, intensite: float, raison: str}.
 """
    t = evenement.get("type")
    if t == "lecture_source":
        duree = evenement.get("duree_s", 0)
        if duree > 15:
            return {"signal": +1, "intensite": min(1.0, duree / 30),
                    "raison": "long reading of a source"}
        if duree < 3:
            return {"signal": -1, "intensite": 0.6,
                    "raison": "source clicked then closed instantly"}
        return {"signal": 0, "intensite": 0.0, "raison": "a brief read"}
    if t == "copier_coller":
        return {"signal": +1, "intensite": 0.9,
                "raison": "the answer copied immediately"}
    if t == "reformulation":
        return {"signal": -1, "intensite": 0.8,
                "raison": "immediate reformulation (an unsatisfactory answer)"}
    if t == "abandon":
        return {"signal": -1, "intensite": 0.7,
                "raison": "closed without reading"}
    if t == "vote":
        v = evenement.get("valeur", 0)
        return {"signal": v, "intensite": 1.0, "raison": "vote explicite"}
    return {"signal": 0, "intensite": 0.0, "raison": "neutre"}


def agreger_signaux(signaux: list[dict]) -> dict:
    """Aggregate the signals into usability indicators, per query and document."""
    par_requete: dict = {}
    par_document: dict = {}
    for s in signaux:
        sig = signal_implicite(s)
        score = sig["signal"] * sig["intensite"]
        rq = s.get("requete", "?")
        doc = s.get("document", "?")
        par_requete.setdefault(rq, []).append(score)
        if doc:
            par_document.setdefault(doc, []).append(score)
    resume_rq = {q: round(sum(v) / len(v), 3) for q, v in par_requete.items()}
    resume_doc = {d: round(sum(v) / len(v), 3) for d, v in par_document.items()}
    problematiques = sorted([q for q, s in resume_rq.items() if s < 0],
                            key=lambda q: resume_rq[q])
    return {"par_requete": resume_rq, "par_document": resume_doc,
            "requetes_problematiques": problematiques}


# ===========================================================================
# 6) Standalone HTML demos, openable in a browser with no server
# ===========================================================================
def html_citations(question: str, ancres: list[dict], provenance: str,
                   path: Path) -> Path:
    """Generate a standalone HTML page: an answer with popover citations."""
    blocs_html = []
    for i, a in enumerate(ancres, 1):
        bloc = html.escape(a["bloc"])
        if a["source"]:
            couleur = ("#2e7d32" if a["fidelite"] >= 0.25 else
                       "#f9a825" if a["fidelite"] >= 0.15 else "#c62828")
            pop = html.escape(a["frag_texte"])
            titre = html.escape(a["frag_titre"])
            blocs_html.append(
                f'{bloc} <span class="cite" style="--c:{couleur}">'
                f'[{i}]<span class="pop"><b>{titre}</b><br>{pop}'
                f'<br><i>fidelity {a["fidelite"]:.0%}</i></span></span>')
        else:
            blocs_html.append(
                f'{bloc} <span class="cite nosrc">[unsourced]</span>')
    corps = " ".join(blocs_html)
    doc = f"""<!doctype html><html lang="fr"><meta charset="utf-8">
<title>Citations interactives — RAG</title>
<style>
 body{{font-family:system-ui,sans-serif;max-width:720px;margin:40px auto;
      line-height:1.7;color:#222;padding:0 16px}}
 .prov{{background:#eef3fb;border-left:4px solid #1f5fbf;padding:10px 14px;
       border-radius:6px;font-size:.95em;margin-bottom:20px}}
 .cite{{position:relative;cursor:pointer;color:#fff;background:var(--c,#1f5fbf);
       border-radius:4px;padding:0 5px;font-size:.8em;font-weight:600}}
 .cite.nosrc{{background:#9e9e9e}}
 .pop{{display:none;position:absolute;left:0;top:1.6em;width:320px;z-index:9;
      background:#fff;color:#222;border:1px solid #ccc;border-radius:8px;
      padding:10px 12px;box-shadow:0 6px 24px rgba(0,0,0,.18);font-weight:400;
      font-size:1rem}}
 .cite:hover .pop{{display:block}}
 h1{{font-size:1.3em}}
</style>
<h1>{html.escape(question)}</h1>
<div class="prov">{html.escape(provenance)}</div>
<p>{corps}</p>
<p style="color:#666;font-size:.85em">Hover the badges to check the source.
The colour encodes the fidelity compass (green: faithful, orange:
partiel, rouge : faible).</p>
</html>"""
    path.write_text(doc, encoding="utf-8")
    return path


def html_stream(question: str, ancres: list[dict], etat: dict,
               profil: dict, path: Path) -> Path:
    """A split-screen demo: the answer streams on the left, sources on the right."""
    texte = " ".join(a["bloc"] for a in ancres)
    sources = [{"id": a["frag_id"], "titre": a["frag_titre"],
                "texte": a["frag_texte"]} for a in ancres if a["source"]]
    data = json.dumps({"texte": texte, "sources": sources, "etat": etat,
                       "profil": profil}, ensure_ascii=False)
    couleur = {"vert": "#2e7d32", "orange": "#f9a825",
               "rouge": "#c62828"}.get(etat.get("couleur", "vert"), "#2e7d32")
    doc = f"""<!doctype html><html lang="fr"><meta charset="utf-8">
<title>Streaming + split-screen — RAG</title>
<style>
 body{{font-family:system-ui,sans-serif;margin:0;color:#222}}
 header{{background:{couleur};color:#fff;padding:12px 18px}}
 .wrap{{display:flex;gap:0;height:70vh}}
 .col{{flex:1;padding:18px;overflow:auto}}
 .left{{border-right:1px solid #e0e0e0}}
 .src{{background:#f6f8fc;border:1px solid #dce4f2;border-radius:8px;
      padding:10px 12px;margin-bottom:10px}}
 .src b{{color:#1f5fbf}} h2{{font-size:1em;color:#555}}
 #curseur{{color:{couleur}}}
</style>
<header><b>{html.escape(question)}</b><br>
<span style="font-size:.9em">{html.escape(etat.get('message',''))}</span></header>
<div class="wrap">
 <div class="col left"><h2>Answer (streaming)</h2><p id="rep"></p>
   <span id="curseur">▌</span></div>
 <div class="col"><h2>Sources (shown as soon as the reranking ends)</h2>
   <div id="src"></div></div>
</div>
<script>
const D = {data};
const src = document.getElementById('src');
D.sources.forEach(s => {{
  const d = document.createElement('div'); d.className='src';
  d.innerHTML = '<b>['+s.id+'] '+s.titre+'</b><br>'+s.texte; src.appendChild(d);
}});
const rep = document.getElementById('rep');
const mots = D.texte.split(' '); let i=0;
const debit = Math.max(1, D.profil.debit_tokens||8);
const timer = setInterval(()=>{{
  if(i>=mots.length){{clearInterval(timer);
    document.getElementById('curseur').style.display='none';return;}}
  rep.textContent += (i?' ':'')+mots[i++];
}}, 1000/debit);
</script></html>"""
    path.write_text(doc, encoding="utf-8")
    return path


# ===========================================================================
# 7) Chargement of the corpus
# ===========================================================================
def _load(nom: str):
    with open(CORPUS / nom, encoding="utf-8") as f:
        return json.load(f)


def load_fragments() -> list[dict]:
    return _load("documents.json")


def load_answers() -> list[dict]:
    return _load("reponses_rag.json")


def load_signals() -> list[dict]:
    return _load("signaux.json")
