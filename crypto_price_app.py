import streamlit as st
import pandas as pd
import requests
import matplotlib.pyplot as plt
from PIL import Image
from textblob import TextBlob
import base64
from dotenv import load_dotenv
import os
import seaborn as sns
import io

# Load API keys
load_dotenv()
coin_api_key = os.getenv("COINMARKETCAP_API_KEY")
news_api_key = os.getenv("NEWS_API_KEY")

# Page config
st.set_page_config(page_title="Crypto Tracker", layout="wide")

# Theme
dark_mode = st.sidebar.toggle("🌙 Dark Mode")
if dark_mode:
    st.markdown("""<style>body {background-color: #0e1117; color: white;}</style>""", unsafe_allow_html=True)

# Logo
try:
    logo = Image.open("logo.png")
    st.image(logo, width=500)
except:
    st.warning("Logo not found.")

# Title & Intro
st.title("📈 Real-time Cryptocurrency Tracker")
st.markdown("Get live crypto prices, market cap, and % change. Powered by CoinMarketCap.")

# About section
expander_bar = st.expander('About')
expander_bar.markdown("""
* Made By: Debasis Prusty  
* Data source: [CoinMarketCap](https://coinmarketcap.com)  
""")

# Sidebar controls
currency = st.sidebar.selectbox("Select currency", ["USD", "INR", "BTC", "ETH"])
percent_timeframe = st.sidebar.selectbox("Change timeframe", ["1h", "24h", "7d"])
refresh = st.sidebar.button("🔁 Refresh")

@st.cache_data(ttl=600)
def fetch_data():
    url = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest"
    headers = {'X-CMC_PRO_API_KEY': coin_api_key}
    params = {"start": "1", "limit": "100", "convert": currency}
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()["data"]
        coins = []
        for c in data:
            coins.append({
                "Name": c["name"],
                "Symbol": c["symbol"],
                "Price": c["quote"][currency]["price"],
                "Market Cap": c["quote"][currency]["market_cap"],
                "Volume (24h)": c["quote"][currency]["volume_24h"],
                "% Change 1h": c["quote"][currency]["percent_change_1h"],
                "% Change 24h": c["quote"][currency]["percent_change_24h"],
                "% Change 7d": c["quote"][currency]["percent_change_7d"],
                "Max Supply": c.get("max_supply"),
                "Circulating Supply": c.get("circulating_supply"),
                "CMC Link": f"https://coinmarketcap.com/currencies/{c['slug']}/"
            })
        return pd.DataFrame(coins)
    except Exception as e:
        st.error(f"API error: {e}")
        return pd.DataFrame()

if refresh:
    st.cache_data.clear()

df = fetch_data()
selected = st.sidebar.multiselect("Choose coins", df["Symbol"].tolist(), ['BTC', 'ETH', 'ADA', 'DOGE', 'BNB'])
filtered = df[df["Symbol"].isin(selected)] if selected else df

# Market Table
st.subheader("📊 Market Overview")
st.dataframe(filtered.sort_values(by="Market Cap", ascending=False), use_container_width=True)

# Pie Chart for Market Cap of Selected Coins
if not filtered.empty:
    st.subheader("🥧 Market Cap Share (Selected Coins)")
    fig1, ax1 = plt.subplots()
    ax1.pie(filtered["Market Cap"], labels=filtered["Symbol"], autopct="%1.1f%%", startangle=90)
    ax1.axis("equal")
    st.pyplot(fig1)

# Bar Chart for % Change
st.subheader(f"📈 % Change ({percent_timeframe})")
percent_column = f"% Change {percent_timeframe}"
fig2, ax2 = plt.subplots()
ax2.bar(filtered["Symbol"], filtered[percent_column], color=["green" if x > 0 else "red" for x in filtered[percent_column]])
ax2.set_ylabel(f"{percent_timeframe} Change (%)")
st.pyplot(fig2)

