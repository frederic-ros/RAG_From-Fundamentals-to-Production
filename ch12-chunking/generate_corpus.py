# -*- coding: utf-8 -*-
"""
generate_corpus.py — test corpus for Chapter 12.

Four deterministic texts, chosen to expose the traps of chunking:

  corpus/remote_work.txt — an HR note (Claire's running example). The number of
  days and the phrase "remote work" are stated far enough apart that an unlucky
  cut makes the answer unfindable (Lab 12-1).

  corpus/public_procurement.txt — a regulatory extract (Sophie). Each article
  states an obligation and then a decisive exception; cutting between the two
  produces a legally false reading (Lab 12-2).

  corpus/technical_manual.txt — a structured manual, with headings and
  subheadings, for the benchmark (Labs 12-3 to 12-5) and for recursive
  chunking (Lab 12-4).

  corpus/blog_article.txt — continuous prose, where every strategy performs
  about as well as the others (Lab 12-3).

Deterministic. Run before the labs: python generate_corpus.py
"""

from pathlib import Path

CORPUS = Path(__file__).resolve().parent / "corpus"
CORPUS.mkdir(exist_ok=True)


REMOTE_WORK = """\
Service note — Remote work

Purpose. This note sets out the remote work arrangements applicable to the \
staff of the authority, with effect from 1 January 2025. It supplements the \
internal regulations and applies to every department, subject to the \
requirements of continuity of public service and to the constraints particular \
to certain field roles.

General principles. Remote work rests on volunteering and on trust. It assumes \
that the member of staff has a suitable working space and a sufficient \
connection. The authority provides the necessary computer equipment and \
supports the arrangement with a code of practice. Team meetings remain \
primarily on site, so as to preserve the working collective.

Eligibility. Staff who have completed their probationary period and who show \
sufficient autonomy in their duties are eligible. Staff whose duties require a \
permanent physical presence, such as reception or on-site technical \
intervention, are not eligible for the scheme, save for an exceptional \
arrangement approved in advance by the management.

Number of days. Remote work is authorised, subject to the needs of the service, \
up to a ceiling of two days per week. That ceiling is a maximum, not an \
automatic entitlement. The days are agreed with the line manager, and may be \
suspended temporarily where the service requires it.

Practical arrangements. A member of staff working away from the office remains \
reachable during the usual hours and takes part in meetings remotely. Any costs \
incurred are handled separately, as set out in the code of practice. Where a \
technical difficulty persists, the member of staff returns to work on site \
until it is resolved.
"""


PUBLIC_PROCUREMENT = """\
Consultation regulations — Extracts

Article 5 — Delivery times. The contractor undertakes to deliver the supplies \
covered by the present contract, in their entirety and to the place designated \
in the technical annex, within thirty days of notification of the contract. \
However, in the event of duly established force majeure, that period is \
extended by fifteen days, without the extension giving rise to any right to \
compensation for the contractor.

Article 6 — Late-delivery penalties. Any late delivery observed on the date \
fixed in the schedule gives rise, without prior formal notice, to a daily \
penalty equal to one thousandth of the total value of the contract. However, no \
penalty is due where the delay results from an act attributable to the \
purchaser or from a case of force majeure recognised by both parties.

Article 7 — Payment terms. Payment is made within thirty days of receipt of the \
invoice. By way of exception, that period is extended to sixty days for \
contracts concluded with a public health establishment, in accordance with the \
applicable regulations.

Article 8 — Subcontracting. The contractor may subcontract part of the \
performance of the contract. Nevertheless, subcontracting is prohibited for the \
services designated as essential in the technical annex, whose performance \
remains personal to the contractor.

Article 9 — Termination. The purchaser may terminate the contract in the event \
of serious default by the contractor. Such termination may however take place \
only after a formal notice has remained without effect for fifteen days.
"""


TECHNICAL_MANUAL = """\
# Maintenance manual — V2 drive

## 1. Installation

### 1.1 Prerequisites
Installation requires a dedicated circuit breaker and a compliant earth \
connection. The nominal supply voltage is 400 volts three-phase. Check \
compatibility before switching on.

### 1.2 Mounting steps
Fix the drive on a ventilated support. Connect the power terminals, respecting \
the phase order. Connect the temperature sensor to the dedicated input. Close \
the cover before switching on.

## 2. Maintenance

### 2.1 Preventive maintenance
Check the tightness of the connections every six months. Clean the ventilation \
grilles to avoid overheating. Record the operating temperature, which must not \
exceed seventy-five degrees.

### 2.2 Fault diagnosis
In the event of an unexpected shutdown, check the power supply first, then the \
temperature sensor. A flashing error code indicates overheating: let the unit \
cool down before restarting.

## 3. Safety
All work is carried out with the power off, and the isolating switch padlocked \
in the open position for the whole duration of the intervention. Protective \
equipment must be worn: insulating gloves, safety glasses, safety footwear. \
Record every intervention in the maintenance log, together with the name of the \
technician and the readings taken before and after the work.
"""


BLOG = """\
The rise of RAG in organisations

For a few years now, retrieval-augmented generation has established itself as \
the obvious way to exploit the internal knowledge of an organisation. Rather \
than retraining a model at great expense, an organisation gives the model \
access to a document corpus that it queries on the fly. The idea is simple, but \
putting the idea into practice raises deep questions.

The first question concerns the quality of the documents. A retrieval system is \
worth no more than the quality of the documents it indexes. Documents that are \
badly prepared, badly structured or out of date produce disappointing answers, \
however refined the model. That is why so much effort now goes into preparing \
the documents before they are indexed.

The second question is trust. Trust is not the same as fluency: a plausible \
answer is not necessarily an accurate answer. Organisations that adopt these \
tools learn to demand citations, to trace the origin of every assertion, and to \
measure trust rather than assume it. The maturity of a deployment often shows \
in that demand for citations and for verifiability.

Then there is the human question. These systems do not replace human \
expertise: they equip it. Field reports show that the successful deployments \
are the ones that involve the business closely, rather than imposing on the \
business a solution that came from elsewhere.
"""


def main() -> None:
    print("Generating the Chapter 12 test corpus:")
    for name, content in [
        ("remote_work.txt", REMOTE_WORK),
        ("public_procurement.txt", PUBLIC_PROCUREMENT),
        ("technical_manual.txt", TECHNICAL_MANUAL),
        ("blog_article.txt", BLOG),
    ]:
        (CORPUS / name).write_text(content, encoding="utf-8")
        print(f"  + {name}")
    print(f"\nDone. Corpus available in: {CORPUS}")


if __name__ == "__main__":
    main()
