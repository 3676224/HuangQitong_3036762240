# Processed data

This folder holds the **processed data** produced by the workflow
(`code/run_all.py`). These files are generated automatically from the raw
input and are the inputs to the estimation and plotting steps.

## Expected contents

- `sample.csv` — the reconstructed analysis sample with derived variables
  (`fte1`, `fte2`, `pctft1`, `pctft2`, `meal1`, `meal2`, `gap`, `nj`, `dfte`),
  after applying the sample rules described in the report (permanently closed
  stores set to zero employment, temporarily closed stores treated as missing).

These files are regenerated from scratch every time `run_all.py` runs, so they
do not need to be committed or edited by hand.
