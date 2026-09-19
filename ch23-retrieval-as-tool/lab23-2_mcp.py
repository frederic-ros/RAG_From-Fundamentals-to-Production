# -*- coding: utf-8 -*-
"""
Lab 23-2 — MCP: the standard socket for calling a tool

Learning objective
------------------
Once retrieval is a tool, how does a model declare and call it? The standard
answer is MCP (Model Context Protocol) — "the USB-C of AI": a single socket
through which a model DECLARES and CALLS its tools.

This lab shows the durable PRINCIPLE, not a precise implementation, which changes
from month to month. A server DECLARES the tool; a client DISCOVERS it
(list_tools) and then INVOKES it (call_tool) WITHOUT knowing its implementation.

The key point of the chapter is checked here: MCP does not replace RAG, it
standardises the call to it.

It is proved by CHANGING the retrieval backend behind the same tool: the client
does not move. A "principle" version, in-process: no network, just the
declarative surface and the decoupling. (A real MCP SDK adds transport and
security, which are outside the scope here.)

No API key. Run generate_corpus.py first.
"""

import json
from pathlib import Path

import agentlib as A

CORPUS = Path(__file__).resolve().parent / "corpus" / "fragments.json"


def main() -> None:
    print("=" * 78)
    print("Lab 23-2 — MCP: exposing retrieval as a standard tool")
    print("=" * 78)

    if not CORPUS.exists():
        print("\nCorpus not found. Run this first: python generate_corpus.py")
        return

    data = json.loads(CORPUS.read_text(encoding="utf-8"))
    frags = data["fragments"]

    # =====================================================================
    # 1) The SERVER declares a tool
    # =====================================================================
    print("\n" + "=" * 78)
    print("1) THE SERVER DECLARES A TOOL (name, description, schema)")
    print("=" * 78)
    rech = A.Search([f["text"] for f in frags])
    tool = A.SearchTool(rech, frags)

    serveur = A.MCPServer("serveur-retrieval")
    serveur.register(
        name=tool.name,
        description=tool.description,
        schema=tool.schema,
        function=lambda query: tool.call(query, k=3),
    )
    print(f"  Server \"{serveur.name}\" started, 1 tool registered.")

    # =====================================================================
    # 2) The CLIENT discovers the tools, without knowing the implementation
    # =====================================================================
    print("\n" + "=" * 78)
    print("2) THE CLIENT DISCOVERS THE TOOLS (list_tools)")
    print("=" * 78)
    for o in serveur.list_tools():
        print(f"  - {o['name']}")
        print(f"      description : {o['description']}")
        print(f"      parameters  : "
              f"{json.dumps(o['schema']['properties'], ensure_ascii=False)}")
    print("  The client sees ONLY the declaration, not the code behind it.")

    # =====================================================================
    # 3) The CLIENT invoque the tool by son name
    # =====================================================================
    print("\n" + "=" * 78)
    print("3) LE CLIENT INVOQUE L'OUTIL (call_tool)")
    print("=" * 78)
    query = "emergency stop pump P-42"
    resultats = serveur.call_tool(tool.name, {"query": query})
    print(f"  call_tool(\"{tool.name}\", {{query: \"{query}\"}})")
    for r in resultats:
        print(f"    → [{r['score']}] {r['subject']} : {r['text'][:50]}…")

    # =====================================================================
    # 4) On CHANGE the backend — the client not bouge not
    # =====================================================================
    print("\n" + "=" * 78)
    print("4) THE BACKEND BEHIND THE TOOL CHANGES — THE CLIENT DOES NOT MOVE")
    print("=" * 78)
    # A new backend: a retrieval restricted to the pump documents alone.
    frags_pompes = [f for f in frags if "stop-P" in f["subject"]]
    rech2 = A.Search([f["text"] for f in frags_pompes])
    outil2 = A.SearchTool(rech2, frags_pompes)
    serveur.register(   # the same name, a different implementation
        name=tool.name, description=tool.description, schema=tool.schema,
        function=lambda query: outil2.call(query, k=3),
    )
    resultats = serveur.call_tool(tool.name, {"query": query})
    print("  The same client call, the backend replaced (index restricted to pumps):")
    for r in resultats:
        print(f"    → [{r['score']}] {r['subject']}")
    print("  The CLIENT code is identical — only the server changed implementation.")

    # =====================================================================
    # 5) The journal appels of the serveur
    # =====================================================================
    print("\n" + "=" * 78)
    print("5) THE CALL LOG (on the server side)")
    print("=" * 78)
    for i, appel in enumerate(serveur.log, 1):
        print(f"    appel {i} : {appel['tool']} {appel['arguments']}")

    print("\n" + "=" * 78)
    print("WHAT THIS LAB REVEALS")
    print("=" * 78)
    print("  The server DECLARES (name, description, schema); the client DISCOVERS")
    print("  and then INVOKES by name, knowing no implementation. Changing the")
    print("  retrieval backend does not touch the client: that is the whole point of a")
    print("  standard.")
    print("\n  WHAT TO REMEMBER: MCP standardises the CALL to the retrieval — it does not replace it.")
    print("  Le travail de search (embeddings, hybride, re-ranking) reste entier,")
    print("  behind the tool. A real SDK adds transport and security; the principle,")
    print("  is here.")


if __name__ == "__main__":
    main()
