
import streamlit as st
import pandas as pd
from pyairtable import Table
import plotly.express as px

st.set_page_config(page_title="📊 Airtable Expense Dashboard", layout="wide")
st.title("📊 Interactive Expense Dashboard (Airtable)")

# Airtable configuration
AIRTABLE_TOKEN = st.secrets["airtable_token"]  # Put this in your Streamlit Cloud secrets
BASE_ID = "appQFvAieZcCk4pGO"
TABLE_NAME = "Bills"

# Fetch data from Airtable
@st.cache_data
def fetch_airtable_data():
    table = Table(AIRTABLE_TOKEN, BASE_ID, TABLE_NAME)
    records = table.all()
    df = pd.DataFrame([record["fields"] for record in records])
    return df

df = fetch_airtable_data()

# Data cleaning
df['Amount'] = df['Amount'].replace('[\\$,]', '', regex=True).astype(float)
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
df.dropna(subset=['InvoiceDate', 'Amount', 'Vendor', 'Expense Category'], inplace=True)

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
vendors = st.sidebar.multiselect("Select Vendors", df['Vendor'].unique(), default=list(df['Vendor'].unique()))
categories = st.sidebar.multiselect("Select Categories", df['Expense Category'].unique(), default=list(df['Expense Category'].unique()))
view_option = st.sidebar.radio("View By", ["Monthly", "Quarterly"])

# Apply filters
df_filtered = df[df['Vendor'].isin(vendors) & df['Expense Category'].isin(categories)]

# Create period for aggregation
if view_option == "Monthly":
    df_filtered.loc[:, 'Period'] = df_filtered['InvoiceDate'].dt.to_period('M').dt.to_timestamp()
else:
    df_filtered.loc[:, 'Period'] = df_filtered['InvoiceDate'].dt.to_period('Q').dt.to_timestamp()

# Group by Period and Category
grouped = df_filtered.groupby(['Period', 'Expense Category'])['Amount'].sum().reset_index()

# Plot
fig = px.bar(
    grouped,
    x="Period",
    y="Amount",
    color="Expense Category",
    barmode="group",
    title=f"Expenses Grouped by {view_option}"
)
st.plotly_chart(fig, use_container_width=True)

# Table view
with st.expander("📄 Show Filtered Data Table"):
    st.dataframe(df_filtered.sort_values("InvoiceDate", ascending=False))
