import streamlit as st
import pandas as pd
import plotly.express as px
from databricks import sql

st.set_page_config(page_title="Online Retail Sales Analysis", page_icon="🛒", layout="wide")

st.title("🛒 Online Retail Sales Analysis & Forecasting")
st.caption("BBIM709 Assessment 2 · live data from Databricks Unity Catalog · Dec 2010 – Dec 2011")

@st.cache_resource(ttl=3600)
def get_connection():
    return sql.connect(
        server_hostname=st.secrets["DATABRICKS_HOST"],
        http_path=st.secrets["DATABRICKS_HTTP_PATH"],
        access_token=st.secrets["DATABRICKS_TOKEN"],
    )

@st.cache_data(ttl=3600, show_spinner="Loading data from Databricks…")
def run_query(sql_text):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql_text)
            columns = [col[0] for col in cur.description]
            return pd.DataFrame(cur.fetchall(), columns=columns)

KPI_SQL = """
SELECT COUNT(*) AS total_transactions,
       SUM(CAST(Quantity AS DOUBLE)) AS total_quantity,
       COUNT(DISTINCT CustomerID) AS distinct_customers,
       COUNT(DISTINCT StockCode) AS distinct_products
FROM marketbasket.marketschema.retail_raw
"""

DAILY_SALES_SQL = """
SELECT to_date(`Date`, 'yyyy-MM-dd') AS order_date, COUNT(*) AS sales
FROM marketbasket.marketschema.retail_raw
GROUP BY 1 ORDER BY 1
"""

TOP_PRODUCTS_SQL = """
SELECT Description AS product, COUNT(*) AS purchase_count
FROM marketbasket.marketschema.retail_raw
WHERE Description IS NOT NULL
GROUP BY 1 ORDER BY purchase_count DESC LIMIT 10
"""

kpi = run_query(KPI_SQL).iloc[0]
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Transactions", f"{int(kpi.total_transactions):,}")
c2.metric("Total Quantity Sold", f"{int(kpi.total_quantity):,}")
c3.metric("Distinct Customers", f"{int(kpi.distinct_customers):,}")
c4.metric("Distinct Products", f"{int(kpi.distinct_products):,}")

daily = run_query(DAILY_SALES_SQL)
fig = px.line(daily, x="order_date", y="sales", title="Daily Sales Trend")
fig.update_layout(xaxis_title="Date", yaxis_title="Sales (transactions per day)", height=420)
st.plotly_chart(fig, use_container_width=True)

top = run_query(TOP_PRODUCTS_SQL)
fig2 = px.bar(top, x="purchase_count", y="product", orientation="h",
              title="Top 10 Seasonal Products by Purchase Count")
fig2.update_layout(yaxis=dict(autorange="reversed"), xaxis_title="Purchase Count", height=450)
st.plotly_chart(fig2, use_container_width=True)
