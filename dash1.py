"""
Dataset Intelligence Dashboard — Dark Mode
-------------------------------------------
Reads ANY dataset (CSV or Excel), analyzes it automatically, and renders
a professional, dark-themed, multi-panel dashboard — all in pure Python.

Folder layout expected:
    project/
      dashboard.py
      .streamlit/config.toml   <-- sets the native dark theme

Run with:
    pip install "streamlit>=1.32" pandas plotly openpyxl
    streamlit run dashboard.py
"""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# ----------------------------------------------------------------------
# Page setup
# ----------------------------------------------------------------------
st.set_page_config(
    page_title="Dataset Intelligence Dashboard",
    page_icon="\u25c6",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ----------------------------------------------------------------------
# Design tokens (a deliberate palette, not the default near-black + neon)
# ----------------------------------------------------------------------
BG = "#0B0E14"
SURFACE = "#161B22"
BORDER = "#262B36"
TEXT = "#E6E8EB"
MUTED = "#8A8F98"
AMBER = "#F2B84B"   # primary accent
BLUE = "#7C9EFF"    # secondary accent
TEAL = "#4FD1C5"
PURPLE = "#C084FC"
GREEN = "#4ADE80"
RED = "#F87171"

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&family=JetBrains+Mono:wght@500;600&display=swap');

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}

    .stApp {{ font-family: 'Inter', sans-serif; }}
    h1, h2, h3 {{ font-family: 'Space Grotesk', sans-serif !important; }}

    .dash-eyebrow {{
        font-family: 'JetBrains Mono', monospace;
        color: {AMBER};
        font-size: 0.72rem;
        letter-spacing: 0.18em;
        font-weight: 600;
        margin-bottom: 0.35rem;
    }}
    .dash-title {{
        font-size: 2.1rem;
        font-weight: 600;
        color: {TEXT};
        margin: 0 0 0.6rem 0;
    }}
    .dash-rule {{
        height: 3px;
        width: 64px;
        background: linear-gradient(90deg, {AMBER}, {BLUE});
        border-radius: 2px;
        margin-bottom: 1.4rem;
    }}
    .metric-card {{
        background: {SURFACE};
        border: 1px solid {BORDER};
        border-left: 3px solid {AMBER};
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
    }}
    .metric-label {{
        font-family: 'JetBrains Mono', monospace;
        color: {MUTED};
        font-size: 0.68rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.3rem;
    }}
    .metric-value {{
        font-family: 'JetBrains Mono', monospace;
        color: {TEXT};
        font-size: 1.55rem;
        font-weight: 600;
    }}
    .section-label {{
        font-family: 'JetBrains Mono', monospace;
        color: {MUTED};
        font-size: 0.72rem;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        margin-bottom: 0.6rem;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# Shared Plotly dark template (keeps every chart visually consistent)
# ----------------------------------------------------------------------
custom_template = go.layout.Template(
    layout=go.Layout(
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="Inter, sans-serif", color=TEXT, size=12),
        colorway=[AMBER, BLUE, TEAL, PURPLE, GREEN, RED],
        xaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        yaxis=dict(gridcolor=BORDER, zerolinecolor=BORDER, linecolor=BORDER),
        legend=dict(bgcolor="rgba(0,0,0,0)"),
        margin=dict(t=50, l=10, r=10, b=10),
    )
)
pio.templates["dash_dark"] = custom_template
pio.templates.default = "dash_dark"


def metric_card(col, label, value, accent=AMBER):
    col.markdown(
        f"""
        <div class="metric-card" style="border-left-color:{accent};">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ----------------------------------------------------------------------
# Header
# ----------------------------------------------------------------------
st.markdown(
    """
    <div class="dash-eyebrow">\u25c6 DATA ANALYTICS</div>
    <div class="dash-title" style="color: #000000; font-weight: 700;">Dataset Intelligence Dashboard</div>
    <div class="dash-rule"></div>
    """,
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
@st.cache_data
def load_data(file) -> pd.DataFrame:
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    elif name.endswith((".xlsx", ".xls")):
        return pd.read_excel(file)
    raise ValueError("Unsupported file type. Please upload a .csv or .xlsx file.")


def try_parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.select_dtypes(include="object").columns:
        if "date" in col.lower() or "time" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors="raise")
            except (ValueError, TypeError):
                pass
    return df


st.sidebar.markdown("### \u2699 Configuration")
st.sidebar.markdown("**1. Dataset**")
uploaded_file = st.sidebar.file_uploader(
    "Upload CSV or Excel", type=["csv", "xlsx", "xls"], label_visibility="collapsed"
)

if uploaded_file is None:
    st.info("\U0001F448 Upload a CSV or Excel file from the sidebar to begin.")
    st.stop()

try:
    df = load_data(uploaded_file)
    df = try_parse_dates(df)
except Exception as e:
    st.error(f"Could not read the file: {e}")
    st.stop()

if df.empty:
    st.warning("The uploaded file has no rows.")
    st.stop()

numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
datetime_cols = df.select_dtypes(include="datetime64[ns]").columns.tolist()
categorical_cols = df.select_dtypes(include=["object", "category", "bool"]).columns.tolist()

# ----------------------------------------------------------------------
# Filters
# ----------------------------------------------------------------------
st.sidebar.markdown("**2. Filters**")
filtered_df = df.copy()

filter_col = st.sidebar.selectbox("Filter by category", ["None"] + categorical_cols)
if filter_col != "None":
    options = sorted(filtered_df[filter_col].dropna().unique().tolist())
    selected = st.sidebar.multiselect(f"{filter_col} values", options, default=options)
    if selected:
        filtered_df = filtered_df[filtered_df[filter_col].isin(selected)]

if numeric_cols:
    range_col = st.sidebar.selectbox("Filter by numeric range", ["None"] + numeric_cols)
    if range_col != "None":
        col_min, col_max = float(filtered_df[range_col].min()), float(filtered_df[range_col].max())
        if col_min < col_max:
            lo, hi = st.sidebar.slider(f"{range_col} range", col_min, col_max, (col_min, col_max))
            filtered_df = filtered_df[filtered_df[range_col].between(lo, hi)]

st.sidebar.caption(f"Showing {len(filtered_df):,} of {len(df):,} rows")

# ----------------------------------------------------------------------
# KPI row
# ----------------------------------------------------------------------
total_cells = filtered_df.shape[0] * filtered_df.shape[1]
missing_total = int(filtered_df.isna().sum().sum())
missing_pct = (missing_total / total_cells * 100) if total_cells else 0
quality_color = GREEN if missing_pct == 0 else (AMBER if missing_pct < 5 else RED)

c1, c2, c3, c4, c5 = st.columns(5)
metric_card(c1, "ROWS", f"{filtered_df.shape[0]:,}", AMBER)
metric_card(c2, "COLUMNS", f"{filtered_df.shape[1]:,}", BLUE)
metric_card(c3, "NUMERIC FIELDS", f"{len(numeric_cols)}", TEAL)
metric_card(c4, "CATEGORICAL FIELDS", f"{len(categorical_cols)}", PURPLE)
metric_card(c5, "MISSING DATA", f"{missing_pct:.1f}%", quality_color)

st.write("")

# ----------------------------------------------------------------------
# Tabs
# ----------------------------------------------------------------------
tab_overview, tab_dist, tab_rel, tab_cat, tab_trend = st.tabs(
    ["Overview", "Distributions", "Relationships", "Categories", "Trends"]
)

with tab_overview:
    with st.container(border=True):
        st.markdown('<div class="section-label">DATA PREVIEW</div>', unsafe_allow_html=True)
        st.dataframe(filtered_df.head(50), use_container_width=True, height=280)

    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown('<div class="section-label">SUMMARY STATISTICS</div>', unsafe_allow_html=True)
            if numeric_cols:
                st.dataframe(filtered_df[numeric_cols].describe().T, use_container_width=True)
            else:
                st.caption("No numeric columns detected.")
    with col_b:
        with st.container(border=True):
            st.markdown('<div class="section-label">MISSING VALUES</div>', unsafe_allow_html=True)
            missing = filtered_df.isna().sum()
            missing = missing[missing > 0].sort_values(ascending=False)
            if missing.empty:
                st.caption("No missing values.")
            else:
                fig = px.bar(x=missing.values, y=missing.index, orientation="h", labels={"x": "Missing", "y": ""})
                fig.update_layout(height=280, showlegend=False)
                st.plotly_chart(fig, use_container_width=True)

with tab_dist:
    if numeric_cols:
        col_a, col_b = st.columns(2)
        with col_a:
            with st.container(border=True):
                sel = st.selectbox("Numeric column", numeric_cols, key="hist_col")
                bins = st.slider("Bins", 5, 100, 30, key="hist_bins")
                fig = px.histogram(filtered_df, x=sel, nbins=bins)
                fig.update_layout(height=340, title=f"Distribution \u2014 {sel}")
                st.plotly_chart(fig, use_container_width=True)
        with col_b:
            with st.container(border=True):
                sel2 = st.selectbox("Compare via box plot", numeric_cols, key="box_col")
                group = st.selectbox("Group by (optional)", ["None"] + categorical_cols, key="box_group")
                fig = px.box(filtered_df, x=None if group == "None" else group, y=sel2)
                fig.update_layout(height=340, title=f"Spread \u2014 {sel2}")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No numeric columns to visualize.")

with tab_rel:
    if len(numeric_cols) >= 2:
        col_a, col_b = st.columns(2)
        with col_a:
            with st.container(border=True):
                corr = filtered_df[numeric_cols].corr(numeric_only=True)
                fig = px.imshow(corr, text_auto=".2f", aspect="auto", color_continuous_scale="Tealrose")
                fig.update_layout(height=380, title="Correlation Heatmap")
                st.plotly_chart(fig, use_container_width=True)
        with col_b:
            with st.container(border=True):
                x_col = st.selectbox("X axis", numeric_cols, key="scatter_x")
                y_default = 1 if len(numeric_cols) > 1 else 0
                y_col = st.selectbox("Y axis", numeric_cols, index=y_default, key="scatter_y")
                color_col = st.selectbox("Color by", ["None"] + categorical_cols, key="scatter_color")
                fig = px.scatter(filtered_df, x=x_col, y=y_col, color=None if color_col == "None" else color_col)
                fig.update_layout(height=380, title=f"{y_col} vs {x_col}")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Need at least two numeric columns for relationship analysis.")

with tab_cat:
    if categorical_cols:
        cat_col = st.selectbox("Categorical column", categorical_cols, key="cat_col")
        counts = filtered_df[cat_col].value_counts().reset_index()
        counts.columns = [cat_col, "count"]
        col_a, col_b = st.columns(2)
        with col_a:
            with st.container(border=True):
                fig = px.bar(counts.head(20), x=cat_col, y="count")
                fig.update_layout(height=360, title=f"Counts \u2014 {cat_col}")
                st.plotly_chart(fig, use_container_width=True)
        with col_b:
            with st.container(border=True):
                fig = px.pie(counts.head(10), names=cat_col, values="count", hole=0.55)
                fig.update_layout(height=360, title=f"Share \u2014 {cat_col}")
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("No categorical columns detected.")

with tab_trend:
    if datetime_cols and numeric_cols:
        with st.container(border=True):
            date_col = st.selectbox("Date column", datetime_cols, key="trend_date")
            y_col = st.selectbox("Value column", numeric_cols, key="trend_y")
            agg = st.selectbox("Aggregation", ["Sum", "Mean", "Count"], key="trend_agg")
            trend_df = filtered_df.dropna(subset=[date_col, y_col]).copy()
            trend_df["_period"] = trend_df[date_col].dt.to_period("D").dt.to_timestamp()
            if agg == "Sum":
                grouped = trend_df.groupby("_period")[y_col].sum().reset_index()
            elif agg == "Mean":
                grouped = trend_df.groupby("_period")[y_col].mean().reset_index()
            else:
                grouped = trend_df.groupby("_period")[y_col].count().reset_index()
            fig = px.line(grouped, x="_period", y=y_col, markers=True)
            fig.update_layout(height=380, title=f"{y_col} over time ({agg.lower()})", xaxis_title="Date", yaxis_title=y_col)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("Add a date/time column to unlock trend analysis.")

st.markdown(
    f'<div style="color:{MUTED}; font-size:0.75rem; margin-top:2rem;">Built with Streamlit + Plotly</div>',
    unsafe_allow_html=True,
)