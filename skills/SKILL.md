# Skill: Card & Krueger (1994) Replication Workflow

A reusable, end-to-end workflow that turns the raw survey data into the main
tables and figures of Card & Krueger (1994).

## Purpose

Given `data/raw/public.csv`, generate:

1. The reconstructed analysis sample (FTE employment, wage GAP).
2. The core difference-in-differences employment estimates (Tables 3 and 4).
3. The starting-wage distribution figure (Figure 1).
4. One independent extension.

## How to use

1. Place `public.csv` in `data/raw/` (do not rename).
2. Run `python code/run_all.py` from the repository root.
3. Collect the outputs from `outputs/tables/` and `outputs/figures/`.

## Key implementation decisions

- **FTE employment** = full-time employees (incl. managers) + 0.5 × part-time
  employees.
- **GAP** = 0 for Pennsylvania stores and New Jersey stores already paying
  ≥ $5.05; otherwise `(5.05 − starting_wage) / starting_wage`.
- **Permanently closed stores**: wave-2 employment set to 0.
- **Temporarily closed stores**: wave-2 employment treated as missing (and set
  to 0 in a robustness check).
- **Dependent variable**: change in FTE employment between wave 1 and wave 2.

## Extension

(TODO: document the independent extension here once implemented.)
