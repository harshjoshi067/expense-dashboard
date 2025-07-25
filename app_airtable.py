import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table
from datetime import datetime

# ────────────────────────────────────────────────────────────────────────────────
# Page configuration
# ────────────────────────────────────────────────────────────────────────────────
st.set_page_config(page_title="📊 Expense Dashboard — Bills", layout="wide")
st.title("📊 Interactive Expense Dashboard — Bills")

# ────────────────────────────────────────────────────────────────────────────────
# Airtable connection
# ────────────────────────────────────────────────────────────────────────────────
AIRTABLE_TOKEN = st.secrets["airtable_token"]
BASE_ID = "appQFvAieZcCk4pGO"
TABLE_NAME = "Bills"

table = Table(AIRTABLE_TOKEN, BASE_ID, TABLE_NAME)
records = table.all()

df = pd.DataFrame([rec["fields"] for rec in records])

# ────────────────────────────────────────────────────────────────────────────────
# Basic inspection / column list
# ────────────────────────────────────────────────────────────────────────────────
with st.expander("🗂️ Columns from Airtable"):
    st.write(list(df.columns))

# ────────────────────────────────────────────────────────────────────────────────
# Pre‑processing
# ────────────────────────────────────────────────────────────────────────────────
required_cols = ["Vendor", "Expense Category", "Amount", "InvoiceDate"]
df = df.dropna(subset=required_cols).copy()

df["Amount"] = df["Amount"].replace("[\\$,]", "", regex=True).astype(float)
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")

# Helper period columns
df["Period_Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
df["Period_Quarter"] = df["InvoiceDate"].dt.to_period("Q").dt.to_timestamp()

# ────────────────────────────────────────────────────────────────────────────────
# Sidebar — Interactive filters
# ────────────────────────────────────────────────────────────────────────────────
st.sidebar.header("🔍 Filter Options")
vendors = st.sidebar.multiselect("Select Vendors", df["Vendor"].dropna().unique(), default=list(df["Vendor"].dropna().unique()))
categories = st.sidebar.multiselect("Select Categories", df["Expense Category"].dropna().unique(), default=list(df["Expense Category"].dropna().unique()))
view_option = st.sidebar.radio("View By", ["Monthly", "Quarterly"])
group_by = st.sidebar.selectbox("Group Lines By", ["Expense Category", "Vendor"])

# Apply filters
df_filtered = df[df["Vendor"].isin(vendors) & df["Expense Category"].isin(categories)].copy()

# Select appropriate period for plotting
df_filtered["Period"] = df_filtered["Period_Month"] if view_option == "Monthly" else df_filtered["Period_Quarter"]

# ────────────────────────────────────────────────────────────────────────────────
# Line chart (replacing bar chart)
# ────────────────────────────────────────────────────────────────────────────────
if group_by == "Expense Category":
    group_fields = ["Period", "Expense Category"]
    color_field = "Expense Category"
else:
    group_fields = ["Period", "Vendor"]
    color_field = "Vendor"

grouped = df_filtered.groupby(group_fields)["Amount"].sum().reset_index()

fig = px.line(
    grouped,
    x="Period",
    y="Amount",
    color=color_field,
    markers=True,
    title=f"Expenses Over Time — Grouped by {group_by}"
)
fig.update_layout(xaxis_title="Period", yaxis_title="Amount (₹)")
st.plotly_chart(fig, use_container_width=True)

# ────────────────────────────────────────────────────────────────────────────────
# Helper functions for the summary tables
# ────────────────────────────────────────────────────────────────────────────────
LATEST_DATE = df_filtered["InvoiceDate"].max() or datetime.today()
LAST_12_START = (LATEST_DATE - pd.DateOffset(months=12)).replace(day=1)

START_MONTH = pd.Timestamp("2024-01-01")
month_range = pd.date_range(start=START_MONTH, end=LATEST_DATE, freq="MS")
month_labels = [d.strftime("%b %Y") for d in month_range]


def build_pivot(index_cols: list) -> pd.DataFrame:
    """Return pivot table with last‑12‑month total and monthly columns ≥ Jan 2024."""
    # Monthly sums >= Jan 2024
    monthly = (
        df_filtered[df_filtered["InvoiceDate"] >= START_MONTH]
        .assign(YearMonth=lambda x: x["InvoiceDate"].dt.to_period("M").dt.to_timestamp())
        .pivot_table(index=index_cols, columns="YearMonth", values="Amount", aggfunc="sum", fill_value=0)
        .reindex(columns=month_range, fill_value=0)
    )
    # Flatten columns
    monthly.columns = month_labels

    # Last‑12‑month totals
    last12 = (
        df_filtered[df_filtered["InvoiceDate"] >= LAST_12_START]
        .groupby(index_cols)["Amount"].sum()
    )

    result = monthly.copy()
    result.insert(0, "Last 12 Months Total", last12)
    result.reset_index(inplace=True)
    return result

# Expenses by Category
category_table = build_pivot(["Expense Category"]).rename(columns={"Expense Category": "Category"})

# Expenses by Vendor & Category
vendor_table = build_pivot(["Vendor", "Expense Category"]).rename(columns={"Expense Category": "Category"})

# ────────────────────────────────────────────────────────────────────────────────
# Display summary tables
# ────────────────────────────────────────────────────────────────────────────────
with st.expander("📄 Expenses by Category (Jan 2024 onward)"):
    st.dataframe(category_table)

with st.expander("📄 Expenses by Vendor & Category (Jan 2024 onward)"):
    st.dataframe(vendor_table)
