# ----------------------------------------------------------------------
# 股市戰情室 (美股 + 台股 + 總經 + 歷史演變) - 旗艦版 (修正補回遺失函數)
# ----------------------------------------------------------------------

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

# --- 1. Streamlit 頁面設定 ---
st.set_page_config(
    page_title="股市全方位戰情室", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    h3 { margin-top: 2rem; border-bottom: 2px solid #f0f2f6; padding-bottom: 0.5rem; font-family: 'Arial Black', sans-serif; }
    
    /* 景氣燈號 CSS */
    .light-circle {
        height: 100px; width: 100px; border-radius: 50%; display: inline-block;
        box-shadow: 0 0 20px rgba(0,0,0,0.5); margin: 10px;
    }
    .light-text { font-size: 24px; font-weight: bold; text-align: center; margin-top: 10px; }
    .score-text { font-size: 50px; font-weight: bold; color: #333; text-align: center; line-height: 100px; }
</style>
""", unsafe_allow_html=True)

# --- 2. 側邊欄控制 ---
st.sidebar.header("⚙️ 戰情控制台")
market_mode = st.sidebar.radio(
    "📊 選擇儀表板",
    [
        "🇺🇸 美股 S&P 500", 
        "🇹🇼 台股權值股 (TWSE)", 
        "📉 總經與風險指標 (Macro)",
        "⏳ 歷史市值霸主變遷 (History)"
    ]
)

if st.sidebar.button('🔄 強制更新數據', type="primary"):
    st.cache_data.clear()
    st.session_state.pop('last_update', None)
    st.rerun()

if 'last_update' in st.session_state:
    st.sidebar.caption(f"資料時間: {st.session_state['last_update']}")

st.title(f"📊 {market_mode}")

# --- 3. 核心數據函數 (股票與總經) ---

@st.cache_data(ttl=24 * 3600)
def get_tw_constituents():
    data = [
        {'Ticker': '2330.TW', 'Name': '台積電', 'Sector': '半導體', 'Industry': '晶圓代工'},
        {'Ticker': '2454.TW', 'Name': '聯發科', 'Sector': '半導體', 'Industry': 'IC設計'},
        {'Ticker': '3711.TW', 'Name': '日月光', 'Sector': '半導體', 'Industry': '封測'},
        {'Ticker': '2317.TW', 'Name': '鴻海', 'Sector': '電子代工', 'Industry': 'EMS'},
        {'Ticker': '2382.TW', 'Name': '廣達', 'Sector': '電子代工', 'Industry': 'AI伺服器'},
        {'Ticker': '3231.TW', 'Name': '緯創', 'Sector': '電子代工', 'Industry': 'AI伺服器'},
        {'Ticker': '2357.TW', 'Name': '華碩', 'Sector': '品牌電腦', 'Industry': 'PC'},
        {'Ticker': '2376.TW', 'Name': '技嘉', 'Sector': '品牌電腦', 'Industry': '板卡'},
        {'Ticker': '2308.TW', 'Name': '台達電', 'Sector': '電子零組件', 'Industry': '電源'},
        {'Ticker': '2881.TW', 'Name': '富邦金', 'Sector': '金融', 'Industry': '金控'},
        {'Ticker': '2882.TW', 'Name': '國泰金', 'Sector': '金融', 'Industry': '金控'},
        {'Ticker': '2891.TW', 'Name': '中信金', 'Sector': '金融', 'Industry': '金控'},
        {'Ticker': '2886.TW', 'Name': '兆豐金', 'Sector': '金融', 'Industry': '金控'},
        {'Ticker': '1301.TW', 'Name': '台塑', 'Sector': '傳產', 'Industry': '塑膠'},
        {'Ticker': '2002.TW', 'Name': '中鋼', 'Sector': '傳產', 'Industry': '鋼鐵'},
        {'Ticker': '2603.TW', 'Name': '長榮', 'Sector': '航運', 'Industry': '貨櫃'},
        {'Ticker': '2609.TW', 'Name': '陽明', 'Sector': '航運', 'Industry': '貨櫃'},
        {'Ticker': '2618.TW', 'Name': '長榮航', 'Sector': '航運', 'Industry': '航空'},
        {'Ticker': '2610.TW', 'Name': '華航', 'Sector': '航運', 'Industry': '航空'},
        {'Ticker': '2412.TW', 'Name': '中華電', 'Sector': '通信', 'Industry': '電信'}
    ]
    return pd.DataFrame(data)

@st.cache_data(ttl=24 * 3600)
def get_sp500_constituents():
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    try:
        df = pd.read_csv(url)
        df = df.rename(columns={'Symbol': 'Ticker', 'GICS Sector': 'Sector'})
        df['Ticker'] = df['Ticker'].str.replace('.', '-', regex=False)
        if 'GICS Sub-Industry' in df.columns:
            df = df.rename(columns={'GICS Sub-Industry': 'Industry'})
        else:
            df['Industry'] = df['Sector']
        return df
    except Exception:
        return pd.DataFrame()

@st.cache_data(ttl=24 * 3600)
def fetch_market_caps(tickers):
    caps = {}
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).fast_info
            caps[ticker] = info['market_cap']
        except:
            caps[ticker] = 0
    return caps

@st.cache_data(ttl=21600) 
def fetch_price_history(tickers, period="1y"):
    try:
        data = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True, progress=False)
        return data
    except Exception:
        return pd.DataFrame()

# --- 4. 總經數據獲取 ---
@st.cache_data(ttl=3600)
def get_macro_data():
    tickers = ["^VIX", "^GSPC"]
    data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, progress=False)
    return data

@st.cache_data(ttl=24 * 3600)
def get_taiwan_light():
    url = "https://index.ndc.gov.tw/n/json/data/measure"
    try:
        response = requests.post(url, headers={"User-Agent": "Mozilla/5.0"})
        data = response.json()
        measure_data = data['indicators']['measure'][0]['data']
        df = pd.DataFrame(measure_data)
        df['date_str'] = df['y'] + df['m']
        latest = df.iloc[-1]
        
        history_df = df.tail(12).copy()
        history_df['display_date'] = history_df['y'] + '/' + history_df['m']
        history_df['score'] = history_df['s'].astype(int)
        
        return {
            'score': int(latest['s']),
            'light': latest['l'],
            'date': f"{latest['y']}年{latest['m']}月",
            'history': history_df
        }
    except: return None

def calculate_fear_greed(vix_close, sp500_close):
    vix_score = max(0, min(100, (40 - vix_close) * (100 / 30)))
    delta = sp500_close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    final = (vix_score * 0.6) + (rsi.iloc[-1] * 0.4)
    return int(final), vix_close, rsi.iloc[-1]

# --- 5. 新增：歷史市值數據 (精選) ---
@st.cache_data
def get_historical_market_cap_data():
    """提供 1980 - 2025 的歷史市值霸主數據 (單位：十億美元)"""
    data = [
        # 1980: 石油與 IBM 時代
        {"Year": 1980, "Company": "IBM", "Market Cap": 34, "Sector": "Technology"},
        {"Year": 1980, "Company": "AT&T", "Market Cap": 47, "Sector": "Telecom"},