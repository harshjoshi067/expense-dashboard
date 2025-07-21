import streamlit as st
import pandas as pd
import plotly.express as px
import requests

# --- CONFIG ---
st.set_page_config(page_title="📊 Interactive Expense Dashboard (Airtable)", layout="wide")
st.title("📊 Interactive Expense Dashboard — Bills")

# --- Airtable Setup ---
AIRTABLE_TOKEN = st.secrets["airtable_token"]  # Set this in Streamlit Cloud secrets
BASE_ID = "appQFvAieZcCk4pGO"
TABLE_NAME = "Bills"
VIEW_NAME = "Grid view"

# --- Airtable API Call ---
headers = {
    "Authorization": f"Bearer {AIRTABLE_TOKEN}"
}
url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}?view={VIEW_NAME}"
records = []

# Paginate if needed
while url:
    res = requests.get(url, headers=headers)
    if res.status_code != 200:
        st.error(f"Error fetching data: {res.status_code}")
        st.stop()
    data = res.json()
    records.extend(data["records"])
    url = data.get("offset", None)
    if url:
        url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}?view={VIEW_NAME}&offset={url}"

# --- Transform Records to DataFrame ---
df = pd.DataFrame([record["fields"] for record in records])
df.columns = df.columns.str.strip()  # Clean column names

# Debug columns
st.write("🧾 Columns from Airtable:", df.columns.tolist())

# --- Data Cleaning ---
if 'InvoiceDate' not in df.columns:
    st.error("❌ 'InvoiceDate' column is missing in Airtable data.")
    st.stop()

df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')

if 'Amount' in df.columns:
    df['Amount'] = df['Amount'].replace('[\$,]', '', regex=True).astype(float)
else:
    st.error("❌ 'Amount' column missing.")
    st.stop()

required_cols = ['InvoiceDate', 'Vendor', 'Amount', 'Expense Category']
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"Missing columns: {', '.join(missing_cols)}")
    st.stop()

df.dropna(subset=required_cols, inplace=True)

# --- Filters ---
st.sidebar.header("🔍 Filter Options")
vendors = st.sidebar.multiselect("Select Vendors", df['Vendor'].unique(), default=list(df['Vendor'].unique()))
categories = st.sidebar.multiselect("Select Categories", df['Expense Category'].unique(), default=list(df['Expense Category'].unique()))
view_option = st.sidebar.radio("View By", ["Monthly", "Quarterly"])

df_filtered = df[df['Vendor'].isin(vendors) & df['Expense Category'].isin(categories)]

# --- Aggregation ---
if view_option == "Monthly":
    df_filtered['Period'] = df_filtered['InvoiceDate'].dt.to_period('M').dt.to_timestamp()
else:
    df_filtered['Period'] = df_filtered['InvoiceDate'].dt.to_period('Q').dt.to_timestamp()

grouped = df_filtered.groupby(['Period', 'Expense Category', 'Vendor'])['Amount'].sum().reset_index()

# --- Plotting ---
fig = px.bar(
    grouped,
    x="Period",
    y="Amount",
    color="Expense Category",
    barmode="group",
    title=f"Expenses Grouped by {view_option}"
)
st.plotly_chart(fig, use_container_width=True)

# --- Table View ---
with st.expander("📄 Show Filtered Data Table"):
    st.dataframe(
        df_filtered[['InvoiceDate', 'Vendor', 'Expense Category', 'Amount']].sort_values(
            by='InvoiceDate', ascending=False
        )
    )
