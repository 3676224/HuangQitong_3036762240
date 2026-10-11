"""Card & Krueger (1994) replication — one-command entry point.

Run from the repository root after placing ``public.csv`` in ``data/raw/``::

    python code/run_all.py

The script reconstructs the analysis sample, reproduces the paper's main
tables and figures, and runs the independent extension. All outputs are
written to ``outputs/tables/`` and ``outputs/figures/``.
"""

from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = ROOT / "data" / "raw" / "public.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"

# Wave-1 sample frame and refusal counts are survey field records documented
# in the paper (Table 1); they are not stored in public.csv and are reproduced
# here as documented constants.
WAVE1_FRAME = {"All": 473, "NJ": 364, "PA": 109}
WAVE1_REFUSALS = {"All": 63, "NJ": 33, "PA": 30}

# STATE: 1 = New Jersey, 0 = Pennsylvania.
# STATUS2: 0 = refusal, 1 = interviewed, 2 = under renovation,
#          3 = permanently closed, 4/5 = temporarily closed.


def load_raw() -> pd.DataFrame:
    """Load the raw survey data."""
    if not RAW_DATA.exists():
        raise FileNotFoundError(
            f"{RAW_DATA} not found. Copy public.csv into data/raw/ first "
            "(see data/raw/README.md)."
        )
    return pd.read_csv(RAW_DATA)