# Correlation Heatmap
if len(filtered) > 1:
    st.subheader("📊 Correlation Heatmap (Price vs % Changes)")
    corr = filtered[["Price", "% Change 1h", "% Change 24h", "% Change 7d"]].corr()
    fig3, ax3 = plt.subplots()
    sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax3)
    st.pyplot(fig3)

# Tokenomics Table
st.subheader("📘 Tokenomics Overview")
tokenomics_cols = ["Name", "Symbol", "Max Supply", "Circulating Supply", "CMC Link"]
st.dataframe(filtered[tokenomics_cols], use_container_width=True)

# Download Option
st.download_button("💾 Download Data (CSV)", data=filtered.to_csv(index=False), file_name="crypto_data.csv", mime="text/csv")

# -----------------------------
# 🔍 Coin News Section (at bottom)
# -----------------------------
st.markdown("---")
st.subheader("📰 Want to see crypto news?")

news_coin = st.selectbox("Choose a coin to view latest news", df["Name"].unique())
sentiment_filter = st.radio("Filter by Sentiment", ["All", "Positive", "Negative"])

if news_coin:
    def fetch_news(query):
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&pageSize=10&apiKey={news_api_key}"
        res = requests.get(url)
        if res.status_code == 200:
            return res.json().get("articles", [])
        else:
            return []

    with st.spinner(f"Fetching latest news on {news_coin}..."):
        articles = fetch_news(news_coin)

    sentiment_data = []
    for article in articles:
        desc = article.get("description") or ""
        if desc:
            sentiment = TextBlob(desc).sentiment.polarity
            label = "Positive" if sentiment > 0.1 else "Negative" if sentiment < -0.1 else "Neutral"
            sentiment_data.append((article, label, sentiment))

    if sentiment_filter != "All":
        sentiment_data = [a for a in sentiment_data if a[1] == sentiment_filter]

    if sentiment_data:
        for article, label, polarity in sentiment_data:
            st.markdown(f"### [{article['title']}]({article['url']})")
            st.markdown(f"- 🗞 {article['source']['name']} | 📅 {article['publishedAt'][:10]} | 💬 Sentiment: {label} ({polarity:.2f})")
            st.markdown(f"> {article['description']}")
            st.markdown("---")

        # Sentiment Trend Plot
        st.subheader("📉 Sentiment Trend (Polarity Scores)")
        sentiment_df = pd.DataFrame(sentiment_data, columns=["Article", "Label", "Polarity"])
        fig4, ax4 = plt.subplots()
        ax4.plot(sentiment_df["Polarity"], marker="o", linestyle="-")
        ax4.set_ylabel("Polarity")
        ax4.set_xlabel("Article Index")
        st.pyplot(fig4)

        # News as TXT download
        news_text = "\n\n".join([f"{a['title']}\n{a['description']}\n{a['url']}" for a, _, _ in sentiment_data])
        st.download_button("💾 Download News (TXT)", data=news_text, file_name="news_summary.txt", mime="text/plain")
    else:
        st.info("No matching news found.")

# Profit Calculator
st.markdown("---")
st.subheader("💰 Profit Calculator")
calc_coin = st.selectbox("Choose Coin", df["Symbol"].unique())
investment = st.number_input("Investment Amount (in selected currency)", min_value=0.0, step=100.0)
buy_price = st.number_input("Buy Price (in selected currency)", min_value=0.0)
current_price = df[df["Symbol"] == calc_coin]["Price"].values[0]
if investment > 0 and buy_price > 0:
    units = investment / buy_price
    profit = units * (current_price - buy_price)
    st.success(f"Current Price of {calc_coin}: {current_price:.2f} {currency}")
    st.success(f"Estimated Profit/Loss: {profit:.2f} {currency}")

# Footer
st.markdown("---")
st.markdown("Built with ❤ by Debasis using [Streamlit](https://streamlit.io), CoinMarketCap & NewsAPI.")