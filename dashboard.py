import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# 1. PAGE CONFIGURATION
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Apple Financial Analytics Dashboard",
    page_icon="🍎",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# 2. STYLING (Premium Shadcn-like CSS)
# -----------------------------------------------------------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        color: #09090b; /* Zinc 950 */
    }
    
    .stApp {
        background-color: #fafafa; /* Zinc 50 */
    }
    
    /* Typography */
    h1, h2, h3 {
        font-weight: 700;
        color: #18181b; /* Zinc 900 */
        letter-spacing: -0.025em;
    }
    h4, h5, h6 {
        font-weight: 600;
        color: #27272a; /* Zinc 800 */
    }
    
    /* Metrics Cards */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e4e4e7; /* Zinc 200 */
        padding: 1.5rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        transition: box-shadow 0.2sease-in-out;
    }
    [data-testid="stMetric"]:hover {
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Charts Container */
    [data-testid="stChart"] {
        background-color: #ffffff;
        border: 1px solid #e4e4e7;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        background-color: transparent;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        white-space: nowrap;
        background-color: transparent;
        border: none;
        color: #71717a; /* Zinc 500 */
        font-weight: 500;
        padding: 0 0.5rem;
    }
    
    .stTabs [aria-selected="true"] {
        color: #18181b; /* Zinc 900 */
        border-bottom: 2px solid #18181b;
    }

    /* Slider Styling */
    div[data-baseweb="slider"] > div > div > div > div {
        background-color: #18181b !important;
    }
    
    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #f4f4f5; /* Zinc 100 */
        border-right: 1px solid #e4e4e7;
    }
    
    /* Dataframes */
    [data-testid="stDataFrame"] {
        border: 1px solid #e4e4e7;
        border-radius: 0.5rem;
        overflow: hidden;
    }
    
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 3. DATA LOADING
# -----------------------------------------------------------------------------
@st.cache_data
def load_financial_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    notebooks_dir = os.path.join(base_dir, "notebooks")
    
    try:
        income = pd.read_csv(os.path.join(notebooks_dir, "apple_income_statement.csv"), index_col=0, parse_dates=True).sort_index()
        balance = pd.read_csv(os.path.join(notebooks_dir, "apple_balance_sheet.csv"), index_col=0, parse_dates=True).sort_index()
        cashflow = pd.read_csv(os.path.join(notebooks_dir, "apple_cash_flow.csv"), index_col=0, parse_dates=True).sort_index()
        return income, balance, cashflow
    except Exception as e:
        st.error(f"Critical Error: Could not load financial data. Ensure CSV files are in the 'notebooks' folder.\nDetails: {e}")
        st.stop()

income, balance, cashflow = load_financial_data()

# -----------------------------------------------------------------------------
# 4. CALCULATIONS
# -----------------------------------------------------------------------------
def compute_metrics(income, balance, cashflow):
    # Ratios DataFrame
    ratios = pd.DataFrame(index=income.index)
    
    # Profitability
    if "Total Revenue" in income.columns:
        ratios["Gross Margin"] = income.get("Gross Profit", 0) / income["Total Revenue"]
        ratios["Operating Margin"] = income.get("Operating Income", 0) / income["Total Revenue"]
        ratios["Net Margin"] = income.get("Net Income", 0) / income["Total Revenue"]
        
    # Growth (YoY)
    ratios["Revenue Growth"] = income["Total Revenue"].pct_change()
    ratios["Net Income Growth"] = income.get("Net Income", pd.Series(0)).pct_change()

    # Liquidity & Solvency
    if "Current Liabilities" in balance.columns:
        ratios["Current Ratio"] = balance.get("Cash And Cash Equivalents", 0) / balance["Current Liabilities"]
    
    if "Total Liabilities Net Minority Interest" in balance.columns:
        if "Stockholders Equity" in balance.columns:
            ratios["Debt to Equity"] = balance["Total Liabilities Net Minority Interest"] / balance["Stockholders Equity"]
        if "Total Assets" in balance.columns:
            ratios["Debt to Assets"] = balance["Total Liabilities Net Minority Interest"] / balance["Total Assets"]
    
    # Efficiency
    if "Net Income" in income.columns:
        if "Total Assets" in balance.columns:
            ratios["ROA"] = income["Net Income"] / balance["Total Assets"]
        if "Stockholders Equity" in balance.columns:
            ratios["ROE"] = income["Net Income"] / balance["Stockholders Equity"]

    return ratios

ratios = compute_metrics(income, balance, cashflow)

