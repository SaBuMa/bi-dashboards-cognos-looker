#!/usr/bin/env python3
"""
validate_kpis.py: recompute every dashboard KPI from the raw data.

A dashboard is only as trustworthy as the numbers behind it. This script:

  1. Loads the raw Excel/CSV files into an in-memory SQLite database,
     normalising column names to snake_case.
  2. Runs every query in sql/dashboard_queries.sql (one per dashboard panel).
  3. Compares each result with the value the Cognos Analytics and
     Looker Studio dashboards actually display.
  4. Runs data-quality checks (nulls, duplicates, referential integrity,
     suspicious values).
  5. Writes a Markdown report to reports/kpi_validation_report.md.

Usage
-----
    python analysis/validate_kpis.py                  # validate data/raw (AU_* files)
    python analysis/validate_kpis.py --dataset legacy # validate data/legacy files

Exit code is 0 when every dashboard check passes, 1 otherwise, so the
script can run in CI.
"""

from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SQL_FILE = ROOT / "sql" / "dashboard_queries.sql"
REPORT_DIR = ROOT / "reports"

DATASETS = {
    "raw": {
        "dir": ROOT / "data" / "raw",
        "files": {
            "sales_by_model": "AU_Sales_By_Model.xlsx",
            "car_recalls": "AU_Car_Recalls.xlsx",
            "sentiment": "AU_Sentiment.csv",
            "dealers": "AU_Dealers.xlsx",
            "car_models": "AU_Car_Models.xlsx",
            "bad_sentiment": "AU_Bad_Sentiment.xlsx",
        },
    },
    "legacy": {
        "dir": ROOT / "data" / "legacy",
        "files": {
            "sales_by_model": "sales_by_model.xlsx",
            "car_recalls": "Car_Recalls.xlsx",
            "sentiment": "sentiment.csv",
            "dealers": "dealers.xlsx",
            "car_models": "car_models.xlsx",
            "bad_sentiment": "bad_sentiments.xlsx",
        },
    },
}

# ---------------------------------------------------------------------------
# What the published dashboards display (read off the exported PDFs).
# ---------------------------------------------------------------------------
EXPECTED = {
    "profit_label": "$78.4M",
    "quantity_sold": 58118,
    "avg_quantity": 19.37,
    "model_rank_by_qty_asc": ["Champlain", "Beaufort", "Salish", "Labrador", "Hudson"],
    "dealer_rank_by_profit_asc": [1222, 1402, 1401, 1212, 1336, 1217, 1215, 1224, 1301, 1288],
    "recall_rank_desc": ["Beaufort", "Labrador", "Champlain", "Hudson", "Salish"],
    "sentiment_min_max": (14528, 44885),          # Cognos treemap legend
    "peak_profit_month": "May",                   # tallest column, both tools
    "lowest_profit_month": "December",
    "heatmap_min_max": (3300.0, 70422.354),       # Cognos heat-map legend
    "heatmap_cells_k": {                           # Looker pivot table cells (k units)
        ("Beaufort", "Airbag"): "70.4k",
        ("Champlain", "Suspension"): "60.9k",
        ("Hudson", "Airbag"): "52k",
        ("Labrador", "Tires"): "40k",
        ("Salish", "Engine"): "3.3k",
    },
}


@dataclass
class Check:
    panel: str
    description: str
    expected: str
    actual: str
    passed: bool


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------
def snake(name: str) -> str:
    """'Dealer ID' -> 'dealer_id', 'System_Affected' -> 'system_affected'."""
    return re.sub(r"[^0-9a-zA-Z]+", "_", name).strip("_").lower()


def load_frames(dataset: str) -> dict[str, pd.DataFrame]:
    cfg = DATASETS[dataset]
    frames = {}
    for table, filename in cfg["files"].items():
        path = cfg["dir"] / filename
        df = pd.read_csv(path) if path.suffix == ".csv" else pd.read_excel(path)
        df.columns = [snake(c) for c in df.columns]
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].dt.strftime("%Y-%m-%d %H:%M:%S")
        frames[table] = df
    return frames


