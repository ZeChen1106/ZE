# ----------------------------------------------------------------------
# 股市戰情室 - 旗艦版 (含資金籌碼、總經、與 個股/ETF 深度技術分析)
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
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    h3 { margin-top: 2rem; border-bottom: 2px solid #f0f2f6; padding-bottom: 0.5rem; font-family: 'Arial Black', sans-serif; }
    .metric-card {
        background-color: #f9f9f9;
        border-left: 5px solid #2b7de9;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    .metric-title { font-size: 16px; color: #555; }
    .metric-value { font-size: 24px; font-weight: bold; color: #333; }
    .stLinkButton { text-decoration: none; }
    .analysis-box {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        padding: 15px;
        background-color: #ffffff;
        margin-bottom: 15px;
    }
    .bullish { color: #008000; font-weight: bold; }
    .bearish { color: #ff4b4b; font-weight: bold; }
    .neutral { color: #ffa500; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

# --- 2. 側邊欄控制 ---
st.sidebar.header("⚙️ 戰情控制台")
market_mode = st.sidebar.radio(
    "📊 選擇儀表板",
    [
        "🇺🇸 美股 S&P 500", 
        "🇹🇼 台股權值股 (TWSE)", 
        "🔎 個股技術戰略 (Stock Strategy)",  # 更新名稱
        "💰 資金與籌碼 (Liquidity)",
        "🚢 原物料與航運 (Commodities)",
        "📉 總經與風險指標 (Macro)"
    ]
)

if st.sidebar.button('🔄 強制更新數據', type="primary"):
    st.cache_data.clear()
    st.session_state.pop('last_update', None)
    st.rerun()

if 'last_update' in st.session_state:
    st.sidebar.caption(f"資料時間: {st.session_state['last_update']}")

st.title(f"📊 {market_mode}")

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
        df = df.rename(columns={'Symbol': 'Ticker', 'GICS Sector': 'Sector'})
        df['Ticker'] = df['Ticker'].str.replace('.', '-', regex=False)
        if 'GICS Sub-Industry' in df.columns:
            df = df.rename(columns={'GICS Sub-Industry': 'Industry'})
        else:
            df['Industry'] = df['Sector']
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
    try:
        data = yf.download(tickers, period=period, group_by='ticker', auto_adjust=True, threads=True, progress=False)
        return data
    except Exception:
        return pd.DataFrame()

# --- 4. 總經/原物料/資金 數據獲取 ---
@st.cache_data(ttl=3600)
def get_macro_data():
    tickers = ["^VIX", "^GSPC"]
    data = yf.download(tickers, period="2y", group_by='ticker', auto_adjust=True, progress=False)
    return data

@st.cache_data(ttl=3600)
def get_commodity_data():
    tickers = ["BDRY", "DBC", "HG=F", "CL=F", "GC=F"]
    data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, progress=False)
    return data

@st.cache_data(ttl=3600)
def get_stock_data(ticker, period="2y"):
    """獲取單一股票的詳細數據"""
    data = yf.download(ticker, period=period, auto_adjust=True, progress=False)
    
    # yfinance 有時會回傳 MultiIndex (Price, Ticker)，需轉為單層 Index 避免錯誤
    if isinstance(data.columns, pd.MultiIndex):
        try:
            # 嘗試取得 Price 層級 (Open, Close 等)
            data.columns = data.columns.get_level_values(0)
        except Exception:
            pass # 如果失敗則維持原狀，避免崩潰

    return data

def check_ticker_validity(ticker):
    """檢查代號是否有效 (嘗試抓取 5 天數據)"""
    try:
        data = yf.download(ticker, period="5d", progress=False)
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
    """計算 MA, RSI, MACD, Bollinger Bands"""
    df = df.copy()
    
    # Moving Averages (PDF Page 8)
    df['MA20'] = df['Close'].rolling(window=20).mean()
    df['MA50'] = df['Close'].rolling(window=50).mean()
    df['MA200'] = df['Close'].rolling(window=200).mean()
    
    # RSI (PDF Page 9)
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    
    # MACD (PDF Page 9)
    exp12 = df['Close'].ewm(span=12, adjust=False).mean()
    exp26 = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = exp12 - exp26
    df['Signal_Line'] = df['MACD'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['MACD'] - df['Signal_Line']
    
    # Bollinger Bands (用於輔助判斷波動與壓力支撐)
    df['BB_Upper'] = df['MA20'] + (df['Close'].rolling(window=20).std() * 2)
    df['BB_Lower'] = df['MA20'] - (df['Close'].rolling(window=20).std() * 2)
    
    return df

# --- 6. 核心計算邏輯 (股票) ---
def process_data_for_periods(base_df, history_data, market_caps):
    results = []
    tickers = base_df['Ticker'].tolist()
    valid_tickers = [t for t in tickers if t in history_data.columns.levels[0]]
    
    for ticker in valid_tickers:
        try:
            stock_df = history_data[ticker]['Close'].dropna()
            if len(stock_df) < 2: continue
            
            last_price = stock_df.iloc[-1]
            mkt_cap = market_caps.get(ticker, 0)
            
            chg_1d = stock_df.pct_change(1).iloc[-1] * 100
            chg_1w = stock_df.pct_change(5).iloc[-1] * 100 if len(stock_df) > 5 else 0
            chg_1m = stock_df.pct_change(21).iloc[-1] * 100 if len(stock_df) > 21 else 0
            chg_ytd = ((last_price - stock_df.iloc[0]) / stock_df.iloc[0]) * 100
            
            row = base_df[base_df['Ticker'] == ticker].iloc[0]
            results.append({
                'Ticker': ticker, 'Name': row.get('Name', ticker), 'Sector': row['Sector'],
                'Industry': row['Industry'], 'Market Cap': mkt_cap, 'Close': last_price,
                '1D Change': chg_1d, '1W Change': chg_1w, '1M Change': chg_1m, 'YTD Change': chg_ytd
            })
        except: continue
    return pd.DataFrame(results)

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
    fig.update_layout(height=600, margin=dict(t=40, l=10, r=10, b=10))
    st.plotly_chart(fig, use_container_width=True)

def plot_gauge(score):
    fig = go.Figure(go.Indicator(
        mode = "gauge+number", value = score,
        domain = {'x': [0, 1], 'y': [0, 1]}, title = {'text': "市場情緒 (Proxy)"},
        gauge = {'axis': {'range': [None, 100]}, 'bar': {'color': "darkblue"},
                 'steps': [{'range': [0, 25], 'color': '#ff4b4b'}, {'range': [25, 45], 'color': '#ffbaba'},
                           {'range': [45, 55], 'color': '#e0e0e0'}, {'range': [55, 75], 'color': '#baffba'},
                           {'range': [75, 100], 'color': '#008000'}]}
    ))
    fig.update_layout(height=300, margin=dict(t=30, b=10, l=30, r=30))
    st.plotly_chart(fig, use_container_width=True)

def plot_line_chart(data, title, color):
    fig = px.line(data, title=title)
    fig.update_traces(line_color=color, line_width=2)
    fig.update_layout(height=350, margin=dict(l=20, r=20, t=40, b=20), xaxis_title=None, yaxis_title=None)
    st.plotly_chart(fig, use_container_width=True)

def plot_tech_chart(df, ticker, title):
    """繪製包含 MA, Volume, RSI, MACD 的互動式圖表"""
    # 創建子圖結構 (主圖, 成交量, RSI, MACD)
    fig = make_subplots(
        rows=4, cols=1, 
        shared_xaxes=True, 
        vertical_spacing=0.03, 
        row_heights=[0.5, 0.15, 0.15, 0.2],
        subplot_titles=(f"{title} 價格趨勢 (含 MA & Bollinger)", "成交量 (Volume)", "RSI 強弱指標", "MACD 動能")
    )

    # 1. 主圖：K線 + MA
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name='Price'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='orange', width=1), name='MA20 (月線)'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], line=dict(color='blue', width=1.5), name='MA50 (季線)'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA200'], line=dict(color='red', width=2), name='MA200 (年線)'), row=1, col=1)
    
    # 布林通道
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Upper'], line=dict(color='gray', width=0), showlegend=False, hoverinfo='skip'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['BB_Lower'], line=dict(color='gray', width=0), fill='tonexty', fillcolor='rgba(128,128,128,0.1)', name='BB Band'), row=1, col=1)

    # 2. 成交量
    colors = ['green' if o >= c else 'red' for o, c in zip(df['Open'], df['Close'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='Volume'), row=2, col=1)

    # 3. RSI
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], line=dict(color='purple', width=2), name='RSI'), row=3, col=1)
    fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1) # 超買
    fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1) # 超賣

    # 4. MACD
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], line=dict(color='blue', width=1.5), name='MACD'), row=4, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['Signal_Line'], line=dict(color='orange', width=1.5), name='Signal'), row=4, col=1)
    colors_hist = ['green' if v >= 0 else 'red' for v in df['MACD_Hist']]
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], marker_color=colors_hist, name='Histogram'), row=4, col=1)

    # 設定
    fig.update_layout(
        height=900, 
        xaxis_rangeslider_visible=False,
        title_text=f"{ticker} 技術分析儀表板",
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

# --- 8. 頁面渲染邏輯 ---

def render_stock_strategy_page():
    st.header("🔎 個股技術戰略分析 (PDF 規則實戰)")
    st.caption("輸入代號查詢美股或台股，系統將依據《Technical Analysis Profitability Rules》進行趨勢、動能與風險檢測。")

    # --- 輸入區塊 ---
    with st.container():
        col_input1, col_input2, col_btn = st.columns([3, 1, 1])
        with col_input1:
            ticker_input = st.text_input("輸入股票代號 (例如: NVDA, AAPL, 2330.TW, 0050.TW)", value="AAPL")
        with col_input2:
            timeframe = st.selectbox("分析週期", ["1y", "2y", "5y"], index=0)
        with col_btn:
            st.write("") # Spacer for alignment
            st.write("") 
            analyze_btn = st.button("🚀 開始分析", type="primary")

    # 若按下按鈕或已有輸入，且代號不為空
    if analyze_btn or (ticker_input and ticker_input != ""):
        ticker = ticker_input.upper().strip()
        
        # [新增] 台股代號防呆機制：若只輸入4位數字，預設為台股上市 (加上 .TW)
        if ticker.isdigit() and len(ticker) == 4:
            st.caption(f"💡 偵測到數字代號，已自動轉換為台股上市格式：{ticker}.TW")
            ticker = f"{ticker}.TW"

        # --- 步驟 1: 驗證代號 ---
        with st.spinner(f"正在連線交易所查詢 {ticker} ..."):
            is_valid = check_ticker_validity(ticker)
            
        if not is_valid:
            st.error(f"❌ 查無代號：{ticker}")
            st.info("💡 提示：台股請加上 .TW (例如 2330.TW)，美股直接輸入代號 (例如 AAPL)。請檢查拼字或網路連線。")
            return

        # --- 步驟 2: 獲取詳細數據與計算 ---
        with st.spinner(f"✅ 代號確認！正在計算 {ticker} 技術指標..."):
            df = get_stock_data(ticker, period=timeframe)
            if df.empty or len(df) < 50: # 至少要有足夠數據算 MA50
                st.warning("⚠️ 數據不足，無法進行完整技術分析 (可能是新上市股票)。")
                return
            
            df = calculate_indicators(df)
            last_row = df.iloc[-1]
            prev_row = df.iloc[-2]

            # --- A. 狀態儀表板 ---
            st.markdown("### 1. 即時技術狀態總覽")
            m1, m2, m3, m4 = st.columns(4)
            
            # 價格與漲跌
            chg = (last_row['Close'] - prev_row['Close']) / prev_row['Close'] * 100
            m1.metric(f"{ticker} 收盤價", f"${last_row['Close']:.2f}", f"{chg:.2f}%")
            
            # 趨勢判斷 (Dow Theory / MA)
            trend_status = "盤整 / 不明"
            if last_row['Close'] > last_row['MA200']:
                if last_row['MA50'] > last_row['MA200']:
                    trend_status = "🚀 長期多頭 (Bull Market)"
                else:
                    trend_status = "⚠️ 多頭回調 (Correction)"
            else:
                trend_status = "🐻 長期空頭 (Bear Market)"
            m2.metric("主要趨勢 (Primary Trend)", trend_status)

            # RSI 動能
            rsi_val = last_row['RSI']
            rsi_status = "中性"
            if rsi_val > 70: rsi_status = "🔴 超買 (Overbought)"
            elif rsi_val < 30: rsi_status = "🟢 超賣 (Oversold)"
            m3.metric("RSI 動能", f"{rsi_val:.1f}", rsi_status)
            
            # MACD 信號
            macd_val = last_row['MACD_Hist']
            macd_sig = "多方控盤" if macd_val > 0 else "空方控盤"
            m4.metric("MACD 動能", f"{macd_val:.2f}", macd_sig)

            # --- B. 圖表區域 ---
            st.markdown("---")
            plot_tech_chart(df, ticker, ticker)

            # --- C. 策略檢查清單 (PDF Page 14) ---
            st.markdown("---")
            st.subheader("📋 交易決策檢查清單 (Checklist)")
            
            c1, c2 = st.columns(2)
            
            with c1:
                st.markdown("#### 🔍 趨勢與型態 (Chart Analysis)")
                
                # 1. 均線排列
                ma_bullish = last_row['MA20'] > last_row['MA50'] > last_row['MA200']
                st.markdown(f"- **均線排列 (MA Alignment)**: {'✅ 多頭排列' if ma_bullish else '⚠️ 糾結或空頭排列'}")
                st.caption("PDF 重點：確認趨勢方向，順勢而為 (Trend Following)。")

                # 2. 價格位置
                dist_ma200 = (last_row['Close'] - last_row['MA200']) / last_row['MA200'] * 100
                st.markdown(f"- **乖離率 (Distance to MA200)**: {dist_ma200:.1f}%")
                if dist_ma200 > 15:
                    st.warning("  ⚠️ 乖離過大，依據 PDF「均值回歸」概念，追高風險增加。")
                else:
                    st.info("  ℹ️ 乖離適中，趨勢健康。")

                # 3. 支撐壓力 (簡單用近期高低點)
                recent_high = df['High'].tail(60).max()
                recent_low = df['Low'].tail(60).min()
                st.markdown(f"- **近期區間 (60日)**: High ${recent_high:.0f} / Low ${recent_low:.0f}")
                
            with c2:
                st.markdown("#### 🛡️ 風險管理與進場 (Risk Management)")
                
                # 4. RSI 背離檢查 (簡易版)
                price_high_recent = df['Close'].tail(20).max()
                rsi_high_recent = df['RSI'].tail(20).max()
                price_high_prev = df['Close'].iloc[-60:-20].max()
                rsi_high_prev = df['RSI'].iloc[-60:-20].max()
                
                divergence = "無明顯背離"
                if price_high_recent > price_high_prev and rsi_high_recent < rsi_high_prev:
                    divergence = "🚨 潛在頂部背離 (Bearish Divergence)"
                st.markdown(f"- **背離訊號**: {divergence}")
                st.caption("PDF 重點：動能指標與價格方向不一致時，往往是反轉前兆。")

                # 5. 賺賠比建議
                st.markdown("- **賺賠比 (R/R Ratio) 3:1 原則**")
                st.info(f"""
                若現在進場做多 {ticker}：
                1. **停損點 (Stop Loss)**：建議設在近期支撐 ${recent_low:.2f} 或 MA20 ${last_row['MA20']:.2f} 下方。
                2. **目標價 (Target)**：需大於進場價 + 3倍風險。
                """)

            # --- D. 綜合建議 ---
            st.markdown("### 🤖 系統綜合評語")
            if trend_status.startswith("🚀") and rsi_val < 70 and macd_val > 0:
                st.success(f"目前 {ticker} 處於強勢多頭趨勢，且尚未過度超買。依據 PDF 順勢交易原則，可沿 MA20 操作，設好停損。")
            elif rsi_val > 75:
                st.warning(f"雖然 {ticker} 趨勢向上，但 RSI 顯示超買 (>75)。依據 PDF 建議，不宜追高，等待拉回測試支撐（如 MA20）再佈局。")
            elif trend_status.startswith("🐻"):
                st.error(f"目前 {ticker} 處於空頭趨勢 (價格 < 年線)。依據 PDF 原則，此時做多風險極高，應等待底部型態完成或突破下降趨勢線。")
            else:
                st.info(f"{ticker} 趨勢震盪整理中。依據 PDF 建議，可觀察箱型突破方向或等待均線重新排列。")

def render_macro_page():
    with st.spinner("正在計算總經風險指標..."):
        macro_data = get_macro_data()
        
        if macro_data.empty:
            st.error("無法取得市場數據")
            return

        vix_series = macro_data['^VIX']['Close'].dropna()
        sp500_series = macro_data['^GSPC']['Close'].dropna()
        f_g_score, v_val, r_val = calculate_fear_greed(vix_series.iloc[-1], sp500_series)
        
        col1, col2 = st.columns([1, 1])
        with col1:
            st.subheader("😨 Fear & Greed (模擬)")
            plot_gauge(f_g_score)
            st.info(f"VIX: {v_val:.2f} | RSI: {r_val:.2f}")

        with col2:
            st.subheader("🇹🇼 台灣景氣對策信號")
            st.info("由於國發會連線限制，請點擊下方按鈕前往官方網站查看最新數據。")
            st.link_button("👉 國發會 - 景氣指標查詢系統", "https://index.ndc.gov.tw/n/zh_tw/indicators")
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 10px; border-radius: 5px; font-size: 0.9em;">
                <b>🔴紅燈</b>: 熱絡 | <b>🟢綠燈</b>: 穩定 | <b>🔵藍燈</b>: 低迷
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("📉 VIX 波動率 (1 Year)")
        fig_vix = px.line(vix_series, title="CBOE VIX Index")
        fig_vix.add_hline(y=20, line_dash="dash", line_color="red")
        st.plotly_chart(fig_vix, use_container_width=True)

def render_commodity_page():
    st.caption("註：BDI 與 SCFI 為交易所專有數據，此處使用相關性高度連動的 ETF 或期貨作為即時走勢參考。")
    with st.spinner("正在獲取原物料行情..."):
        comm_data = get_commodity_data()
        
        st.markdown("### 🚢 航運指標 (Shipping)")
        c1, c2 = st.columns([2, 1])
        with c1:
            if 'BDRY' in comm_data.columns.levels[0]:
                data = comm_data['BDRY']['Close'].dropna()
                plot_line_chart(data, "BDI 替代指標 (BDRY ETF) - 散裝航運", "#1f77b4")
        with c2:
            st.markdown("""
            <div class="metric-card">
                <div class="metric-title">BDI 波羅的海乾散貨</div>
                <div class="metric-value">原物料運價</div>
                <div style="font-size:12px; color:#666; margin-top:5px;">全球經濟領先指標</div>
            </div>
            """, unsafe_allow_html=True)
            st.link_button("📊 Investing.com (BDI)", "https://www.investing.com/indices/baltic-dry")
            st.link_button("📦 上海航交所 (SCFI)", "https://en.sse.net.cn/indices/scfinew.jsp")

        st.markdown("---")
        st.markdown("### 🛢️ 原物料與能源 (Commodities)")
        c3, c4 = st.columns([1, 1])
        with c3:
            if 'DBC' in comm_data.columns.levels[0]:
                data = comm_data['DBC']['Close'].dropna()
                plot_line_chart(data, "CRB 替代指標 (DBC ETF)", "#ff7f0e")
        with c4:
            if 'CL=F' in comm_data.columns.levels[0]:
                data = comm_data['CL=F']['Close'].dropna()
                plot_line_chart(data, "紐約輕原油 (WTI)", "#d62728")
        
        st.markdown("---")
        st.markdown("### 🏗️ 工業金屬 (LME Metals)")
        c5, c6 = st.columns([1, 1])
        with c5:
            if 'HG=F' in comm_data.columns.levels[0]:
                data = comm_data['HG=F']['Close'].dropna()
                plot_line_chart(data, "銅 (Copper) - 製造業風向球", "#2ca02c")
                st.link_button("🔗 LME 官網", "https://www.lme.com/")
        with c6:
            if 'GC=F' in comm_data.columns.levels[0]:
                data = comm_data['GC=F']['Close'].dropna()
                plot_line_chart(data, "黃金 (Gold) - 避險情緒", "#bcbd22")

def render_liquidity_page():
    st.header("💰 資金量體與籌碼戰情室")
    st.caption("結合自動化量價分析與手動輸入的關鍵籌碼數據，全方位評估市場水位。")

    # --- Section 1: 手動輸入區 (使用 Expander 收納) ---
    with st.expander("🛠️ 關鍵籌碼數據輸入 (請點此展開輸入)", expanded=True):
        st.markdown("由於 M1B、融資維持率等數據無法自動抓取，請手動輸入最新數值以進行分析。")
        
        col_in1, col_in2, col_in3 = st.columns(3)
        
        with col_in1:
            st.subheader("🇹🇼 台灣貨幣供給")
            st.link_button("🔍 查詢央行 M1B/M2", "https://www.cbc.gov.tw/tw/cp-537-25624-F4C5E-1.html")
            m1b_val = st.number_input("M1B 年增率 (%)", value=5.24, step=0.01, format="%.2f")
            m2_val = st.number_input("M2 年增率 (%)", value=5.44, step=0.01, format="%.2f")
        
        with col_in2:
            st.subheader("🇹🇼 台股信用交易")
            st.link_button("🔍 查詢融資維持率", "https://www.twse.com.tw/zh/page/trading/exchange/MI_MARGN.html")
            margin_ratio = st.number_input("融資維持率 (%)", value=169.39, step=0.1, format="%.2f")
            margin_balance = st.number_input("融資餘額 (億元)", value=3321.0, step=1.0)
            
        with col_in3:
            st.subheader("🇺🇸 美股槓桿")
            st.link_button("🔍 查詢 FINRA Margin Debt", "https://www.finra.org/investors/insight/margin-stats")
            us_margin_debt = st.number_input("Margin Debt (兆美元)", value=1.21, step=0.01, format="%.2f")

    # --- Section 2: 手動數據分析結果 ---
    st.markdown("---")
    st.subheader("📊 籌碼水位診斷")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        gap = m1b_val - m2_val
        status = "🔴 死亡交叉 (資金緊縮)" if gap < 0 else "🟢 黃金交叉 (資金充沛)"
        delta_color = "normal" if gap > 0 else "inverse"
        
        st.metric("資金剪刀差 (M1B - M2)", f"{gap:.2f}%", delta=gap, delta_color=delta_color)
        st.info(f"狀態：{status}")
        if gap < 0 and gap > -0.5:
            st.caption("💡 差距縮小中，留意翻正訊號！")

    with col_res2:
        status_margin = "🟢 安全水位"
        if margin_ratio < 140: status_margin = "🔴 斷頭風險高"
        elif margin_ratio < 160: status_margin = "🟡 警戒水位 (整戶維持率偏低)"
        elif margin_ratio > 175: status_margin = "🔥 過熱 (散戶大開槓桿)"
        
        st.metric("融資維持率", f"{margin_ratio}%")
        st.info(f"評估：{status_margin}")

    with col_res3:
        st.metric("美股融資餘額", f"${us_margin_debt}T")
        st.info("評估：處於歷史相對高檔，顯示市場槓桿意願強。")

    # --- Section 3: 自動化量價分析 (OBV + VIX) ---
    st.markdown("---")
    st.subheader("🌊 自動化量價趨勢 (S&P 500)")
    
    with st.spinner("正在計算 OBV 與 VIX..."):
        macro_data = get_macro_data() # 取得 2 年數據
        sp500 = macro_data['^GSPC'].copy()
        vix = macro_data['^VIX'].copy()

        # 計算 OBV
        sp500['Daily_Ret'] = sp500['Close'].pct_change()
        sp500['Direction'] = np.where(sp500['Daily_Ret'] >= 0, 1, -1)
        sp500['OBV'] = (sp500['Volume'] * sp500['Direction']).cumsum()

        # 計算 RSI
        delta = sp500['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        sp500['RSI'] = 100 - (100 / (1 + rs))

        col_chart1, col_chart2 = st.columns([2, 1])
        
        with col_chart1:
            # 繪製標準化比較圖
            norm_price = (sp500['Close'] - sp500['Close'].min()) / (sp500['Close'].max() - sp500['Close'].min())
            norm_obv = (sp500['OBV'] - sp500['OBV'].min()) / (sp500['OBV'].max() - sp500['OBV'].min())
            
            df_chart = pd.DataFrame({
                'S&P 500 走勢': norm_price,
                'OBV 資金動能': norm_obv
            })
            st.line_chart(df_chart)
            st.caption("藍線(股價)與橘線(資金)若出現背離(方向不同)，通常是變盤前兆。")

        with col_chart2:
            latest_rsi = sp500['RSI'].iloc[-1]
            latest_vix = vix['Close'].iloc[-1]
            
            st.metric("RSI (強弱指標)", f"{latest_rsi:.1f}")
            st.metric("VIX (恐慌指數)", f"{latest_vix:.1f}")
            
            if latest_rsi > 75 and latest_vix < 13:
                st.error("🚨 資金極度過熱！")
            elif latest_rsi < 30 and latest_vix > 30:
                st.success("🟢 資金恐慌築底")
            else:
                st.warning("🟡 資金情緒中性")

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
    elif "個股" in market_mode: # 修改條件以符合新選項
        render_stock_strategy_page()
    else:
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

        st.subheader(f"🌞 1 日短期趨勢 ({title_prefix})")
        plot_treemap(final_df, '1D Change', f'{title_prefix} (1 Day)', [-4, 4])
        st.subheader(f"📅 1 週趨勢 ({title_prefix})")
        plot_treemap(final_df, '1W Change', f'{title_prefix} (1 Week)', [-8, 8])
        st.subheader(f"🌕 1 月趨勢 ({title_prefix})")
        plot_treemap(final_df, '1M Change', f'{title_prefix} (1 Month)', [-15, 15])
        st.subheader(f"📅 1 年/長期趨勢 ({title_prefix})")
        plot_treemap(final_df, 'YTD Change', f'{title_prefix} (YTD)', [-40, 40])
    
    st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    main()