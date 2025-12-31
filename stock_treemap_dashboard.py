# ----------------------------------------------------------------------
# 股市戰情室 - 旗艦版 v2.0 (Optimized)
# ----------------------------------------------------------------------
# Updates:
#   1. Session State Persistence for Inputs & Search History
#   2. Improved Layout with Tabs for Analysis
#   3. Robust Error Handling & Fallback Data
#   4. Added "Fundamental Score" Logic
#   5. CSV Data Export
# 股市戰情室 - 旗艦版 (含資金籌碼、總經、與 個股/ETF 深度技術分析)
# Style: High Contrast Light Theme (All Text Darkened)
# Fixes: 
#   1. KeyError 'Name' in S&P 500 Treemap (Renamed 'Security' to 'Name')
#   2. Enforced High Contrast (Black Text on White Bg) for ALL Plotly charts
# [版本說明]
# Style: High Contrast Light Theme (高對比亮色主題，字體加深)
# Features:
#   1. S&P 500 熱力圖修復 (KeyError 'Name' fixed)
#   2. 強制圖表黑字白底 (High visibility)
#   3. 平行運算抓取基本面 (Parallel Fetching)
# ----------------------------------------------------------------------

import streamlit as st
@@ -18,127 +15,152 @@
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures
from datetime import datetime, timedelta
import io

