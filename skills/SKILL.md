# Skill: Card & Krueger (1994) Replication Workflow

A reusable, end-to-end workflow that turns the raw survey data into the main
tables and figures of Card & Krueger (1994).

## Purpose

Given `data/raw/public.csv`, generate:

1. The reconstructed analysis sample (FTE employment, wage GAP).
2. The full set of replication tables (Tables 1–7) and Figure 1.
3. Two independent extensions: randomization inference and treatment-effect
   heterogeneity.

## How to use

1. Place `public.csv` in `data/raw/` (do not rename).
2. Run `python code/run_all.py` from the repository root.
3. Collect the outputs from `outputs/tables/` and `outputs/figures/`.

## Key implementation decisions

- **FTE employment** = full-time employees + managers + 0.5 × part-time
  employees.
- **% full-time** = full-time (non-manager) employees / FTE × 100.
- **GAP** = 0 for Pennsylvania stores and New Jersey stores already paying
  ≥ $5.05; otherwise `(5.05 − starting_wage) / starting_wage`.
- **Permanently closed stores**: wave-2 employment set to 0.
- **Temporarily closed / renovation stores**: wave-2 employment treated as
  missing (and set to 0 in a robustness check).
- **Dependent variable**: change in FTE employment between wave 1 and wave 2.

## Extensions

1. **Randomization inference.** Under the sharp null of no minimum-wage effect,
   the treatment assignment is permuted 10,000 times to reconstruct the null
   distribution of the DiD and of the wage-gap coefficient; the permutation
   p-values are compared with the paper's asymptotic p-values.
2. **Treatment-effect heterogeneity.** The DiD is re-estimated within subgroups
   defined by wave-1 store characteristics (initial wage, size, ownership,
   chain), with an interacted-DiD F test for heterogeneous effects.
