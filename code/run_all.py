"""Card & Krueger (1994) replication — one-command entry point.

Run from the repository root after placing ``public.csv`` in ``data/raw/``::

    python code/run_all.py

The script reconstructs the analysis sample, reproduces the paper's main
tables and figures, and runs the independent extension. All outputs are
written to ``outputs/tables/`` and ``outputs/figures/``.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW_DATA = ROOT / "data" / "raw" / "public.csv"
PROCESSED_DIR = ROOT / "data" / "processed"
TABLES_DIR = ROOT / "outputs" / "tables"
FIGURES_DIR = ROOT / "outputs" / "figures"


def step1_build_sample() -> None:
    """Reconstruct variables (FTE employment, wage GAP) and write processed data."""
    raise NotImplementedError("TODO: implement sample construction (step 1).")


def step2_replicate() -> None:
    """Reproduce the main table(s) and figure(s)."""
    raise NotImplementedError("TODO: implement replication (step 2).")


def step3_extension() -> None:
    """Run the independent extension."""
    raise NotImplementedError("TODO: implement extension (step 3).")


def main() -> None:
    print("Card & Krueger (1994) replication workflow")
    step1_build_sample()
    step2_replicate()
    step3_extension()
    print("Done. Outputs written to outputs/tables/ and outputs/figures/.")


if __name__ == "__main__":
    main()