# --- 1. Streamlit 頁面設定 ---
st.set_page_config(
    page_title="股市全方位戰情室 Pro", 
page_title="股市全方位戰情室", 
page_icon="📈",
layout="wide",
initial_sidebar_state="expanded"
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Session State 初始化 ---
if 'search_history' not in st.session_state:
    st.session_state['search_history'] = []
if 'm1b_val' not in st.session_state:
    st.session_state['m1b_val'] = 5.24
if 'm2_val' not in st.session_state:
    st.session_state['m2_val'] = 5.44
if 'margin_ratio' not in st.session_state:
    st.session_state['margin_ratio'] = 169.39
if 'us_margin_debt' not in st.session_state:
    st.session_state['us_margin_debt'] = 1.21

# --- CSS 全局高對比深色字體注入 ---
# --- [UI/UX] CSS 全局高對比深色字體注入 ---
# 說明：此區塊強制覆蓋 Streamlit 預設樣式，確保在亮色背景下文字為深黑，提升閱讀性。
st.markdown("""
<style>
   /* 引入現代字體 Inter */
   @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
   
    /* 1. 全局基礎設定 - 強制深色 */
   html, body, .stApp {
       font-family: 'Inter', sans-serif;
        color: #000000 !important;
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    /* 1. 全局基礎設定 - 強制深色字體與淺灰背景 */
    html, body, .stApp {
        font-family: 'Inter', sans-serif;
       color: #000000 !important; /* 純黑字體 */
       background-color: #f8f9fa;
   }

    /* 針對所有 Markdown 內文 */
    /* 2. 針對所有 Markdown 內文 */
   .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
       color: #111111 !important;
       font-weight: 500;
   }

    /* 所有標題 */
    h1, h2, h3, h4, h5, h6 {
    /* 3. 所有標題 (H1-H6) */
        background-color: #f8f9fa;
    }

    /* 2. 針對 Markdown 內文加深 */
    .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
        color: #111111 !important;
        font-weight: 500;
    }

    /* 3. 標題層級強化 (H1-H6) */
   h1, h2, h3, h4, h5, h6, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
       color: #000000 !important;
       font-weight: 800 !important;
       letter-spacing: -0.5px;
   }
   
    /* 標題裝飾線 */
   h3 {
       margin-top: 1rem;
       border-left: 5px solid #2b7de9;
       padding-left: 10px;
   }

    /* 輸入元件與 Tabs */
    /* 4. 輸入元件標籤 */
   .stTextInput label, .stSelectbox label, .stNumberInput label, .stRadio label {
       color: #000000 !important;
        font-weight: 700;
        color: #000000 !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    /* 自定義標題裝飾線 */
    h3 {
        margin-top: 1rem;
        border-left: 5px solid #2b7de9;
        padding-left: 10px;
    }

    /* 4. 輸入元件 (Input Widgets) 標籤加深 */
    .stTextInput label, .stSelectbox label, .stNumberInput label, .stRadio label {
        color: #000000 !important;
       font-weight: 700 !important;
       font-size: 1rem !important;
   }
   
    /* 5. Expander 標題 */
    }
    
    /* 5. Expander (折疊區塊) 標題優化 */
   .streamlit-expanderHeader p {
       color: #000000 !important;
        background-color: #f8f9fa;
       font-weight: 700 !important;
       font-size: 1.1rem !important;
   }

    /* 6. Tabs 標籤 */
   .stTabs button {
        color: #555555 !important;
    /* 6. Tabs 分頁標籤 */
    .stTabs button {
       color: #333333 !important;
       font-weight: 700 !important;
   }
   .stTabs [aria-selected="true"] {
       color: #2b7de9 !important;
        border-bottom-color: #2b7de9 !important;
   }

    /* Metric 指標元件優化 */
    /* 7. Metric 指標元件 */
   [data-testid="stMetric"] {
       background-color: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        font-weight: 700 !important;
    }
    .stTabs [aria-selected="true"] {
        color: #2b7de9 !important; /* 選中時呈現藍色 */
    }

    /* 7. Metric (關鍵指標) 元件優化 */
    [data-testid="stMetric"] {
        background-color: #ffffff;
       border: 1px solid #d1d5db;
       padding: 15px 20px;
       border-radius: 10px;
       box-shadow: 0 2px 5px rgba(0,0,0,0.08);
       transition: transform 0.2s ease, box-shadow 0.2s ease;
   }
   
    }
    
   [data-testid="stMetric"]:hover {
       transform: translateY(-2px);
       box-shadow: 0 5px 15px rgba(0,0,0,0.15);
       border-color: #2b7de9;
   }

   [data-testid="stMetricLabel"] {
        font-size: 14px !important;
    [data-testid="stMetricLabel"] {
       font-size: 15px !important;
       color: #444444 !important;
        font-weight: 600 !important;
        color: #444444 !important;
       font-weight: 700 !important;
   }
    }

   [data-testid="stMetricValue"] {
        font-size: 24px !important;
    [data-testid="stMetricValue"] {
       font-size: 28px !important;
       color: #000000 !important;
       font-weight: 800 !important;
   }
   
    /* 8. 側邊欄 */
        color: #000000 !important;
        font-weight: 800 !important;
    }
    
    /* 8. 側邊欄樣式 */
   [data-testid="stSidebar"] {
       background-color: #ffffff;
       border-right: 1px solid #e5e7eb;
@@ -151,20 +121,15 @@
       color: #111111 !important;
   }

    /* 9. Caption */
    /* 9. 輔助文字 (Caption) */
   .stCaption {
       color: #555555 !important;
       font-size: 0.9rem !important;
   }

   /* Dashboard Card */
   .dashboard-card {
       background-color: #ffffff;
        padding: 20px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    /* 自定義 Dashboard 卡片容器 */
    .dashboard-card {
        background-color: #ffffff;
       padding: 25px;
       border-radius: 12px;
       border: 1px solid #d1d5db;
@@ -177,11 +142,9 @@
       border-radius: 8px;
       font-weight: 700;
       color: #ffffff !important;
   }
    }

   /* 狀態顏色 */
    .bullish { color: #059669; font-weight: bold; }
    .bearish { color: #DC2626; font-weight: bold; }
    /* 狀態顏色定義 (深色版，適合白底) */
   .bullish { color: #059669 !important; font-weight: 800; }
   .bearish { color: #DC2626 !important; font-weight: 800; }
   .neutral { color: #D97706 !important; font-weight: 800; }
@@ -195,105 +158,145 @@

# --- 2. 側邊欄控制 ---
with st.sidebar:
st.header("⚙️ 戰情控制台")
st.markdown("---")
    
    # 搜尋歷史 (New Feature)
    if st.session_state['search_history']:
        st.caption("🕒 最近查詢")
        selected_history = st.selectbox("快速切換", [""] + st.session_state['search_history'], index=0, key="history_box")
    else:
        selected_history = ""

market_mode = st.radio(
"📊 選擇儀表板",
[
"🔎 個股技術戰略 (Stock Strategy)",
            "🇺🇸 美股 S&P 500 Map", 
    st.header("⚙️ 戰情控制台")
    st.markdown("---")
    market_mode = st.radio(
        "📊 選擇儀表板",
        [
            "🔎 個股技術戰略 (Stock Strategy)",
"🇺🇸 美股 S&P 500", 
"🇹🇼 台股權值股 (TWSE)", 
"💰 資金與籌碼 (Liquidity)",
"🚢 原物料與航運 (Commodities)",
@@ -149,13 +171,13 @@
st.markdown("---")
if st.button('🔄 強制更新數據', type="primary", use_container_width=True):
st.cache_data.clear()
        st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            "🇹🇼 台股權值股 (TWSE)", 
            "💰 資金與籌碼 (Liquidity)",
            "🚢 原物料與航運 (Commodities)",
            "📉 總經與風險指標 (Macro)"
        ]
    )
    
    st.markdown("---")
    if st.button('🔄 強制更新數據', type="primary", use_container_width=True):
        st.cache_data.clear()
st.session_state.pop('last_update', None)
st.rerun()
        st.rerun()

if 'last_update' in st.session_state:
st.caption(f"Last Update: {st.session_state['last_update']}")
    if 'last_update' in st.session_state:
        st.caption(f"Last Update: {st.session_state['last_update']}")

st.title(f"📊 {market_mode.split('(')[0]}")
st.title(f"📊 {market_mode}")
st.markdown("---")

# --- 3. 核心數據函數 (股票) ---
@@ -188,32 +210,18 @@ def get_tw_constituents():
# --- 3. 核心數據函數 (股票清單) ---

@st.cache_data(ttl=24 * 3600)
def get_sp500_constituents():
    # Fallback data in case GitHub is down or CSV format changes
    fallback_data = [
        {'Ticker': 'MSFT', 'Name': 'Microsoft', 'Sector': 'Technology', 'Industry': 'Software'},
        {'Ticker': 'AAPL', 'Name': 'Apple', 'Sector': 'Technology', 'Industry': 'Consumer Electronics'},
        {'Ticker': 'NVDA', 'Name': 'Nvidia', 'Sector': 'Technology', 'Industry': 'Semiconductors'},
        {'Ticker': 'AMZN', 'Name': 'Amazon', 'Sector': 'Consumer Cyclical', 'Industry': 'Internet Retail'},
        {'Ticker': 'GOOGL', 'Name': 'Alphabet', 'Sector': 'Communication Services', 'Industry': 'Internet Content'},
        {'Ticker': 'META', 'Name': 'Meta', 'Sector': 'Communication Services', 'Industry': 'Internet Content'},
        {'Ticker': 'TSLA', 'Name': 'Tesla', 'Sector': 'Consumer Cyclical', 'Industry': 'Auto Manufacturers'},
        {'Ticker': 'BRK-B', 'Name': 'Berkshire Hathaway', 'Sector': 'Financial', 'Industry': 'Insurance'},
        {'Ticker': 'LLY', 'Name': 'Eli Lilly', 'Sector': 'Healthcare', 'Industry': 'Drug Manufacturers'},
        {'Ticker': 'JPM', 'Name': 'JPMorgan', 'Sector': 'Financial', 'Industry': 'Banks'}
def get_tw_constituents():
    # [說明] 手動維護的台股清單，確保都是流動性高的權值股
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
    
url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
try:
df = pd.read_csv(url)
        # [Fix] Rename 'Security' to 'Name' to match TWSE data structure and prevent KeyError
rename_map = {'Symbol': 'Ticker', 'GICS Sector': 'Sector', 'GICS Sub-Industry': 'Industry', 'Security': 'Name'}
df = df.rename(columns=rename_map)
df['Ticker'] = df['Ticker'].str.replace('.', '-', regex=False)
if 'Industry' not in df.columns:
df['Industry'] = df['Sector'] if 'Sector' in df.columns else 'Unknown'
return df
    except Exception as e:
        st.toast(f"⚠️ S&P 500 完整清單下載失敗，使用備援數據。Error: {str(e)}", icon="⚠️")
        return pd.DataFrame(fallback_data)
    return pd.DataFrame(data)

@st.cache_data(ttl=24 * 3600)
def get_sp500_constituents():
    # [修復] 從 GitHub 獲取 S&P 500 清單並標準化欄位名稱，避免 KeyError
    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    try:
        df = pd.read_csv(url)
        # Rename 'Security' to 'Name' to match TWSE data structure
        rename_map = {'Symbol': 'Ticker', 'GICS Sector': 'Sector', 'GICS Sub-Industry': 'Industry', 'Security': 'Name'}
        df = df.rename(columns=rename_map)
        df['Ticker'] = df['Ticker'].str.replace('.', '-', regex=False)
        if 'Industry' not in df.columns:
            df['Industry'] = df['Sector'] if 'Sector' in df.columns else 'Unknown'
        return df
except Exception:
return pd.DataFrame()

def fetch_single_cap(ticker):
try:
@@ -225,8 +233,7 @@ def fetch_single_cap(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        return ticker, info['market_cap']
    except:
        return ticker, 0

@st.cache_data(ttl=24 * 3600)
def fetch_market_caps(tickers):
caps = {}
    # Lowered max_workers to prevent rate limiting
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    # [優化] 使用 ThreadPool 加速市值獲取
    caps = {}
with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
results = executor.map(fetch_single_cap, tickers)
for ticker, cap in results:
caps[ticker] = cap
@@ -275,18 +282,28 @@ def get_stock_data(ticker, period="2y"):
if data.empty:
return pd.DataFrame()

        # Handle MultiIndex Logic Cleaner
if isinstance(data.columns, pd.MultiIndex):
            # Attempt to find the price level
            try:
                data = data.xs(ticker, axis=1, level=1)
            except:
                 # Fallback: flatten and check
                 data.columns = [c[0] for c in data.columns]
        results = executor.map(fetch_single_cap, tickers)
        for ticker, cap in results:
            caps[ticker] = cap
    return caps

@st.cache_data(ttl=21600) 
def fetch_price_history(tickers, period="1y"):
    """下載大量股票歷史數據"""
    try:
        data = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True, progress=False)
        return data
    except Exception:
        return pd.DataFrame()

# --- 4. 總經/原物料/資金 數據獲取 ---
@st.cache_data(ttl=3600)
def get_macro_data():
    tickers = ["^VIX", "^GSPC"]
    data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, progress=False)
    
    # [修復] 強制校正 MultiIndex 層級，避免 KeyError
    if isinstance(data.columns, pd.MultiIndex):
        level0 = data.columns.get_level_values(0)
        if 'Close' in level0:
            data = data.swaplevel(0, 1, axis=1)
            data.sort_index(axis=1, inplace=True)
            
    return data

@st.cache_data(ttl=3600)
def get_commodity_data():
    tickers = ["BDRY", "DBC", "HG=F", "CL=F", "GC=F"]
    data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, progress=False)
    
    # [修復] 同樣加入層級校正
    if isinstance(data.columns, pd.MultiIndex):
        level0 = data.columns.get_level_values(0)
        if 'Close' in level0:
            data = data.swaplevel(0, 1, axis=1)
            data.sort_index(axis=1, inplace=True)
            
    return data

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period="2y"):
    """獲取單一股票詳細數據，包含 MultiIndex 智能偵測"""
    try:
        data = yf.download(ticker, period=period, auto_adjust=True, progress=False)

        # Ensure Close exists
        if 'Close' not in data.columns and 'Adj Close' in data.columns:
             data['Close'] = data['Adj Close']
        if data.empty:
            return pd.DataFrame()

        if isinstance(data.columns, pd.MultiIndex):
target_level = None
found = False
            # 自動搜尋包含 'Close' 的層級
for i in range(data.columns.nlevels):
if 'Close' in data.columns.get_level_values(i):
target_level = i
@@ -303,6 +306,7 @@ def fetch_market_caps(tickers):
if found:
data.columns = data.columns.get_level_values(target_level)
else:
                # 備援：尋找 Adj Close
for i in range(data.columns.nlevels):
if 'Adj Close' in data.columns.get_level_values(i):
target_level = i
@@ -311,182 +315,200 @@ def fetch_market_caps(tickers):
if not found and data.columns.nlevels > 1:
data.columns = data.columns.droplevel(0)

        # 標準化欄位名稱
if 'Adj Close' in data.columns and 'Close' not in data.columns:
data.rename(columns={'Adj Close': 'Close'}, inplace=True)

if 'Close' in data.columns:
data = data.dropna(subset=['Close'])
@@ -298,41 +315,49 @@ def get_stock_data(ticker, period="2y"):
print(f"Error fetching {ticker}: {e}")
return pd.DataFrame()
        if 'Close' in data.columns:
            data = data.dropna(subset=['Close'])
            return data
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

# Helpers for Fundamentals
# 平行處理 Helper Functions
# [優化] 平行處理 Helper Functions - 隔離 API 呼叫
def _fetch_info_helper(stock):
try: return stock.info
except: return {}
    try:
        return stock.info
    except:
        return {}

def _fetch_cashflow_helper(stock):
try: return stock.cashflow
except: return pd.DataFrame()
    try:
        return stock.cashflow
    except:
        return pd.DataFrame()

def _fetch_balance_sheet_helper(stock):
try: return stock.balance_sheet
except: return pd.DataFrame()
    try:
        return stock.balance_sheet
    except:
        return pd.DataFrame()

def _fetch_estimates_helper(stock):
try: return stock.earnings_estimate, stock.eps_trend, stock.recommendations_summary
except: return None, None, None
    try:
        return stock.earnings_estimate, stock.eps_trend, stock.recommendations_summary
    except:
        return None, None, None

@st.cache_data(ttl=12 * 3600)
def get_fundamentals(ticker):
result = {
'P/FCF': None, 'FCF': None, 'MarketCap': None,
'GrossMargin': None, 'OperatingMargin': None,
        'EarningsGrowth': None, 'RevenueGrowth': None,
    """
    [核心優化] 使用 ThreadPoolExecutor 平行抓取基本面數據，大幅提升速度
    並包含 Fuzzy Lookup (模糊搜尋) 來應對 yfinance 欄位名稱變動
    """
    result = {
        'P/FCF': None, 'FCF': None, 'MarketCap': None,
        'GrossMargin': None, 'OperatingMargin': None,
'EarningsGrowth': None, 'ContractLiabilities': None,
'TrailingPE': None, 'ForwardPE': None,
'PEG': None, 'ForwardEPS': None,
'EarningsEst': None, 'EPSTrend': None,
'TargetMean': None, 'TargetHigh': None, 'TargetLow': None,
'Recommendation': None, 'NumAnalysts': None,
        'RecSummary': None, 'ContractLiabilities': None
        'TrailingPE': None, 'ForwardPE': None,
        'PEG': None, 'ForwardEPS': None,
        'EarningsEst': None, 'EPSTrend': None,
        'TargetMean': None, 'TargetHigh': None, 'TargetLow': None,
        'Recommendation': None, 'NumAnalysts': None,
'RecSummary': None
}

try:
stock = yf.Ticker(ticker)

        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    }
    
    try:
        stock = yf.Ticker(ticker)
        
        # 平行發送請求
with concurrent.futures.ThreadPoolExecutor() as executor:
future_info = executor.submit(_fetch_info_helper, stock)
future_cf = executor.submit(_fetch_cashflow_helper, stock)
future_bs = executor.submit(_fetch_balance_sheet_helper, stock)
@@ -355,7 +380,6 @@ def get_val(keys_list, default=None):
result['GrossMargin'] = get_val(['grossMargins', 'grossMargin'])
result['OperatingMargin'] = get_val(['operatingMargins', 'operatingMargin'])
result['EarningsGrowth'] = get_val(['earningsGrowth'])
        result['RevenueGrowth'] = get_val(['revenueGrowth'])
result['TrailingPE'] = get_val(['trailingPE'])
result['ForwardPE'] = get_val(['forwardPE'])
result['PEG'] = get_val(['pegRatio'])
@@ -376,7 +400,6 @@ def get_val(keys_list, default=None):
result['Recommendation'] = get_val(['recommendationKey'])
result['NumAnalysts'] = get_val(['numberOfAnalystOpinions'])

        # Free Cash Flow Logic
fcf = get_val(['freeCashflow'])
if fcf is None and not cf.empty:
try:
@@ -391,24 +414,20 @@ def get_val(keys_list, default=None):
capex = recent_cf[idx]

if op_cf is not None and capex is not None:
                    fcf = op_cf + capex # Capex is usually negative
            future_info = executor.submit(_fetch_info_helper, stock)
            future_cf = executor.submit(_fetch_cashflow_helper, stock)
            future_bs = executor.submit(_fetch_balance_sheet_helper, stock)
            future_est = executor.submit(_fetch_estimates_helper, stock)
            
            info = future_info.result()
            cf = future_cf.result()
            bs = future_bs.result()
            est_data = future_est.result() 

        info_lower = {k.lower(): v for k, v in info.items()} if info else {}
        
        def get_val(keys_list, default=None):
            for k in keys_list:
                if k.lower() in info_lower:
                    return info_lower[k.lower()]
            return default

        # 填入數據
        result['MarketCap'] = get_val(['marketCap'])
        result['GrossMargin'] = get_val(['grossMargins', 'grossMargin'])
        result['OperatingMargin'] = get_val(['operatingMargins', 'operatingMargin'])
        result['EarningsGrowth'] = get_val(['earningsGrowth'])
        result['TrailingPE'] = get_val(['trailingPE'])
        result['ForwardPE'] = get_val(['forwardPE'])
        result['PEG'] = get_val(['pegRatio'])
        result['ForwardEPS'] = get_val(['forwardEps', 'forwardEPS'])
        
        # 數值推算備援 (Fallback Calculations)
        if result['ForwardEPS'] is None and result['ForwardPE']:
             curr_price = get_val(['currentPrice', 'regularMarketPrice', 'ask', 'bid'])
             if curr_price:
                 result['ForwardEPS'] = curr_price / result['ForwardPE']

        if result['PEG'] is None and result['TrailingPE'] and result['EarningsGrowth']:
             if result['EarningsGrowth'] > 0:
                result['PEG'] = result['TrailingPE'] / (result['EarningsGrowth'] * 100)

        result['TargetMean'] = get_val(['targetMeanPrice'])
        result['TargetHigh'] = get_val(['targetHighPrice'])
        result['TargetLow'] = get_val(['targetLowPrice'])
        result['Recommendation'] = get_val(['recommendationKey'])
        result['NumAnalysts'] = get_val(['numberOfAnalystOpinions'])

        # 現金流解析
        fcf = get_val(['freeCashflow'])
        if fcf is None and not cf.empty:
            try:
                recent_cf = cf.iloc[:, 0]
                op_cf = None
                capex = None
                for idx in recent_cf.index:
                    idx_str = str(idx).lower()
                    if 'operating' in idx_str and 'cash' in idx_str:
                        op_cf = recent_cf[idx]
                    if 'capital' in idx_str and 'expenditure' in idx_str:
                        capex = recent_cf[idx]
                
                if op_cf is not None and capex is not None:
fcf = op_cf + capex 
except: pass
result['FCF'] = fcf

if fcf and result['MarketCap'] and fcf > 0:
result['P/FCF'] = result['MarketCap'] / fcf

        # Contract Liabilities (RPO Proxy)
if not bs.empty:
try:
for idx in bs.index:
idx_str = str(idx).lower()
if ('contract' in idx_str and 'liabilities' in idx_str) or \
('deferred' in idx_str and 'revenue' in idx_str):
                        val = bs.loc[idx].iloc[0]
                        # Sum if multiple rows match (rare)
                        if isinstance(val, pd.Series): val = val.sum()
                        result['ContractLiabilities'] = val
                        result['ContractLiabilities'] = bs.loc[idx].iloc[0]
break
except: pass
            except: pass
        result['FCF'] = fcf

        if fcf and result['MarketCap'] and fcf > 0:
            result['P/FCF'] = result['MarketCap'] / fcf

@@ -422,45 +441,6 @@ def get_val(keys_list, default=None):
        # 資產負債表解析
        if not bs.empty:
            try:
                for idx in bs.index:
                    idx_str = str(idx).lower()
                    if ('contract' in idx_str and 'liabilities' in idx_str) or \
                       ('deferred' in idx_str and 'revenue' in idx_str):
                        result['ContractLiabilities'] = bs.loc[idx].iloc[0]
                        break
            except: pass

return result
        if est_data:
            result['EarningsEst'] = est_data[0]
            result['EPSTrend'] = est_data[1]
            result['RecSummary'] = est_data[2]

# New Function: Calculate Fundamental Score
def calculate_fundamental_score(data):
    score = 0
    total = 0
    
    # 1. PEG < 2 (Value/Growth)
    if data.get('PEG') is not None:
        total += 2
        if 0 < data['PEG'] < 1.5: score += 2
        elif 1.5 <= data['PEG'] < 2.5: score += 1
    except Exception as e:
        print(f"Fundamentals critical error for {ticker}: {e}")

    # 2. Operating Margin > 15% (Profitability)
    if data.get('OperatingMargin') is not None:
        total += 2
        if data['OperatingMargin'] > 0.20: score += 2
        elif data['OperatingMargin'] > 0.10: score += 1

    # 3. Revenue/Earnings Growth (Growth)
    if data.get('EarningsGrowth') is not None:
        total += 2
        if data['EarningsGrowth'] > 0.20: score += 2
        elif data['EarningsGrowth'] > 0.05: score += 1
        
    # 4. Analyst Recommendation (Sentiment)
    if data.get('Recommendation'):
        total += 2
        rec = data['Recommendation'].lower()
        if 'buy' in rec: score += 2
        elif 'hold' in rec: score += 1
        
    # 5. P/FCF (Cash Flow)
    if data.get('P/FCF') is not None:
        total += 2
        if 0 < data['P/FCF'] < 20: score += 2
        elif 20 <= data['P/FCF'] < 35: score += 1
        
    if total == 0: return 0
    return (score / total) * 10
    return result

def check_ticker_validity(ticker):
try:
data = yf.download(ticker, period="1d", progress=False)
@@ -504,24 +484,28 @@ def calculate_indicators(df):
    try:
        data = yf.download(ticker, period="1d", progress=False)
        return not data.empty
    except:
        return False

def calculate_fear_greed(vix_close, sp500_close):
    vix_score = max(0, min(100, (40 - vix_close) * (100 / 30)))
    delta = sp500_close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    final = (vix_score * 0.6) + (rsi.iloc[-1] * 0.4)
    return int(final), vix_close, rsi.iloc[-1]

# --- 5. 技術指標計算 ---
def calculate_indicators(df):
    df = df.copy()
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
    
    df['BB_Upper'] = df['MA20'] + (df['Close'].rolling(window=20).std() * 2)
    df['BB_Lower'] = df['MA20'] - (df['Close'].rolling(window=20).std() * 2)
    
    return df

# --- 6. 核心計算邏輯 (股票) ---
def process_data_for_periods(base_df, history_data, market_caps):
    if history_data.empty: return pd.DataFrame()
    """
    [優化] 向量化運算，極大化提升市場儀表板計算速度
    """
if history_data.empty:
return pd.DataFrame()

closes = pd.DataFrame()
    # Robust MultiIndex handling for vectorization
    closes = pd.DataFrame()

if isinstance(history_data.columns, pd.MultiIndex):
        try:
            closes = history_data.xs('Close', axis=1, level=1)
        except KeyError:
            # Try Alt structure
            if 'Close' in history_data.columns.get_level_values(0):
                 # This implies shape is (Ticker, Close) which is wrong for group_by='ticker'
                 # but YF varies. Let's try simple select
                 closes = history_data['Close']
    # 處理 MultiIndex，提取 Close 數據
    if isinstance(history_data.columns, pd.MultiIndex):
level0 = history_data.columns.get_level_values(0)
if 'Close' in level0:
closes = history_data['Close']
@@ -497,194 +519,247 @@ def process_data_for_periods(base_df, history_data, market_caps):
else:
if 'Adj Close' in level1:
closes = history_data.xs('Adj Close', level=1, axis=1)
else:
if 'Close' in history_data.columns:
closes = history_data[['Close']]

    if closes.empty: return pd.DataFrame()
    else:
        if 'Close' in history_data.columns:
            closes = history_data[['Close']]
    
if closes.empty:
return pd.DataFrame()

closes = closes.ffill()
    closes = closes.ffill()
    
    try:
        current_prices = closes.iloc[-1]
        res_1d = closes.pct_change(1).iloc[-1] * 100
        res_1w = closes.pct_change(5).iloc[-1] * 100
        res_1m = closes.pct_change(21).iloc[-1] * 100
        res_ytd = ((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]) * 100
        
        metrics_df = pd.DataFrame({
            'Ticker': current_prices.index,
            'Close': current_prices.values,
            '1D Change': res_1d.values,
            '1W Change': res_1w.values,
            '1M Change': res_1m.values,
            'YTD Change': res_ytd.values
        })
        
        base_df['Ticker'] = base_df['Ticker'].astype(str)
        metrics_df['Ticker'] = metrics_df['Ticker'].astype(str)
        
        merged_df = pd.merge(base_df, metrics_df, on='Ticker', how='inner')
        merged_df['Market Cap'] = merged_df['Ticker'].map(market_caps).fillna(0)
        merged_df = merged_df.dropna(subset=['Close'])
        merged_df = merged_df[merged_df['Market Cap'] > 0]
        
        return merged_df

@@ -557,7 +541,9 @@ def process_data_for_periods(base_df, history_data, market_caps):
    except Exception as e:
        print(f"Vectorization error: {e}")
        return pd.DataFrame()

# --- 7. 繪圖函數 ---
def plot_treemap(df, change_col, title, color_range):
    if 'Name' not in df.columns: df['Name'] = df['Ticker']
# Ensure 'Name' column exists to prevent KeyError
if 'Name' not in df.columns:
df['Name'] = df['Ticker']

df['Label'] = np.where(
df['Ticker'].str.contains('TW') | (df['Name'] != df['Ticker']),
@@ -575,11 +561,13 @@ def plot_treemap(df, change_col, title, color_range):
textfont=dict(family="Arial Black", size=15), 
hovertemplate='<b>%{label}</b><br>代號: %{customdata[0]}<br>股價: %{customdata[1]:.2f}<br>漲跌幅: %{customdata[2]:.2f}%'
)
    df['Label'] = np.where(
        df['Ticker'].str.contains('TW') | (df['Name'] != df['Ticker']),
        df['Name'] + "\n" + df[change_col].map('{:+.2f}%'.format),
        df['Ticker'] + "\n" + df[change_col].map('{:+.2f}%'.format)
    )
    
    fig = px.treemap(
        df, path=[px.Constant(title), 'Sector', 'Industry', 'Name'], values='Market Cap',
        color=change_col, color_continuous_scale='RdYlGn', color_continuous_midpoint=0, range_color=color_range,
        custom_data=['Ticker', 'Close', change_col]
    )
    fig.update_traces(
        textinfo="label+text", 
        textfont=dict(family="Arial Black", size=15), 
        hovertemplate='<b>%{label}</b><br>代號: %{customdata[0]}<br>股價: %{customdata[1]:.2f}<br>漲跌幅: %{customdata[2]:.2f}%'
    )
# [Fix] Enforce High Contrast Black Text
fig.update_layout(
height=600, 
margin=dict(t=20, l=10, r=10, b=10),
font=dict(color='black', size=14),
        paper_bgcolor='white', plot_bgcolor='white'
    fig.update_layout(
        height=600, 
        margin=dict(t=20, l=10, r=10, b=10),
        font=dict(color='black', size=14),
paper_bgcolor='white',
plot_bgcolor='white'
)
st.plotly_chart(fig, use_container_width=True)

@@ -600,21 +588,27 @@ def plot_gauge(score):
]
}
))
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_gauge(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = score,
        domain = {'x': [0, 1], 'y': [0, 1]}, 
        title = {'text': "市場情緒 (Proxy)", 'font': {'size': 18, 'color': 'black'}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': 'black'}, 
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [0, 25], 'color': '#ff4b4b'}, # Red
                {'range': [25, 45], 'color': '#ffbaba'}, # Light Red
                {'range': [45, 55], 'color': '#e0e0e0'}, # Grey
                {'range': [55, 75], 'color': '#baffba'}, # Light Green
                {'range': [75, 100], 'color': '#008000'} # Green
            ]
        }
    ))
# [Fix] Enforce High Contrast Black Text
fig.update_layout(
height=300, 
margin=dict(t=60, b=20, l=30, r=30),
        paper_bgcolor='white', plot_bgcolor='white', font=dict(color='black')
    fig.update_layout(
        height=300, 
        margin=dict(t=60, b=20, l=30, r=30),
paper_bgcolor='white',
plot_bgcolor='white',
font=dict(color='black')
)
st.plotly_chart(fig, use_container_width=True)
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_line_chart(data, title, color):
fig = px.line(data, title=title)
fig.update_traces(line_color=color, line_width=2)
    fig = px.line(data, title=title)
    fig.update_traces(line_color=color, line_width=2)
# [Fix] Enforce High Contrast Black Text
fig.update_layout(
height=350, 
margin=dict(l=20, r=20, t=40, b=20), 
xaxis_title=None, yaxis_title=None,
        paper_bgcolor='white', plot_bgcolor='white', font=dict(color='black')
    fig.update_layout(
        height=350, 
        margin=dict(l=20, r=20, t=40, b=20), 
        xaxis_title=None, yaxis_title=None,
paper_bgcolor='white',
plot_bgcolor='white',
font=dict(color='black')
)
st.plotly_chart(fig, use_container_width=True)

@@ -627,15 +621,17 @@ def plot_tech_chart(df, ticker, title):
subplot_titles=(f"{title} 價格趨勢", "成交量", "RSI", "MACD")
)
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_tech_chart(df, ticker, title):
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(f"{title} 價格趨勢", "成交量", "RSI", "MACD")
    )

    # 1. Price
# 1. 主圖：K線 + MA
fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='blue', width=1.5), name='MA50'), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], line=dict(color='red', width=2), name='MA200'), row=1, col=1)
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='blue', width=1.5), name='MA50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], line=dict(color='red', width=2), name='MA200'), row=1, col=1)

# 布林通道
fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='gray', width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='gray', width=0), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='BB Band'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='gray', width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='gray', width=0), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='BB Band'), row=1, col=1)

    # 2. Volume
# 2. 成交量
colors = ['green' if o >= c else 'red' for o, c in zip(df['Open'], df['Close'])]
fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)
    colors = ['green' if o >= c else 'red' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

@@ -650,11 +646,13 @@ def plot_tech_chart(df, ticker, title):
colors_hist = ['green' if v >= 0 else 'red' for v in df['MACD_Hist']]
fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_hist, name='Hist'), row=4, col=1)
    # 3. RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # 4. MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue', width=1.5), name='MACD'), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], line=dict(color='orange', width=1.5), name='Signal'), row=4, col=1)
    colors_hist = ['green' if v >= 0 else 'red' for v in df['MACD_Hist']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_hist, name='Hist'), row=4, col=1)

# [Fix] Enforce High Contrast Black Text & Light Grid
fig.update_layout(
height=900, 
xaxis_rangeslider_visible=False,
hovermode='x unified',
        plot_bgcolor='white', paper_bgcolor='white',
    fig.update_layout(
        height=900, 
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
plot_bgcolor='white',
paper_bgcolor='white',
margin=dict(t=30, b=30),
font=dict(color='black')
)
@@ -665,7 +663,7 @@ def plot_tech_chart(df, ticker, title):
        margin=dict(t=30, b=30),
        font=dict(color='black')
    )
    fig.update_xaxes(showgrid=True, gridcolor='#e0e0e0')
    fig.update_yaxes(showgrid=True, gridcolor='#e0e0e0')
    
    st.plotly_chart(fig, use_container_width=True)

# --- 8. 頁面渲染邏輯 ---

def render_stock_strategy_page(initial_ticker=""):
def render_stock_strategy_page():
st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
c1, c2 = st.columns([4, 1])
with c1:
@@ -674,9 +672,7 @@ def render_stock_strategy_page(initial_ticker=""):

col_input1, col_input2, col_btn = st.columns([3, 1, 1])
with col_input1:
        # Link with sidebar selection if available
        default_val = initial_ticker if initial_ticker else "AAPL"
        ticker_input = st.text_input("輸入股票代號 (例如: NVDA, AAPL, 2330.TW)", value=default_val)
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    c1, c2 = st.columns([4, 1])
    with c1:
        st.subheader("🔍 個股技術戰略分析 (Technical Strategy)")
        st.caption("基於《Technical Analysis Profitability Rules》與基本面估值模型")
    
    col_input1, col_input2, col_btn = st.columns([3, 1, 1])
    with col_input1:
ticker_input = st.text_input("輸入股票代號 (例如: NVDA, AAPL, 2330.TW)", value="AAPL")
with col_input2:
timeframe = st.selectbox("分析週期", ["1y", "2y", "5y"], index=0)
with col_btn:
@@ -688,12 +684,6 @@ def render_stock_strategy_page(initial_ticker=""):
if analyze_btn or (ticker_input and ticker_input != ""):
ticker = ticker_input.upper().strip()

        # Add to history
        if ticker not in st.session_state['search_history']:
            st.session_state['search_history'].insert(0, ticker)
            if len(st.session_state['search_history']) > 10:
                st.session_state['search_history'].pop()

if ticker.isdigit() and len(ticker) == 4:
ticker = f"{ticker}.TW"
st.caption(f"💡 偵測到數字代號，將以台股上市模式查詢：{ticker}")
@@ -748,94 +738,159 @@ def render_stock_strategy_page(initial_ticker=""):
macd_val = last_row['MACD_Hist']
macd_sig = "多方控盤" if macd_val > 0 else "空方控盤"
m4.metric("MACD 動能", f"{macd_val:.2f}", macd_sig)
    with col_input2:
        timeframe = st.selectbox("分析週期", ["1y", "2y", "5y"], index=0)
    with col_btn:
        st.write("") 
        st.write("") 
        analyze_btn = st.button("🚀 開始分析", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if analyze_btn or (ticker_input and ticker_input != ""):
        ticker = ticker_input.upper().strip()
        
        if ticker.isdigit() and len(ticker) == 4:
            ticker = f"{ticker}.TW"
            st.caption(f"💡 偵測到數字代號，將以台股上市模式查詢：{ticker}")

        with st.spinner(f"正在連線交易所查詢 {ticker} ..."):
            is_valid = check_ticker_validity(ticker)
            if not is_valid and ticker.endswith('.TW'):
                ticker_two = ticker.replace('.TW', '.TWO')
                if check_ticker_validity(ticker_two):
                    ticker = ticker_two
                    is_valid = True

        if not is_valid:
            st.error(f"❌ 查無代號：{ticker}")
            return

        with st.spinner(f"✅ 代號確認！正在計算 {ticker} 技術指標與基本面..."):
            df = get_stock_data(ticker, period=timeframe)
            fund_data = get_fundamentals(ticker) 

            if df.empty or len(df) < 50:
                st.warning("⚠️ 數據不足，無法進行完整技術分析。")
                return

            # --- New Feature: Download Data ---
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer)
            st.download_button(
                label="📥 下載技術指標數據 (CSV)",
                data=csv_buffer.getvalue(),
                file_name=f"{ticker}_tech_data.csv",
                mime="text/csv",
            )

st.write("")
            df = calculate_indicators(df)
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            # --- A. 狀態儀表板 ---
            st.markdown("### 1. 即時技術狀態 (Technical Status)")
            m1, m2, m3, m4 = st.columns(4)

            # --- Tabs for Clean Layout ---
            tab_tech, tab_fund, tab_analyst = st.tabs(["📈 技術分析圖表", "🏢 基本面體質", "👥 分析師觀點"])

            with tab_tech:
                 plot_tech_chart(df, ticker, ticker)
                 
                 # 策略檢查清單
                 c1, c2 = st.columns(2)
                 with c1:
                    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
                    st.markdown("#### 🔍 趨勢與型態")
                    ma_bullish = last_row['MA20'] > last_row['MA50'] > last_row['MA200']
                    st.markdown(f"- **均線排列**: {'✅ 多頭' if ma_bullish else '⚠️ 糾結/空頭'}")
                    dist_ma200 = (last_row['Close'] - last_row['MA200']) / last_row['MA200'] * 100
                    st.markdown(f"- **乖離率**: {dist_ma200:.1f}%")
                    st.markdown('</div>', unsafe_allow_html=True)
                 with c2:
                    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
                    st.markdown("#### 🛡️ 風險與建議")
                    if trend_status.startswith("🚀") and rsi_val < 70 and macd_val > 0:
                        st.success("評語：強勢多頭，沿 MA20 操作。")
                    elif rsi_val > 75:
                        st.warning("評語：趨勢向上但超買，勿追高。")
                    elif trend_status.startswith("🐻"):
                        st.error("評語：空頭走勢，保守觀望。")
                    else:
                        st.info("評語：區間震盪，等待突破。")
                    st.markdown('</div>', unsafe_allow_html=True)
            chg = (last_row['Close'] - prev_row['Close']) / prev_row['Close'] * 100
            m1.metric(f"收盤價 ({ticker})", f"${last_row['Close']:.2f}", f"{chg:.2f}%")
            
            trend_status = "盤整 / 不明"
            if last_row['Close'] > last_row['MA200']:
                if last_row['MA50'] > last_row['MA200']:
                    trend_status = "🚀 長期多頭"
                else:
                    trend_status = "⚠️ 多頭回調"
            else:
                trend_status = "🐻 長期空頭"
            m2.metric("主要趨勢", trend_status)

            rsi_val = last_row['RSI']
            rsi_status = "中性"
            if rsi_val > 70: rsi_status = "🔴 超買"
            elif rsi_val < 30: rsi_status = "🟢 超賣"
            m3.metric("RSI 動能", f"{rsi_val:.1f}", rsi_status)
            
            macd_val = last_row['MACD_Hist']
            macd_sig = "多方控盤" if macd_val > 0 else "空方控盤"
            m4.metric("MACD 動能", f"{macd_val:.2f}", macd_sig)

            st.write("")

            with tab_fund:
                try:
                    f_score = calculate_fundamental_score(fund_data)
                    st.progress(f_score / 10, text=f"基本面 AI 評分: {f_score:.1f} / 10")
                    
                    f1, f2, f3, f4 = st.columns(4)
                    fwd_eps = fund_data.get('ForwardEPS')
                    f1.metric("Forward EPS", f"${fwd_eps:.2f}" if fwd_eps is not None else "N/A")
# --- 基本面快照區塊 ---
try:
st.markdown("### 2. 基本面體質快照 (Fundamental Snapshot)")
@@ -708,53 +783,24 @@ def render_stock_strategy_page():
peg_str = f"{peg:.2f}" if peg is not None else "N/A"
f3.metric("PEG (Est.)" if peg_est else "PEG", peg_str)

                    pe = fund_data.get('TrailingPE')
                    f2.metric("P/E (本益比)", f"{pe:.1f}x" if pe is not None else "N/A")
p_fcf = fund_data.get('P/FCF')
f4.metric("P/FCF", f"{p_fcf:.1f}x" if p_fcf is not None else "N/A")

                    peg = fund_data.get('PEG')
                    f3.metric("PEG Ratio", f"{peg:.2f}" if peg is not None else "N/A")
st.write("")
                f5, f6, f7, f8 = st.columns(4)
                f5, f6, f7 = st.columns(3)

                    p_fcf = fund_data.get('P/FCF')
                    f4.metric("P/FCF", f"{p_fcf:.1f}x" if p_fcf is not None else "N/A")
gm = fund_data.get('GrossMargin')
f5.metric("毛利率", f"{gm*100:.1f}%" if gm is not None else "N/A")

                    st.markdown("---")
                    f5, f6, f7, f8 = st.columns(4)
                    gm = fund_data.get('GrossMargin')
                    f5.metric("毛利率", f"{gm*100:.1f}%" if gm is not None else "N/A")
                    om = fund_data.get('OperatingMargin')
                    f6.metric("營益率", f"{om*100:.1f}%" if om is not None else "N/A")
om = fund_data.get('OperatingMargin')
f6.metric("營益率", f"{om*100:.1f}%" if om is not None else "N/A")

                    cl = fund_data.get('ContractLiabilities')
                    val_str = "N/A"
                    if cl is not None:
                        val_str = f"${cl/1e9:.1f}B" if cl > 1e9 else f"${cl/1e6:.1f}M"
                    f7.metric("合約負債 (RPO)", val_str)
                    f8.metric("資料日期", datetime.now().strftime("%m-%d"))

                except Exception as e:
                    st.error(f"基本面數據渲染錯誤: {e}")

            with tab_analyst:
                try:
                    est_df = fund_data.get('EarningsEst')
                    trend_df = fund_data.get('EPSTrend')
                    rec_summary = fund_data.get('RecSummary')
                    target_mean = fund_data.get('TargetMean')
                    
cl = fund_data.get('ContractLiabilities')
val_str = "N/A"
if cl is not None:
val_str = f"${cl/1e9:.1f}B" if cl > 1e9 else f"${cl/1e6:.1f}M"
f7.metric("合約負債 (RPO)", val_str)

                f8.metric("資料日期", datetime.now().strftime("%m-%d"))
st.write("")

except Exception as e:
@@ -774,8 +820,7 @@ def render_stock_strategy_page():
recommendation = fund_data.get('Recommendation')

with st.expander("📊 點擊展開：分析師看法 (Analyst Estimates & Consensus)", expanded=True):

                    if target_mean:
                    
tabs = []
if has_est_data: tabs.append("未來預估")
if has_trend_data: tabs.append("修正趨勢")
@@ -857,38 +902,26 @@ def render_stock_strategy_page():
if target_mean is not None:
st.markdown("#### 🎯 目標價與評級 (Price Targets)")

col_t1, col_t2 = st.columns([1, 2])
with col_t1:
                            st.metric("平均目標價", f"${target_mean}", delta=f"{((target_mean - last_row['Close'])/last_row['Close']*100):.1f}%")
                        col_t1, col_t2 = st.columns([1, 2])
                        with col_t1:
st.metric("分析師評級", str(recommendation).upper().replace('_', ' ') if recommendation else "N/A")
st.metric("平均目標價", f"${target_mean}", delta=f"{((target_mean - last_row['Close'])/last_row['Close']*100):.1f}%" if last_row['Close'] else None)
if fund_data.get('NumAnalysts'):
st.caption(f"基於 {fund_data['NumAnalysts']} 位分析師")

with col_t2:
current_price = last_row['Close']
low_target = fund_data.get('TargetLow', current_price * 0.9)
@@ -846,45 +901,75 @@ def render_stock_strategy_page(initial_ticker=""):
fig_target.add_trace(go.Bar(y=['Price'], x=[target_mean - low_target], name='Mean', orientation='h', marker_color='#2b7de9', base=low_target))
fig_target.add_trace(go.Bar(y=['Price'], x=[high_target - target_mean], name='High', orientation='h', marker_color='#008000', base=target_mean))
fig_target.add_vline(x=current_price, line_width=3, line_dash="dash", line_color="black", annotation_text="Now")
                            fig_target.update_layout(barmode='stack', title="目標價區間", height=150, margin=dict(l=20, r=20, t=30, b=20), showlegend=False, plot_bgcolor='white', font=dict(color='black'))
                        with col_t2:
                            current_price = last_row['Close']
                            low_target = fund_data.get('TargetLow', current_price * 0.9)
                            high_target = fund_data.get('TargetHigh', current_price * 1.1)
                            
                            fig_target = go.Figure()
                            fig_target.add_trace(go.Bar(y=['Price'], x=[low_target], name='Low', orientation='h', marker_color='#ff4b4b'))
                            fig_target.add_trace(go.Bar(y=['Price'], x=[target_mean - low_target], name='Mean', orientation='h', marker_color='#2b7de9', base=low_target))
                            fig_target.add_trace(go.Bar(y=['Price'], x=[high_target - target_mean], name='High', orientation='h', marker_color='#008000', base=target_mean))
                            fig_target.add_vline(x=current_price, line_width=3, line_dash="dash", line_color="black", annotation_text="Now")

fig_target.update_layout(barmode='stack', title="目標價區間", height=200, margin=dict(l=20, r=20, t=30, b=20), showlegend=False, plot_bgcolor='white', font=dict(color='black'))
st.plotly_chart(fig_target, use_container_width=True)
                    
                    if rec_summary is not None and not rec_summary.empty:
                        latest_rec = rec_summary.iloc[0]
                        rec_keys = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']
                        rec_vals = [latest_rec.get(k, 0) for k in rec_keys]
                        fig_rec = px.bar(x=rec_keys, y=rec_vals, title="分析師評級分佈", color=rec_keys,
                                         color_discrete_map={'strongBuy': 'green', 'buy': 'lightgreen', 'hold': 'grey', 'sell': 'pink', 'strongSell': 'red'})
                        fig_rec.update_layout(plot_bgcolor='white', font=dict(color='black'), height=300)
                        st.plotly_chart(fig_rec, use_container_width=True)
                    else:
                        st.info("暫無評級分佈數據")
                except Exception as e:
                    st.info("部分分析師數據無法顯示")
                            st.plotly_chart(fig_target, use_container_width=True)

except Exception as e:
st.error(f"分析師預估區塊錯誤: {e}")
@@ -939,56 +972,36 @@ def render_stock_strategy_page():
st.markdown('</div>', unsafe_allow_html=True)

def render_macro_page():
st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
st.subheader("📉 總經與風險指標 (Macro Risk)")
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📉 總經與風險指標 (Macro Risk)")
st.caption("市場恐慌指數 (VIX) 與 貪婪指數")

with st.spinner("正在計算總經風險指標..."):
macro_data = get_macro_data()

    
    with st.spinner("正在計算總經風險指標..."):
        macro_data = get_macro_data()
        
# [Safety Check] Ensure Close column exists and handle MultiIndex properly
try:
            # Check for data existence
            vix_data = macro_data.get('^VIX')
            gspc_data = macro_data.get('^GSPC')

            if vix_data is None or gspc_data is None or vix_data.empty or gspc_data.empty:
                st.error("無法取得 VIX 或 S&P 500 數據")
        try:
# macro_data is guaranteed to be (Ticker, Price) via get_macro_data
if '^VIX' not in macro_data.columns.get_level_values(0):
st.error("無法取得 VIX 數據")
return

            vix_series = vix_data['Close'].dropna()
            sp500_series = gspc_data['Close'].dropna()
                return

            if vix_series.empty:
                 st.error("VIX 數據為空")
                 return

vix_series = macro_data['^VIX']['Close'].dropna()
sp500_series = macro_data['^GSPC']['Close'].dropna()
f_g_score, v_val, r_val = calculate_fear_greed(vix_series.iloc[-1], sp500_series)

col1, col2 = st.columns([1, 1])
@@ -896,72 +981,69 @@ def render_macro_page():
st.info("💡 台灣景氣對策信號請參閱國發會")
st.link_button("👉 國發會查詢系統", "https://index.ndc.gov.tw/n/zh_tw/indicators")
st.caption("Fear & Greed 模型基於 VIX 與 RSI 加權計算。")
                
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
            st.markdown("#### VIX 波動率走勢 (1 Year)")
            fig_vix = px.line(vix_series, title="CBOE VIX Index")
            fig_vix.add_hline(y=20, line_dash="dash", line_color="red")
            fig_vix.update_layout(plot_bgcolor='white', font=dict(color='black'))
            st.plotly_chart(fig_vix, use_container_width=True)
            st.markdown('</div>', unsafe_allow_html=True)
            f_g_score, v_val, r_val = calculate_fear_greed(vix_series.iloc[-1], sp500_series)

except Exception as e:
st.error(f"數據處理錯誤: {e}")
return
            col1, col2 = st.columns([1, 1])
            with col1:
                plot_gauge(f_g_score)
                st.metric("VIX 恐慌指數", f"{v_val:.2f}")

            with col2:
                st.info("💡 台灣景氣對策信號請參閱國發會")
                st.link_button("👉 國發會查詢系統", "https://index.ndc.gov.tw/n/zh_tw/indicators")
                st.caption("Fear & Greed 模型基於 VIX 與 RSI 加權計算。")
        except Exception as e:
            st.error(f"數據處理錯誤: {e}")
            return

st.markdown('</div>', unsafe_allow_html=True)

@@ -1001,146 +1014,141 @@ def render_macro_page():
st.markdown('</div>', unsafe_allow_html=True)

def render_commodity_page():
st.subheader("🚢 原物料與航運 (Commodities)")
with st.spinner("正在獲取原物料行情..."):
comm_data = get_commodity_data()

    st.subheader("🚢 原物料與航運 (Commodities)")
    with st.spinner("正在獲取原物料行情..."):
        comm_data = get_commodity_data()
        
# 航運區塊
st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
st.markdown("#### ⚓ 航運指標 (Shipping)")
c1, c2 = st.columns([3, 1])
with c1:
            # Check if BDRY exists in top level columns (since we flattened or swapped)
            if 'BDRY' in comm_data.columns.get_level_values(0):
                 data = comm_data['BDRY']['Close'].dropna()
                 plot_line_chart(data, "BDI 替代指標 (BDRY ETF)", "#1f77b4")
            else:
                st.warning("無法取得 BDRY 數據")

        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### ⚓ 航運指標 (Shipping)")
        c1, c2 = st.columns([3, 1])
        with c1:
if 'BDRY' in comm_data.columns.levels[0]:
data = comm_data['BDRY']['Close'].dropna()
plot_line_chart(data, "BDI 替代指標 (BDRY ETF)", "#1f77b4")
with c2:
st.metric("BDI 狀態", "監控中")
st.link_button("查看 Investing.com", "https://www.investing.com/indices/baltic-dry")
st.markdown('</div>', unsafe_allow_html=True)
        with c2:
            st.metric("BDI 狀態", "監控中")
            st.link_button("查看 Investing.com", "https://www.investing.com/indices/baltic-dry")
        st.markdown('</div>', unsafe_allow_html=True)

# 能源區塊
st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
st.markdown("#### 🛢️ 能源與金屬 (Energy & Metals)")
c3, c4 = st.columns(2)
with c3:
            if 'CL=F' in comm_data.columns.get_level_values(0):
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### 🛢️ 能源與金屬 (Energy & Metals)")
        c3, c4 = st.columns(2)
        with c3:
if 'CL=F' in comm_data.columns.levels[0]:
data = comm_data['CL=F']['Close'].dropna()
plot_line_chart(data, "WTI 原油", "#ef4444")
with c4:
            if 'HG=F' in comm_data.columns.get_level_values(0):
                data = comm_data['CL=F']['Close'].dropna()
                plot_line_chart(data, "WTI 原油", "#ef4444")
        with c4:
if 'HG=F' in comm_data.columns.levels[0]:
data = comm_data['HG=F']['Close'].dropna()
plot_line_chart(data, "銅 (Copper)", "#10b981")
st.markdown('</div>', unsafe_allow_html=True)
                data = comm_data['HG=F']['Close'].dropna()
                plot_line_chart(data, "銅 (Copper)", "#10b981")
        st.markdown('</div>', unsafe_allow_html=True)

def render_liquidity_page():
st.header("💰 資金量體與籌碼戰情室")
    st.header("💰 資金量體與籌碼戰情室")

    # 手動輸入卡片 (使用 Session State)
# 手動輸入卡片
st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
with st.expander("🛠️ 關鍵數據輸入面板 (Input Panel)", expanded=True):
col_in1, col_in2, col_in3 = st.columns(3)
with col_in1:
st.markdown("**🇹🇼 貨幣供給**")
            st.number_input("M1B 年增率 (%)", step=0.01, key='m1b_val')
            st.number_input("M2 年增率 (%)", step=0.01, key='m2_val')
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    with st.expander("🛠️ 關鍵數據輸入面板 (Input Panel)", expanded=True):
        col_in1, col_in2, col_in3 = st.columns(3)
        with col_in1:
            st.markdown("**🇹🇼 貨幣供給**")
m1b_val = st.number_input("M1B 年增率 (%)", value=5.24, step=0.01)
m2_val = st.number_input("M2 年增率 (%)", value=5.44, step=0.01)
with col_in2:
st.markdown("**🇹🇼 信用交易**")
            st.number_input("融資維持率 (%)", step=0.1, key='margin_ratio')
        with col_in2:
            st.markdown("**🇹🇼 信用交易**")
margin_ratio = st.number_input("融資維持率 (%)", value=169.39, step=0.1)
with col_in3:
st.markdown("**🇺🇸 美股槓桿**")
            st.number_input("Margin Debt ($T)", step=0.01, key='us_margin_debt')
        with col_in3:
            st.markdown("**🇺🇸 美股槓桿**")
us_margin_debt = st.number_input("Margin Debt ($T)", value=1.21, step=0.01)
st.markdown('</div>', unsafe_allow_html=True)

# 結果卡片
@@ -970,62 +1052,49 @@ def render_liquidity_page():
col_res1, col_res2, col_res3 = st.columns(3)
    st.markdown('</div>', unsafe_allow_html=True)

with col_res1:
        gap = st.session_state['m1b_val'] - st.session_state['m2_val']
    # 結果卡片
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📊 籌碼水位診斷")
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
gap = m1b_val - m2_val
st.metric("資金剪刀差 (M1B - M2)", f"{gap:.2f}%", delta=gap)
st.caption("正值代表資金動能充沛")
        st.metric("資金剪刀差 (M1B - M2)", f"{gap:.2f}%", delta=gap)
        st.caption("正值代表資金動能充沛")

with col_res2:
        val = st.session_state['margin_ratio']
        status_margin = "🟢 安全" if val > 160 else "🔴 危險"
        st.metric("融資維持率", f"{val}%", delta=status_margin, delta_color="off")
    with col_res2:
status_margin = "🟢 安全" if margin_ratio > 160 else "🔴 危險"
st.metric("融資維持率", f"{margin_ratio}%", delta=status_margin, delta_color="off")

with col_res3:
        st.metric("美股融資餘額", f"${st.session_state['us_margin_debt']}T")
    with col_res3:
st.metric("美股融資餘額", f"${us_margin_debt}T")
st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# OBV 分析
st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
st.subheader("🌊 量價趨勢 (S&P 500)")
with st.spinner("計算 OBV 中..."):
macro_data = get_macro_data()
    # OBV 分析
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("🌊 量價趨勢 (S&P 500)")
    with st.spinner("計算 OBV 中..."):
        macro_data = get_macro_data()
sp500 = macro_data['^GSPC'].copy()
sp500['Daily_Ret'] = sp500['Close'].pct_change()
sp500['Direction'] = np.where(sp500['Daily_Ret'] >= 0, 1, -1)
sp500['OBV'] = (sp500['Volume'] * sp500['Direction']).cumsum()

        if '^GSPC' in macro_data.columns.get_level_values(0):
            sp500 = macro_data['^GSPC'].copy()
            if not sp500.empty:
                sp500['Daily_Ret'] = sp500['Close'].pct_change()
                sp500['Direction'] = np.where(sp500['Daily_Ret'] >= 0, 1, -1)
                sp500['OBV'] = (sp500['Volume'] * sp500['Direction']).cumsum()
                
                # 正規化繪圖
                norm_price = (sp500['Close'] - sp500['Close'].min()) / (sp500['Close'].max() - sp500['Close'].min())
                norm_obv = (sp500['OBV'] - sp500['OBV'].min()) / (sp500['OBV'].max() - sp500['OBV'].min())
                
                df_chart = pd.DataFrame({'S&P 500': norm_price, 'OBV (資金)': norm_obv})
                st.line_chart(df_chart)
            else:
                 st.warning("無足夠數據繪製 OBV")
        else:
            st.warning("無法取得 S&P 500 數據")
        
# 正規化繪圖
norm_price = (sp500['Close'] - sp500['Close'].min()) / (sp500['Close'].max() - sp500['Close'].min())
norm_obv = (sp500['OBV'] - sp500['OBV'].min()) / (sp500['OBV'].max() - sp500['OBV'].min())

df_chart = pd.DataFrame({'S&P 500': norm_price, 'OBV (資金)': norm_obv})
st.line_chart(df_chart)
st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. 主程式 ---
def main():
if 'last_update' not in st.session_state:
st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Handle Sidebar History Selection
    selected_ticker = ""
    if 'history_box' in st.session_state and st.session_state['history_box']:
         selected_ticker = st.session_state['history_box']

if "總經" in market_mode:
render_macro_page()
elif "原物料" in market_mode:
render_commodity_page()
elif "資金" in market_mode:
render_liquidity_page()
elif "個股" in market_mode:
        render_stock_strategy_page(initial_ticker=selected_ticker)
    if 'last_update' not in st.session_state:
        st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if "總經" in market_mode:
        render_macro_page()
    elif "原物料" in market_mode:
        render_commodity_page()
    elif "資金" in market_mode:
        render_liquidity_page()
    elif "個股" in market_mode:
render_stock_strategy_page()
else:
# 市場概況 (Treemap)
with st.spinner(f'正在載入 {market_mode} 數據...'):
    else:
        # 市場概況 (Treemap)
        with st.spinner(f'正在載入 {market_mode} 數據...'):
            if "S&P 500" in market_mode:
                base_df = get_sp500_constituents()
                title_prefix = "S&P 500"
            else:
                base_df = get_tw_constituents()
                title_prefix = "TWSE"

            if base_df.empty: st.error("無法取得清單"); return
            tickers_list = base_df['Ticker'].tolist()
            
            market_caps = fetch_market_caps(tickers_list)
            history_data = fetch_price_history(tickers_list)
            
            if history_data.empty: st.error("無法取得股價"); return
            final_df = process_data_for_periods(base_df, history_data, market_caps)
            
        if final_df.empty: st.warning("無數據"); return
        final_df = final_df[final_df['Market Cap'] > 0]

        st.subheader(f"🗺️ 市場熱力圖 ({title_prefix})")
        
        tab_1d, tab_1w, tab_1m, tab_ytd = st.tabs(["1 Day", "1 Week", "1 Month", "YTD"])
        
        with tab_1d:
            plot_treemap(final_df, '1D Change', f'{title_prefix} (1 Day)', [-4, 4])
        with tab_1w:
            plot_treemap(final_df, '1W Change', f'{title_prefix} (1 Week)', [-8, 8])
        with tab_1m:
            plot_treemap(final_df, '1M Change', f'{title_prefix} (1 Month)', [-15, 15])
        with tab_ytd:
            plot_treemap(final_df, 'YTD Change', f'{title_prefix} (YTD)', [-40, 40])
    
    st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    main()
