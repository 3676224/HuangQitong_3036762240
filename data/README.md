# Data folder

This is the **documented input folder** for the project.

## Required input file

Place the raw survey data here before running the workflow:

- **`public.csv`** — Card & Krueger (1994) New Jersey–Pennsylvania fast-food survey data
  (410 stores, 46 columns). Source: course data package `01_DID.zip`.

## Why the CSV is not in this repository

`public.csv` is **restricted course data** and must not be committed to a
public GitHub repository. It is therefore listed in `.gitignore`.

To reproduce the results:

1. Obtain `public.csv` from the course `01_DID.zip` package.
2. Copy it into this `data/` folder **without renaming it**.
3. Run the workflow (see top-level `README.md`).

The column definitions are documented in `../01_DID/DATA_DICTIONARY.md`
(reproduced in the report's data section).
