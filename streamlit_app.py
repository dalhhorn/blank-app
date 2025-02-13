import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

# -------------------------------
# Auto-refresh every 5 minutes
# -------------------------------
st_autorefresh(interval=5 * 60 * 1000, limit=None, key="datarefresh")

# -------------------------------
# Title and Description
# -------------------------------
st.title("Energy Price Trading Tracker")
st.markdown(
    """
    This dashboard displays intraday energy pricing and volume data with a crypto trading marketplace feel. 
    It includes trading simulation features (simple moving average crossover strategy) for buy/sell signals.
    """
)

# -------------------------------
# Data fetching with caching (5 min TTL)
# -------------------------------
@st.cache_data(ttl=300)
def fetch_data():
    # Placeholder API endpoint – replace with the correct one from https://api.energy-charts.info/
    url = "https://api.energy-charts.info/intraday"  
    try:
        response = requests.get(url)
        response.raise_for_status()
        json_data = response.json()
        
        # Assuming the JSON structure is:
        # { "data": [ {"timestamp": "2025-02-13T10:00:00Z", "price": 50.0, "volume": 200}, ... ] }
        df = pd.DataFrame(json_data.get("data", []))
        if df.empty:
            st.error("No data received from the API.")
            return df
        
        # Convert timestamp column to datetime
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        return df
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return pd.DataFrame()

df = fetch_data()

# -------------------------------
# Ensure data is available
# -------------------------------
if df.empty:
    st.write("No data available at this time.")
else:
    # -------------------------------
    # Time Filter – slider to select a time range
    # -------------------------------
    st.subheader("Filter Data by Time")
    start_time = df['timestamp'].min()
    end_time = df['timestamp'].max()
    time_range = st.slider(
        "Select time range",
        min_value=start_time,
        max_value=end_time,
        value=(start_time, end_time),
        format="YYYY-MM-DD HH:mm"
    )
    
    # Filter the DataFrame based on the selected time range
    df = df[(df['timestamp'] >= time_range[0]) & (df['timestamp'] <= time_range[1])]
    df = df.sort_values("timestamp")

    if df.empty:
        st.write("No data in the selected time range.")
    else:
        # -------------------------------
        # Trading Simulation / Analytics
        # Compute simple moving averages for a basic crossover strategy.
        # -------------------------------
        st.subheader("Trading Simulation / Analytics")
        df['SMA_5'] = df['price'].rolling(window=5).mean()
        df['SMA_15'] = df['price'].rolling(window=15).mean()

        # Generate a trading signal based on the latest available data point
        latest = df.iloc[-1]
        if np.isnan(latest['SMA_5']) or np.isnan(latest['SMA_15']):
            signal = "Not enough data for signal"
        elif latest['SMA_5'] > latest['SMA_15']:
            signal = "Buy"
        elif latest['SMA_5'] < latest['SMA_15']:
            signal = "Sell"
        else:
            signal = "Hold"

        st.write(f"**Latest Signal:** {signal}")
        st.write(f"SMA (5): {latest['SMA_5']:.2f} | SMA (15): {latest['SMA_15']:.2f}")

        # -------------------------------
        # Visualizations
        # -------------------------------
        st.subheader("Intraday Price Chart")
        price_chart_data = df.set_index('timestamp')[['price']]
        st.line_chart(price_chart_data)

        st.subheader("Intraday Volume Chart")
        volume_chart_data = df.set_index('timestamp')[['volume']]
        st.line_chart(volume_chart_data)

