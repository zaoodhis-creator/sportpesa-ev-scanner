import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timezone
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
    "SportPesa +EV Scanner: Manual and automatic "
    "Pinnacle vs SportPesa football 1X2 comparisons. "
    "Verify current odds before placing bets."
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

st.divider()
st.header("⚽ Automatic Football Odds Retrieval")

API_BASE = "https://api.prop-line.com/v1"

if st.button("Load Football Competitions"):
    try:
        api_key = st.secrets["PROP_LINE_API_KEY"]

        response = requests.get(
            f"{API_BASE}/sports",
            headers={"X-API-Key": api_key},
            timeout=20
        )
        response.raise_for_status()

        all_sports = response.json()

        soccer_sports = [
            s for s in all_sports
            if s.get("key", "").startswith("soccer_")
        ]

        if soccer_sports:
            st.session_state["soccer_sports"] = soccer_sports
            st.success(
                f"Found {len(soccer_sports)} football competitions."
            )
        else:
            st.warning("No football competitions were returned.")

    except Exception as error:
        st.error(f"Could not load competitions: {error}")


if "soccer_sports" in st.session_state:

    competitions = st.session_state["soccer_sports"]

    competition_names = {
        s["title"]: s["key"] for s in competitions
    }

    selected_competition = st.selectbox(
        "Choose a football competition",
        list(competition_names.keys())
    )

    if st.button("Retrieve Pinnacle vs SportPesa Odds"):

        try:
            api_key = st.secrets["PROP_LINE_API_KEY"]

            sport_key = competition_names[selected_competition]

            response = requests.get(
                f"{API_BASE}/sports/{sport_key}/odds",
                headers={"X-API-Key": api_key},
                params={
                    "markets": "h2h",
                    "bookmakers": "pinnacle,sportpesa"
                },
                timeout=30
            )

            response.raise_for_status()
            events = response.json()

            results = []

            def to_decimal(outcome):
                if outcome.get("price_decimal"):
                    return float(outcome["price_decimal"])

                price = outcome.get("price")

                if price is None:
                    return None

                price = float(price)

                if price > 0:
                    return 1 + price / 100

                if price < 0:
                    return 1 + 100 / abs(price)

                return None

            for event in events:

                home = event.get("home_team")
                away = event.get("away_team")

                if not home or not away:
                    continue

                books = {
                    book.get("key"): book
                    for book in event.get("bookmakers", [])
                }

                if "pinnacle" not in books or "sportpesa" not in books:
                    continue

                def get_1x2(book):
                    for market in book.get("markets", []):
                        if market.get("key") == "h2h":
                            prices = {}

                            for outcome in market.get("outcomes", []):
                                name = outcome.get("name")
                                price = to_decimal(outcome)

                                if price and name:
                                    prices[name.strip().lower()] = price

                            return prices

                    return {}

                pinnacle = get_1x2(books["pinnacle"])
                sportpesa = get_1x2(books["sportpesa"])

                home_key = home.strip().lower()
                away_key = away.strip().lower()

                if not all(
                    key in pinnacle and key in sportpesa
                    for key in [home_key, away_key, "draw"]
                ):
                    continue

                p_odds = [
                    pinnacle[home_key],
                    pinnacle["draw"],
                    pinnacle[away_key]
                ]

                s_odds = [
                    sportpesa[home_key],
                    sportpesa["draw"],
                    sportpesa[away_key]
                ]

                raw_probs = [1 / odds for odds in p_odds]
                total = sum(raw_probs)
                fair_probs = [p / total for p in raw_probs]

                for outcome, fair_prob, sp_odds in zip(
                    ["Home Win", "Draw", "Away Win"],
                    fair_probs,
                    s_odds
                ):
                    ev = (fair_prob * sp_odds - 1) * 100

                    results.append({
                        "Match": f"{home} vs {away}",
                        "Kickoff": event.get("commence_time"),
                        "Outcome": outcome,
                        "Pinnacle odds": round(
                            p_odds[
                                ["Home Win", "Draw", "Away Win"].index(outcome)
                            ], 3
                        ),
                        "SportPesa odds": round(sp_odds, 3),
                        "Fair probability (%)": round(fair_prob * 100, 2),
                        "EV (%)": round(ev, 2),
                        "Qualifies": ev >= min_ev
                    })

            if results:
                df_auto = pd.DataFrame(results)

                st.success(
                    f"Retrieved {len(results)} comparable outcomes."
                )

                st.subheader("Automatic EV Results")
                st.dataframe(
                    df_auto,
                    use_container_width=True
                )

                qualified_auto = df_auto[
                    df_auto["Qualifies"]
                ]

                st.subheader("Qualifying +EV selections")

                if not qualified_auto.empty:
                    st.success(
                        f"{len(qualified_auto)} selections meet your "
                        f"{min_ev:.1f}% EV threshold."
                    )
                    st.dataframe(
                        qualified_auto,
                        use_container_width=True
                    )
                else:
                    st.warning(
                        "No selections meet your minimum EV threshold."
                    )

            else:
                st.warning(
                    "No fixtures were returned with matching "
                    "Pinnacle and SportPesa 1X2 prices."
                )

        except Exception as error:
            st.error(f"Odds retrieval failed: {error}")
