# 🦟 Mosquito Trends India — Streamlit App

A Streamlit app that visualises **Google Trends** data for the keyword **"mosquito"** across every Indian state, helping you spot where the trend is picking up.

## Features
- 📊 Per-state line charts with a rolling-average overlay
- 📈 Automatic "Picking Up" vs "Stable/Declining" classification
- 🗺️ Region filter (North / East / West / Central / South India)
- ⏱️ Configurable time period: 7, 14, 30, 60, or 90 days
- 🔄 Data cached for 1 hour to respect Google Trends rate limits

## Local Setup

```bash
git clone https://github.com/<your-username>/<your-repo>.git
cd <your-repo>
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud (Free)

1. Push this repo to GitHub (public repo recommended for free tier).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app** → select your repo → set **Main file path** to `app.py`.
4. Click **Deploy** — done! 🎉

No secrets or API keys are required; pytrends uses the public Google Trends API.

## File Structure

```
.
├── app.py            # Main Streamlit application
├── requirements.txt  # Python dependencies
└── README.md
```

## How "Picking Up" is Determined

The app compares the **average interest of the last 7 days** against the **average interest of the first 7 days** of the selected window. If the recent average is more than 10% higher, the trend is classified as **Picking Up** (shown in red).

## Notes

- Google Trends data is relative (0–100) and anonymised.
- State-level data can sometimes be sparse (especially smaller north-eastern states), returning "No Data".
- pytrends may occasionally be rate-limited by Google; the 1-hour cache minimises repeated calls.
