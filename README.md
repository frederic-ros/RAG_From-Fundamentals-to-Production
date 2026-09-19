# RAG — From Fundamentals to Production · Labs

Companion code for the book **RAG — From Fundamentals to Production**
(Frédéric Ros, Yann Ros, Springer).

**251 Python files** — 180 labs, 30 corpus generators and 41 shared modules —
across **34 chapter folders** plus a closing demonstration. Everything runs
**offline, with no API key**: every corpus is generated locally and
deterministically, so two runs give the same numbers.

The step-by-step walkthrough of each lab — objectives, procedure, checkpoints,
reflection questions — is in the book's *companion*, a separate document. This
repository is the code.

## Install

```bash
# everything at once (recommended)
pip install -r requirements-all.txt

# ... or chapter by chapter: each folder has its own minimal requirements.txt
pip install -r ch08-office-documents/requirements.txt
```

The great majority of the labs need only `numpy` and `scikit-learn`.

## Run a lab

Each chapter folder is self-contained. **Always generate the corpus first**,
then run the lab:

```bash
cd ch12-chunking
python generate_corpus.py          # run the chapter generator where present
python lab12-1_unfindable_information.py
```

## Three kinds of lab

| Kind | What it means | How to run it |
|---|---|---|
| **Offline** | No network, no input. The great majority. | `python labN-M_*.py` |
| **Interactive** | Waits for keyboard input via `input()`. | Run it, then answer the prompt. |
| **Network / service** | May reach a feed, a page or a mailbox. Runs on simulated data by default. | `python labN-M_*.py` (simulated mode) |

### The three interactive labs

- `ch01-lexical-search/lab1-1_tfidf_cosine_topk.py` — asks a single question,
  prints the result, exits.
- `ch01-lexical-search/lab1-3_mini_rag_without_llm.py` — asks a single question,
  prints the result, exits.
- `ch01-lexical-search/lab1-4_chatbot_lexical_rules.py` — a question-and-answer
  loop; press **Enter on an empty line** to quit.

### The ten network / service labs

These touch the web, feeds or mail. **By default they run on simulated data**
and need no connection. The real-source mode — a live RSS feed, an IMAP
mailbox — is optional and documented in the README of the chapter concerned.

- `ch06-ingestion` — Lab 6-4, Lab 6-5
- `ch07-ai-ready` — Lab 7-4
- `ch08-office-documents` — Lab 8-5
- `ch09-tables` — Lab 9-4
- `ch10-vision` — Lab 10-2, Lab 10-3
- `ch11-web-sources` — Lab 11-2, Lab 11-5, Lab 11-6

Some of them need extra packages (`feedparser`, `readability-lxml`), all
included in `requirements-all.txt`.

## The closing demonstration

`final-demonstration/` carries the book's thesis end to end: one corpus, one
unchanging harness, and a score that climbs tier by tier from a naive retrieval
system to a governed one.

```bash
cd final-demonstration
python generate_corpus.py     # RUN THIS FIRST
python tiers.py               # the curve, tier by tier
python admission.py           # the document admission gate
```

Run `admission.py` before generating the corpus and it will say so rather than
crash.

## Repository layout

```
rag-labs/
├── README.md                     ← you are here
├── LICENSE
├── requirements-all.txt          ← every dependency, in one file
├── ch01-lexical-search/          ← one folder per chapter
│   ├── README.md
│   ├── requirements.txt
│   ├── generate_corpus.py
│   └── lab1-*.py
├── ...
├── ch36-domain-calibration/
└── final-demonstration/          ← the closing demonstration
```

Folder names follow the chapters of the book. A chapter with no labs has no
folder, which is why the numbering skips 34, 35 and 37.

## Naming

- `chNN-topic/` — one folder per chapter of the book.
- `labN-M_what_it_does.py` — lab M of chapter N. The book and the companion cite
  it as **Lab N-M**.
- `generate_*.py` — builds the local corpus or fixtures for a chapter. Run it
  first.
- anything else — a shared module imported by the labs of that chapter, not
  meant to be run on its own.

## Test status

Every script was executed in a clean environment: **212 of 212 entry points run
without error**. That covers the 30 generators, the 180 labs, the three
interactive labs when given input, and the network labs both in simulated mode
and with their real dependencies installed.

## Licence

MIT — see `LICENSE`. The corpora shipped here are fictional and generated for
teaching; any resemblance to a real organisation is coincidental.
