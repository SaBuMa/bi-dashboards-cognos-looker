# 🧰 Dashboard Management

Building a dashboard is a one-off task. Keeping it correct, fast and in the right hands is ongoing work. This document covers how these dashboards are managed across their lifecycle.

```text
  ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐   ┌────────────┐
  │ 1. Data    │──►│ 2. Build   │──►│ 3. Check   │──►│ 4. Share   │──►│ 5. Maintain│
  │    sources │   │            │   │            │   │  & export  │   │  & version │
  └────────────┘   └────────────┘   └────────────┘   └────────────┘   └─────┬──────┘
        ▲                                                                   │
        └──────────────────── data or requirement changes ──────────────────┘
```

---

## 1. Data-source management

| Topic | Cognos Analytics | Looker Studio |
|---|---|---|
| Where the data lives | *Auto group data module* in Team content | Google Sheets in Drive, one data source per sheet |
| Joins | Defined once in the data module | Per chart, using blends |
| Field roles | Set in the module (measure vs. attribute) | Set per data source (Dimension vs. Metric, type) |
| Refresh | Module reloads from its source; uploaded files must be replaced | Sheets refresh on Looker's cache cycle or with **Refresh data** |
| Credentials | Cognos service / user credentials | *Owner's* or *viewer's* credentials, chosen per data source |

**Practices used**
- Fix field types **at the source layer** (e.g. `Dealer ID` → text) rather than in each chart.
- Keep the **raw files versioned** in [`data/`](../data/), so you can always tell which release a dashboard was built on (see [`--dataset legacy`](../reports/kpi_validation_report_legacy.md)).
- Keep **one KPI definition** for both tools in the [KPI catalog](kpi-catalog.md).

---

## 2. Validation as a regression test

Every time the data or a chart changes, re-run:

```bash
python analysis/validate_kpis.py
```

It recomputes each panel in SQL and compares the result with the values the dashboards are expected to show. In this repo it also runs automatically on every push through **GitHub Actions** ([`validate-kpis.yml`](../.github/workflows/validate-kpis.yml)). A failing check means a dashboard number has drifted from its definition.

---

## 3. Sharing & access control

| Need | Cognos Analytics | Looker Studio |
|---|---|---|
| Private draft | Save in **My content** | Report owned by you, not shared |
| Team access | Save in **Team content** folder with role-based permissions | **Share** → add people/groups as *Viewer* or *Editor* |
| Wide distribution | Schedule delivery / export | Link sharing ("Anyone with the link can view") or **Schedule email delivery** |
| Static snapshot | **Share → Export → PDF** (with filters) | **Download report → PDF**, all pages |

**Principle of least privilege:** viewers get *view*, only maintainers get *edit*. For Looker Studio, using **owner's credentials** lets viewers see the data without being given access to the underlying Sheets.

---

## 4. Design standards applied

| Standard | How it shows up |
|---|---|
| **Summary first, detail below** | KPI tiles across the top of *Sales*; detail chart underneath |
| **One question per visual** | Every panel answers a single question from the [requirements](requirements.md) |
| **Right chart for the job** | Single number → KPI tile · ranking → bar/column · part-to-whole → treemap · two measures over time → combo · two-dimensional outliers → heat map |
| **Consistent formatting** | Profit always in USD millions with 1 decimal; compact axis labels |
| **Readable titles** | Titles say what is measured ("Profit by Dealer ID"), not the chart type |
| **Sort with intent** | Ascending to surface under-performers (Cognos P5), descending for a leaderboard (Looker P5) |

---

## 5. Versioning & change log

Dashboards in both tools have limited native version history, so the repo is the record:

| Artifact | Location | Role |
|---|---|---|
| PDF + PNG exports | [`dashboards/`](../dashboards/) | Snapshot of what users saw |
| Data release | [`data/raw/`](../data/raw/) | Exact inputs |
| KPI definitions | [`docs/kpi-catalog.md`](kpi-catalog.md) | What each number means |
| Validation report | [`reports/`](../reports/) | Proof that numbers matched the data at that commit |

A dashboard change = new exports + re-run validation + one commit describing what changed.

---

## 6. Maintenance checklist

Use on each data refresh or dashboard change:

- [ ] New data loaded to the source (data module / Google Sheets)
- [ ] Field types unchanged (IDs still text, Profit still currency)
- [ ] `python analysis/validate_kpis.py` passes
- [ ] Data-quality warnings reviewed (duplicates, fractional units, date coverage)
- [ ] Titles, sorting and number formats still correct
- [ ] Sharing permissions reviewed: no unintended editors or public links
- [ ] PDF/PNG exports refreshed in `dashboards/`
- [ ] Change committed with a descriptive message

---

## 7. Improvements for a v2

| Improvement | Why |
|---|---|
| Add a **date-range filter** to both dashboards | Tables cover different years (see [data issue #5](../data/README.md#5-known-data-quality-issues)) |
| Add **Model** and **Dealer** filter controls | Let a dealer manager see only their own store |
| Rename "# of Recalls" → **"Recalled units"** and add a **campaign count** KPI | The current label is misleading ([issue #3](../data/README.md#5-known-data-quality-issues)) |
| Add a **profit-per-unit** KPI | Volume and profit rank models differently ([insights](insights.md#1-volume-is-not-profit)) |
| Add a **negative-sentiment trend** line | The share of negative reviews rose from 15% to 26% ([insights](insights.md#2-customer-sentiment-is-deteriorating-everywhere)) |
| Deduplicate the **2020 recall rows** upstream | 2020 is a copy of 2021 ([issue #1](../data/README.md#5-known-data-quality-issues)) |
| Move the data to a warehouse (e.g. **BigQuery**) and point both tools at it | One governed source instead of files |
