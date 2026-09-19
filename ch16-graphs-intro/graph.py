# -*- coding: utf-8 -*-
"""
graph.py — the minimal knowledge graph of Chapter 16.

No graph database (Neo4j, Cypher) is needed. A relation is information in its own
right, and that is shown here by proof: a directed, labelled graph held in a
handful of dictionaries.

    A graph shows how the pieces of information are linked to each other.

Vocabulary (the chapter's "right word"):

  - a NODE is an entity: a piece of equipment, a supplier, a procedure.
    Identified by a unique name, for instance "P-42".
  - an EDGE is a NAMED relation between two nodes, written as a triple
    (subject, relation, object). For example ("P-42", "depends on", "M-18").

The relation labels are data, not decoration: the traversals below match on them
literally, so they must stay in step with generate_corpus.py.

This module supplies the strict minimum the labs need:

  - build the graph from triples;
  - traverse it (neighbours, a chain such as "superseded by", breadth-first
    search);
  - compute the domino effect, the set of nodes impacted by one of them.

No external dependency. Offline, deterministic, no API key.
"""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

# A triple: (subject, relation, object). The atomic unit of a graph.
Triple = Tuple[str, str, str]


class Graph:
    """A directed, labelled graph, held in plain dictionaries.

    The internal representation is deliberately transparent, so the reader can
    "see" the structure:

        self.types      : node name -> type, for instance "Pump"
        self.outgoing[n]: a list of (relation, neighbour) leaving n
        self.incoming[n]: a list of (relation, neighbour) arriving at n

    Both directions are kept, outgoing AND incoming, because some questions read
    one way ("what does P-42 depend on?") and others the other way ("what depends
    on M-18?" — the domino effect).
    """

    def __init__(self) -> None:
        self.types: Dict[str, str] = {}
        self.outgoing: Dict[str, List[Tuple[str, str]]] = {}
        self.incoming: Dict[str, List[Tuple[str, str]]] = {}

    # ------------------------------------------------------------------ build
    def add_node(self, name: str, type_: str = "Entity") -> None:
        """Declare a node and its type, drawn if you like from a taxonomy."""
        self.types.setdefault(name, type_)
        self.outgoing.setdefault(name, [])
        self.incoming.setdefault(name, [])

    def add_relation(self, subject: str, relation: str, obj: str) -> None:
        """Add a triple subject --[relation]--> object to the graph."""
        # The nodes named are created on the fly if they did not exist.
        self.add_node(subject, self.types.get(subject, "Entity"))
        self.add_node(obj, self.types.get(obj, "Entity"))
        if (relation, obj) not in self.outgoing[subject]:
            self.outgoing[subject].append((relation, obj))
        if (relation, subject) not in self.incoming[obj]:
            self.incoming[obj].append((relation, subject))

    def add_triples(self, triples: List[Triple]) -> None:
        """Load a list of triples in one go."""
        for subject, relation, obj in triples:
            self.add_relation(subject, relation, obj)

    # ------------------------------------------------------------- read-only
    def nodes(self) -> List[str]:
        return sorted(self.types)

    def triples(self) -> List[Triple]:
        """Return every triple (subject, relation, object), sorted."""
        out: List[Triple] = []
        for subject in sorted(self.outgoing):
            for relation, obj in self.outgoing[subject]:
                out.append((subject, relation, obj))
        return sorted(out)

    def outgoing_neighbours(self, node: str) -> List[Tuple[str, str]]:
        """The (relation, neighbour) pairs leaving `node`."""
        return list(self.outgoing.get(node, []))

    def incoming_neighbours(self, node: str) -> List[Tuple[str, str]]:
        """The (relation, neighbour) pairs pointing AT `node`."""
        return list(self.incoming.get(node, []))

    # ------------------------------------------------------------- traversal
    def follow_relation(self, start: str, relation: str) -> Optional[str]:
        """Follow ONE `relation` edge from `start`. Return the object, or None."""
        for rel, obj in self.outgoing.get(start, []):
            if rel == relation:
                return obj
        return None

    def chain(self, start: str, relation: str) -> List[str]:
        """Follow one relation as a CHAIN, for as long as it exists.

        For example `chain("P-17", "superseded by")` returns
        ["P-17", "P-18", "P-21"], following the successive edges. This resolves a
        multi-hop question along a single relation.
        """
        path = [start]
        current = start
        seen: Set[str] = {start}
        while True:
            nxt = self.follow_relation(current, relation)
            if nxt is None or nxt in seen:  # the end of the chain, or a cycle
                break
            path.append(nxt)
            seen.add(nxt)
            current = nxt
        return path

    def path_bfs(self, start: str, goal: str) -> Optional[List[Tuple[str, str]]]:
        """Breadth-first search: the shortest path `start` -> `goal`.

        Returns a list of (relation, node) pairs describing the route, or None if
        no path exists. This is the chapter's "underground route": no longer
        "where is the station?" but "how do I get there?".
        """
        if start == goal:
            return []
        queue = deque([start])
        # To rebuild the path: node -> (relation taken, predecessor)
        parent: Dict[str, Tuple[str, str]] = {start: ("", "")}
        while queue:
            current = queue.popleft()
            for relation, neighbour in self.outgoing.get(current, []):
                if neighbour not in parent:
                    parent[neighbour] = (relation, current)
                    if neighbour == goal:
                        return self._rebuild(parent, goal)
                    queue.append(neighbour)
        return None

    @staticmethod
    def _rebuild(parent: Dict[str, Tuple[str, str]], goal: str) -> List[Tuple[str, str]]:
        path: List[Tuple[str, str]] = []
        current = goal
        while parent[current][1] != "":
            relation, predecessor = parent[current]
            path.append((relation, current))
            current = predecessor
        path.reverse()
        return path

    def impacted_by(self, source: str, relations: Optional[Set[str]] = None) -> List[Tuple[str, int]]:
        """The domino effect: everything that depends, directly or not, on `source`.

        The INCOMING edges are walked back from `source` — what depends on it,
        what depends on what depends on it, and so on. Returns a list of
        (impacted_node, depth) sorted by increasing depth. This is exactly the
        question "which equipment goes down if X closes?".

        `relations`, optional, restricts the propagation to a set of relations —
        for instance {"uses", "depends on", "supplied by"}, to follow only the
        physical dependencies and ignore the chain of procedures. That filter
        illustrates one of the chapter's lessons: the way you MODEL the graph
        decides the answer directly, and the number of hops with it.
        """
        results: List[Tuple[str, int]] = []
        seen: Set[str] = {source}
        file: deque = deque([(source, 0)])
        while file:
            current, depth = file.popleft()
            for relation, upstream in self.incoming.get(current, []):
                if relations is not None and relation not in relations:
                    continue
                if upstream not in seen:
                    seen.add(upstream)
                    results.append((upstream, depth + 1))
                    file.append((upstream, depth + 1))
        results.sort(key=lambda t: (t[1], t[0]))
        return results

    # --------------------------------------------------------------- display
    def show(self) -> None:
        """Print the graph as readable triples."""
        for subject, relation, obj in self.triples():
            print(f"  {subject:<14} --[{relation}]--> {obj}")


# ---------------------------------------------------------------------------
# Shared display helpers, to keep the labs' output uniform
# ---------------------------------------------------------------------------
def format_path(steps: List[Tuple[str, str]], start: str) -> str:
    """Format a BFS path as 'A --[r1]--> B --[r2]--> C'."""
    text = start
    for relation, node in steps:
        text += f" --[{relation}]--> {node}"
    return text
