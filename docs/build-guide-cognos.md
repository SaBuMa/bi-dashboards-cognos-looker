# 🛠 Build Guide: IBM Cognos Analytics

How the Sales and Service dashboards were built in **IBM Cognos Analytics** (trial edition). Menu names can change slightly between Cognos versions.

**Result:** [Sales](../dashboards/cognos-analytics/sales-dashboard.png) · [Service](../dashboards/cognos-analytics/service-dashboard.png) · [PDF export](../dashboards/cognos-analytics/cognos-dashboards-export.pdf)

---

## 0. How Cognos works (mental model)

Think of Cognos as a **kitchen with a stocked pantry**. The *data module* is the pantry: tables are already joined and every field already knows whether it is a measure (number to add up) or an attribute (label to group by). The dashboard is the counter where you drag ingredients onto plates (widgets).

```text
 Data module (pantry)                  Dashboard (counter)
 ┌───────────────────────┐            ┌──────────────┬──────────────┐
 │ Sales_By_Model        │  drag &    │  Widget      │  Widget      │
 │   ├─ Profit      (#)  │──drop────► │  (KPI tile)  │  (bar chart) │
 │   ├─ Quantity    (#)  │            ├──────────────┴──────────────┤
 │   └─ Model       (Aa) │            │        Widget (column)      │
 │ Car_Recalls ...       │            └─────────────────────────────┘
 └───────────────────────┘
   (#) measure  (Aa) attribute
```

---

## 1. Open the data and create the dashboard

1. In the left navigation, open **Team content → Samples → By industry → Automotive → Data**.
2. Right-click **Auto group data module** → **Create dashboard**.
3. Choose the **Tabbed** template with **4 small rectangles on top and 1 large rectangle below**.
4. Double-click the first tab name and rename it to **Sales**.
5. Add a second tab (**+** next to the tab bar), choose the **2 × 2** template and rename it **Service**.

---

## 2. Sales tab

### Panel 1: Profit
1. Expand `Sales_By_Model` in the data panel and drag **Profit** into the first small rectangle. Cognos creates a **Summary** (KPI) visualization.
2. Format the value: select the widget → **Format data** → **Currency (USD)** with **1 decimal place**. The summary widget abbreviates the value to **$78.4M**.

### Panel 2: Quantity Sold
Drag **Quantity Sold** into the second rectangle (Summary visualization, default sum) → **58118**.

### Panel 3: Quantity Sold by Model
1. Drag **Quantity Sold** and **Model** into the third rectangle.
2. Change the visualization to **Bar**. The bars run Champlain → Hudson (ascending).

### Panel 4: Average Quantity Sold
1. Drag **Quantity Sold** into the fourth rectangle.
2. In the field's properties, change **Summarization** from *Total* to **Average** → **19.37**.

### Panel 5: Profit by Dealer ID
1. Drag **Profit** and **Dealer ID** into the large rectangle and set the visualization to **Column**.
2. Make sure **Dealer ID** is treated as an *attribute* (a label), not a measure. Otherwise Cognos sums the IDs.
3. Sort the X axis by **Profit, ascending** → 1222 (lowest) … 1288 (highest).

---

## 3. Service tab

### Panel 1: # of Recalls by Model
Drag **Units** (from `Car_Recalls`) and **Model** into the top-left area → **Column** chart. Rename the measure label to *# of Recalls*.

### Panel 2: Customer sentiment
1. Drag **Sentiment** and the record **Count** (from `Sentiment`) into the top-right area.
2. Change the visualization to **Treemap**: Sentiment as the hierarchy, size and colour by Count.

### Panel 3: Quantity Sold and Profit by Month
1. Drag **Month**, **Profit** and **Quantity Sold** into the bottom-left area.
2. Choose the **Line and column** visualization: **Profit → Column**, **Quantity Sold → Line**, each on its own Y axis.
3. Sort Month by its natural (calendar) order.

### Panel 4: # of Recalls by Model and Affected System
1. Drag **Model**, **System Affected** and **Units** into the bottom-right area.
2. Choose **Heat map**: Model on rows, Affected System on columns, Units as the colour scale.
3. Check the legend: the darkest cell is Beaufort × Airbag (70,422).

---

## 4. Export to PDF

1. Click **Share** on the application toolbar.
2. On the **Export** tab, tick **Include filters** → **Export**.
3. In the print dialog, set **Destination → Save as PDF**.

---

## 5. Lessons learned

- **Check the role of every ID field.** Numeric IDs (Dealer ID, Car_ID) are often imported as measures and get summed. Set them to attributes before charting.
- **Summary widgets abbreviate automatically.** 1-decimal formatting plus auto-scaling gives `$78.4M` without a calculated field.
- **The data module does the joins for you**, which is convenient. The downside is that it is less obvious where a number comes from, which is why this repo includes [SQL equivalents](../sql/dashboard_queries.sql) of every panel.
