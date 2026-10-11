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
    df["nj"] = (df["STATE"] == 1).astype(int)

    # Wave-2 employment is set to 0 at permanently closed stores (paper note).
    df.loc[df["STATUS2"] == 3, ["fte2", "EMPFT2", "NMGRS2", "EMPPT2"]] = 0
    df.loc[df["STATUS2"] == 3, "pctft2"] = np.nan

    df["dfte"] = df["fte2"] - df["fte1"]

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


def _ols(y: np.ndarray, X: np.ndarray) -> dict:
    """OLS with an unrestricted constant. ``X`` is (n, k) without the constant."""
    X = np.column_stack([np.ones(len(y)), X])
    n, k = X.shape
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    resid = y - X @ beta
    sigma2 = resid @ resid / (n - k)
    cov = sigma2 * np.linalg.inv(X.T @ X)
    return {
        "beta": beta,
        "se": np.sqrt(np.diag(cov)),
        "resid": resid,
        "ser": np.sqrt(sigma2),
        "n": n,
        "k": k,
    }


def _f_pvalue(y: np.ndarray, X_full: np.ndarray, X_restricted: np.ndarray) -> tuple:
    """p-value of the joint F test that the extra regressors in X_full are zero."""
    full = _ols(y, X_full)
    rest = _ols(y, X_restricted)
    q = full["k"] - rest["k"]
    df = full["n"] - full["k"]
    sse_f = full["resid"] @ full["resid"]
    sse_r = rest["resid"] @ rest["resid"]
    F = ((sse_r - sse_f) / q) / (sse_f / df)
    try:
        from scipy.stats import f as fdist
        p = 1 - fdist.cdf(F, q, df)
    except ImportError:
        p = np.nan
    return F, p


