# ----------------------------------------------------------------------
# 股市戰情室 - 旗艦版 (含資金籌碼、總經、與 個股/ETF 深度技術分析)
# Style: Reverted to Clean Light Theme
# Optimization: 
#   1. Parallel Fetching for Fundamentals (Significant speedup for single stock)
#   2. Vectorized Calculation for Market Dashboard (Speedup for S&P 500)
#   3. Reduced data fetch period for Macro (1y)
# Features: Robust Fixes for yfinance MultiIndex retained
# ----------------------------------------------------------------------

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures
from datetime import datetime, timedelta

# --- 1. Streamlit 頁面設定 ---
st.set_page_config(
    page_title="股市全方位戰情室", 
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS 亮色簡潔風格注入 ---
st.markdown("""
<style>
    /* 引入現代字體 Inter */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"]  {
        font-family: 'Inter', sans-serif;
    }

    /* 背景微調 - 亮色系 */
    .stApp {
        background-color: #f8f9fa;
    }

    /* 頂部標題區塊調整 */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    /* --- Dashboard Card 風格 (亮色卡片) --- */
    .dashboard-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* 強制美化 st.metric 原生元件 (亮色版) */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        padding: 15px 20px;
        border-radius: 10px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    [data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        border-color: #2b7de9;
    }

    [data-testid="stMetricLabel"] {
        font-size: 14px;
        color: #666;
        font-weight: 600;
    }

    [data-testid="stMetricValue"] {
        font-size: 26px;
        color: #1f2937;
        font-weight: 700;
    }

    /* 標題樣式 */
    h1, h2, h3 {
        color: #111827;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    
    h3 {
        margin-top: 1rem;
        border-left: 5px solid #2b7de9;
        padding-left: 10px;
        font-size: 1.25rem;
    }

    /* 側邊欄樣式優化 */
    [data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    /* 按鈕樣式 */
    .stButton button {
        border-radius: 8px;
        font-weight: 600;
    }

    /* 連結按鈕 */
    .stLinkButton a {
        background-color: #f3f4f6;
        color: #374151;
        border: 1px solid #d1d5db;
        border-radius: 6px;
        padding: 5px 10px;
        font-size: 0.9em;
        text-decoration: none;
        transition: all 0.2s;
    }
    .stLinkButton a:hover {
        background-color: #e5e7eb;
        color: #111827;
    }

    .bullish { color: #10b981; font-weight: bold; }
    .bearish { color: #ef4444; font-weight: bold; }
    .neutral { color: #f59e0b; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. 側邊欄控制 ---
with st.sidebar:
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
            "📉 總經與風險指標 (Macro)"
        ]
    )
    
    st.markdown("---")
    if st.button('🔄 強制更新數據', type="primary", use_container_width=True):
        st.cache_data.clear()
        st.session_state.pop('last_update', None)
        st.rerun()

    if 'last_update' in st.session_state:
        st.caption(f"Last Update: {st.session_state['last_update']}")

st.title(f"📊 {market_mode}")
st.markdown("---")

# --- 3. 核心數據函數 (股票) ---

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
        rename_map = {'Symbol': 'Ticker', 'GICS Sector': 'Sector', 'GICS Sub-Industry': 'Industry'}
        df = df.rename(columns=rename_map)
        df['Ticker'] = df['Ticker'].str.replace('.', '-', regex=False)
        if 'Industry' not in df.columns:
            df['Industry'] = df['Sector'] if 'Sector' in df.columns else 'Unknown'
        return df
    except Exception:
        return pd.DataFrame()

def fetch_single_cap(ticker):
    try:
        info = yf.Ticker(ticker).fast_info
        return ticker, info['market_cap']
    except:
        return ticker, 0

@st.cache_data(ttl=24 * 3600)
def fetch_market_caps(tickers):
    caps = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        results = executor.map(fetch_single_cap, tickers)
        for ticker, cap in results:
            caps[ticker] = cap
    return caps

@st.cache_data(ttl=21600) 
def fetch_price_history(tickers, period="1y"):
    """
    下載大量股票歷史數據
    """
    try:
        data = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True, progress=False)
        return data
    except Exception:
        return pd.DataFrame()

# --- 4. 總經/原物料/資金 數據獲取 ---
@st.cache_data(ttl=3600)
def get_macro_data():
    """
    [Critical Fix] 確保回傳的 DataFrame 結構一定是 (Ticker, Price)
    """
    tickers = ["^VIX", "^GSPC"]
    # 縮短獲取時間為 1y，加速載入
    data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, progress=False)
    
    # [Robust Logic] 檢查 Close 到底在哪一層
    if isinstance(data.columns, pd.MultiIndex):
        level0 = data.columns.get_level_values(0)
        # 如果第一層發現 'Close'，代表結構是 (Price, Ticker)，需要交換
        if 'Close' in level0:
            data = data.swaplevel(0, 1, axis=1)
            data.sort_index(axis=1, inplace=True)
            
    return data

@st.cache_data(ttl=3600)
def get_commodity_data():
    tickers = ["BDRY", "DBC", "HG=F", "CL=F", "GC=F"]
    data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, progress=False)
    
    # 同樣的保護機制
    if isinstance(data.columns, pd.MultiIndex):
        level0 = data.columns.get_level_values(0)
        if 'Close' in level0:
            data = data.swaplevel(0, 1, axis=1)
            data.sort_index(axis=1, inplace=True)
            
    return data

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period="2y"):
    """
    獲取單一股票的詳細數據 (針對個股分析頁面)
    """
    try:
        data = yf.download(ticker, period=period, auto_adjust=True, progress=False)
        
        if data.empty:
            return pd.DataFrame()

        # 1. 處理 MultiIndex
        if isinstance(data.columns, pd.MultiIndex):
            target_level = None
            found = False
            for i in range(data.columns.nlevels):
                if 'Close' in data.columns.get_level_values(i):
                    target_level = i
                    found = True
                    break
            
            if found:
                data.columns = data.columns.get_level_values(target_level)
            else:
                for i in range(data.columns.nlevels):
                    if 'Adj Close' in data.columns.get_level_values(i):
                        target_level = i
                        data.columns = data.columns.get_level_values(target_level)
                        break
                if not found and data.columns.nlevels > 1:
                     data.columns = data.columns.droplevel(0)

        # 2. 欄位標準化
        if 'Adj Close' in data.columns and 'Close' not in data.columns:
            data.rename(columns={'Adj Close': 'Close'}, inplace=True)

        # 3. 最終檢查
        if 'Close' in data.columns:
            data = data.dropna(subset=['Close'])
            return data
        else:
            return pd.DataFrame()

    except Exception as e:
        print(f"Error fetching {ticker}: {e}")
        return pd.DataFrame()

# [OPTIMIZATION] 平行處理 Helper Functions
def _fetch_info_helper(stock):
    try:
        return stock.info
    except:
        return {}

def _fetch_cashflow_helper(stock):
    try:
        return stock.cashflow
    except:
        return pd.DataFrame()

def _fetch_balance_sheet_helper(stock):
    try:
        return stock.balance_sheet
    except:
        return pd.DataFrame()

def _fetch_estimates_helper(stock):
    try:
        return stock.earnings_estimate, stock.eps_trend, stock.recommendations_summary
    except:
        return None, None, None

@st.cache_data(ttl=12 * 3600)
def get_fundamentals(ticker):
    """
    嘗試獲取基本面數據 (Extreme Robustness & Speed)
    使用 ThreadPoolExecutor 進行平行抓取
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
        'RecSummary': None
    }
    
    try:
        stock = yf.Ticker(ticker)
        
        # [OPTIMIZATION] 平行抓取所有資料源
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_info = executor.submit(_fetch_info_helper, stock)
            future_cf = executor.submit(_fetch_cashflow_helper, stock)
            future_bs = executor.submit(_fetch_balance_sheet_helper, stock)
            future_est = executor.submit(_fetch_estimates_helper, stock)
            
            info = future_info.result()
            cf = future_cf.result()
            bs = future_bs.result()
            est_data = future_est.result() # returns tuple (earnings_estimate, eps_trend, rec_summary)

        # --- A. 處理 Info ---
        # 轉成全小寫 key 的 map
        info_lower = {k.lower(): v for k, v in info.items()} if info else {}
        
        def get_val(keys_list, default=None):
            for k in keys_list:
                if k.lower() in info_lower:
                    return info_lower[k.lower()]
            return default

        result['MarketCap'] = get_val(['marketCap'])
        result['GrossMargin'] = get_val(['grossMargins', 'grossMargin'])
        result['OperatingMargin'] = get_val(['operatingMargins', 'operatingMargin'])
        result['EarningsGrowth'] = get_val(['earningsGrowth'])
        result['TrailingPE'] = get_val(['trailingPE'])
        result['ForwardPE'] = get_val(['forwardPE'])
        result['PEG'] = get_val(['pegRatio'])
        result['ForwardEPS'] = get_val(['forwardEps', 'forwardEPS'])
        
        # 補救 Forward EPS
        if result['ForwardEPS'] is None and result['ForwardPE']:
             curr_price = get_val(['currentPrice', 'regularMarketPrice', 'ask', 'bid'])
             if curr_price:
                 result['ForwardEPS'] = curr_price / result['ForwardPE']

        # 補救 PEG
        if result['PEG'] is None and result['TrailingPE'] and result['EarningsGrowth']:
             if result['EarningsGrowth'] > 0:
                result['PEG'] = result['TrailingPE'] / (result['EarningsGrowth'] * 100)

        result['TargetMean'] = get_val(['targetMeanPrice'])
        result['TargetHigh'] = get_val(['targetHighPrice'])
        result['TargetLow'] = get_val(['targetLowPrice'])
        result['Recommendation'] = get_val(['recommendationKey'])
        result['NumAnalysts'] = get_val(['numberOfAnalystOpinions'])

        # --- B. 處理現金流 ---
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

        # --- C. 處理資產負債表 ---
        if not bs.empty:
            try:
                for idx in bs.index:
                    idx_str = str(idx).lower()
                    if ('contract' in idx_str and 'liabilities' in idx_str) or \
                       ('deferred' in idx_str and 'revenue' in idx_str):
                        result['ContractLiabilities'] = bs.loc[idx].iloc[0]
                        break
            except: pass

        # --- D. 處理分析師預估 ---
        if est_data:
            result['EarningsEst'] = est_data[0]
            result['EPSTrend'] = est_data[1]
            result['RecSummary'] = est_data[2]

    except Exception as e:
        print(f"Fundamentals critical error for {ticker}: {e}")
    
    return result

def check_ticker_validity(ticker):
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
    """
    [OPTIMIZATION] 向量化運算取代迴圈，大幅提升大量股票的處理速度
    """
    if history_data.empty:
        return pd.DataFrame()

    # 1. 確保 Close 數據被提取出來並正規化為 (Date, Ticker) 的 DataFrame
    closes = pd.DataFrame()
    
    if isinstance(history_data.columns, pd.MultiIndex):
        level0 = history_data.columns.get_level_values(0)
        # 判斷結構是 (Price, Ticker) 還是 (Ticker, Price)
        if 'Close' in level0:
            # 結構: (Price, Ticker) -> 直接取 Close 層
            closes = history_data['Close']
        else:
            # 結構: (Ticker, Price) -> 需要 xs 或 swaplevel
            # 檢查 level 1 是否有 Close
            level1 = history_data.columns.get_level_values(1)
            if 'Close' in level1:
                closes = history_data.xs('Close', level=1, axis=1)
            else:
                # 嘗試 Adj Close
                if 'Adj Close' in level1:
                    closes = history_data.xs('Adj Close', level=1, axis=1)
    else:
        # 單層 Index (可能是單一股票，或已處理過)
        if 'Close' in history_data.columns:
            closes = history_data[['Close']] # 轉為 DataFrame
    
    if closes.empty:
        return pd.DataFrame()

    # 2. 向量化計算漲跌幅 (Vectorized Calculations)
    # 使用 ffill 處理中間的 NaN，避免計算斷掉
    closes = closes.ffill()
    
    # 確保最後一行有效 (有些股票可能當天還沒開盤或停牌)
    # 這裡不做太嚴格的 dropna，保留大盤整體數據
    
    try:
        # 取出最新的價格 (Series)
        current_prices = closes.iloc[-1]
        
        # 1D Change
        res_1d = closes.pct_change(1).iloc[-1] * 100
        
        # 1W (5 days)
        res_1w = closes.pct_change(5).iloc[-1] * 100
        
        # 1M (21 days)
        res_1m = closes.pct_change(21).iloc[-1] * 100
        
        # YTD / 1Y (Roll) - 使用第一筆與最後一筆比較 (近似 YTD)
        # 注意：如果資料不足 1 年，iloc[0] 就是該股最早的資料
        res_ytd = ((closes.iloc[-1] - closes.iloc[0]) / closes.iloc[0]) * 100
        
        # 3. 組合結果
        metrics_df = pd.DataFrame({
            'Ticker': current_prices.index,
            'Close': current_prices.values,
            '1D Change': res_1d.values,
            '1W Change': res_1w.values,
            '1M Change': res_1m.values,
            'YTD Change': res_ytd.values
        })
        
        # 4. 合併基本資料 (Sector, Name, Market Cap)
        # 確保 Ticker 欄位型態一致
        base_df['Ticker'] = base_df['Ticker'].astype(str)
        metrics_df['Ticker'] = metrics_df['Ticker'].astype(str)
        
        merged_df = pd.merge(base_df, metrics_df, on='Ticker', how='inner')
        
        # 填入 Market Cap
        merged_df['Market Cap'] = merged_df['Ticker'].map(market_caps).fillna(0)
        
        # 過濾無效數據
        merged_df = merged_df.dropna(subset=['Close'])
        merged_df = merged_df[merged_df['Market Cap'] > 0]
        
        return merged_df

    except Exception as e:
        print(f"Vectorization error: {e}")
        return pd.DataFrame()

# --- 7. 繪圖函數 ---
def plot_treemap(df, change_col, title, color_range):
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
    fig.update_layout(height=600, margin=dict(t=20, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

def plot_gauge(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = score,
        domain = {'x': [0, 1], 'y': [0, 1]}, 
        title = {'text': "市場情緒 (Proxy)", 'font': {'size': 18}},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1}, 
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
    fig.update_layout(
        height=300, 
        margin=dict(t=60, b=20, l=30, r=30)
    )
    st.plotly_chart(fig, use_container_width=True)

def plot_line_chart(data, title, color):
    fig = px.line(data, title=title)
    fig.update_traces(line_color=color, line_width=2)
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20), xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

def plot_tech_chart(df, ticker, title):
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(f"{title} 價格趨勢", "成交量", "RSI", "MACD")
    )

    # 1. 主圖：K線 + MA
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA20'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='blue', width=1.5), name='MA50'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], line=dict(color='red', width=2), name='MA200'), row=1, col=1)
    
    # 布林通道
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='gray', width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='gray', width=0), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='BB Band'), row=1, col=1)

    # 2. 成交量
    colors = ['green' if o >= c else 'red' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

    # 3. RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)

    # 4. MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue', width=1.5), name='MACD'), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], line=dict(color='orange', width=1.5), name='Signal'), row=4, col=1)
    colors_hist = ['green' if v >= 0 else 'red' for v in df['MACD_Hist']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_hist, name='Hist'), row=4, col=1)

    fig.update_layout(
        height=900, 
        xaxis_rangeslider_visible=False,
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        margin=dict(t=30, b=30)
    )
    fig.update_xaxes(showgrid=True, gridcolor='#f0f0f0')
    fig.update_yaxes(showgrid=True, gridcolor='#f0f0f0')
    
    st.plotly_chart(fig, use_container_width=True)