def build_db(frames: dict[str, pd.DataFrame]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    for table, df in frames.items():
        df.to_sql(table, con, index=False)
    return con


def load_queries() -> dict[str, str]:
    text = SQL_FILE.read_text(encoding="utf-8")
    blocks = re.split(r"^-- name:\s*(\S+)\s*$", text, flags=re.MULTILINE)
    # blocks = [preamble, name1, body1, name2, body2, ...]
    return {blocks[i]: blocks[i + 1].strip() for i in range(1, len(blocks), 2)}


# ---------------------------------------------------------------------------
# Dashboard checks
# ---------------------------------------------------------------------------
def k_label(value: float) -> str:
    """Mimic Looker Studio compact numbers: 70422 -> '70.4k', 52041 -> '52k'."""
    k = round(value / 1000, 1)
    return f"{k:g}k"


def dashboard_checks(results: dict[str, pd.DataFrame]) -> list[Check]:
    checks: list[Check] = []

    def fmt(v):
        if isinstance(v, list):
            return " → ".join(map(str, v))
        if isinstance(v, tuple):
            return " to ".join(f"{x:,}" if isinstance(x, (int, float)) else str(x) for x in v)
        if isinstance(v, int):
            return f"{v:,}"
        return str(v)

    def add(panel, desc, expected, actual):
        checks.append(Check(panel, desc, fmt(expected), fmt(actual), expected == actual))

    # ---- Sales -------------------------------------------------------------
    p1 = results["sales_p1_total_profit"].iloc[0]
    add("Sales P1", "Total profit ($M, 1 dp)", EXPECTED["profit_label"],
        f"${p1.total_profit_musd:.1f}M")

    p2 = int(results["sales_p2_quantity_sold"].iloc[0, 0])
    add("Sales P2", "Total quantity sold", EXPECTED["quantity_sold"], p2)

    p3 = results["sales_p3_quantity_by_model"]["model"].tolist()
    add("Sales P3", "Model ranking by quantity (asc)", EXPECTED["model_rank_by_qty_asc"], p3)

    p4 = float(results["sales_p4_avg_quantity"].iloc[0, 0])
    add("Sales P4", "Average quantity sold", EXPECTED["avg_quantity"], p4)

    p5 = results["sales_p5_profit_by_dealer"]["dealer_id"].astype(int).tolist()
    add("Sales P5", "Dealer ranking by profit (low → high)", EXPECTED["dealer_rank_by_profit_asc"], p5)

    # ---- Service -----------------------------------------------------------
    s1 = results["service_p1_recalls_by_model"]["model"].tolist()
    add("Service P1", "Model ranking by recalled units (desc)", EXPECTED["recall_rank_desc"], s1)

    s2 = results["service_p2_sentiment"]["reviews"]
    add("Service P2", "Sentiment count range (min, max)", EXPECTED["sentiment_min_max"],
        (int(s2.min()), int(s2.max())))

    s3 = results["service_p3_monthly_qty_profit"].set_index("month")["profit"]
    add("Service P3", "Peak profit month", EXPECTED["peak_profit_month"], s3.idxmax())
    add("Service P3", "Lowest profit month", EXPECTED["lowest_profit_month"], s3.idxmin())

    s4 = results["service_p4_recall_heatmap"]
    add("Service P4", "Heat-map colour range (min, max)", EXPECTED["heatmap_min_max"],
        (round(float(s4.recalled_units.min()), 3), round(float(s4.recalled_units.max()), 3)))
    cells = s4.set_index(["model", "system_affected"])["recalled_units"]
    for (model, system), label in EXPECTED["heatmap_cells_k"].items():
        actual = k_label(cells.get((model, system), 0))
        add("Service P4", f"Cell {model} x {system}", label, actual)

    return checks


# ---------------------------------------------------------------------------
# Data-quality checks
# ---------------------------------------------------------------------------
def quality_checks(frames: dict[str, pd.DataFrame]) -> list[tuple[str, str, str]]:
    """Return (status, check, detail). status is PASS / WARN."""
    out = []
    sales, recalls = frames["sales_by_model"], frames["car_recalls"]
    dealers, models = frames["dealers"], frames["car_models"]

    for name, df in frames.items():
        nulls = int(df.isna().sum().sum())
        dups = int(df.duplicated().sum())
        if name == "sentiment":
            # One row = one review, with no review ID. Two reviews from the same
            # postal code on the same day with the same label are legitimately
            # identical, so duplicates are expected here and not an error.
            out.append(("INFO" if nulls == 0 else "WARN", f"`{name}`: nulls / identical rows",
                        f"{len(df):,} rows, {nulls} nulls, {dups:,} identical rows "
                        "(expected: event log without a review ID)"))
            continue
        status = "PASS" if nulls == 0 and dups == 0 else "WARN"
        out.append((status, f"`{name}`: nulls / exact duplicate rows",
                    f"{len(df):,} rows, {nulls} nulls, {dups} duplicates"))

    orphans = sorted(set(sales.dealer_id) - set(dealers.dealer_id))
    out.append(("PASS" if not orphans else "WARN", "Sales dealer IDs exist in `dealers`",
                "all matched" if not orphans else f"orphans: {orphans}"))

    orphans = sorted(set(recalls.car_id) - set(models.car_id))
    out.append(("PASS" if not orphans else "WARN", "Recall car IDs exist in `car_models`",
                "all matched" if not orphans else f"orphans: {orphans}"))

    mismatch = recalls.merge(models, on="car_id", suffixes=("", "_ref"))
    bad = int((mismatch.model != mismatch.model_ref).sum())
    out.append(("PASS" if bad == 0 else "WARN", "Recall model name agrees with `car_models`",
                f"{bad} mismatches"))

    frac = int((recalls.units % 1 != 0).sum())
    out.append(("PASS" if frac == 0 else "WARN", "Recall `units` are whole vehicles",
                f"{frac} of {len(recalls)} rows hold fractional units "
                f"(e.g. {recalls.loc[recalls.units % 1 != 0, 'units'].iloc[0]:.3f})"
                if frac else "all integers"))

    neg = int((sales.profit < 0).sum()) + int((sales.quantity_sold < 0).sum())
    out.append(("PASS" if neg == 0 else "WARN", "No negative profit or quantity", f"{neg} negative values"))

    # Year-over-year copy detection in recalls
    r = recalls.copy()
    r["year"] = r.date.str[:4]
    r["md"] = r.date.str[5:10]
    sig = {y: frozenset(map(tuple, g[["md", "model", "system_affected", "units"]].values))
           for y, g in r.groupby("year")}
    years = sorted(sig)
    copies = [f"{a} = {b}" for i, a in enumerate(years) for b in years[i + 1:] if sig[a] == sig[b]]
    out.append(("PASS" if not copies else "WARN", "No recall year is a copy of another year",
                "none found" if not copies else f"identical years: {', '.join(copies)}"))

    def span(df, col="date"):
        return f"{df[col].min()[:10]} to {df[col].max()[:10]}"
    out.append(("INFO", "Date coverage",
                f"sales {span(sales)} · recalls {span(recalls)} · sentiment {span(frames['sentiment'])}"))
    return out


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------
def df_to_md(df: pd.DataFrame) -> str:
    """Render a DataFrame as a GitHub Markdown table with readable numbers."""
    id_like = re.compile(r"(_id|year|_num)$")
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for row in df.itertuples(index=False):
        cells = []
        for col, v in zip(cols, row):
            if id_like.search(col):
                cells.append(str(int(v)) if pd.notna(v) else "")
            elif col.startswith("pct_"):
                cells.append(f"{v:.1f}%")
            elif isinstance(v, float):
                cells.append(f"{v:,.0f}" if v.is_integer() else f"{v:,.2f}")
            elif isinstance(v, int) and not isinstance(v, bool):
                cells.append(f"{v:,}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def write_report(dataset, checks, quality, results, path: Path) -> None:
    passed = sum(c.passed for c in checks)
    lines = [
        "# KPI Validation Report",
        "",
        f"*Generated by `analysis/validate_kpis.py` on {datetime.now():%Y-%m-%d %H:%M}*  ",
        f"*Dataset: `{DATASETS[dataset]['dir'].relative_to(ROOT)}`*",
        "",
        f"**Result: {passed}/{len(checks)} dashboard checks passed.**",
        "",
        "## 1. Dashboard values vs. recomputed values",
        "",
        "| Panel | Check | Dashboard shows | Recomputed | Status |",
        "|---|---|---|---|---|",
    ]
    for c in checks:
        lines.append(f"| {c.panel} | {c.description} | {c.expected} | {c.actual} | "
                     f"{'✅ PASS' if c.passed else '❌ FAIL'} |")
    lines += ["", "## 2. Data-quality checks", "", "| Status | Check | Detail |", "|---|---|---|"]
    icon = {"PASS": "✅", "WARN": "⚠️", "INFO": "ℹ️"}
    for status, name, detail in quality:
        lines.append(f"| {icon[status]} {status} | {name} | {detail} |")
    lines += ["", "## 3. Query results", ""]
    for name, df in results.items():
        lines += [f"### `{name}`", "", df_to_md(df), ""]
    path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--dataset", choices=DATASETS, default="raw")
    parser.add_argument("--report", type=Path, default=None,
                        help="output path (default: reports/kpi_validation_report[_legacy].md)")
    args = parser.parse_args()

    frames = load_frames(args.dataset)
    con = build_db(frames)
    results = {name: pd.read_sql_query(sql, con) for name, sql in load_queries().items()}

    checks = dashboard_checks(results)
    quality = quality_checks(frames)

    width = max(len(c.description) for c in checks) + 2
    print(f"\nDashboard checks against data/{args.dataset}\n" + "-" * (width + 40))
    for c in checks:
        mark = "PASS" if c.passed else "FAIL"
        print(f"[{mark}] {c.panel:<11} {c.description:<{width}} {c.actual}")
    print("\nData-quality checks\n" + "-" * (width + 40))
    for status, name, detail in quality:
        print(f"[{status}] {re.sub('`', '', name)}: {detail}")

    REPORT_DIR.mkdir(exist_ok=True)
    suffix = "" if args.dataset == "raw" else f"_{args.dataset}"
    report = args.report or REPORT_DIR / f"kpi_validation_report{suffix}.md"
    write_report(args.dataset, checks, quality, results, report)
    passed = sum(c.passed for c in checks)
    print(f"\n{passed}/{len(checks)} dashboard checks passed. Report: {report.relative_to(ROOT)}")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BrokenPipeError:  # output piped to `head` etc.
        sys.exit(0)
