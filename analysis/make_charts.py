#!/usr/bin/env python3
"""
make_charts.py: build the supporting charts used in docs/insights.md.

Reuses the loader and SQL queries from validate_kpis.py so the charts and the
KPI report always come from the same numbers.

    python analysis/make_charts.py      # writes docs/images/*.png
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

from validate_kpis import ROOT, build_db, load_frames, load_queries  # noqa: E402

OUT = ROOT / "docs" / "images"

BLUE, ORANGE = "#2a78d6", "#eb6834"
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e4e3df"


def style(ax, title, subtitle):
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK, pad=24)
    ax.text(0, 1.02, subtitle, transform=ax.transAxes, fontsize=9.5, color=INK_2)
    for side in ("top", "right", "left"):
        ax.spines[side].set_visible(False)
    ax.spines["bottom"].set_color(GRID)
    ax.tick_params(colors=INK_2, length=0)
    ax.set_axisbelow(True)


def profit_mix(df: pd.DataFrame) -> None:
    df = df.sort_values("pct_of_profit")
    fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150)
    y = range(len(df))
    h = 0.36
    ax.barh([i + h / 2 + 0.02 for i in y], df.pct_of_units, height=h, color=BLUE, label="Share of units sold")
    ax.barh([i - h / 2 - 0.02 for i in y], df.pct_of_profit, height=h, color=ORANGE, label="Share of profit")
    for i, (u, p) in enumerate(zip(df.pct_of_units, df.pct_of_profit)):
        ax.text(u + 0.6, i + h / 2 + 0.02, f"{u:.0f}%", va="center", fontsize=8.5, color=INK_2)
        ax.text(p + 0.6, i - h / 2 - 0.02, f"{p:.0f}%", va="center", fontsize=8.5, color=INK_2)
    ax.set_yticks(list(y), df.model, color=INK)
    ax.xaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_xlim(0, 50)
    ax.xaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    style(ax, "Salish earns 44% of profit from 20% of volume",
          "Share of total units sold vs. share of total profit, by model (2021–2025)")
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK_2)
    fig.tight_layout()
    fig.savefig(OUT / "profit-mix-by-model.png", facecolor="white")
    plt.close(fig)


def negative_trend(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 3.8), dpi=150)
    years = df.year.astype(str)
    ax.bar(years, df.pct_negative, width=0.55, color=ORANGE)
    for x, v in zip(years, df.pct_negative):
        ax.text(x, v + 0.5, f"{v:.1f}%", ha="center", fontsize=9, color=INK_2)
    ax.yaxis.grid(True, color=GRID, linewidth=0.8)
    ax.set_ylim(0, 30)
    ax.yaxis.set_major_formatter(lambda v, _: f"{v:.0f}%")
    ax.tick_params(axis="x", colors=INK)
    style(ax, "Negative reviews rose from 15% to 26% in four years",
          "Share of customer reviews classified as Negative, per year")
    fig.tight_layout()
    fig.savefig(OUT / "negative-sentiment-trend.png", facecolor="white")
    plt.close(fig)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    con = build_db(load_frames("raw"))
    q = load_queries()
    profit_mix(pd.read_sql_query(q["extra_profit_mix_by_model"], con))
    negative_trend(pd.read_sql_query(q["extra_negative_sentiment_trend"], con))
    print(f"Charts written to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
