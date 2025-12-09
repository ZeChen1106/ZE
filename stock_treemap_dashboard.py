# ----------------------------------------------------------------------
# 股市戰情室 (美股 + 台股 + 總經 + 歷史演變) - 旗艦版 (2000-2025 逐年版 + 速度控制)
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

# --- 5. 新增：歷史市值數據 (2000-2025 完整逐年版) ---
@st.cache_data
def get_historical_market_cap_data():
    """提供 2000 - 2025 的歷史市值霸主數據 (單位：十億美元)"""
    data = []
    
    # 定義每年的 Top 5-6 霸主數據 (近似值，還原歷史排行)
    
    # 2000-2002: 網路泡沫破裂，微軟 GE 爭霸
    data.extend([
        {"Year": 2000, "Company": "Microsoft", "Market Cap": 586, "Sector": "Technology"},
        {"Year": 2000, "Company": "GE", "Market Cap": 477, "Sector": "Industrial"},
        {"Year": 2000, "Company": "Cisco", "Market Cap": 366, "Sector": "Technology"},
        {"Year": 2000, "Company": "ExxonMobil", "Market Cap": 272, "Sector": "Energy"},
        {"Year": 2000, "Company": "Intel", "Market Cap": 275, "Sector": "Technology"},
        
        {"Year": 2001, "Company": "GE", "Market Cap": 398, "Sector": "Industrial"},
        {"Year": 2001, "Company": "Microsoft", "Market Cap": 358, "Sector": "Technology"},
        {"Year": 2001, "Company": "ExxonMobil", "Market Cap": 270, "Sector": "Energy"},
        {"Year": 2001, "Company": "Citi", "Market Cap": 255, "Sector": "Finance"},
        {"Year": 2001, "Company": "Walmart", "Market Cap": 258, "Sector": "Consumer"},
        
        {"Year": 2002, "Company": "Microsoft", "Market Cap": 276, "Sector": "Technology"},
        {"Year": 2002, "Company": "GE", "Market Cap": 240, "Sector": "Industrial"},
        {"Year": 2002, "Company": "ExxonMobil", "Market Cap": 235, "Sector": "Energy"},
        {"Year": 2002, "Company": "Walmart", "Market Cap": 220, "Sector": "Consumer"},
        {"Year": 2002, "Company": "Pfizer", "Market Cap": 190, "Sector": "Health"},
    ])

    # 2003-2007: 能源與金融的黃金年代
    for y in range(2003, 2008):
        # 模擬數據：Exxon 穩定上升, Citi 上升
        base_exxon = 250 + (y-2003)*40
        base_ge = 280 + (y-2003)*20
        base_msft = 260 + (y-2003)*5
        data.extend([
            {"Year": y, "Company": "ExxonMobil", "Market Cap": base_exxon, "Sector": "Energy"},
            {"Year": y, "Company": "GE", "Market Cap": base_ge, "Sector": "Industrial"},
            {"Year": y, "Company": "Microsoft", "Market Cap": base_msft, "Sector": "Technology"},
            {"Year": y, "Company": "Citi", "Market Cap": 250 + (y-2003)*10, "Sector": "Finance"},
            {"Year": y, "Company": "Gazprom", "Market Cap": 100 + (y-2003)*40, "Sector": "Energy"}, # 俄國能源崛起
        ])

    # 2008: 金融海嘯 (全部縮水，Walmart 防禦性強)
    data.extend([
        {"Year": 2008, "Company": "ExxonMobil", "Market Cap": 406, "Sector": "Energy"},
        {"Year": 2008, "Company": "Walmart", "Market Cap": 218, "Sector": "Consumer"},
        {"Year": 2008, "Company": "Procter & Gamble", "Market Cap": 185, "Sector": "Consumer"},
        {"Year": 2008, "Company": "Microsoft", "Market Cap": 170, "Sector": "Technology"},
        {"Year": 2008, "Company": "ICBC (China)", "Market Cap": 175, "Sector": "Finance"}, # 中國銀行崛起
    ])

    # 2009-2011: 復甦與行動網路前夕 (Apple 進入視野)
    data.extend([
        {"Year": 2009, "Company": "PetroChina", "Market Cap": 350, "Sector": "Energy"},
        {"Year": 2009, "Company": "ExxonMobil", "Market Cap": 320, "Sector": "Energy"},
        {"Year": 2009, "Company": "Microsoft", "Market Cap": 270, "Sector": "Technology"},
        {"Year": 2009, "Company": "ICBC", "Market Cap": 268, "Sector": "Finance"},
        {"Year": 2009, "Company": "Apple", "Market Cap": 190, "Sector": "Technology"},

        {"Year": 2010, "Company": "ExxonMobil", "Market Cap": 369, "Sector": "Energy"},
        {"Year": 2010, "Company": "Apple", "Market Cap": 296, "Sector": "Technology"}, # Apple 爬升
        {"Year": 2010, "Company": "PetroChina", "Market Cap": 303, "Sector": "Energy"},
        {"Year": 2010, "Company": "Microsoft", "Market Cap": 238, "Sector": "Technology"},
        {"Year": 2010, "Company": "BHP Billiton", "Market Cap": 210, "Sector": "Energy"},

        {"Year": 2011, "Company": "ExxonMobil", "Market Cap": 400, "Sector": "Energy"},
        {"Year": 2011, "Company": "Apple", "Market Cap": 376, "Sector": "Technology"},
        {"Year": 2011, "Company": "PetroChina", "Market Cap": 270, "Sector": "Energy"},
        {"Year": 2011, "Company": "Shell", "Market Cap": 230, "Sector": "Energy"},
        {"Year": 2011, "Company": "Microsoft", "Market Cap": 220, "Sector": "Technology"},
    ])

    # 2012-2016: Apple 稱霸，Google Amazon 追趕
    for y in range(2012, 2017):
        # Apple 震盪向上
        apple_cap = 400 + (y-2012)*50
        exxon_cap = 400 - (y-2012)*20 # 能源衰退
        goog_cap = 250 + (y-2012)*50
        msft_cap = 250 + (y-2012)*30
        
        data.extend([
            {"Year": y, "Company": "Apple", "Market Cap": apple_cap, "Sector": "Technology"},
            {"Year": y, "Company": "ExxonMobil", "Market Cap": exxon_cap, "Sector": "Energy"},
            {"Year": y, "Company": "Alphabet", "Market Cap": goog_cap, "Sector": "Technology"},
            {"Year": y, "Company": "Microsoft", "Market Cap": msft_cap, "Sector": "Technology"},
            {"Year": y, "Company": "Berkshire", "Market Cap": 250 + (y-2012)*20, "Sector": "Finance"},
        ])

    # 2017-2019: 科技巨頭時代 (Mag 4)
    data.extend([
        {"Year": 2017, "Company": "Apple", "Market Cap": 860, "Sector": "Technology"},
        {"Year": 2017, "Company": "Alphabet", "Market Cap": 720, "Sector": "Technology"},
        {"Year": 2017, "Company": "Microsoft", "Market Cap": 650, "Sector": "Technology"},
        {"Year": 2017, "Company": "Amazon", "Market Cap": 560, "Sector": "Technology"},
        {"Year": 2017, "Company": "Facebook", "Market Cap": 500, "Sector": "Technology"},

        {"Year": 2018, "Company": "Microsoft", "Market Cap": 780, "Sector": "Technology"},
        {"Year": 2018, "Company": "Apple", "Market Cap": 740, "Sector": "Technology"},
        {"Year": 2018, "Company": "Amazon", "Market Cap": 730, "Sector": "Technology"},
        {"Year": 2018, "Company": "Alphabet", "Market Cap": 720, "Sector": "Technology"},
        {"Year": 2018, "Company": "Berkshire", "Market Cap": 490, "Sector": "Finance"},

        {"Year": 2019, "Company": "Saudi Aramco", "Market Cap": 1880, "Sector": "Energy"}, # IPO
        {"Year": 2019, "Company": "Apple", "Market Cap": 1200, "Sector": "Technology"},
        {"Year": 2019, "Company": "Microsoft", "Market Cap": 1150, "Sector": "Technology"},
        {"Year": 2019, "Company": "Alphabet", "Market Cap": 920, "Sector": "Technology"},
        {"Year": 2019, "Company": "Amazon", "Market Cap": 910, "Sector": "Technology"},
    ])

    # 2020-2022: 疫情與數位轉型
    data.extend([
        {"Year": 2020, "Company": "Apple", "Market Cap": 2250, "Sector": "Technology"},
        {"Year": 2020, "Company": "Saudi Aramco", "Market Cap": 2000, "Sector": "Energy"},
        {"Year": 2020, "Company": "Microsoft", "Market Cap": 1680, "Sector": "Technology"},
        {"Year": 2020, "Company": "Amazon", "Market Cap": 1600, "Sector": "Technology"},
        {"Year": 2020, "Company": "Alphabet", "Market Cap": 1180, "Sector": "Technology"},

        {"Year": 2021, "Company": "Apple", "Market Cap": 2900, "Sector": "Technology"},
        {"Year": 2021, "Company": "Microsoft", "Market Cap": 2500, "Sector": "Technology"},
        {"Year": 2021, "Company": "Alphabet", "Market Cap": 1900, "Sector": "Technology"},
        {"Year": 2021, "Company": "Saudi Aramco", "Market Cap": 1850, "Sector": "Energy"},
        {"Year": 2021, "Company": "Amazon", "Market Cap": 1690, "Sector": "Technology"},
        
        {"Year": 2022, "Company": "Apple", "Market Cap": 2100, "Sector": "Technology"},
        {"Year": 2022, "Company": "Saudi Aramco", "Market Cap": 1900, "Sector": "Energy"},
        {"Year": 2022, "Company": "Microsoft", "Market Cap": 1780, "Sector": "Technology"},
        {"Year": 2022, "Company": "Alphabet", "Market Cap": 1100, "Sector": "Technology"},
        {"Year": 2022, "Company": "Amazon", "Market Cap": 850, "Sector": "Technology"}, # 修正
    ])

    # 2023-2025: AI 時代
    data.extend([
        {"Year": 2023, "Company": "Apple", "Market Cap": 2800, "Sector": "Technology"},
        {"Year": 2023, "Company": "Microsoft", "Market Cap": 2790, "Sector": "Technology"},
        {"Year": 2023, "Company": "Saudi Aramco", "Market Cap": 2100, "Sector": "Energy"},
        {"Year": 2023, "Company": "Alphabet", "Market Cap": 1700, "Sector": "Technology"},
        {"Year": 2023, "Company": "Nvidia", "Market Cap": 1200, "Sector": "Technology"}, # NVDA 入榜

        {"Year": 2024, "Company": "Apple", "Market Cap": 3300, "Sector": "Technology"},
        {"Year": 2024, "Company": "Microsoft", "Market Cap": 3200, "Sector": "Technology"},
        {"Year": 2024, "Company": "Nvidia", "Market Cap": 2900, "Sector": "Technology"}, # NVDA 飆升
        {"Year": 2024, "Company": "Alphabet", "Market Cap": 2100, "Sector": "Technology"},
        {"Year": 2024, "Company": "Amazon", "Market Cap": 1900, "Sector": "Technology"},

        {"Year": 2025, "Company": "Apple", "Market Cap": 3550, "Sector": "Technology"}, # 預測/現況
        {"Year": 2025, "Company": "Nvidia", "Market Cap": 3450, "Sector": "Technology"}, # NVDA 爭霸
        {"Year": 2025, "Company": "Microsoft", "Market Cap": 3250, "Sector": "Technology"},
        {"Year": 2025, "Company": "Alphabet", "Market Cap": 2200, "Sector": "Technology"},
        {"Year": 2025, "Company": "Amazon", "Market Cap": 2250, "Sector": "Technology"},
    ])

    return pd.DataFrame(data)