def table3_employment(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduce Table 3 (average FTE employment before/after, by state and
    NJ wage group)."""
    groups = {
        "PA": df.STATE == 0,
        "NJ": df.STATE == 1,
        "NJ wage=$4.25": (df.STATE == 1) & (df.WAGE_ST == 4.25),
        "NJ wage=$4.26-4.99": (df.STATE == 1) & (df.WAGE_ST >= 4.26) & (df.WAGE_ST <= 4.99),
        "NJ wage>=$5.00": (df.STATE == 1) & (df.WAGE_ST >= 5.00),
    }

    stats = {gname: {} for gname in groups}
    for gname, mask in groups.items():
        sub = df[mask]
        before = mean_se(sub.fte1)
        after = mean_se(sub.fte2)
        change = (after[0] - before[0], np.sqrt(before[1] ** 2 + after[1] ** 2), np.nan)
        d = sub.dfte.dropna()
        balanced = (d.mean(), d.std(ddof=1) / np.sqrt(len(d)), len(d))
        sub5 = df[mask].copy()
        sub5.loc[sub5.STATUS2.isin([4, 5]), "fte2"] = 0.0
        d5 = (sub5.fte2 - sub5.fte1).dropna()
        temp0 = (d5.mean(), d5.std(ddof=1) / np.sqrt(len(d5)), len(d5))
        stats[gname] = {"before": before, "after": after, "change": change,
                        "balanced": balanced, "temp0": temp0}

    row_names = ["before", "after", "change", "balanced", "temp0"]
    records = []
    for r in row_names:
        for gname in groups:
            m, se, n = stats[gname][r]
            records.append({"Row": r, "Group": gname, "mean": m, "se": se, "n": n})

    # Difference-in-differences on the balanced sample (headline result).
    d_nj = df.loc[df.STATE == 1, "dfte"].dropna()
    d_pa = df.loc[df.STATE == 0, "dfte"].dropna()
    did = d_nj.mean() - d_pa.mean()
    se_did = np.sqrt(d_nj.var(ddof=1) / len(d_nj) + d_pa.var(ddof=1) / len(d_pa))
    records.append({"Row": "DiD (balanced, NJ-PA)", "Group": "t-stat",
                    "mean": did, "se": se_did, "n": did / se_did})

    return pd.DataFrame(records)


def table4_reduced_form(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduce Table 4 (reduced-form models for change in FTE employment).

    Sample: open stores with complete wave-1/2 employment and wage data, plus
    the six permanently closed stores (employment change = -FTE1).
    """
    open_mask = (
        (df.STATUS2 == 1)
        & df.fte1.notna() & df.fte2.notna()
        & df.WAGE_ST.notna() & df.WAGE_ST2.notna()
    )
    closed_mask = (df.STATUS2 == 3) & df.fte1.notna() & df.WAGE_ST.notna()
    s = df.loc[open_mask | closed_mask].copy()

    y = s.dfte.to_numpy()
    nj = s.nj.to_numpy()
    gap = s.gap.to_numpy()
    chain = pd.get_dummies(s.CHAIN, prefix="c").drop(columns=["c_1"]).to_numpy()
    coown = s.CO_OWNED.to_numpy().reshape(-1, 1)
    region = s[["CENTRALJ", "NORTHJ", "PA1"]].to_numpy()

    ctrl = np.column_stack([chain, coown])

    def coef(X, term):
        r = _ols(y, X)
        return r["beta"][term], r["se"][term], r["ser"]

    models = {
        "i": ("NJ dummy", nj, None),
        "ii": ("NJ dummy + chain/ownership", np.column_stack([nj, ctrl]), nj),
        "iii": ("wage gap", gap, None),
        "iv": ("wage gap + chain/ownership", np.column_stack([gap, ctrl]), gap),
        "v": ("wage gap + chain/ownership + region", np.column_stack([gap, ctrl, region]), gap),
    }

    records = []
    for key, (label, X, base_X) in models.items():
        term_idx = 1  # coefficient on the first regressor (NJ dummy or GAP)
        b, se, ser = coef(X, term_idx)
        F = p = np.nan
        if base_X is not None:
            F, p = _f_pvalue(y, X, base_X)
        records.append({
            "Model": key,
            "Specification": label,
            "coefficient": b,
            "se": se,
            "ser": ser,
            "F_controls": F,
            "p_controls": p,
            "n": len(y),
        })

    out = pd.DataFrame(records)
    out.attrs["depvar_mean"] = y.mean()
    out.attrs["depvar_sd"] = y.std(ddof=1)
    return out


def figure1_wages(df: pd.DataFrame) -> Path:
    """Reproduce Figure 1 (distribution of starting wage rates, by state and wave)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(2, 2, figsize=(8, 7))
    bins = np.arange(4.0, 6.26, 0.25)
    panels = [
        ("WAGE_ST", "February 1992"),
        ("WAGE_ST2", "November 1992"),
    ]
    for row, (wvar, wtitle) in enumerate(panels):
        for col, (state, stitle) in enumerate([(1, "New Jersey"), (0, "Pennsylvania")]):
            ax = axes[row, col]
            vals = df.loc[df.STATE == state, wvar].dropna()
            ax.hist(vals, bins=bins, weights=np.full(len(vals), 100 / len(vals)),
                    edgecolor="black", color="0.85")
            ax.set_title(f"{stitle} — {wtitle}", fontsize=10)
            ax.set_xlabel("Starting wage ($/hour)")
            ax.set_ylabel("Percent of stores")
            ax.set_ylim(0, 90)
            ax.axvline(5.05, color="red", linestyle="--", linewidth=1)
    fig.suptitle("Distribution of Starting Wage Rates", fontsize=12)
    fig.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / "figure1_wage_distribution.png"
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path


def table5_specification_tests(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduce Table 5, rows 1-5 (alternative employment measures).

    Each row runs four reduced-form models (change in FTE, and proportional
    change) on the NJ dummy and on the wage gap, with chain + company-ownership
    controls. The proportional change is dFTE / mean(FTE1, FTE2); closed stores
    are set to -1.
    """

    def make_fte(w_pt: float, include_mgr: bool, temp_zero: bool):
        """Return (fte1, fte2) Series under a given FTE weighting.

        Wave-2 employment is 0 for permanently closed stores and missing (or 0,
        when ``temp_zero``) for temporarily closed stores.
        """
        mgr1 = df.NMGRS if include_mgr else 0.0
        mgr2 = df.NMGRS2 if include_mgr else 0.0
        fte1 = df.EMPFT + mgr1 + w_pt * df.EMPPT
        fte2 = df.EMPFT2 + mgr2 + w_pt * df.EMPPT2
        fte2 = fte2.where(df.STATUS2 != 3, 0.0)                      # closed -> 0
        # renovation (2) + temporarily closed (4,5) = the paper's 4 "temporarily closed" stores
        fte2 = fte2.where(~df.STATUS2.isin([2, 4, 5]), 0.0 if temp_zero else np.nan)
        return fte1, fte2

    # Fixed base sample (351 open + 6 closed = 357). Rows 3-5 keep this sample
    # (the paper reports "no effect", i.e. no sample expansion); only row 2
    # expands it by the four temporarily closed / under-renovation stores.
    base_mask = (
        (df.STATUS2 == 1)
        & df.fte1.notna() & df.fte2.notna()
        & df.WAGE_ST.notna() & df.WAGE_ST2.notna()
    ) | ((df.STATUS2 == 3) & df.fte1.notna() & df.WAGE_ST.notna())

    def run_row(label, fte1, fte2, mask):
        d = df.assign(_fte1=fte1, _fte2=fte2)
        s = d.loc[mask].copy()
        s["dfte"] = s._fte2 - s._fte1
        avg = (s._fte1 + s._fte2) / 2
        s["prop"] = np.where(s._fte2 == 0, -1.0, s.dfte / avg)

        chain = pd.get_dummies(s.CHAIN, prefix="c").drop(columns=["c_1"]).to_numpy()
        coown = s.CO_OWNED.to_numpy().reshape(-1, 1)
        ctrl = np.column_stack([chain, coown])
        nj = s.nj.to_numpy()
        gap = s.gap.to_numpy()
        y_levels = s.dfte.to_numpy()
        y_prop = s.prop.to_numpy()

        def est(dep, X):
            r = _ols(dep, X)
            return r["beta"][1], r["se"][1]

        return {
            "Row": label,
            "NJ_levels": est(y_levels, np.column_stack([nj, ctrl])),
            "GAP_levels": est(y_levels, np.column_stack([gap, ctrl])),
            "NJ_prop": est(y_prop, np.column_stack([nj, ctrl])),
            "GAP_prop": est(y_prop, np.column_stack([gap, ctrl])),
            "n": len(s),
        }

    specs = [
        ("1. base (FTE = FT + mgr + 0.5 PT)", 0.5, True, False, False),
        ("2. temp-closed stores = 0", 0.5, True, True, True),
        ("3. exclude managers", 0.5, False, False, False),
        ("4. part-time = 0.4 FTE", 0.4, True, False, False),
        ("5. part-time = 0.6 FTE", 0.6, True, False, False),
    ]

    records = []
    for label, w_pt, include_mgr, temp_zero, add_temp in specs:
        fte1, fte2 = make_fte(w_pt, include_mgr, temp_zero)
        mask = base_mask
        if add_temp:
            mask = mask | (df.STATUS2.isin([2, 4, 5]) & df.fte1.notna() & df.WAGE_ST.notna())
        r = run_row(label, fte1, fte2, mask)
        rec = {"Row": r["Row"], "n": r["n"]}
        for key in ["NJ_levels", "GAP_levels", "NJ_prop", "GAP_prop"]:
            rec[f"{key}_coef"] = r[key][0]
            rec[f"{key}_se"] = r[key][1]
        records.append(rec)

    return pd.DataFrame(records)


def table6_nonwage(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduce Table 6 (full-time fraction and other nonwage outcomes).

    Each row reports the mean change in the outcome for NJ and PA stores, their
    difference, and the reduced-form coefficient on the NJ dummy / wage gap from
    regressions for the change in the outcome (with chain + company-ownership
    controls; column vi also adds region dummies). The sample is stores with the
    outcome observed in both waves.
    """

    def ind(s: pd.Series, v) -> pd.Series:
        # indicator that s == v, missing where s is missing
        return s.eq(v).where(s.notna()).astype(float)

    outcomes = [
        ("Fraction full-time workers (%)",
         df.EMPFT / (df.EMPFT + df.NMGRS + 0.5 * df.EMPPT) * 100,
         df.EMPFT2 / (df.EMPFT2 + df.NMGRS2 + 0.5 * df.EMPPT2) * 100),
        ("Hours open per weekday", df.HRSOPEN, df.HRSOPEN2),
        ("Cash registers", df.NREGS, df.NREGS2),
        ("Registers open at 11AM", df.NREGS11, df.NREGS112),
        ("Low-price meal program (%)", ind(df.MEALS, 2) * 100, ind(df.MEALS2, 2) * 100),
        ("Free meal program (%)", ind(df.MEALS, 1) * 100, ind(df.MEALS2, 1) * 100),
        ("Low-price and free meals (%)", ind(df.MEALS, 3) * 100, ind(df.MEALS2, 3) * 100),
        ("Time to first raise (weeks)", df.INCTIME, df.INCTIME2),
        ("First raise amount (cents)", df.FIRSTINC * 100, df.FIRSTIN2 * 100),
        ("Slope of wage profile (%/week)",
         df.FIRSTINC / df.WAGE_ST * 100 / df.INCTIME,
         df.FIRSTIN2 / df.WAGE_ST2 * 100 / df.INCTIME2),
    ]

    chain_full = pd.get_dummies(df.CHAIN, prefix="c").drop(columns=["c_1"]).to_numpy()
    coown_full = df.CO_OWNED.to_numpy().reshape(-1, 1)
    region_full = df[["CENTRALJ", "NORTHJ", "PA1"]].to_numpy()
    nj_full = df.nj.to_numpy()
    gap_full = df.gap.to_numpy()
    state_full = df.STATE.to_numpy()

    records = []
    for name, f1, f2 in outcomes:
        change = (f2 - f1).to_numpy()
        valid = ~np.isnan(change)
        nj_v = state_full == 1
        pa_v = state_full == 0
        nj_mean = change[valid & nj_v].mean()
        pa_mean = change[valid & pa_v].mean()
        diff = nj_mean - pa_mean
        nnj = int((valid & nj_v).sum())
        npa = int((valid & pa_v).sum())
        se_diff = np.sqrt(
            change[valid & nj_v].var(ddof=1) / nnj
            + change[valid & pa_v].var(ddof=1) / npa
        )
        t_diff = diff / se_diff if se_diff > 0 else np.nan

        reg = (
            valid
            & df.WAGE_ST.notna().to_numpy()
            & df.CHAIN.notna().to_numpy()
            & df.CO_OWNED.notna().to_numpy()
        )
        y = change[reg]
        X_nj = np.column_stack([nj_full[reg], chain_full[reg], coown_full[reg]])
        X_gap = np.column_stack([gap_full[reg], chain_full[reg], coown_full[reg]])
        X_gap_r = np.column_stack(
            [gap_full[reg], chain_full[reg], coown_full[reg], region_full[reg]]
        )
        r_nj = _ols(y, X_nj)
        r_gap = _ols(y, X_gap)
        r_gap_r = _ols(y, X_gap_r)

        records.append({
            "Outcome": name,
            "NJ_mean_change": nj_mean,
            "PA_mean_change": pa_mean,
            "NJ_minus_PA": diff,
            "NJ_minus_PA_t": t_diff,
            "n": int(reg.sum()),
            "NJ_dummy_coef": r_nj["beta"][1], "NJ_dummy_se": r_nj["se"][1],
            "GAP_coef": r_gap["beta"][1], "GAP_se": r_gap["se"][1],
            "GAP_region_coef": r_gap_r["beta"][1], "GAP_region_se": r_gap_r["se"][1],
        })

    return pd.DataFrame(records)


def table7_prices(df: pd.DataFrame) -> pd.DataFrame:
    """Reproduce Table 7 (reduced-form models for the change in the log price of
    a full meal). The full meal price is PSODA + PFRY + PENTREE (after-tax)."""
    meal1 = df.PSODA + df.PFRY + df.PENTREE
    meal2 = df.PSODA2 + df.PFRY2 + df.PENTREE2
    dlnp = np.log(meal2) - np.log(meal1)

    sample = (
        meal1.notna() & meal2.notna()
        & df.WAGE_ST.notna() & df.WAGE_ST2.notna()
        & df.fte1.notna() & df.fte2.notna()
    )
    s = df.loc[sample].copy()
    y = np.log(s.PSODA2 + s.PFRY2 + s.PENTREE2).to_numpy() - np.log(
        s.PSODA + s.PFRY + s.PENTREE
    ).to_numpy()

    nj = s.nj.to_numpy()
    gap = s.gap.to_numpy()
    chain = pd.get_dummies(s.CHAIN, prefix="c").drop(columns=["c_1"]).to_numpy()
    coown = s.CO_OWNED.to_numpy().reshape(-1, 1)
    region = s[["CENTRALJ", "NORTHJ", "PA1"]].to_numpy()
    ctrl = np.column_stack([chain, coown])

    models = {
        "i": ("NJ dummy", np.column_stack([nj])),
        "ii": ("NJ dummy + chain/ownership", np.column_stack([nj, ctrl])),
        "iii": ("wage gap", np.column_stack([gap])),
        "iv": ("wage gap + chain/ownership", np.column_stack([gap, ctrl])),
        "v": ("wage gap + chain/ownership + region", np.column_stack([gap, ctrl, region])),
    }

    records = []
    for key, (label, X) in models.items():
        r = _ols(y, X)
        records.append({
            "Model": key,
            "Specification": label,
            "coefficient": r["beta"][1],
            "se": r["se"][1],
            "ser": r["ser"],
            "n": r["n"],
        })

    out = pd.DataFrame(records)
    out.attrs["depvar_mean"] = y.mean()
    out.attrs["depvar_sd"] = y.std(ddof=1)
    return out


def extension_randomization(df: pd.DataFrame, n_perm: int = 10000, seed: int = 42):
    """Independent extension: randomization inference (permutation tests).

    Under the sharp null that the New Jersey minimum wage had no effect on any
    store's employment, the change in FTE employment is exchangeable across
    stores. We therefore permute the treatment assignment and reconstruct the
    null distribution of two headline statistics:

      1. the difference-in-differences estimate  mean(dFTE | NJ) - mean(dFTE | PA)
      2. the reduced-form coefficient on the wage gap  (dFTE ~ GAP + controls)

    The permutation p-value is the fraction of permuted statistics at least as
    extreme as the observed one; it is compared with the paper's asymptotic
    (normal) p-value, which assumes normality of the sampling distribution.
    """
    from scipy.stats import norm

    rng = np.random.default_rng(seed)

    # ---- (1) DiD on the balanced sample (open + permanently-closed stores) ----
    d_nj = df.loc[df.STATE == 1, "dfte"].dropna().to_numpy()
    d_pa = df.loc[df.STATE == 0, "dfte"].dropna().to_numpy()
    d = np.concatenate([d_nj, d_pa])
    state = np.concatenate([np.ones(len(d_nj)), np.zeros(len(d_pa))])
    n1 = int(state.sum())
    n0 = int((state == 0).sum())
    obs_did = d[state == 1].mean() - d[state == 0].mean()
    se_did = np.sqrt(d[state == 1].var(ddof=1) / n1 + d[state == 0].var(ddof=1) / n0)
    t_did = obs_did / se_did
    perm_did = np.empty(n_perm)
    for i in range(n_perm):
        dp = rng.permutation(d)
        perm_did[i] = dp[state == 1].mean() - dp[state == 0].mean()

    # ---- (2) wage-gap coefficient (Table 4 model iv sample, n = 357) ----
    open_mask = (
        (df.STATUS2 == 1)
        & df.fte1.notna() & df.fte2.notna()
        & df.WAGE_ST.notna() & df.WAGE_ST2.notna()
    )
    closed_mask = (df.STATUS2 == 3) & df.fte1.notna() & df.WAGE_ST.notna()
    s = df.loc[open_mask | closed_mask]
    y = s.dfte.to_numpy()
    gap = s.gap.to_numpy()
    chain = pd.get_dummies(s.CHAIN, prefix="c").drop(columns=["c_1"]).to_numpy()
    coown = s.CO_OWNED.to_numpy().reshape(-1, 1)
    ctrl = np.column_stack([chain, coown])
    r_obs = _ols(y, np.column_stack([gap, ctrl]))
    obs_gap = r_obs["beta"][1]
    se_gap = r_obs["se"][1]
    t_gap = obs_gap / se_gap
    perm_gap = np.empty(n_perm)
    for i in range(n_perm):
        rr = _ols(y, np.column_stack([rng.permutation(gap), ctrl]))
        perm_gap[i] = rr["beta"][1]

    # ---- assemble comparison table ----
    def row(name, obs, se, t, perm, n):
        p1 = float((perm >= obs).mean())
        p2 = float((np.abs(perm) >= np.abs(obs)).mean())
        return {
            "Statistic": name,
            "observed": obs,
            "se": se,
            "t": t,
            "asymptotic_p_2sided": 2 * (1 - norm.cdf(abs(t))),
            "perm_p_1sided": p1,
            "perm_p_2sided": p2,
            "n_sample": n,
            "n_perm": n_perm,
        }

    table = pd.DataFrame(
        [
            row("DiD (mean dFTE NJ - PA)", obs_did, se_did, t_did, perm_did, len(d)),
            row("GAP coefficient (levels)", obs_gap, se_gap, t_gap, perm_gap, len(y)),
        ]
    )

    # ---- figure: permutation distributions ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, obs, perm, title in [
        (axes[0], obs_did, perm_did, "DiD: mean ΔFTE (NJ) − mean ΔFTE (PA)"),
        (axes[1], obs_gap, perm_gap, "Reduced-form wage-gap coefficient"),
    ]:
        p2 = (np.abs(perm) >= np.abs(obs)).mean()
        ax.hist(perm, bins=60, color="0.82", edgecolor="black",
                linewidth=0.4, density=True)
        ax.axvline(obs, color="red", linewidth=2, label=f"observed = {obs:.2f}")
        ax.set_title(f"{title}\npermutation p (two-sided) = {p2:.4f}", fontsize=9)
        ax.set_xlabel("Permuted statistic")
        ax.set_ylabel("Density")
        ax.legend(fontsize=8)

    fig.suptitle(
        "Randomization inference: null distributions under the sharp null "
        "of no minimum-wage effect",
        fontsize=11,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig_path = FIGURES_DIR / "figure_extension_randomization.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)

    return table, fig_path


def extension_heterogeneity(df: pd.DataFrame):
    """Independent extension: treatment-effect heterogeneity.

    Splits the balanced DiD sample by four pre-treatment (wave-1) store
    characteristics and estimates the DiD (NJ - PA change in FTE employment)
    separately within each subgroup. A formal heterogeneity test (interacted-DiD
    F test) asks whether the effect differs across subgroups. Every subgroup
    variable is measured before the minimum-wage change, so none is itself
    affected by the treatment.
    """
    s = df[df.dfte.notna()].copy()
    y = s.dfte.to_numpy()
    nj = s.nj.to_numpy()

    med = s.fte1.median()

    def dim(name, masks):
        g = np.full(len(s), -1, dtype=int)
        for i, m in enumerate(masks):
            g[m.to_numpy()] = i
        return name, g

    dimensions = [
        dim("Initial wage", [s.WAGE_ST < 5.05, s.WAGE_ST >= 5.05]),
        dim("Store size", [s.fte1 < med, s.fte1 >= med]),
        dim("Ownership", [s.CO_OWNED == 0, s.CO_OWNED == 1]),
        dim("Chain", [s.CHAIN == 1, s.CHAIN == 2, s.CHAIN == 3, s.CHAIN == 4]),
    ]
    subgroup_labels = {
        "Initial wage": ["wage < $5.05", "wage >= $5.05"],
        "Store size": ["small (below median)", "large (>= median)"],
        "Ownership": ["franchise", "company-owned"],
        "Chain": ["Burger King", "KFC", "Roy Rogers", "Wendy's"],
    }

    def subgroup_did(g_idx):
        keep = g_idx >= 0
        yy = y[keep]
        nn = nj[keep]
        gg = g_idx[keep]
        G = int(gg.max()) + 1
        D = np.zeros((len(yy), G))
        D[np.arange(len(yy)), gg] = 1.0
        inter = D * nn[:, None]
        X_full = np.column_stack([inter, D[:, 1:]])
        X_rest = np.column_stack([nn, D[:, 1:]])
        r_full = _ols(yy, X_full)
        F, p = _f_pvalue(yy, X_full, X_rest)
        out = []
        for gg_ in range(G):
            out.append(
                (
                    r_full["beta"][gg_ + 1],
                    r_full["se"][gg_ + 1],
                    int(((nn == 1) & (gg == gg_)).sum()),
                    int(((nn == 0) & (gg == gg_)).sum()),
                )
            )
        return out, F, p

    records = []
    forest = []
    for name, g in dimensions:
        per_group, F, p = subgroup_did(g)
        labels = subgroup_labels[name]
        for (coef, se, n_nj, n_pa), lab in zip(per_group, labels):
            records.append(
                {
                    "Dimension": name,
                    "Subgroup": lab,
                    "n_NJ": n_nj,
                    "n_PA": n_pa,
                    "DiD": coef,
                    "SE": se,
                    "t": coef / se if se > 0 else np.nan,
                    "heterog_F": F,
                    "heterog_p": p,
                }
            )
            forest.append((name, lab, coef, se))

    table = pd.DataFrame(records)

    # ---- forest plot of subgroup DiDs ----
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.lines import Line2D

    pos = np.arange(len(forest))[::-1]
    coefs = np.array([f[2] for f in forest])
    ses = np.array([f[3] for f in forest])
    colors = {
        "Initial wage": "tab:blue",
        "Store size": "tab:green",
        "Ownership": "tab:orange",
        "Chain": "tab:red",
    }
    fig, ax = plt.subplots(figsize=(9, 6))
    for i, (dim_name, lab, c, se) in enumerate(forest):
        ax.errorbar(c, pos[i], xerr=1.96 * se, fmt="o",
                    color=colors[dim_name], capsize=3, ms=5)
    ax.axvline(0, color="0.3", linewidth=0.8)
    ax.set_yticks(pos)
    ax.set_yticklabels([f"{d}  ·  {l}" for d, l, _, _ in forest], fontsize=8)
    ax.set_xlabel("DiD (NJ − PA change in FTE employment)")
    ax.set_title("Heterogeneous treatment effects (DiD with 95% CI)")
    handles = [
        Line2D([0], [0], marker="o", color="none", markerfacecolor=colors[d],
               markersize=7, label=d)
        for d in colors
    ]
    ax.legend(handles=handles, fontsize=8, loc="lower right")
    fig.tight_layout()
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig_path = FIGURES_DIR / "figure_extension_heterogeneity.png"
    fig.savefig(fig_path, dpi=150)
    plt.close(fig)

    return table, fig_path


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

    t3 = table3_employment(df)
    t3.to_csv(TABLES_DIR / "table3_employment.csv", index=False)
    print(f"  table 3 -> {TABLES_DIR / 'table3_employment.csv'}")

    t4 = table4_reduced_form(df)
    t4.to_csv(TABLES_DIR / "table4_reduced_form.csv", index=False)
    print(f"  table 4 -> {TABLES_DIR / 'table4_reduced_form.csv'} "
          f"(n={t4.n.iloc[0]}, depvar mean={t4.attrs['depvar_mean']:.3f})")

    t5 = table5_specification_tests(df)
    t5.to_csv(TABLES_DIR / "table5_specification_tests.csv", index=False)
    print(f"  table 5 -> {TABLES_DIR / 'table5_specification_tests.csv'}")

    t6 = table6_nonwage(df)
    t6.to_csv(TABLES_DIR / "table6_nonwage_outcomes.csv", index=False)
    print(f"  table 6 -> {TABLES_DIR / 'table6_nonwage_outcomes.csv'}")

    t7 = table7_prices(df)
    t7.to_csv(TABLES_DIR / "table7_prices.csv", index=False)
    print(f"  table 7 -> {TABLES_DIR / 'table7_prices.csv'} "
          f"(n={t7.n.iloc[0]}, depvar mean={t7.attrs['depvar_mean']:.4f})")

    fig1 = figure1_wages(df)
    print(f"  figure 1 -> {fig1}")


def step3_extension(df: pd.DataFrame) -> None:
    """Run the independent extensions (randomization inference + heterogeneity)."""
    TABLES_DIR.mkdir(parents=True, exist_ok=True)

    rtable, rfig = extension_randomization(df)
    rtable.to_csv(TABLES_DIR / "extension_randomization.csv", index=False)
    print(f"  extension (randomization inference) -> "
          f"{TABLES_DIR / 'extension_randomization.csv'} and {rfig}")

    htable, hfig = extension_heterogeneity(df)
    htable.to_csv(TABLES_DIR / "extension_heterogeneity.csv", index=False)
    print(f"  extension (heterogeneity) -> "
          f"{TABLES_DIR / 'extension_heterogeneity.csv'} and {hfig}")


def main() -> None:
    print("Card & Krueger (1994) replication workflow")
    df = step1_build_sample()
    step2_replicate(df)
    step3_extension(df)
    print("Done. Outputs written to outputs/tables/ and outputs/figures/.")


if __name__ == "__main__":
    main()