# --- 8. 頁面渲染邏輯 ---

def render_stock_strategy_page():
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
            
            df = calculate_indicators(df)
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            # --- A. 狀態儀表板 ---
            st.markdown("### 1. 即時技術狀態 (Technical Status)")
            m1, m2, m3, m4 = st.columns(4)
            
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

            # --- 基本面快照區塊 ---
            try:
                st.markdown("### 2. 基本面體質快照 (Fundamental Snapshot)")
                f1, f2, f3, f4 = st.columns(4)
                
                fwd_eps = fund_data.get('ForwardEPS')
                f1.metric("Forward EPS", f"${fwd_eps:.2f}" if fwd_eps is not None else "N/A")

                pe = fund_data.get('TrailingPE')
                f2.metric("P/E (本益比)", f"{pe:.1f}x" if pe is not None else "N/A")

                peg = fund_data.get('PEG')
                peg_est = False
                if peg is None:
                    pe_val = fund_data.get('TrailingPE')
                    growth = fund_data.get('EarningsGrowth')
                    if pe_val and growth and growth > 0:
                        peg = pe_val / (growth * 100)
                        peg_est = True
                
                peg_str = f"{peg:.2f}" if peg is not None else "N/A"
                f3.metric("PEG (Est.)" if peg_est else "PEG", peg_str)

                p_fcf = fund_data.get('P/FCF')
                f4.metric("P/FCF", f"{p_fcf:.1f}x" if p_fcf is not None else "N/A")

                st.write("")
                f5, f6, f7, f8 = st.columns(4)

                gm = fund_data.get('GrossMargin')
                f5.metric("毛利率", f"{gm*100:.1f}%" if gm is not None else "N/A")

                om = fund_data.get('OperatingMargin')
                f6.metric("營益率", f"{om*100:.1f}%" if om is not None else "N/A")
                    
                cl = fund_data.get('ContractLiabilities')
                val_str = "N/A"
                if cl is not None:
                    val_str = f"${cl/1e9:.1f}B" if cl > 1e9 else f"${cl/1e6:.1f}M"
                f7.metric("合約負債 (RPO)", val_str)
                
                f8.metric("資料日期", datetime.now().strftime("%m-%d"))
                st.write("")

            except Exception as e:
                st.error(f"基本面數據渲染錯誤: {e}")

            # --- 3. 分析師 EPS 預估 ---
            try:
                est_df = fund_data.get('EarningsEst')
                trend_df = fund_data.get('EPSTrend')
                rec_summary = fund_data.get('RecSummary') # 評級分佈 DataFrame
                
                has_est_data = est_df is not None and not est_df.empty
                has_trend_data = trend_df is not None and not trend_df.empty
                has_rec_data = rec_summary is not None and not rec_summary.empty
                
                target_mean = fund_data.get('TargetMean')
                recommendation = fund_data.get('Recommendation')
                
                with st.expander("📊 點擊展開：分析師看法 (Analyst Estimates & Consensus)", expanded=True):
                    
                    tabs = []
                    if has_est_data: tabs.append("未來預估")
                    if has_trend_data: tabs.append("修正趨勢")
                    if has_rec_data: tabs.append("評級分佈")
                    
                    if tabs:
                        tab_objs = st.tabs(tabs)
                        
                        # 1. 未來預估
                        if has_est_data:
                            with tab_objs[tabs.index("未來預估")]:
                                try:
                                    plot_data = est_df.copy()
                                    plot_data.index = plot_data.index.astype(str).str.lower()
                                    idx_map = {}
                                    for idx in plot_data.index:
                                        if 'avg' in idx: idx_map['avg'] = idx
                                        elif 'low' in idx: idx_map['low'] = idx
                                        elif 'high' in idx: idx_map['high'] = idx
                                    
                                    target_cols = [c for c in plot_data.columns if 'q' in c] or [c for c in plot_data.columns if 'y' in c]
                                    
                                    if 'avg' in idx_map and target_cols:
                                        rows = [idx_map['avg']]
                                        if 'low' in idx_map: rows.append(idx_map['low'])
                                        if 'high' in idx_map: rows.append(idx_map['high'])
                                        plot_df = plot_data.loc[rows, target_cols].T.reset_index()
                                        rename_map = {'index': 'Period', idx_map['avg']: 'Average'}
                                        if 'low' in idx_map: rename_map[idx_map['low']] = 'Low'
                                        if 'high' in idx_map: rename_map[idx_map['high']] = 'High'
                                        plot_df = plot_df.rename(columns=rename_map)
                                        if 'Low' not in plot_df.columns: plot_df['Low'] = plot_df['Average']
                                        if 'High' not in plot_df.columns: plot_df['High'] = plot_df['Average']
                                        
                                        fig_est = px.bar(plot_df, x='Period', y='Average', title="分析師 EPS 預估", text_auto='.2f', color='Average', color_continuous_scale='Blues')
                                        fig_est.update_traces(error_y=dict(type='data', array=plot_df['High']-plot_df['Average'], arrayminus=plot_df['Average']-plot_df['Low'], visible=True))
                                        fig_est.update_layout(plot_bgcolor='white')
                                        st.plotly_chart(fig_est, use_container_width=True)
                                    else:
                                        st.info("無季度數據")
                                except: st.info("繪圖失敗")

                        # 2. 修正趨勢
                        if has_trend_data:
                            with tab_objs[tabs.index("修正趨勢")]:
                                try:
                                    trend_plot = trend_df.T
                                    time_order = ['90daysAgo', '60daysAgo', '30daysAgo', '7daysAgo', 'current']
                                    valid_order = [t for t in time_order if t in trend_plot.index]
                                    if valid_order:
                                        trend_plot = trend_plot.loc[valid_order]
                                        fig_trend = go.Figure()
                                        for col in trend_plot.columns:
                                            fig_trend.add_trace(go.Scatter(x=trend_plot.index, y=trend_plot[col], mode='lines+markers', name=col))
                                        fig_trend.update_layout(title="EPS 預估修正趨勢", plot_bgcolor='white')
                                        st.plotly_chart(fig_trend, use_container_width=True)
                                except: st.info("繪圖失敗")

                        # 3. 評級分佈 (新增)
                        if has_rec_data:
                            with tab_objs[tabs.index("評級分佈")]:
                                try:
                                    latest_rec = rec_summary.iloc[0] # Series
                                    rec_keys = ['strongBuy', 'buy', 'hold', 'sell', 'strongSell']
                                    rec_vals = [latest_rec.get(k, 0) for k in rec_keys]
                                    
                                    fig_rec = px.bar(x=rec_keys, y=rec_vals, title="分析師評級分佈 (Consensus)", 
                                                     labels={'x': 'Rating', 'y': 'Count'}, color=rec_keys,
                                                     color_discrete_map={'strongBuy': 'green', 'buy': 'lightgreen', 'hold': 'grey', 'sell': 'pink', 'strongSell': 'red'})
                                    fig_rec.update_layout(plot_bgcolor='white')
                                    st.plotly_chart(fig_rec, use_container_width=True)
                                except: st.info("繪圖失敗")

                    else:
                        if target_mean is None:
                            st.info("⚠️ 暫無詳細分析師數據。")

                    # 目標價顯示 (Always show if available)
                    if target_mean is not None:
                        st.markdown("#### 🎯 目標價與評級 (Price Targets)")
                        
                        col_t1, col_t2 = st.columns([1, 2])
                        with col_t1:
                            st.metric("分析師評級", str(recommendation).upper().replace('_', ' ') if recommendation else "N/A")
                            st.metric("平均目標價", f"${target_mean}", delta=f"{((target_mean - last_row['Close'])/last_row['Close']*100):.1f}%" if last_row['Close'] else None)
                            if fund_data.get('NumAnalysts'):
                                st.caption(f"基於 {fund_data['NumAnalysts']} 位分析師")

                        with col_t2:
                            current_price = last_row['Close']
                            low_target = fund_data.get('TargetLow', current_price * 0.9)
                            high_target = fund_data.get('TargetHigh', current_price * 1.1)
                            
                            fig_target = go.Figure()
                            fig_target.add_trace(go.Bar(y=['Price'], x=[low_target], name='Low', orientation='h', marker_color='#ff4b4b'))
                            fig_target.add_trace(go.Bar(y=['Price'], x=[target_mean - low_target], name='Mean', orientation='h', marker_color='#2b7de9', base=low_target))
                            fig_target.add_trace(go.Bar(y=['Price'], x=[high_target - target_mean], name='High', orientation='h', marker_color='#008000', base=target_mean))
                            fig_target.add_vline(x=current_price, line_width=3, line_dash="dash", line_color="black", annotation_text="Now")
                            
                            fig_target.update_layout(barmode='stack', title="目標價區間", height=200, margin=dict(l=20, r=20, t=30, b=20), showlegend=False, plot_bgcolor='white')
                            st.plotly_chart(fig_target, use_container_width=True)

            except Exception as e:
                st.error(f"分析師預估區塊錯誤: {e}")

            # --- B. 圖表區域 ---
            st.markdown("### 3. 技術分析圖表")
            plot_tech_chart(df, ticker, ticker)

            # --- C. 策略檢查清單 ---
            st.markdown("---")
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
                st.markdown("#### 🔍 趨勢與型態")
                ma_bullish = last_row['MA20'] > last_row['MA50'] > last_row['MA200']
                st.markdown(f"- **均線排列**: {'✅ 多頭' if ma_bullish else '⚠️ 糾結/空頭'}")
                
                dist_ma200 = (last_row['Close'] - last_row['MA200']) / last_row['MA200'] * 100
                st.markdown(f"- **乖離率**: {dist_ma200:.1f}%")
                
                recent_high = df['High'].tail(60).max()
                recent_low = df['Low'].tail(60).min()
                st.markdown(f"- **區間 (60日)**: ${recent_low:.0f} ~ ${recent_high:.0f}")
                st.markdown('</div>', unsafe_allow_html=True)

            with c2:
                st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
                st.markdown("#### 🛡️ 風險與建議")
                
                price_high_recent = df['Close'].tail(20).max()
                rsi_high_recent = df['RSI'].tail(20).max()
                price_high_prev = df['Close'].iloc[-60:-20].max()
                rsi_high_prev = df['RSI'].iloc[-60:-20].max()
                divergence = "無明顯背離"
                if price_high_recent > price_high_prev and rsi_high_recent < rsi_high_prev:
                    divergence = "🚨 頂部背離 (Bearish Divergence)"
                st.markdown(f"- **背離訊號**: {divergence}")
                
                if trend_status.startswith("🚀") and rsi_val < 70 and macd_val > 0:
                    st.success("評語：強勢多頭，沿 MA20 操作。")
                elif rsi_val > 75:
                    st.warning("評語：趨勢向上但超買，勿追高。")
                elif trend_status.startswith("🐻"):
                    st.error("評語：空頭走勢，保守觀望。")
                else:
                    st.info("評語：區間震盪，等待突破。")
                st.markdown('</div>', unsafe_allow_html=True)

