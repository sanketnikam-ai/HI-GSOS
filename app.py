import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pytrends.request import TrendReq
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="🦟 Mosquito Trends India", layout="wide")

# ── Indian States by Zone (7 zones) ─────────────────────────────────────────
REGIONS = {
    "East": [
        "Arunachal Pradesh", "Assam", "Bihar", "Jharkhand", "Manipur",
        "Meghalaya", "Mizoram", "Nagaland", "Odisha", "Sikkim",
        "Tripura", "West Bengal",
    ],
    "North 1": ["Rajasthan", "Uttar Pradesh", "Uttarakhand"],
    "North 2": [
        "Chandigarh", "Delhi", "Haryana", "Himachal Pradesh",
        "Jammu and Kashmir", "Punjab",
    ],
    "South 1": [
        "Andaman and Nicobar Islands", "Karnataka", "Kerala",
        "Puducherry", "Tamil Nadu",
    ],
    "South 2": ["Andhra Pradesh", "Telangana"],
    "West 1":  ["Chhattisgarh", "Dadra and Nagar Haveli", "Gujarat", "Madhya Pradesh"],
    "West 2":  ["Goa", "Maharashtra"],
}

GEO_CODES = {
    "Andaman and Nicobar Islands": "IN-AN",
    "Andhra Pradesh":        "IN-AP",
    "Arunachal Pradesh":     "IN-AR",
    "Assam":                 "IN-AS",
    "Bihar":                 "IN-BR",
    "Chandigarh":            "IN-CH",
    "Chhattisgarh":          "IN-CT",
    "Dadra and Nagar Haveli":"IN-DN",
    "Delhi":                 "IN-DL",
    "Goa":                   "IN-GA",
    "Gujarat":               "IN-GJ",
    "Haryana":               "IN-HR",
    "Himachal Pradesh":      "IN-HP",
    "Jammu and Kashmir":     "IN-JK",
    "Jharkhand":             "IN-JH",
    "Karnataka":             "IN-KA",
    "Kerala":                "IN-KL",
    "Madhya Pradesh":        "IN-MP",
    "Maharashtra":           "IN-MH",
    "Manipur":               "IN-MN",
    "Meghalaya":             "IN-ML",
    "Mizoram":               "IN-MZ",
    "Nagaland":              "IN-NL",
    "Odisha":                "IN-OR",
    "Puducherry":            "IN-PY",
    "Punjab":                "IN-PB",
    "Rajasthan":             "IN-RJ",
    "Sikkim":                "IN-SK",
    "Tamil Nadu":            "IN-TN",
    "Telangana":             "IN-TG",
    "Tripura":               "IN-TR",
    "Uttar Pradesh":         "IN-UP",
    "Uttarakhand":           "IN-UT",
    "West Bengal":           "IN-WB",
}

KEYWORD = "mosquito"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_trend(geo_code: str, timeframe: str):
    """
    Fetch with up to 3 attempts.
      Attempt 1: immediate
      Attempt 2: retry after 5s
      Attempt 3: retry after 10s
    Returns DataFrame or None if all attempts fail.
    """
    wait_times = [0, 5, 10]
    for attempt, wait in enumerate(wait_times):
        try:
            if wait > 0:
                time.sleep(wait)
            pytrends = TrendReq(hl="en-US", tz=330, timeout=(10, 25))
            pytrends.build_payload([KEYWORD], cat=0, timeframe=timeframe, geo=geo_code)
            df = pytrends.interest_over_time()
            if df.empty:
                if attempt < len(wait_times) - 1:
                    continue   # empty response — retry
                return None
            df = df[[KEYWORD]].reset_index()
            df.columns = ["date", "interest"]
            return df
        except Exception:
            if attempt < len(wait_times) - 1:
                continue       # error — retry
    return None


def classify_trend(df: pd.DataFrame) -> str:
    """
    Option B logic:
      - overall_avg = average of ALL data points in the period
      - last7_avg   = average of the LAST 7 data points
      - ratio = last7_avg / overall_avg
        > 1.20  → Picking Up   (last week is 20% above normal)
        < 0.80  → Declining    (last week is 20% below normal)
        else    → Stable
    """
    if df is None or len(df) < 7:
        return "stable"
    overall_avg = df["interest"].mean()
    if overall_avg == 0:
        return "stable"
    last7_avg = df["interest"].iloc[-7:].mean()
    ratio = last7_avg / overall_avg
    if ratio > 1.20:
        return "picking_up"
    elif ratio < 0.80:
        return "declining"
    else:
        return "stable"


TREND_CONFIG = {
    "picking_up": {"badge": "📈 Picking Up",  "color": "#e74c3c"},
    "declining":  {"badge": "📉 Declining",    "color": "#e67e22"},
    "stable":     {"badge": "➡️ Stable",       "color": "#3498db"},
}

def trend_badge(trend: str) -> str:
    return TREND_CONFIG.get(trend, TREND_CONFIG["stable"])["badge"]

