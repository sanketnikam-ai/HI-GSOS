import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pytrends.request import TrendReq
from datetime import datetime, timedelta
import time

st.set_page_config(page_title="🦟 Mosquito Trends India", layout="wide")

# ── Indian States by Region ──────────────────────────────────────────────────
REGIONS = {
    "North": ["Delhi", "Uttar Pradesh", "Uttarakhand", "Himachal Pradesh",
              "Punjab", "Haryana", "Jammu and Kashmir", "Rajasthan"],
    "East":  ["West Bengal", "Bihar", "Jharkhand", "Odisha",
              "Assam", "Meghalaya", "Manipur", "Mizoram",
              "Nagaland", "Tripura", "Arunachal Pradesh", "Sikkim"],
    "West":  ["Maharashtra", "Gujarat", "Goa"],
    "Central": ["Madhya Pradesh", "Chhattisgarh"],
    "South": ["Karnataka", "Tamil Nadu", "Andhra Pradesh", "Telangana",
              "Kerala"],
}

# Geo codes for pytrends (state-level India sub-regions)
GEO_CODES = {
    "Andhra Pradesh": "IN-AP", "Arunachal Pradesh": "IN-AR",
    "Assam": "IN-AS", "Bihar": "IN-BR", "Chhattisgarh": "IN-CT",
    "Goa": "IN-GA", "Gujarat": "IN-GJ", "Haryana": "IN-HR",
    "Himachal Pradesh": "IN-HP", "Jammu and Kashmir": "IN-JK",
    "Jharkhand": "IN-JH", "Karnataka": "IN-KA", "Kerala": "IN-KL",
    "Madhya Pradesh": "IN-MP", "Maharashtra": "IN-MH",
    "Manipur": "IN-MN", "Meghalaya": "IN-ML", "Mizoram": "IN-MZ",
    "Nagaland": "IN-NL", "Odisha": "IN-OR", "Punjab": "IN-PB",
    "Rajasthan": "IN-RJ", "Sikkim": "IN-SK", "Tamil Nadu": "IN-TN",
    "Telangana": "IN-TG", "Tripura": "IN-TR", "Uttar Pradesh": "IN-UP",
    "Uttarakhand": "IN-UT", "West Bengal": "IN-WB", "Delhi": "IN-DL",
}

KEYWORD = "mosquito"

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_trend(geo_code: str, timeframe: str):
    """Fetch Google Trends data for a given geo and timeframe."""
    try:
        pytrends = TrendReq(hl="en-US", tz=330, timeout=(10, 25))
        pytrends.build_payload([KEYWORD], cat=0, timeframe=timeframe, geo=geo_code)
        df = pytrends.interest_over_time()
        if df.empty:
            return None
        df = df[[KEYWORD]].reset_index()
        df.columns = ["date", "interest"]
        return df
    except Exception:
        return None


def is_picking_up(df: pd.DataFrame) -> bool:
    """Simple heuristic: last-7-day avg > first-7-day avg."""
    if df is None or len(df) < 10:
        return False
    first = df["interest"].iloc[:7].mean()
    last  = df["interest"].iloc[-7:].mean()
    return last > first * 1.1  # 10% growth threshold


def trend_badge(picking: bool):
    return "📈 **Picking Up**" if picking else "📉 Stable / Declining"


def build_chart(df: pd.DataFrame, state: str, picking: bool):
    color = "#e74c3c" if picking else "#3498db"
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["interest"],
        mode="lines+markers",
        line=dict(color=color, width=2),
        marker=dict(size=4),
        name=state,
    ))
    # Trend line (rolling avg)
    df["rolling"] = df["interest"].rolling(5, min_periods=1).mean()
    fig.add_trace(go.Scatter(
        x=df["date"], y=df["rolling"],
        mode="lines",
        line=dict(color=color, width=2, dash="dot"),
        name="7-day avg",
    ))
    fig.update_layout(
        title=dict(text=state, font=dict(size=14)),
        margin=dict(l=10, r=10, t=35, b=10),
        height=220,
        showlegend=False,
        xaxis=dict(showgrid=False),
        yaxis=dict(title="Interest (0–100)", range=[0, 105]),
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font=dict(color="#fafafa"),
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
    "Filter by Region",
    options=list(REGIONS.keys()),
    default=list(REGIONS.keys()),
)

st.sidebar.markdown("---")
st.sidebar.caption("Data refreshes every hour. Powered by pytrends.")

# ── Main ─────────────────────────────────────────────────────────────────────
st.title("🦟 Mosquito Google Trends — India")
st.markdown(f"Showing **last {days} days** | Regions: {', '.join(selected_regions)}")

if not selected_regions:
    st.warning("Please select at least one region.")
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
    progress.progress((i + 1) / len(states_to_show),
                      text=f"Fetching: {state}…")
    time.sleep(0.05)  # slight delay to avoid rate limits on first load
progress.empty()

# Summary banner
picking_states = [s for s, d in all_data.items() if is_picking_up(d)]
stable_states  = [s for s, d in all_data.items() if d is not None and not is_picking_up(d)]
no_data_states = [s for s, d in all_data.items() if d is None]

col1, col2, col3 = st.columns(3)
col1.metric("📈 Picking Up", len(picking_states))
col2.metric("📉 Stable / Declining", len(stable_states))
col3.metric("⚠️ No Data", len(no_data_states))

st.markdown("---")

# Charts per region
for region in selected_regions:
    st.subheader(f"🗺️ {region} India")
    region_states = [s for s in REGIONS[region] if s in all_data]

    if not region_states:
        st.info("No states found for this region.")
        continue

    # 2-column grid
    cols = st.columns(2)
    for idx, state in enumerate(region_states):
        df   = all_data.get(state)
        pick = is_picking_up(df)
        with cols[idx % 2]:
            if df is not None and not df.empty:
                fig = build_chart(df, state, pick)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                st.caption(trend_badge(pick))
            else:
                st.warning(f"No data for **{state}**")
    st.markdown("---")
