# Paper Target Venues

Candidate venues for our polyglot-persistence pharmaceutical supply chain
fragility system paper. Ordered from most competitive to most accessible.

> [!IMPORTANT]
> Deadlines and formats are based on the latest publicly available CFPs
> (searched September 2026). Always re-check the official website before
> submission — dates shift by a few weeks across years.

---

## Venue 1 — SIGMOD 2027 Demo Track ⭐ Recommended

| Field              | Details |
|--------------------|---------|
| **Full name**      | ACM SIGMOD International Conference on Management of Data — Demonstration Track |
| **Track type**     | Demo paper |
| **Submission deadline** | **January 11, 2027** |
| **Notification**   | March 8, 2027 |
| **Camera-ready**   | April 1, 2027 |
| **Conference**     | June/July 2027 (exact dates TBA) |
| **Page limit**     | **4 pages** (all inclusive: title, abstract, body, references) |
| **Template**       | ACM `sigconf` — `\documentclass[sigconf,9pt]{acmart}` |
| **Anonymity**      | NOT double-blind (include author names) |
| **Submission portal** | [Microsoft CMT](https://cmt3.research.microsoft.com/SIGMOD2027) |
| **Website**        | [sigmod.org](https://sigmod.org/) |

### Why this fits
SIGMOD's demo track is the premier venue for working database systems
prototypes. Our polyglot architecture with four interacting stores, a
live simulation engine, and an interactive fragility dashboard is exactly
the kind of system they look for. The 4-page format forces conciseness
and the evaluation focuses on novelty of the system architecture plus
quality of the live demonstration — not on research-track novelty claims.

### What they want to see
- System architecture and novel design decisions
- Demonstration scenario script (what will attendees interact with?)
- Optional but strongly encouraged: a short video (≤5 min) of the demo

---

## Venue 2 — CODS-COMAD 2027 Demo Track / Young Researchers' Symposium

| Field              | Details |
|--------------------|---------|
| **Full name**      | ACM IKDD International Conference on Data Science & Management of Data |
| **Track type**     | Demo paper **or** Young Researchers' Symposium (YRS) poster |
| **Submission deadline** | ~September 2027 (based on CODS 2026 cycle; CFP not yet published) |
| **Conference**     | December 2027, India (city TBA) |
| **Page limit — Demo** | **4 pages** (references excluded from count) |
| **Page limit — YRS** | **4 pages** extended abstract (references excluded) |
| **Template**       | ACM `sigconf` — `\documentclass[sigconf]{acmart}` |
| **Anonymity**      | Check per-track CFP |
| **Submission portal** | OpenReview |
| **Website**        | [ikdd.acm.org](https://ikdd.acm.org/) |

### Why this fits
CODS-COMAD is the premier data-systems venue in India, co-sponsored by
ACM. It has an explicit student-friendly ethos: the YRS track is designed
for undergraduate/postgraduate students presenting work-in-progress or
completed projects. The demo track accepts system prototypes and tools.
Acceptance rates for demo/YRS tracks are significantly more accessible
than SIGMOD while still yielding an ACM-published proceedings paper.

### What they want to see
- **Demo track:** Live or recorded system demonstration, system novelty,
  demonstration plan
- **YRS track:** Extended abstract with initial experimental results or
  proof-of-concept; first author must be a student

> [!TIP]
> The YRS track is an excellent fallback if the demo submission feels
> too system-heavy. It allows presenting the research contribution
> (fragility scoring model, synthetic calibration methodology) with
> lighter system requirements.

---

## Venue 3 — IEEE BigData 2027 Short Paper / Demo Track

| Field              | Details |
|--------------------|---------|
| **Full name**      | IEEE International Conference on Big Data — Short Paper / Demo Track |
| **Track type**     | Short paper (6 pages) **or** Demo paper (4 pages) |
| **Submission deadline** | ~August 2027 (based on BigData 2026 cycle; CFP not yet published) |
| **Conference**     | December 2027 (location TBA) |
| **Page limit — Short** | **6 pages** (all inclusive) |
| **Page limit — Demo** | **4 pages** (all inclusive) |
| **Template**       | **IEEE 2-column format** ([IEEE templates](https://www.ieee.org/conferences/publishing/templates.html)) |
| **Anonymity**      | Single-blind (include author names) |
| **Submission portal** | CyberChair |
| **Website**        | [bigdataieee.org](https://bigdataieee.org/) |

### Why this fits
IEEE BigData casts a wider net than SIGMOD — it welcomes applied systems
work, cross-disciplinary contributions (databases + healthcare + supply
chain), and student participation with undergraduate consortiums and
PhD forums. The **6-page short paper** format gives us room to include
benchmark results alongside the system description, which is hard to
fit into SIGMOD's strict 4-page demo limit.

### What they want to see
- Practical system with empirical evaluation
- Cross-domain relevance (big data + healthcare)
- Student tracks available as additional submission options

---

## Submission Strategy

```
Timeline (working backwards from deadlines):
──────────────────────────────────────────────
Oct 2026    Begin writing (target: SIGMOD demo)
Dec 2026    Internal draft complete, record demo video
Jan 2027    ➜ SUBMIT to SIGMOD Demo Track (Jan 11)
Mar 2027    SIGMOD notification (Mar 8)
             ├─ If accepted → prepare camera-ready (Apr 1)
             └─ If rejected → revise based on reviews
Aug 2027       ➜ SUBMIT to IEEE BigData Short Paper (~Aug)
Sep 2027       ➜ SUBMIT to CODS-COMAD Demo/YRS (~Sep)
```

> [!NOTE]
> **Primary target:** SIGMOD Demo (highest prestige, deadline comes first).
> **Safety nets:** IEEE BigData short paper and CODS-COMAD demo/YRS run
> later in the year, giving time to incorporate SIGMOD reviewer feedback
> if the first submission is not accepted.

## Formatting Target for Phase 9

| Setting | Value |
|---------|-------|
| **Primary template** | ACM `sigconf`, 9pt font |
| **LaTeX preamble** | `\documentclass[sigconf,9pt]{acmart}` |
| **Page limit** | 4 pages (all inclusive) |
| **Figures/tables** | Count toward page limit |
| **References** | Count toward page limit (SIGMOD) |
| **Paper size** | US Letter |

Write the paper to the SIGMOD 4-page ACM format first. It can be
reflowed to IEEE 2-column (6 pages) for BigData with minimal effort,
and the same content works for CODS-COMAD's ACM format as-is.