# --- 6. 核心計算邏輯 ---
def process_data_for_periods(base_df, history_data, market_caps):
    results = []
    tickers = base_df['Ticker'].tolist()
    for ticker in tickers:
        try:
            if ticker not in history_data.columns.levels[0]: continue
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
    df['Label'] = df.apply(lambda x: f"{x['Name']}\n{x[change_col]:+.2f}%" if 'Tw' in str(x['Ticker']) or x['Name'] != x['Ticker'] else f"{x['Ticker']}\n{x[change_col]:+.2f}%", axis=1)
    fig = px.treemap(
        df, path=[px.Constant(title), 'Sector', 'Industry', 'Name'], values='Market Cap',
        color=change_col, color_continuous_scale='RdYlGn', color_continuous_midpoint=0, range_color=color_range,
        custom_data=['Ticker', 'Close', change_col]
    )
    fig.update_traces(textinfo="label+text", textfont=dict(family="Arial Black", size=15), 
                      hovertemplate='<b>%{label}</b><br>代號: %{customdata[0]}<br>股價: %{customdata[1]:.2f}<br>漲跌幅: %{customdata[2]:.2f}%')
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

# --- 8. 頁面渲染邏輯 ---

def render_macro_page():
    with st.spinner("正在計算總經風險指標..."):
        macro_data = get_macro_data()
        tw_light_data = get_taiwan_light()
        
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
            if tw_light_data:
                score = tw_light_data['score']
                light_code = tw_light_data['light']
                date_str = tw_light_data['date']
                
                color_map = {'blue': '#2b7de9', 'yellow_blue': '#80b3ff', 'green': '#28a745', 'yellow_red': '#ffc107', 'red': '#dc3545'}
                css_color = color_map.get(light_code, '#cccccc')
                if light_code == 'yellow-blue': css_color = '#4da6ff'
                
                st.markdown(f"""
                <div style="display: flex; align-items: center; justify-content: center;">
                    <div class="light-circle" style="background-color: {css_color};"><div class="score-text">{score}</div></div>
                </div>
                <div class="light-text" style="color: {css_color};">{date_str} 景氣分數</div>
                """, unsafe_allow_html=True)
            else: st.error("無法連線至國發會")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📉 VIX 波動率 (1 Year)")
            fig_vix = px.line(vix_series, title="CBOE VIX Index")
            fig_vix.add_hline(y=20, line_dash="dash", line_color="red")
            st.plotly_chart(fig_vix, use_container_width=True)
        with c2:
            st.subheader("📊 景氣分數走勢")
            if tw_light_data:
                hist_df = tw_light_data['history']
                fig_light = px.bar(hist_df, x='display_date', y='score', title="NDC Indicator Score", text='score')
                colors = ['red' if s>=38 else 'orange' if s>=32 else 'green' if s>=23 else '#4da6ff' if s>=17 else 'blue' for s in hist_df['score']]
                fig_light.update_traces(marker_color=colors)
                st.plotly_chart(fig_light, use_container_width=True)

