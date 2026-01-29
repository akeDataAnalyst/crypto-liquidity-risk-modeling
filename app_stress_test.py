import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# 1. Page Configuration
st.set_page_config(page_title="CMC | Liquidity Stress Test", layout="wide")
st.title("🛡️ Exchange Liquidity Stress-Test Simulator")
st.markdown("---")

# 2. Data Loading
@st.cache_data
def load_data():
    metrics = pd.read_csv('liquidity_metrics.csv', index_col='symbol')
    quotes = pd.read_csv('market_depth_quotes.csv')
    return metrics, quotes

metrics_df, quotes_df = load_data()

# 3. Interactive Sidebar
st.sidebar.header("Simulation Parameters")
selected_symbol = st.sidebar.selectbox("Select Asset", metrics_df.index)
trade_size = st.sidebar.slider("Market Sell Order ($ USD)", 10000, 2000000, 500000, step=10000)

# 4. Calculation Engine (Square Root Law)
avg_spread_bps = metrics_df.loc[selected_symbol, 'mean']
last_price = quotes_df[quotes_df['symbol'] == selected_symbol]['mid_price'].iloc[-1]

# Model Calibration
Y = 0.8  # Impact coefficient for crypto
base_cost = (avg_spread_bps / 10000) / 2
impact = Y * (avg_spread_bps / 10000) * np.sqrt(trade_size / 100000)
total_slippage_pct = base_cost + impact

exec_price = last_price * (1 - total_slippage_pct)
total_loss = trade_size * total_slippage_pct

# Display Results in Columns
col1, col2, col3 = st.columns(3)
col1.metric("Current Mid-Price", f"${last_price:,.4f}")
col2.metric("Predicted Exec. Price", f"${exec_price:,.4f}", f"-{total_slippage_pct*100:.2f}%", delta_color="inverse")
col3.metric("Trade Execution Loss", f"${total_loss:,.2f}")

# Critical Risk Logic
if total_slippage_pct > 0.01:
    st.error(f"**HIGH SLIPPAGE ALERT**: A trade of this size on {selected_symbol} will lose over 1% of value. This market lacks sufficient depth for institutional orders.")
else:
    st.success(f"**STABLE LIQUIDITY**: {selected_symbol} can absorb this trade with minimal price impact.")

st.subheader("Liquidity Decay Curve")
# Generate curve data
sizes = np.linspace(10000, 2000000, 50)
slips = [(base_cost + Y * (avg_spread_bps / 10000) * np.sqrt(s / 100000)) * 100 for s in sizes]
curve_df = pd.DataFrame({"Size": sizes, "Slippage %": slips})

fig = px.area(curve_df, x="Size", y="Slippage %", 
              title=f"Estimated Price Impact for {selected_symbol}",
              labels={"Size": "Trade Size (USD)", "Slippage %": "Price Drop (%)"})
st.plotly_chart(fig, use_container_width=True)