def render_macro_page():
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📉 總經與風險指標 (Macro Risk)")
    st.caption("市場恐慌指數 (VIX) 與 貪婪指數")
    
    with st.spinner("正在計算總經風險指標..."):
        macro_data = get_macro_data()
        
        # [Safety Check] Ensure Close column exists and handle MultiIndex properly
        try:
            # macro_data is guaranteed to be (Ticker, Price) via get_macro_data
            if '^VIX' not in macro_data.columns.get_level_values(0):
                st.error("無法取得 VIX 數據")
                return
            
            vix_series = macro_data['^VIX']['Close'].dropna()
            sp500_series = macro_data['^GSPC']['Close'].dropna()
            f_g_score, v_val, r_val = calculate_fear_greed(vix_series.iloc[-1], sp500_series)
            
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

    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.markdown("#### VIX 波動率走勢 (1 Year)")
    fig_vix = px.line(vix_series, title="CBOE VIX Index")
    fig_vix.add_hline(y=20, line_dash="dash", line_color="red")
    fig_vix.update_layout(plot_bgcolor='white')
    st.plotly_chart(fig_vix, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def render_commodity_page():
    st.subheader("🚢 原物料與航運 (Commodities)")
    with st.spinner("正在獲取原物料行情..."):
        comm_data = get_commodity_data()
        
        # 航運區塊
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

        # 能源區塊
        st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
        st.markdown("#### 🛢️ 能源與金屬 (Energy & Metals)")
        c3, c4 = st.columns(2)
        with c3:
            if 'CL=F' in comm_data.columns.levels[0]:
                data = comm_data['CL=F']['Close'].dropna()
                plot_line_chart(data, "WTI 原油", "#ef4444")
        with c4:
            if 'HG=F' in comm_data.columns.levels[0]:
                data = comm_data['HG=F']['Close'].dropna()
                plot_line_chart(data, "銅 (Copper)", "#10b981")
        st.markdown('</div>', unsafe_allow_html=True)

def render_liquidity_page():
    st.header("💰 資金量體與籌碼戰情室")

    # 手動輸入卡片
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    with st.expander("🛠️ 關鍵數據輸入面板 (Input Panel)", expanded=True):
        col_in1, col_in2, col_in3 = st.columns(3)
        with col_in1:
            st.markdown("**🇹🇼 貨幣供給**")
            m1b_val = st.number_input("M1B 年增率 (%)", value=5.24, step=0.01)
            m2_val = st.number_input("M2 年增率 (%)", value=5.44, step=0.01)
        with col_in2:
            st.markdown("**🇹🇼 信用交易**")
            margin_ratio = st.number_input("融資維持率 (%)", value=169.39, step=0.1)
        with col_in3:
            st.markdown("**🇺🇸 美股槓桿**")
            us_margin_debt = st.number_input("Margin Debt ($T)", value=1.21, step=0.01)
    st.markdown('</div>', unsafe_allow_html=True)

    # 結果卡片
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("📊 籌碼水位診斷")
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        gap = m1b_val - m2_val
        st.metric("資金剪刀差 (M1B - M2)", f"{gap:.2f}%", delta=gap)
        st.caption("正值代表資金動能充沛")

    with col_res2:
        status_margin = "🟢 安全" if margin_ratio > 160 else "🔴 危險"
        st.metric("融資維持率", f"{margin_ratio}%", delta=status_margin, delta_color="off")

    with col_res3:
        st.metric("美股融資餘額", f"${us_margin_debt}T")
    st.markdown('</div>', unsafe_allow_html=True)

    # OBV 分析
    st.markdown('<div class="dashboard-card">', unsafe_allow_html=True)
    st.subheader("🌊 量價趨勢 (S&P 500)")
    with st.spinner("計算 OBV 中..."):
        macro_data = get_macro_data()
        sp500 = macro_data['^GSPC'].copy()
        sp500['Daily_Ret'] = sp500['Close'].pct_change()
        sp500['Direction'] = np.where(sp500['Daily_Ret'] >= 0, 1, -1)
        sp500['OBV'] = (sp500['Volume'] * sp500['Direction']).cumsum()
        
        # 正規化繪圖
        norm_price = (sp500['Close'] - sp500['Close'].min()) / (sp500['Close'].max() - sp500['Close'].min())
        norm_obv = (sp500['OBV'] - sp500['OBV'].min()) / (sp500['OBV'].max() - sp500['OBV'].min())
        
        df_chart = pd.DataFrame({'S&P 500': norm_price, 'OBV (資金)': norm_obv})
        st.line_chart(df_chart)
    st.markdown('</div>', unsafe_allow_html=True)

# --- 9. 主程式 ---
def main():
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
