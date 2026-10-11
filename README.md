# Card & Krueger (1994) Replication — ECO6067 Individual Project

Replication of *"Minimum Wages and Employment: A Case Study of the Fast-Food
Industry in New Jersey and Pennsylvania"* (Card & Krueger, *American Economic
Review*, 1994), using a difference-in-differences design.

Author: **HuangQitong** (`u3676224@connect.hku.hk`)

## Repository structure

```
.
├── code/
│   └── run_all.py               # One-command entry point (regenerates all outputs)
├── data/
│   ├── raw/                     # Raw input (public.csv — not committed)
│   │   └── README.md            # How to obtain public.csv
│   └── processed/               # Processed data written by run_all.py
│       └── README.md
├── outputs/
│   ├── figures/                 # Generated figures
│   └── tables/                  # Generated tables
├── skills/
│   └── SKILL.md                 # Reusable skill / workflow description
├── AI_USE_DISCLOSURE.md         # AI usage and verification
├── report.pdf                   # Final empirical report
└── README.md                    # This file
```

## Reproducing the results (for a human or an AI agent)

1. **Obtain the input data.** Get `public.csv` from the course `01_DID.zip`
   package and copy it into `data/raw/` **without renaming** it. The file is
   restricted, so it is not committed here (see `data/raw/README.md`).

2. **Run the workflow.** From the repository root, run:

   ```bash
   python code/run_all.py
   ```

3. **Check the outputs.** The main tables are written to `outputs/tables/` and
   the main figures to `outputs/figures/`.

The workflow requires no manual modification of the data or the code once the
input file is in place.

## What the workflow produces

- Reconstructed analysis sample (FTE employment, wage-GAP variable, balanced
  sample, handling of closed stores).
- Replication of the paper's core results (difference-in-differences employment
  estimates, reduced-form models, starting-wage distribution figure).
- One independent extension (see the report and `skills/SKILL.md`).
