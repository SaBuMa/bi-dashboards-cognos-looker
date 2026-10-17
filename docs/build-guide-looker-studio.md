# 🛠 Build Guide: Google Looker Studio

How the Sales and Service pages were built in **Google Looker Studio** (free version). Menu names can change slightly as Google updates the product.

**Result:** [Sales](../dashboards/looker-studio/sales-dashboard.png) · [Service](../dashboards/looker-studio/service-dashboard.png) · [PDF export](../dashboards/looker-studio/looker-studio-report-export.pdf)

---

## 0. How Looker Studio works (mental model)

Think of Looker Studio as a **set of TV screens, each tuned to one channel**. Every Google Sheet becomes a *data source* (a channel), and every chart is a screen tuned to exactly one channel. To show recalls and sales on the same page, you add two channels to the report and tune each chart to the one it needs.

```text
 Google Drive          Google Sheets            Looker Studio report
 ┌──────────────┐     ┌────────────────┐       ┌───────────────────────────┐
 │ AU_*.xlsx    │────►│ Sales_By_Model │──┐    │ Page "Sales"              │
 │ AU_*.csv     │     │ Car_Recalls    │──┼──► │   scorecards, bar, column │
 └──────────────┘     │ Sentiment      │──┘    │ Page "Service"            │
     upload            └────────────────┘       │   column, treemap, combo, │
                        import / open with       │   pivot heat map          │
                        Google Sheets            └───────────────────────────┘
                                         Google Sheets connector
                                         (one data source per sheet)
```

---

## 1. Prepare the data

1. Upload the files from [`data/raw/`](../data/raw/) to **Google Drive**.
2. Open each one with **Google Sheets** (right-click → *Open with → Google Sheets*). If a file does not appear later, create a blank Google Sheet and use **File → Import** to load it.
3. You need at least: `AU_Sales_By_Model`, `AU_Car_Recalls` and `AU_Sentiment`.

## 2. Create the report and connect the data

1. Go to [lookerstudio.google.com](https://lookerstudio.google.com) → **Blank report**.
2. **Add data → Google Sheets** → pick `AU_Sales_By_Model` → worksheet → **Add**.
3. Repeat **Resource → Manage added data sources → Add a data source** for `AU_Car_Recalls` and `AU_Sentiment`.
4. In each data source, check the field types:
   - `Dealer ID` → **Text** (a label, not a number to sum)
   - `Profit` → **Currency (USD)**
   - `Month` → Text; `Date` → Date
5. Rename page 1 to **Sales** and add a page named **Service** (**Page → Manage pages**).

---

## 3. Sales page (data source: `AU_Sales_By_Model`)

| Panel | Chart type | Setup | Style |
|---|---|---|---|
| 1 · Profit | **Scorecard** | Metric: `Profit` (SUM) | Compact numbers ✔, Decimal precision **1** → `$78.4m` |
| 2 · Quantity Sold | **Scorecard** | Metric: `Quantity Sold` (SUM) | Thousands separator → `58,118` |
| 3 · Quantity Sold by Model | **Column/Bar chart** | Dimension: `Model` · Metric: `Quantity Sold` · Sort: Quantity Sold ↓ | Single colour, compact axis |
| 4 · Average Quantity Sold | **Scorecard** | Metric: `Quantity Sold`, aggregation changed to **AVG** | Decimal precision 2 → `19.37` |
| 5 · Profit by Dealer ID | **Column chart** | Dimension: `Dealer ID` · Metric: `Profit` · Sort: **Profit, descending** · Bars: 10 | Compact axis (`10m`) |

Panel 5 is sorted **descending**, so the page reads as a dealer leaderboard with the top earner (1288) on the left.

---

## 4. Service page

| Panel | Data source | Chart type | Setup |
|---|---|---|---|
| 1 · # of Recalls by Model | `AU_Car_Recalls` | **Column chart** | Dimension `Model` · Metric `Units` (SUM) · Sort Units ↓ |
| 2 · Customer sentiment | `AU_Sentiment` | **Treemap** | Dimension `Sentiment` · Metric **Record Count** |
| 3 · Quantity Sold and Profit by Month | `AU_Sales_By_Model` | **Combo chart** | Dimension `Month` · Metrics `Quantity Sold` (bars, right axis) and `Profit` (line, left axis) |
| 4 · # of Recalls by Models and Affected System | `AU_Car_Recalls` | **Pivot table with heatmap** | Row dimension `Model` · Column dimension `System_Affected` · Metric `Units` (SUM) |

**Combo chart dual axis:** in **Style**, set the *Quantity Sold* series to **Bars** on the **right** axis and *Profit* to **Line** on the **left** axis. Their scales differ by more than 1,000×, so one axis would flatten the bars.

**Heat map:** the *Pivot table with heatmap* type shades each cell automatically. Use compact numbers so cells read `70.4k` instead of `70422.354`.

---

## 5. Export to PDF

1. Click the small triangle next to **Share** → **Download report**.
2. Select **All pages** → **Download**.

---

## 6. Lessons learned

- **One chart = one data source.** Unlike Cognos, there is no pre-built model. To combine tables in a single chart you need a **blend** (a left-join-style merge on a shared key).
- **Field types matter more than chart types.** A numeric `Dealer ID` appears as a sum on the axis until it is changed to Text.
- **Sheets is a staging layer.** If the source file changes, re-import the Sheet. Looker Studio picks up the new data on its next cache refresh (or with **Refresh data**).
