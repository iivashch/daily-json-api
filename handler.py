#/handler.py
import os
import json
import yfinance as yf
import pandas as pd
import pandas_datareader.data as web
import datetime
from dotenv import load_dotenv


load_dotenv()

# Environment variables
FRED_API_KEY = os.getenv("FRED_API_KEY")

FRED_INDICATORS = {
    "CPI": "CPIAUCSL",
    "PPI": "PPIACO",
    "Unemployment Rate": "UNRATE",
    "NFP": "PAYEMS",
    "Consumer Sentiment": "UMCSENT",
    "Yield Curve": "T10Y2Y",
    "10Y Bond": "GS10",
    "Dollar Index": "DTWEXBGS",
    "CBOE Gold ETF": "GVZCLS",
    "Oil Futures Brent": "DCOILBRENTEU"
}

STOCKS = ["^GSPC", "^N100", "000001.SS"]

def get_stock_data():
    quote = []
    for ticker in STOCKS:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="2d")
            info = stock.info
            if hist.empty:
                continue

            latest = hist['Close'].iloc[-1]
            previous = hist['Close'].iloc[-2]
            change = latest - previous
            pct_change = (change / previous) * 100

            volume = info.get('volume')
            volume_str = f"{volume:,}" if isinstance(volume, (int, float)) else "N/A"

            pe_ratio = info.get('trailingPE', 'N/A')
            market_cap = info.get('marketCap')
            market_cap_str = f"{market_cap:,}" if isinstance(market_cap, (int, float)) else "N/A"

            quote.append({
                "ticker": ticker,
                "price": round(latest, 2),
                "change": round(change, 2),
                "percent": round(pct_change, 2),
                "volume": volume_str,
                "pe": pe_ratio,
                "market_cap": market_cap_str
            })
        except Exception as e:
            print(f"Error fetching stock data for {ticker}: {e}")
    return quote

def get_economic_data():
    end = datetime.datetime.today()
    start = end - pd.DateOffset(years=1)
    data = {}
    for name, code in FRED_INDICATORS.items():
        try:
            df = web.DataReader(code, 'fred', start, end).dropna()
            df.reset_index(inplace=True)
            df['date'] = df['DATE'].dt.strftime('%Y-%m')
            df.rename(columns={code: 'value'}, inplace=True)

            data[name.lower().replace(" ", "_")] = {
                "title": name,
                "labels": df['date'].tolist(),
                "values": df['value'].round(2).tolist(),
                "full_report": df[['date', 'value']].rename(columns={"value": name}).to_dict(orient="records")
            }
        except Exception as e:
            print(f"Error fetching {name} ({code}): {e}")
    return data

def build_dashboard():
    quote = get_stock_data()
    economic_data = get_economic_data()

    dashboard = {
        "stocks": {
            "sp500": quote[0]["price"] if len(quote) > 0 else None,
            "N100": quote[1]["price"] if len(quote) > 1 else None,
            "SSE": quote[2]["price"] if len(quote) > 2 else None
        },
        "updated_at": datetime.datetime.utcnow().isoformat()
    }

    dashboard.update(economic_data)
    return dashboard

dashboard_data = build_dashboard()
    
with open("public/data.json", "w") as f:
    json.dump(dashboard_data, f, indent=2)
print("Dashboard data updated successfully.")