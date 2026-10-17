# 📋 Requirements Specification

## Scenario

> As the regional manager of a chain of car dealerships, I need dashboards that help me understand my **sales** and **service** departments.

The same specification was delivered in two tools:

| | IBM Cognos Analytics | Google Looker Studio |
|---|---|---|
| Deliverable | One dashboard with **two tabs** | One report with **two pages** |
| Data access | *Auto group data module* (Team content → Samples → By industry → Automotive → Data) | Course files uploaded to Google Drive, imported to Google Sheets, connected with the **Google Sheets connector** |
| Export | Share → Export → *Include filters* → Save as PDF | Share ▾ → Download report → PDF, *All pages* |

---

## Sales dashboard

**Layout:** four small tiles across the top and one large panel below.

```text
┌───────────┬───────────┬───────────┬───────────┐
│  Panel 1  │  Panel 2  │  Panel 3  │  Panel 4  │
│  Profit   │  Qty sold │ Qty/model │  Avg qty  │
├───────────┴───────────┴───────────┴───────────┤
│                    Panel 5                    │
│             Profit by Dealer ID               │
└───────────────────────────────────────────────┘
```

| Panel | Metric | Visual | Rule |
|---|---|---|---|
| 1 | Profit | KPI / scorecard | Millions of USD, **1 decimal place** (`$78.4M`) |
| 2 | Quantity sold | KPI / scorecard | Total units |
| 3 | Quantity sold by model | Bar chart | One bar per model |
| 4 | Average quantity sold | KPI / scorecard | Mean units per record |
| 5 | Profit by Dealer ID | Column chart | **Cognos:** sorted ascending (lowest-profit dealer first, so under-performers are seen first). **Looker Studio:** sorted descending (highest-profit dealer first, reading as a leaderboard) |

---

## Service dashboard

**Layout:** 2 × 2 grid.

```text
┌───────────────────────┬───────────────────────┐
│       Panel 1         │       Panel 2         │
│   Recalls by model    │  Customer sentiment   │
├───────────────────────┼───────────────────────┤
│       Panel 3         │       Panel 4         │
│ Qty & profit by month │ Recalls model×system  │
└───────────────────────┴───────────────────────┘
```

| Panel | Metric | Cognos visual | Looker Studio visual | Purpose |
|---|---|---|---|---|
| 1 | Number of recalls per model | Column chart | Column chart | Which models are recalled most |
| 2 | Positive vs. neutral vs. negative reviews | Treemap | Treemap | Customer sentiment split |
| 3 | Quantity sold per month vs. profit | Line and column chart | Combo chart | Seasonality of volume and profit |
| 4 | Recalls by model and affected system | Heat map | Pivot table with heat map | Spot outliers for a model or a system |

---

## Acceptance criteria

- [x] Sales tab/page renamed **Sales**; Service tab/page renamed **Service**
- [x] All 9 visuals present in each tool (18 in total)
- [x] Profit shown as `$78.4M` / `$78.4m` (1 decimal, millions)
- [x] Profit by Dealer sorted as specified per tool
- [x] Both dashboards exported to PDF ([Cognos](../dashboards/cognos-analytics/cognos-dashboards-export.pdf) · [Looker Studio](../dashboards/looker-studio/looker-studio-report-export.pdf))
- [x] Every displayed KPI reproduced from raw data ([validation report](../reports/kpi_validation_report.md))
