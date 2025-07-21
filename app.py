
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="📊 Expense Dashboard", layout="wide")
st.title("📊 Interactive Expense Dashboard")

# Upload CSV
uploaded_file = st.file_uploader("Upload Expense CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file)
else:
    st.warning("Please upload a CSV file to proceed.")
    st.stop()

# Clean and preprocess data
df['Amount'] = df['Amount'].replace('[\\$,]', '', regex=True).astype(float)
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'], errors='coerce')
df.dropna(subset=['InvoiceDate', 'Amount', 'Vendor', 'Category'], inplace=True)

# Sidebar filters
st.sidebar.header("🔍 Filter Options")
vendors = st.sidebar.multiselect("Select Vendors", df['Vendor'].unique(), default=list(df['Vendor'].unique()))
categories = st.sidebar.multiselect("Select Categories", df['Category'].unique(), default=list(df['Category'].unique()))
view_option = st.sidebar.radio("View By", ["Monthly", "Quarterly"])

# Apply filters
df_filtered = df[df['Vendor'].isin(vendors) & df['Category'].isin(categories)]

# Create period for aggregation
if view_option == "Monthly":
    df_filtered.loc[:, 'Period'] = df_filtered['InvoiceDate'].dt.to_period('M').dt.to_timestamp()
else:
    df_filtered.loc[:, 'Period'] = df_filtered['InvoiceDate'].dt.to_period('Q').dt.to_timestamp()

# Group by Period, Category, Vendor
grouped = df_filtered.groupby(['Period', 'Category', 'Vendor'])['Amount'].sum().reset_index()

# Bar chart
fig = px.bar(
    grouped,
    x="Period",
    y="Amount",
    color="Category",
    barmode="group",
    title=f"Expenses Grouped by {view_option}"
)
st.plotly_chart(fig, use_container_width=True)

# Table view
with st.expander("📄 Show Filtered Data Table"):
    st.dataframe(
        df_filtered[['InvoiceDate', 'Vendor', 'Category', 'Amount', 'Description']].sort_values(
            by='InvoiceDate', ascending=False
        )
    )
