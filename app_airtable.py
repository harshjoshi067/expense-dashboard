import streamlit as st
import pandas as pd
import plotly.express as px
from pyairtable import Table

# Set Streamlit layout
st.set_page_config(page_title="📊 Expense Dashboard — Bills", layout="wide")
st.title("📊 Interactive Expense Dashboard — Bills")

# Load Airtable API
AIRTABLE_TOKEN = st.secrets["airtable_token"]
BASE_ID = "appQFvAieZcCk4pGO"
TABLE_NAME = "Bills"

# Fetch data from Airtable
table = Table(AIRTABLE_TOKEN, BASE_ID, TABLE_NAME)
records = table.all()
df = pd.DataFrame([r["fields"] for r in records])

# Show raw column names
with st.expander("🗂️ Columns from Airtable:"):
    st.write(list(df.columns))

# Preprocess: drop rows missing key columns
required_cols = ["Vendor", "Expense Category", "Amount", "InvoiceDate"]
df = df.dropna(subset=required_cols)

# Clean Amount
df["Amount"] = df["Amount"].replace('[\$,]', '', regex=True).astype(float)

# Convert InvoiceDate
df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors='coerce')

# Period creation
df["Period_Month"] = df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()
df["Period_Quarter"] = df["InvoiceDate"].dt.to_period("Q").dt.to_timestamp()

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
vendors = st.sidebar.multiselect("Select Vendors", df["Vendor"].dropna().unique(), default=list(df["Vendor"].dropna().unique()))
categories = st.sidebar.multiselect("Select Categories", df["Expense Category"].dropna().unique(), default=list(df["Expense Category"].dropna().unique()))
view_option = st.sidebar.radio("View By", ["Monthly", "Quarterly"])
group_by = st.sidebar.selectbox("Group Bars By", ["Expense Category", "Vendor", "Both"])

# Apply filters
df_filtered = df[df["Vendor"].isin(vendors) & df["Expense Category"].isin(categories)]

# Select correct period column
if view_option == "Monthly":
    df_filtered["Period"] = df_filtered["Period_Month"]
else:
    df_filtered["Period"] = df_filtered["Period_Quarter"]

# Set group fields and color
if group_by == "Expense Category":
    group_fields = ["Period", "Expense Category"]
    color_field = "Expense Category"
elif group_by == "Vendor":
    group_fields = ["Period", "Vendor"]
    color_field = "Vendor"
else:
    group_fields = ["Period", "Vendor", "Expense Category"]
    df_filtered["Vendor+Category"] = df_filtered["Vendor"] + " - " + df_filtered["Expense Category"]
    color_field = "Vendor+Category"

# Group and plot
grouped = df_filtered.groupby(group_fields)["Amount"].sum().reset_index()

fig = px.bar(
    grouped,
    x="Period",
    y="Amount",
    color=color_field,
    barmode="group",
    title=f"Expenses Grouped by {group_by}"
)
st.plotly_chart(fig, use_container_width=True)

# Table
with st.expander("📄 Show Filtered Data Table"):
    st.dataframe(df_filtered.sort_values(by="InvoiceDate", ascending=False))
