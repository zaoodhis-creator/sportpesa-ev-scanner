
import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="SportPesa EV Scanner",
    page_icon="⚽",
    layout="wide"
)

st.title("⚽ SportPesa +EV Scanner")
st.write("Pinnacle vs SportPesa — Football 1X2")

st.info(
    "Enter matching pre-match odds from both bookmakers. "
    "The calculator removes Pinnacle's margin."
)

st.header("Scanner Settings")

min_ev = st.number_input(
    "Minimum EV (%)",
    min_value=0.0,
    value=3.0,
    step=0.5
)

st.header("Enter Match Odds")

match = st.text_input("Match name")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Pinnacle")
    p_home = st.number_input("Pinnacle Home", min_value=1.01, value=2.00)
    p_draw = st.number_input("Pinnacle Draw", min_value=1.01, value=3.50)
    p_away = st.number_input("Pinnacle Away", min_value=1.01, value=4.00)

with col2:
    st.subheader("SportPesa")
    s_home = st.number_input("SportPesa Home", min_value=1.01, value=2.20)
    s_draw = st.number_input("SportPesa Draw", min_value=1.01, value=3.60)
    s_away = st.number_input("SportPesa Away", min_value=1.01, value=4.10)

if st.button("Calculate +EV", type="primary"):

    pinnacle = [p_home, p_draw, p_away]
    sportpesa = [s_home, s_draw, s_away]
    outcomes = ["Home Win", "Draw", "Away Win"]

    raw_probs = [1 / odds for odds in pinnacle]
    total = sum(raw_probs)
    fair_probs = [p / total for p in raw_probs]

    results = []

    for outcome, fair_prob, sp_odds in zip(
        outcomes, fair_probs, sportpesa
    ):
        ev = (fair_prob * sp_odds - 1) * 100

        results.append({
            "Outcome": outcome,
            "Fair probability (%)": round(fair_prob * 100, 2),
            "Fair odds": round(1 / fair_prob, 3),
            "SportPesa odds": sp_odds,
            "EV (%)": round(ev, 2),
            "Qualifies": ev >= min_ev
        })

    df = pd.DataFrame(results)

    st.subheader(f"Results: {match or 'Selected Match'}")
    st.dataframe(df, use_container_width=True)

    qualified = df[df["Qualifies"]]

    st.subheader("Qualifying +EV bets")

    if len(qualified) > 0:
        st.success(
            f"{len(qualified)} outcome(s) meet your EV threshold."
        )
        st.dataframe(qualified, use_container_width=True)
    else:
        st.warning("No outcomes meet your minimum EV threshold.")

st.caption(
    "Manual odds calculator. No live bookmaker connection yet. "
    "Verify that all odds refer to the same fixture and market."
)
import requests

st.divider()
st.header("Automatic Odds API Test")

if st.button("Test API Connection"):
    try:
        api_key = st.secrets["PROP_LINE_API_KEY"]

        response = requests.get(
            "https://api.prop-line.com/v1/sports",
            headers={"X-API-Key": api_key},
            timeout=20
        )

        if response.status_code == 200:
            sports = response.json()
            st.success("API connection successful!")

            soccer = [
                sport for sport in sports
                if "soccer" in sport.get("key", "")
            ]

            st.write("Available football competitions:")
            st.json(soccer)

        elif response.status_code == 401:
            st.error("API key is invalid. Check Streamlit Secrets.")

        else:
            st.error(f"API error: {response.status_code}")
            st.write(response.text)

    except Exception as error:
        st.error(f"Connection problem: {error}")
