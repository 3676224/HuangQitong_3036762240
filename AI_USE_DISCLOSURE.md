# AI Use Disclosure

This document records where and how AI tools assisted this project, how
AI-generated output was verified, and which AI errors or suggestions were
corrected or rejected. AI was used as a supporting tool, always under the
author's direction and review; all substantive choices and conclusions remain
the author's responsibility.

## Where and how AI was used

AI tools were used at two locations — **at home and at school** — as a
supporting tool at specific stages of the project:

- **Understanding the paper.** AI helped clarify the research design, variable
  definitions and table structure; the author verified this understanding
  against the paper itself before using it.
- **Drafting code.** AI assisted in drafting the sample-construction and
  estimation code (`code/run_all.py`); the author reviewed each step, checked
  the formulas against the paper's definitions, and re-derived key quantities
  independently.
- **Suggesting the extension.** AI proposed several candidate extensions; the
  author selected randomization inference and heterogeneity analysis and
  specified the exact statistics, samples and outputs.
- **Drafting the report.** AI assisted with drafting, formatting and
  fact-checking the empirical report; the author edited and verified it against
  the generated tables and the published paper.

The core data choices — the FTE definition, the wage-GAP formula, the treatment
of closed stores and the sample restrictions — were made by the author and
checked against the paper's published statistics.

## How AI-generated code, analysis, and writing were checked

- Every reported coefficient was compared to the published tables (for example,
  Table 4 columns i–iv reproduce exactly; Table 6's +7.3 percentage points and
  +2.5 weeks match the paper).
- Key constructed variables were validated against the paper's descriptive
  statistics (for example, 32.8% full-time employees in wave-1 NJ, and 85.5% of
  NJ stores paying exactly $5.05 in wave 2).
- Where a formula was ambiguous (the fraction of full-time employees), several
  candidate definitions were tested and the one matching the paper was selected.
- The estimation code was re-run end-to-end from scratch and its outputs were
  inspected table by table.

## Important AI errors or suggestions corrected or rejected

- **Fraction full-time.** AI initially proposed a headcount-based denominator;
  the correct definition (EMPFT / FTE × 100) was identified by testing against
  the paper's +7.3-percentage-point result and adopted.
- **Temporarily-closed sample.** AI first treated only 2 stores as temporarily
  closed; the paper's "4 temporarily closed stores" (2 under renovation plus 2
  temporarily closed) was the correct count and was applied.
- **Specification-test sample.** AI initially re-expanded the sample when
  managers were excluded; the paper reports "no effect", so the fixed
  357-store sample was restored.
- **Heterogeneity coefficient indexing.** AI read the wrong position from the
  regression output (an off-by-one error), mislabelling the subgroup DiDs; this
  was caught by comparing against hand-computed subgroup means and corrected.
- **Region-augmented columns.** AI could not reconcile Table 4(v) and
  Table 7(v) with the paper; investigation showed the public release codes New
  Jersey regions differently, a data limitation rather than a code error, which
  is documented in the report.
