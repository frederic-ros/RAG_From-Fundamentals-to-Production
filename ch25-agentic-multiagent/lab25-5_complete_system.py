# -*- coding: utf-8 -*-
"""
Lab 25-5 — A complete agentic system

Learning objective
------------------
Assemble everything the chapter has built into one system: a conditional brain, a
bounded investigation, short- and long-term memory, a council of specialists, and
a supervisor with a budget.

For each question the execution graph is produced — the sequence of steps
actually taken — with its cost and an estimate of quality. The point is that each
question follows a DIFFERENT route through the same system.

    A reliable agentic system is not the one that can do the most.
    It is the one that knows what it need not do.

No API key. Run generate_corpus.py first.
"""

import json
import re
import time
from collections import deque
from pathlib import Path

import agentkit as A

FRAG = Path(__file__).resolve().parent / "corpus" / "fragments.json"
DOM = Path(__file__).resolve().parent / "corpus" / "domains.json"
MEM = Path(__file__).resolve().parent / "corpus" / "memoire_assistant.json"

ENTITE = re.compile(r"\b[ELPM]-\d{1,3}\b")
BUDGET_GLOBAL = 10


class AutonomousAssistant:
    """System agentique complet, under control of a budget global and of garde-fous."""

    def __init__(self, frags, domaines):
        self.frags = frags
        self.dependances = {}
        rech = A.Search([f["text"] for f in frags])
        self.outil = A.search_tool(rech, frags, k=4)
        # The council of specialists
        self.specialistes = []
        for cle, info in domaines.items():
            sub = [frags[i] for i in info["fragments"]]
            r = A.Search([f["text"] for f in sub])
            o = A.search_tool(r, sub, k=2)
            self.specialistes.append(A.SpecialistAgent(
                nom=info["agent"], domaine=cle, outil=o, mots_cles=info["keywords"]))
        self.orch = A.Orchestrator(self.specialistes, budget=6)
        self.memoire = A.LongTermMemory(str(MEM))

    def process(self, question, dependances):
        self.dependances = dependances
        cpt = A.Counter()
        graphe = []
        t0 = time.perf_counter()

        # --- 1. ANALYSER (routeur conditionnel) ---------------------------
        decision, _ = A.cerveau_conditionnel(question, [], cpt)
        graphe.append(("ANALYSE", f"routeur → {decision}"))
        if decision == "repondre":
            graphe.append(("ANSWER", "a direct answer, no resource mobilised"))
            return self._finaliser(question, "A direct answer (no search).",
                                   graphe, cpt, t0, qualite=float("nan"))

        # --- 2-3. INVESTIGATE: decompose the dependencies -------------------------
        entites = ENTITE.findall(question)
        chaine = []
        if entites:
            chaine = self._enqueter(entites[0], cpt, graphe)

        # --- 4. CONSULTER the conseil multi-agents -------------------------
        if cpt.total < BUDGET_GLOBAL:
            res_orch = self.orch.process(question, cpt)
            for r in res_orch["retenues"]:
                graphe.append(("CONSULTATION", f"{r['agent']} : {r['contribution'][:55]}…"))
            for r in res_orch["rejetees"]:
                graphe.append(("CRITIC", f"{r['agent']} rejected (unreliable)"))
            synthese = res_orch["reponse"]
        else:
            graphe.append(("SUPERVISOR", "global budget reached, consultation short-circuited"))
            synthese = "A partial synthesis (budget reached)."

        # --- 5. MEMORISE ----------------------------------------------------------
        if chaine:
            self.memoire.memoriser(f"impact_{entites[0]}", " → ".join([entites[0]] + chaine),
                                   "fait")
            graphe.append(("MEMORY", f"impact chain memorised: "
                                      f"{entites[0]} → {' → '.join(chaine)}"))

        # --- 6. RECOMMANDER -----------------------------------------------
        reco = self._recommander(entites[0] if entites else None, chaine, synthese)
        graphe.append(("RECOMMANDATION", reco[:60] + "…"))

        # Quality : the recommandation cite-t-it the string of impact attendue ?
        q = self._qualite(chaine, reco)
        return self._finaliser(question, reco, graphe, cpt, t0, qualite=q)

    def _enqueter(self, depart, cpt, graphe):
        """Decompose the chain of dependencies: the investigator agent, budget-bounded."""
        file, vus, chaine = deque([depart]), {depart}, []
        while file and cpt.total < BUDGET_GLOBAL:
            courant = file.popleft()
            cpt.rech()
            res = self.outil.appeler(requete=f"{courant} supplies depends impact equipment")
            # Prefer the passage that mentions the entity AND names other entities
            # (ses dependances), not seulement the meilleur score lexical.
            candidats = [r["text"] for r in res if courant.lower() in r["text"].lower()]
            passage = max(candidats or [res[0]["text"]],
                          key=lambda txt: len([e for e in ENTITE.findall(txt)
                                               if e != courant]))
            for dep in ENTITE.findall(passage):
                if dep not in vus:
                    vus.add(dep)
                    file.append(dep)
                    chaine.append(dep)
            graphe.append(("INVESTIGATION", f"{courant} -> dependencies: "
                                      f"{', '.join(d for d in ENTITE.findall(passage) if d != courant) or '—'}"))
        return chaine

    def _recommander(self, entite, chaine, synthese):
        if entite and chaine:
            return (f"{entite} failure: downstream equipment impacted ({' -> '.join(chaine)}). "
                    f"Recommendation: isolate {entite}, warn those responsible for "
                    f"{chaine[-1]}, apply the emergency stop procedure. "
                    f"Contexte expert : {synthese[:80]}")
        return f"A recommendation founded on the consultation: {synthese[:160]}"

    def _qualite(self, chaine, reco):
        if not chaine:
            return 0.5
        cites = sum(1 for e in chaine if e in reco)
        return cites / len(chaine)

    def _finaliser(self, question, reponse, graphe, cpt, t0, qualite):
        latence = (time.perf_counter() - t0) * 1000
        return {"reponse": reponse, "graphe": graphe, "cout": cpt,
                "latence_ms": latence, "qualite": qualite}