def calculate_cagr(series):
    series = series.dropna()
    if len(series) < 2: return 0.0
    start = series.iloc[0]
    end = series.iloc[-1]
    if start == 0: return 0.0
    return (end / start) ** (1 / (len(series) - 1)) - 1

def run_forecast(start, cagr, years, scenario_mult):
    rate = cagr * scenario_mult
    forecast = [start * ((1 + rate) ** i) for i in range(1, years + 1)]
    return forecast, rate

# -----------------------------------------------------------------------------
# 5. CHARTING HELPERS
# -----------------------------------------------------------------------------
def plot_trend(df, x, ys, title, y_title, type="line", colors=None):
    if colors is None: colors = ["#18181b", "#71717a", "#a1a1aa"]
    fig = go.Figure()
    for i, y_col in enumerate(ys):
        if y_col in df.columns:
            if type == "line":
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[y_col], name=y_col,
                    line=dict(color=colors[i % len(colors)], width=3),
                    mode='lines+markers'
                ))
            elif type == "bar":
                fig.add_trace(go.Bar(
                    x=df.index, y=df[y_col], name=y_col,
                    marker_color=colors[i % len(colors)]
                ))
    
    fig.update_layout(
        title=dict(text=title, font=dict(family="Inter", size=18, color="#18181b")),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", color="#71717a"),
        hovermode="x unified",
        margin=dict(l=20, r=20, t=50, b=20),
        yaxis=dict(title=y_title, showgrid=True, gridcolor="#f4f4f5"),
        xaxis=dict(showgrid=False),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig

# -----------------------------------------------------------------------------
# 6. DASHBOARD UI
# -----------------------------------------------------------------------------

# Sidebar
st.sidebar.title("🍎 Apple Analytics")
st.sidebar.caption("Financial Analysis & Forecasting Tool")
st.sidebar.markdown("---")
view_mode = st.sidebar.radio("Navigate", ["Executive Summary", "Financial Statements", "Ratio Analysis", "Forecasting Model"])

# Header
st.title("Apple Financial Dashboard")
current_yr = income.index[-1].year
st.markdown(f"**Reporting Period:** Fiscal Year End {current_yr}")

if view_mode == "Executive Summary":
    # Top Row Metrics
    c1, c2, c3, c4 = st.columns(4)
    curr_rev = income["Total Revenue"].iloc[-1]
    curr_ni = income["Net Income"].iloc[-1]
    curr_ocf = cashflow["Operating Cash Flow"].iloc[-1]
    
    prev_rev = income["Total Revenue"].iloc[-2]
    rev_growth = (curr_rev - prev_rev) / prev_rev

    c1.metric("Total Revenue", f"${curr_rev/1e9:.1f}B", f"{rev_growth:.1%}")
    c2.metric("Net Income", f"${curr_ni/1e9:.1f}B", f"{ratios['Net Income Growth'].iloc[-1]:.1%}")
    c3.metric("Operating Cash Flow", f"${curr_ocf/1e9:.1f}B")
    c4.metric("Net Margin", f"{ratios['Net Margin'].iloc[-1]:.1%}")

    st.markdown("### 📈 Core Performance Trends")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Revenue vs Net Income")
        fig = plot_trend(income, income.index, ["Total Revenue", "Net Income"], "Top & Bottom Line Growth", "Billions (USD)")
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("Cash Flow Strength")
        # Ensure FCF exists
        if "Free Cash Flow" not in cashflow.columns:
            cashflow["Free Cash Flow"] = cashflow["Operating Cash Flow"] - cashflow.get("Capital Expenditure", 0)
        fig = plot_trend(cashflow, cashflow.index, ["Operating Cash Flow", "Free Cash Flow"], "OCF & FCF", "Billions (USD)", type="bar")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 📊 Profitability Margins")
    fig = plot_trend(ratios, ratios.index, ["Gross Margin", "Operating Margin", "Net Margin"], "Margin Evolution", "Ratio (0.00)")
    st.plotly_chart(fig, use_container_width=True)


elif view_mode == "Financial Statements":
    st.subheader("📂 Raw Financial Data Viewer")
    
    tab1, tab2, tab3 = st.tabs(["Income Statement", "Balance Sheet", "Cash Flow"])
    
    with tab1:
        st.caption("Consolidated Statement of Operations")
        st.dataframe(income.style.format("${:,.0f}", subset=income.select_dtypes(include=np.number).columns), use_container_width=True)
        csv = income.to_csv().encode('utf-8')
        st.download_button("Download CSV", csv, "apple_income_statement.csv", "text/csv")
        
    with tab2:
        st.caption("Consolidated Balance Sheet")
        st.dataframe(balance.style.format("${:,.0f}", subset=balance.select_dtypes(include=np.number).columns), use_container_width=True)
        csv = balance.to_csv().encode('utf-8')
        st.download_button("Download CSV", csv, "apple_balance_sheet.csv", "text/csv")
        
    with tab3:
        st.caption("Consolidated Statement of Cash Flows")
        st.dataframe(cashflow.style.format("${:,.0f}", subset=cashflow.select_dtypes(include=np.number).columns), use_container_width=True)
        csv = cashflow.to_csv().encode('utf-8')
        st.download_button("Download CSV", csv, "apple_cash_flow.csv", "text/csv")


elif view_mode == "Ratio Analysis":
    st.subheader("🔍 Financial Ratio Deep-Dive")
    
    tab1, tab2, tab3 = st.tabs(["Liquidity & Solvency", "Efficiency & Returns", "Growth"])
    
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### Liquidity")
            fig = plot_trend(ratios, ratios.index, ["Current Ratio"], "Current Ratio", "Ratio")
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.markdown("#### Solvency")
            fig = plot_trend(ratios, ratios.index, ["Debt to Equity", "Debt to Assets"], "Leverage Ratios", "Ratio")
            st.plotly_chart(fig, use_container_width=True)
            
    with tab2:
        st.markdown("#### Management Effectiveness")
        fig = plot_trend(ratios, ratios.index, ["ROE", "ROA"], "Return on Equity & Assets", "Ratio")
        st.plotly_chart(fig, use_container_width=True)
        
    with tab3:
        st.markdown("#### Growth Rates (YoY)")
        fig = plot_trend(ratios, ratios.index, ["Revenue Growth", "Net Income Growth"], "Year-over-Year Growth", "Percentage")
        st.plotly_chart(fig, use_container_width=True)
        
    st.dataframe(ratios.style.format("{:.2f}"))


elif view_mode == "Forecasting Model":
    st.subheader("🤖 DCF & Scenario Forecasting")
    st.caption("Project future Revenue and Net Income based on historical CAGR and adjustable market scenarios.")
    
    # Controls
    with st.expander("Model Configuration", expanded=True):
        c1, c2 = st.columns(2)
        years_forecast = c1.slider("Forecast Horizon (Years)", 1, 10, 5)
        scenario = c2.select_slider("Select Market Scenario", options=["Bear", "Conservative", "Base", "Optimistic", "Bull"], value="Base")
    
    # Scenarios factors
    scenario_map = {
        "Bear": 0.6,
        "Conservative": 0.8,
        "Base": 1.0,
        "Optimistic": 1.2,
        "Bull": 1.5
    }
    factor = scenario_map[scenario]
    
    # Calculations
    rev_cagr = calculate_cagr(income["Total Revenue"])
    ni_cagr = calculate_cagr(income["Net Income"])
    
    start_year = income.index[-1].year
    future_years = [start_year + i for i in range(1, years_forecast + 1)]
    
    rev_proj, rev_rate = run_forecast(income["Total Revenue"].iloc[-1], rev_cagr, years_forecast, factor)
    ni_proj, ni_rate = run_forecast(income["Net Income"].iloc[-1], ni_cagr, years_forecast, factor)
    
    st.info(f"**{scenario} Scenario**: Projecting with **{(rev_rate*100):.2f}%** annual Revenue growth and **{(ni_rate*100):.2f}%** Net Income growth.")
    
    # Visualization
    c1, c2 = st.columns(2)
    
    with c1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=income.index.year, y=income["Total Revenue"], name="Historical", line=dict(color="#71717a", dash="dash")))
        fig.add_trace(go.Scatter(x=future_years, y=rev_proj, name="Forecast", line=dict(color="#18181b", width=4)))
        fig.update_layout(title="Revenue Projection", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)
        
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=income.index.year, y=income["Net Income"], name="Historical", line=dict(color="#71717a", dash="dash")))
        fig.add_trace(go.Scatter(x=future_years, y=ni_proj, name="Forecast", line=dict(color="#18181b", width=4)))
        fig.update_layout(title="Net Income Projection", plot_bgcolor="rgba(0,0,0,0)")
        st.plotly_chart(fig, use_container_width=True)

    # Forecast Table
    df_proj = pd.DataFrame({
        "Revenue": rev_proj,
        "Net Income": ni_proj
    }, index=future_years)
    st.dataframe(df_proj.style.format("${:,.0f}"))
