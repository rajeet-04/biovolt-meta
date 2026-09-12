# Offline rehearsal record

Status for this repository review: **NOT RUN**. A real rehearsal requires a
production deployment, an upstream-disabled network, a real operator, and
preferably a non-author teammate. Do not mark this record `PASS` from unit or
simulation tests.

Record before the final release gate:

```text
revision:
operator:
non_author_reviewer:
evidence_class: measured | synthetic_demo
startup_to_ready_s:
segments_s: {status: , electrical: , science: , experiment: , results: , export: , offline: }
failure_injected:
recovery_card_used:
recovery_s:
ambiguous_instructions:
headline_trace_report:
screenshots_or_private_evidence:
reviewer_signoff:
```

Acceptance is three consecutive cold starts within the Phase 9.2 limits, no
IDE/source edits, a five-minute judged sequence, one benign failure recovered
from a card, and no spoken headline without a passing traceability report.