def main() -> None:
    print("=" * 78)
    print("Lab 25-5 — L'assistant industriel autonome")
    print("=" * 78)

    if not FRAG.exists() or not DOM.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(FRAG.read_text(encoding="utf-8"))
    frags = data["fragments"]
    dependances = data.get("dependencies", {})
    domaines = json.loads(DOM.read_text(encoding="utf-8"))

    print(f"\nMode retrieval : {A.mode_retrieval()}   |   "
          f"Cerveau : {A.mode_cerveau()}   |   Budget global : {BUDGET_GLOBAL}")

    assistant = AutonomousAssistant(frags, domaines)

    panne = ("An unexpected failure: pump P-42 has stopped on the production line. "
             "Which equipment is impacted, and what do you recommend?")
    print("\n" + "=" * 78)
    print("INCIDENT")
    print("=" * 78)
    print(f"  \"{panne}\"")

    r = assistant.process(panne, dependances)

    # --- The execution graph --------------------------------------------------
    print("\n" + "=" * 78)
    print("THE EXECUTION GRAPH")
    print("=" * 78)
    for i, (etape, detail) in enumerate(r["graphe"], 1):
        print(f"  {i:>2d}. [{etape:<14s}] {detail}")

    print("\n  RECOMMANDATION FINALE :")
    print(f"    {r['reponse'][:260]}")

    # --- Analyse ------------------------------------------------------------
    print("\n" + "=" * 78)
    print("ANALYSIS OF THE SYSTEM")
    print("=" * 78)
    cpt = r["cout"]
    print(f"  Tools / searches called     : {cpt.recherches}")
    print(f"  Delegations to agents       : {cpt.delegations}")
    print(f"  Appels LLM                  : {cpt.appels_llm}")
    print(f"  Total cost                  : {cpt.total} (global budget {BUDGET_GLOBAL})")
    qa = "n/a" if r["qualite"] != r["qualite"] else f"{r['qualite']:.2f}"
    print(f"  Latency (simulated)         : {r['latence_ms']:.1f} ms")
    print(f"  Quality (the impact chain)  : {qa}")
    print("  Garde-fous actifs           : budget global, Critic, Supervisor")

    # --- Persistance --------------------------------------------------------
    print("\n  Long-term memory (persisted):")
    for cle, item in assistant.memoire.tout().items():
        print(f"    - {cle} = {item['valeur']}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  The system chains analysis, investigation, consultation, memorisation and")
    print("  recommendation on its own. But what makes it USABLE is not its capacity to")
    print("  act: it is the global budget that bounds its spending, the Critic that")
    print("  discards doubtful contributions, the Supervisor that can stop everything.")
    print("\n  WHAT TO REMEMBER: the challenge is no longer building an agent — the")
    print("  blocks are there. The challenge is CONTROLLING it: without guard rails,")
    print("  autonomy is not a feature, it is an amplifier of risk.")


if __name__ == "__main__":
    main()
