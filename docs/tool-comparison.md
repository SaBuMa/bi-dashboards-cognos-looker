# ⚖️ Tool Comparison: IBM Cognos Analytics vs Google Looker Studio

Same data, same requirements, two tools. Both produced **identical numbers** (confirmed by the [validation report](../reports/kpi_validation_report.md)). What differed was how each tool got there.

---

## At a glance

| Dimension | IBM Cognos Analytics | Google Looker Studio |
|---|---|---|
| **Category** | Enterprise BI platform | Free, self-service reporting |
| **Data connection** | Governed **data module** with joins and field roles already defined | One **data source per Google Sheet**; joins only through *blends* |
| **Data preparation** | Done once in the module and reused by every dashboard | Done per data source (field types, aggregations) |
| **Layout** | Pre-built templates (tabbed, 4 + 1, 2 × 2) | Free-form canvas; layout drawn by hand |
| **KPI tile** | *Summary* visualization, auto-abbreviates (`$78.4M`) | *Scorecard*, compact numbers toggle (`$78.4m`) |
| **Heat map** | Native **Heat map** visualization with colour legend | **Pivot table with heatmap** (numbers are visible in every cell) |
| **Combo chart** | *Line and column* | *Combo chart*, dual axis set in Style |
| **Treemap** | Hierarchy + size + colour scale | Dimension + metric, categorical colours |
| **Sharing** | Team content folders, role-based permissions, scheduled delivery | Google-Drive-style sharing (viewer/editor), link sharing, scheduled email |
| **Cost** | Licensed (trial used here) | Free |
| **Best for** | Governed, organisation-wide reporting on modelled data | Fast, shareable reports on Google-ecosystem data |

---

## Panel-by-panel differences

| Panel | Cognos | Looker Studio | Comment |
|---|---|---|---|
| Sales P1 Profit | `$78.4M` | `$78.4m` | Same value, different abbreviation case |
| Sales P2 Qty | `58118` | `58,118` | Looker adds the thousands separator by default |
| Sales P3 by model | Ascending (Champlain → Hudson) | Descending (Hudson → Champlain) | Descending puts the leader first |
| Sales P5 by dealer | **Ascending** (1222 → 1288) | **Descending** (1288 → 1222) | Ascending highlights under-performers; descending reads as a leaderboard |
| Service P1 recalls | Alphabetical by model | Sorted by value ↓ | Value sort makes ranking immediate |
| Service P2 sentiment | Colour scale by count (Neutral and Negative look alike) | One colour per class | Categorical colours separate the three classes better |
| Service P3 combo | Profit = columns, Qty = line | Qty = columns, Profit = line | Both valid; each tool's default series assignment was kept |
| Service P4 heat map | Colour only, 14 systems | Colour **and** numbers, 8 systems visible | Looker's pivot can be read without hovering; Cognos shows the full system list |

---

## What I'd pick, and when

- **Cognos Analytics** when the data model has to be **governed and reused**: many dashboards on the same certified definitions, role-based security, and an enterprise environment that already licenses IBM.
- **Looker Studio** for **speed and reach**: free, quick to share with anyone who has a Google account, and a good fit when the data already lives in Sheets, BigQuery or GA4.
- **Either way**, keep metric definitions *outside* the tool (see [KPI catalog](kpi-catalog.md)) and verify them against the source (see [`validate_kpis.py`](../analysis/validate_kpis.py)). That is what kept the two builds consistent.