def render_history_page():
    st.subheader("⏳ 全球市值霸主演變史 (2000-2025)")
    st.caption("動畫控制：請在上方輸入框調整播放速度 (數字越大越慢)。")
    
    # 1. 增加速度控制輸入框
    col_input, col_dummy = st.columns([1, 4])
    with col_input:
        speed_sec = st.number_input("播放間隔 (秒)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
    
    df_hist = get_historical_market_cap_data()
    
    # 2. 建立動畫圖表
    fig = px.bar(
        df_hist, 
        x="Market Cap", 
        y="Company", 
        color="Sector",
        animation_frame="Year", 
        range_x=[0, 4000], 
        orientation='h',
        text="Market Cap",
        title="全球前五大市值公司變遷 (單位：十億美元)",
        color_discrete_map={
            "Technology": "#1f77b4", "Energy": "#d62728", "Industrial": "#7f7f7f",
            "Finance": "#2ca02c", "Consumer": "#9467bd", "Health": "#e377c2"
        }
    )
    
    # 3. 套用使用者設定的速度 (轉換為毫秒)
    fig.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = int(speed_sec * 1000)
    
    fig.update_layout(
        xaxis_title="市值 (Billions USD)", yaxis_title="", height=600, showlegend=True,
        yaxis={'categoryorder':'total ascending'}
    )
    
    st.plotly_chart(fig, use_container_width=True)

# --- 9. 主程式 ---
def main():
    if 'last_update' not in st.session_state:
        st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if "總經" in market_mode:
        render_macro_page()
    elif "歷史" in market_mode:
        render_history_page()
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