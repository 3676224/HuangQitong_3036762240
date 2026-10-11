# ECO6067 Individual Project — Card & Krueger (1994) Replication

Replicating *"Minimum Wages and Employment: A Case Study of the Fast-Food
Industry in New Jersey and Pennsylvania"* (Card & Krueger, *American Economic
Review*, 1994) using a difference-in-differences design.

## Repository structure

```
.
├── data/                 # Documented input folder (raw data is gitignored)
│   └── README.md
├── code/                 # Analysis code (build sample → replicate → extend)
├── output/
│   ├── tables/           # Generated tables
│   └── figures/          # Generated figures
├── report/               # Empirical report
├── .gitignore
└── README.md
```

## Reproducing the results

1. Obtain `public.csv` from the course `01_DID.zip` package.
2. Copy it into `data/` **without renaming** (see `data/README.md`).
3. Run the workflow entry point:
   ```bash
   python run_all.py
   ```
4. The main tables and figures are written to `output/`.

No manual modification of the data or code is required after the input file is
in place.

## Author

- HuangQiTong (`u3676224@connect.hku.hk`)
