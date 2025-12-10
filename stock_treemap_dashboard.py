# ----------------------------------------------------------------------
# 股市戰情室 - 極速穩定版 (修正 SyntaxError)
# ----------------------------------------------------------------------

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np
import concurrent.futures
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
</style>
""", unsafe_allow_html=True)

# --- 2. 側邊欄控制 ---
st.sidebar.header("⚙️ 戰情控制台")
market_mode = st.sidebar.radio(
    "📊 選擇儀表板",
    [
        "🇺🇸 美股 S&P 500", 
        "🇹🇼 台股權值股 (TWSE)", 
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

# 使用多執行緒平行抓取市值
def fetch_single_cap(ticker):
    try:
        # 修正處：補上 .Ticker(ticker)
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

# --- 4. 總經數據獲取 (僅剩 VIX) ---
@st.cache_data(ttl=3600)
def get_macro_data():
    tickers = ["^VIX", "^GSPC"]
    data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, progress=False)
    return data

def calculate_fear_greed(vix_close, sp500_close):
    vix_score = max(0, min(100, (40 - vix_close) * (100 / 30)))
    delta = sp500_close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    final = (vix_score * 0.6) + (rsi.iloc[-1] * 0.4)
    return int(final), vix_close, rsi.iloc[-1]

# --- 5. 核心計算邏輯 ---
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

# --- 6. 繪圖函數 ---
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

# --- 7. 頁面渲染邏輯 ---

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
            
            # 使用 Streamlit 原生 link_button
            st.link_button("👉 國發會 - 景氣指標查詢系統", "https://index.ndc.gov.tw/n/zh_tw/indicators")
            
            st.markdown("""
            <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; margin-top: 20px;">
                <h4>💡 燈號意義說明：</h4>
                <ul>
                    <li><span style='color: #dc3545; font-weight: bold;'>🔴 紅燈</span>：景氣熱絡 (38-45分)</li>
                    <li><span style='color: #ffc107; font-weight: bold;'>🟠 黃紅燈</span>：景氣轉向 (32-37分)</li>
                    <li><span style='color: #28a745; font-weight: bold;'>🟢 綠燈</span>：景氣穩定 (23-31分)</li>
                    <li><span style='color: #80b3ff; font-weight: bold;'>🔵 黃藍燈</span>：景氣轉向 (17-22分)</li>
                    <li><span style='color: #2b7de9; font-weight: bold;'>🔵 藍燈</span>：景氣低迷 (9-16分)</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        # 只保留 VIX 線圖，且佔滿全寬
        st.subheader("📉 VIX 波動率 (1 Year)")
        fig_vix = px.line(vix_series, title="CBOE VIX Index")
        fig_vix.add_hline(y=20, line_dash="dash", line_color="red")
        st.plotly_chart(fig_vix, use_container_width=True)

# --- 8. 主程式 ---
def main():
    if 'last_update' not in st.session_state:
        st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if "總經" in market_mode:
        render_macro_page()
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
            
            # 使用多執行緒加速市值獲取
            market_caps = fetch_market_caps(tickers_list)
            
            # 獲取股價歷史
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