def trend_color(trend: str) -> str:
    return TREND_CONFIG.get(trend, TREND_CONFIG["stable"])["color"]


def build_chart(df: pd.DataFrame, state: str, trend: str):
    color = trend_color(trend)
    df = df.copy()
    df["rolling"] = df["interest"].rolling(5, min_periods=1).mean()
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["interest"],
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=4),
        name="Interest",
    ))
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["rolling"],
        mode="lines",
        line=dict(color=color, width=2, dash="dot"),
        name="5-pt avg",
    ))
    fig.update_layout(
        title=dict(text=state, font=dict(size=14)),
        margin=dict(l=10, r=10, t=35, b=10),
        height=230,
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Interest (0–100)", range=[0, 105]),
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        font=dict(color="#111111"),
    )
    return fig


# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.title("🦟 Mosquito Trends")
st.sidebar.markdown("Google Trends data for **mosquito** across Indian states.")

days = st.sidebar.selectbox("Time Period", [7, 14, 30, 60, 90], index=2,
                             format_func=lambda x: f"Last {x} days")
end   = datetime.today()
start = end - timedelta(days=days)
timeframe = f"{start.strftime('%Y-%m-%d')} {end.strftime('%Y-%m-%d')}"

selected_regions = st.sidebar.multiselect(
    "Filter by Zone",
    options=list(REGIONS.keys()),
    default=list(REGIONS.keys()),
)

st.sidebar.markdown("---")
st.sidebar.markdown("#### ℹ️ How is the trend decided?")
st.sidebar.info(
    "We compare the **last 7 days** of search interest "
    "against the **average for the whole selected period**.\n\n"
    "📈 **Picking Up** — last 7 days avg is 20% or more *above* the period average\n\n"
    "📉 **Declining** — last 7 days avg is 20% or more *below* the period average\n\n"
    "➡️ **Stable** — last 7 days avg is within ±20% of the period average"
)
st.sidebar.caption("Data refreshes every hour. Powered by pytrends.")

# ── Main ─────────────────────────────────────────────────────────────────────
st.title("🦟 Mosquito Google Trends — India")
st.markdown(f"Showing **last {days} days** | Zones: {', '.join(selected_regions)}")

# Inline logic note below the title
with st.expander("ℹ️ How is the trend label calculated?", expanded=False):
    st.markdown(
        """
        Each state's trend is classified by comparing the **last 7 days** of Google search 
        interest to the **average interest over the entire selected period**:

        | Label | Condition |
        |---|---|
        | 📈 **Picking Up** | Last 7-day avg is **≥ 20% above** the period average |
        | 📉 **Declining**  | Last 7-day avg is **≥ 20% below** the period average |
        | ➡️ **Stable**     | Last 7-day avg is **within ±20%** of the period average |

        > **Example:** If the 30-day average interest is 40 and the last 7 days average is 52,  
        > the ratio is 52/40 = 1.30 → 30% above normal → 📈 **Picking Up**

        Google Trends interest values are relative scores from 0–100, not absolute search volumes.
        """
    )

if not selected_regions:
    st.warning("Please select at least one zone.")
    st.stop()

states_to_show = []
for r in selected_regions:
    states_to_show.extend(REGIONS[r])

# Progress bar while fetching
progress = st.progress(0, text="Fetching trends data…")
all_data = {}
for i, state in enumerate(states_to_show):
    geo = GEO_CODES.get(state)
    if geo:
        all_data[state] = fetch_trend(geo, timeframe)
    progress.progress((i + 1) / len(states_to_show), text=f"Fetching: {state}…")
    time.sleep(1.5)   # pause between states to avoid Google rate limiting
progress.empty()

# Classify all states
all_trends = {s: classify_trend(d) for s, d in all_data.items()}

# Summary banner
picking_states   = [s for s, t in all_trends.items() if t == "picking_up"]
declining_states = [s for s, t in all_trends.items() if t == "declining"]
stable_states    = [s for s, t in all_trends.items() if t == "stable"]
no_data_states   = [s for s, d in all_data.items() if d is None]

col1, col2, col3, col4 = st.columns(4)
col1.metric("📈 Picking Up",  len(picking_states))
col2.metric("📉 Declining",   len(declining_states))
col3.metric("➡️ Stable",      len(stable_states))
col4.metric("⚠️ No Data",     len(no_data_states))

st.markdown("---")

# Charts per zone
for region in selected_regions:
    st.subheader(f"🗺️ Zone: {region}")
    region_states = [s for s in REGIONS[region] if s in all_data]

    if not region_states:
        st.info("No states found for this zone.")
        continue

    cols = st.columns(2)
    for idx, state in enumerate(region_states):
        df    = all_data.get(state)
        trend = all_trends.get(state, "stable")
        with cols[idx % 2]:
            if df is not None and not df.empty:
                fig = build_chart(df, state, trend)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.caption(trend_badge(trend))
            else:
                st.warning(f"No data for **{state}**")
    st.markdown("---")