def build_sample(df: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct the analysis variables used by the paper.

    FTE employment  = full-time employees + managers + 0.5 * part-time
    % full-time     = full-time (non-manager) employees / FTE * 100
    wage GAP        = 0 for PA stores and NJ stores paying >= $5.05, else
                      (5.05 - starting wage) / starting wage
    """
    df = df.copy()

    df["fte1"] = df["EMPFT"] + df["NMGRS"] + 0.5 * df["EMPPT"]
    df["fte2"] = df["EMPFT2"] + df["NMGRS2"] + 0.5 * df["EMPPT2"]

    df["pctft1"] = df["EMPFT"] / df["fte1"] * 100
    df["pctft2"] = df["EMPFT2"] / df["fte2"] * 100

    df["meal1"] = df["PSODA"] + df["PFRY"] + df["PENTREE"]
    df["meal2"] = df["PSODA2"] + df["PFRY2"] + df["PENTREE2"]

    df["gap"] = np.where(
        (df["STATE"] == 0) | (df["WAGE_ST"] >= 5.05),
        0.0,
        (5.05 - df["WAGE_ST"]) / df["WAGE_ST"],
    )

    # Wave-2 employment is set to 0 at permanently closed stores (paper note).
    df.loc[df["STATUS2"] == 3, ["fte2", "EMPFT2", "NMGRS2", "EMPPT2"]] = 0
    df.loc[df["STATUS2"] == 3, "pctft2"] = np.nan

    return df


def mean_se(s: pd.Series) -> tuple[float, float, int]:
    """Return (mean, standard error, n) over nonmissing values."""
    x = s.dropna()
    n = len(x)
    return (x.mean(), x.std(ddof=1) / np.sqrt(n), n) if n else (np.nan, np.nan, 0)


def tstat(df: pd.DataFrame, var: str) -> float:
    """t statistic for equality of means between NJ (STATE==1) and PA."""
    m1, se1, _ = mean_se(df.loc[df.STATE == 1, var])
    m0, se0, _ = mean_se(df.loc[df.STATE == 0, var])
    se_diff = np.sqrt(se1**2 + se0**2)
    return (m1 - m0) / se_diff if se_diff > 0 else np.nan


def pct_wage(df: pd.DataFrame, var: str, thr: float) -> dict:
    """Percentage of stores paying exactly `thr`.

    Denominator is ALL stores in the state (missing treated as "not equal"),
    matching the paper's convention (e.g. 30.5% wave-1 NJ at $4.25).
    """
    out = {}
    for state, name in [(1, "NJ"), (0, "PA")]:
        s = df.loc[df.STATE == state, var]
        p = (s == thr).mean() * 100
        se = np.sqrt(p * (100 - p) / len(s))
        out[name] = (p, se, len(s))
    return out


def table1_survey_response(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduce Table 1 (survey response, waves 1 and 2)."""
    n_nj = int((df.STATE == 1).sum())
    n_pa = int((df.STATE == 0).sum())
    n_all = n_nj + n_pa

    rows = []
    # Wave 1: frame and refusals are paper constants; interviewed from data.
    rows.append(
        {
            "Wave": "1",
            "Item": "Sample frame",
            "All": WAVE1_FRAME["All"],
            "NJ": WAVE1_FRAME["NJ"],
            "PA": WAVE1_FRAME["PA"],
        }
    )
    rows.append(
        {
            "Wave": "1",
            "Item": "Refusals",
            "All": WAVE1_REFUSALS["All"],
            "NJ": WAVE1_REFUSALS["NJ"],
            "PA": WAVE1_REFUSALS["PA"],
        }
    )
    rows.append({"Wave": "1", "Item": "Interviewed", "All": n_all, "NJ": n_nj, "PA": n_pa})
    rows.append(
        {
            "Wave": "1",
            "Item": "Response rate (%)",
            "All": n_all / WAVE1_FRAME["All"] * 100,
            "NJ": n_nj / WAVE1_FRAME["NJ"] * 100,
            "PA": n_pa / WAVE1_FRAME["PA"] * 100,
        }
    )

    # Wave 2: all counts come from STATUS2.
    status_items = [
        ("Sample frame", None),
        ("Closed (STATUS2=3)", 3),
        ("Under renovation (STATUS2=2)", 2),
        ("Temporarily closed (STATUS2=4,5)", [4, 5]),
        ("Refusals (STATUS2=0)", 0),
        ("Interviewed (STATUS2=1)", 1),
    ]
    for label, status in status_items:
        if status is None:
            counts = {"All": n_all, "NJ": n_nj, "PA": n_pa}
        elif isinstance(status, list):
            mask = df.STATUS2.isin(status)
            counts = {
                "All": int(mask.sum()),
                "NJ": int((mask & (df.STATE == 1)).sum()),
                "PA": int((mask & (df.STATE == 0)).sum()),
            }
        else:
            mask = df.STATUS2 == status
            counts = {
                "All": int(mask.sum()),
                "NJ": int((mask & (df.STATE == 1)).sum()),
                "PA": int((mask & (df.STATE == 0)).sum()),
            }
        rows.append({"Wave": "2", "Item": label, **counts})

    return pd.DataFrame(rows)


def table2_means(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduce Table 2 (means of key variables, by wave and state)."""
    spec = [
        # (label, wave-1 var, wave-2 var, kind)
        ("FTE employment", "fte1", "fte2", "mean"),
        ("% full-time employees", "pctft1", "pctft2", "mean"),
        ("Starting wage", "WAGE_ST", "WAGE_ST2", "mean"),
        ("% wage = $4.25", "WAGE_ST", "WAGE_ST2", "pct:4.25"),
        ("% wage = $5.05", None, "WAGE_ST2", "pct:5.05"),
        ("Price of full meal", "meal1", "meal2", "mean"),
        ("Hours open (weekday)", "HRSOPEN", "HRSOPEN2", "mean"),
        ("% recruiting bonus", "BONUS", "SPECIAL2", "pct:ind"),
    ]

    rows = []
    for label, v1, v2, kind in spec:
        for wave, var in [(1, v1), (2, v2)]:
            if var is None:
                continue
            if kind == "mean":
                m_nj, se_nj, n_nj = mean_se(df.loc[df.STATE == 1, var])
                m_pa, se_pa, n_pa = mean_se(df.loc[df.STATE == 0, var])
                t = tstat(df, var)
            elif kind.startswith("pct:"):
                thr = kind.split(":")[1]
                if thr == "ind":
                    nj = df.loc[df.STATE == 1, var].dropna()
                    pa = df.loc[df.STATE == 0, var].dropna()
                    m_nj, m_pa = nj.mean() * 100, pa.mean() * 100
                    se_nj = np.sqrt(m_nj * (100 - m_nj) / len(nj))
                    se_pa = np.sqrt(m_pa * (100 - m_pa) / len(pa))
                    n_nj, n_pa = len(nj), len(pa)
                    se_diff = np.sqrt(se_nj**2 + se_pa**2)
                    t = (m_nj - m_pa) / se_diff if se_diff > 0 else np.nan
                else:
                    res = pct_wage(df, var, float(thr))
                    m_nj, se_nj, n_nj = res["NJ"]
                    m_pa, se_pa, n_pa = res["PA"]
                    se_diff = np.sqrt(se_nj**2 + se_pa**2)
                    t = (m_nj - m_pa) / se_diff if se_diff > 0 else np.nan
            else:
                raise ValueError(f"unknown kind {kind}")

            rows.append(
                {
                    "Wave": wave,
                    "Variable": label,
                    "NJ_mean": m_nj,
                    "NJ_se": se_nj,
                    "NJ_n": n_nj,
                    "PA_mean": m_pa,
                    "PA_se": se_pa,
                    "PA_n": n_pa,
                    "t": t,
                }
            )

    return pd.DataFrame(rows)


def step1_build_sample() -> pd.DataFrame:
    """Reconstruct variables (FTE employment, wage GAP) and write processed data."""
    df = build_sample(load_raw())
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_DIR / "sample.csv", index=False)
    print(f"  sample -> {PROCESSED_DIR / 'sample.csv'} ({len(df)} rows)")
    return df


def step2_replicate(df: pd.DataFrame) -> None:
    """Reproduce the main table(s) and figure(s)."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    t1 = table1_survey_response(df)
    t1.to_csv(TABLES_DIR / "table1_survey_response.csv", index=False)
    print(f"  table 1 -> {TABLES_DIR / 'table1_survey_response.csv'}")

    t2 = table2_means(df)
    t2.to_csv(TABLES_DIR / "table2_means.csv", index=False)
    print(f"  table 2 -> {TABLES_DIR / 'table2_means.csv'}")

    # TODO: Table 3 (DiD), Table 4 (reduced-form models), Figure 1 (wage dist).


def step3_extension() -> None:
    """Run the independent extension."""
    raise NotImplementedError("TODO: implement extension (step 3).")


def main() -> None:
    print("Card & Krueger (1994) replication workflow")
    df = step1_build_sample()
    step2_replicate(df)
    step3_extension()
    print("Done. Outputs written to outputs/tables/ and outputs/figures/.")


if __name__ == "__main__":
    main()
