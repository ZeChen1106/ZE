# ----------------------------------------------------------------------
# 股市戰情室 (美股 S&P 500 + 台股權值 + 風險總經) - 旗艦版
# ----------------------------------------------------------------------

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
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
    .stMetric { background-color: #f9f9f9; padding: 10px; border-radius: 5px; border-left: 5px solid #ff4b4b; }
</style>
""", unsafe_allow_html=True)

# --- 2. 側邊欄：模式切換與控制 ---
st.sidebar.header("⚙️ 戰情控制台")

# 新增：市場選擇模式 (三種模式)
market_mode = st.sidebar.radio(
    "📊 選擇儀表板",
    ["🇺🇸 美股 S&P 500", "🇹🇼 台股權值股 (TWSE)", "📉 總經與風險指標 (Macro)"]
)

if st.sidebar.button('🔄 強制更新數據', type="primary"):
    st.cache_data.clear()
    st.session_state.pop('last_update', None)
    st.rerun()

if 'last_update' in st.session_state:
    st.sidebar.caption(f"資料時間: {st.session_state['last_update']}")

st.title(f"📊 {market_mode}")

# --- 3. 核心數據函數 (快取) ---

@st.cache_data(ttl=24 * 3600)
def get_tw_constituents():
    """台股主要權值股清單"""
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
    """美股 S&P 500 清單"""
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
        data = yf.download(
            tickers, 
            period=period, 
            group_by='ticker', 
            auto_adjust=True, 
            threads=True, 
            progress=False
        )
        return data
    except Exception:
        return pd.DataFrame()

# --- 4. 總經數據獲取與計算 ---
@st.cache_data(ttl=3600)
def get_macro_data():
    """抓取 VIX, 台股大盤, 美股大盤 用於計算指標"""
    tickers = ["^VIX", "^TWII", "^GSPC"]
    data = yf.download(tickers, period="1y", group_by='ticker', auto_adjust=True, progress=False)
    return data

def calculate_fear_greed(vix_close, sp500_close):
    """
    自製「技術面恐貪指數」 (Proxy):
    由 VIX (恐慌程度) 與 RSI (市場動能) 加權計算。
    0-25: 極度恐懼, 25-45: 恐懼, 45-55: 中立, 55-75: 貪婪, 75-100: 極度貪婪
    """
    # 1. VIX 分數 (VIX 越高越恐慌，分數越低)
    # 假設 VIX 10 是極度貪婪 (100分), VIX 40 是極度恐慌 (0分)
    vix_score = max(0, min(100, (40 - vix_close) * (100 / 30)))
    
    # 2. RSI 分數 (RSI 越高越貪婪)
    delta = sp500_close.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    rsi_score = rsi.iloc[-1]
    
    # 綜合分數 (VIX 佔 60%, RSI 佔 40%)
    final_score = (vix_score * 0.6) + (rsi_score * 0.4)
    return int(final_score), vix_close, rsi_score

# --- 5. 繪圖與邏輯 ---

def process_data_for_periods(base_df, history_data, market_caps):
    results = []
    tickers = base_df['Ticker'].tolist()
    
    for ticker in tickers:
        try:
            if ticker not in history_data.columns.levels[0]:
                continue
            stock_df = history_data[ticker]['Close'].dropna()
            if len(stock_df) < 2: continue

            last_price = stock_df.iloc[-1]
            mkt_cap = market_caps.get(ticker, 0)
            
            # 計算漲跌幅
            chg_1d = stock_df.pct_change(1).iloc[-1] * 100
            chg_1w = stock_df.pct_change(5).iloc[-1] * 100 if len(stock_df) > 5 else 0
            chg_1m = stock_df.pct_change(21).iloc[-1] * 100 if len(stock_df) > 21 else 0
            chg_ytd = ((last_price - stock_df.iloc[0]) / stock_df.iloc[0]) * 100
            
            row = base_df[base_df['Ticker'] == ticker].iloc[0]
            
            results.append({
                'Ticker': ticker,
                'Name': row.get('Name', ticker),
                'Sector': row['Sector'],
                'Industry': row['Industry'],
                'Market Cap': mkt_cap,
                'Close': last_price,
                '1D Change': chg_1d,
                '1W Change': chg_1w,
                '1M Change': chg_1m,
                'YTD Change': chg_ytd
            })
        except: continue
    return pd.DataFrame(results)

def plot_treemap(df, change_col, title, color_range):
    df['Label'] = df.apply(lambda x: f"{x['Name']}\n{x[change_col]:+.2f}%" if 'Tw' in str(x['Ticker']) or x['Name'] != x['Ticker'] else f"{x['Ticker']}\n{x[change_col]:+.2f}%", axis=1)
    
    fig = px.treemap(
        df,
        path=[px.Constant(title), 'Sector', 'Industry', 'Name'],
        values='Market Cap',
        color=change_col,
        color_continuous_scale='RdYlGn', 
        color_continuous_midpoint=0,
        range_color=color_range,
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
    """繪製恐懼與貪婪儀表板"""
    fig = go.Figure(go.Indicator(
        mode = "gauge+number",
        value = score,
        domain = {'x': [0, 1], 'y': [0, 1]},
        title = {'text': "市場情緒指數 (0=恐慌, 100=貪婪)"},
        gauge = {
            'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "black"},
            'bar': {'color': "darkblue"},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 25], 'color': '#ff4b4b'}, # 恐慌
                {'range': [25, 45], 'color': '#ffbaba'},
                {'range': [45, 55], 'color': '#e0e0e0'}, # 中立
                {'range': [55, 75], 'color': '#baffba'},
                {'range': [75, 100], 'color': '#008000'} # 貪婪
            ],
        }
    ))
    fig.update_layout(height=300, margin=dict(t=30, b=10, l=30, r=30))
    st.plotly_chart(fig, use_container_width=True)

# --- 6. 總經頁面渲染 ---
def render_macro_page():
    with st.spinner("正在計算總經風險指標..."):
        macro_data = get_macro_data()
        
        # 準備數據
        vix_series = macro_data['^VIX']['Close'].dropna()
        sp500_series = macro_data['^GSPC']['Close'].dropna()
        twii_series = macro_data['^TWII']['Close'].dropna()
        
        current_vix = vix_series.iloc[-1]
        
        # 計算恐貪指數
        f_g_score, v_val, r_val = calculate_fear_greed(current_vix, sp500_series)
        
        # --- 版面配置 ---
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("😨 Fear & Greed (模擬)")
            plot_gauge(f_g_score)
            st.info(f"當前 VIX: {v_val:.2f} | S&P500 RSI: {r_val:.2f}\n\n(指數 < 25 表市場極度恐慌，可能為買點；指數 > 75 表市場過熱)")
            
            st.markdown("---")
            st.subheader("🇹🇼 台灣景氣指標")
            st.caption("由於國發會無提供即時 API，請參考下方大盤年線趨勢，或點擊按鈕查看官方燈號。")
            st.link_button("前往國發會查詢最新「景氣對策信號」", "https://index.ndc.gov.tw/n/zh_tw")

        with col2:
            st.subheader("📉 VIX 波動率趨勢 (過去一年)")
            # 繪製 VIX 線圖
            fig_vix = px.line(vix_series, title="CBOE VIX Index")
            fig_vix.add_hline(y=20, line_dash="dash", line_color="red", annotation_text="警戒線 (20)")
            fig_vix.update_layout(height=350)
            st.plotly_chart(fig_vix, use_container_width=True)
            
            st.subheader("📈 台灣加權指數 vs 年線 (景氣概況)")
            # 計算簡單的年線 (240日)
            tw_df = pd.DataFrame({'Close': twii_series})
            tw_df['MA240'] = tw_df['Close'].rolling(window=240).mean()
            
            fig_tw = px.line(tw_df, y=['Close', 'MA240'], title="TWSE Index vs 240MA (Yearly Trend)")
            fig_tw.update_traces(line=dict(width=2))
            fig_tw.update_layout(height=350, legend_title_text='')
            st.plotly_chart(fig_tw, use_container_width=True)

# --- 7. 主程式 ---
def main():
    if 'last_update' not in st.session_state:
        st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 判斷頁面模式
    if "總經" in market_mode:
        render_macro_page()
    else:
        # 股市 Treemap 模式
        with st.spinner(f'正在載入 {market_mode} 數據...'):
            if "S&P 500" in market_mode:
                base_df = get_sp500_constituents()
                title_prefix = "S&P 500"
            else:
                base_df = get_tw_constituents()
                title_prefix = "TWSE"

            if base_df.empty:
                st.error("無法取得成分股清單。")
                return
                
            tickers_list = base_df['Ticker'].tolist()
            market_caps = fetch_market_caps(tickers_list)
            history_data = fetch_price_history(tickers_list)
            
            if history_data.empty:
                st.error("無法取得股價數據。")
                return
                
            final_df = process_data_for_periods(base_df, history_data, market_caps)
            
        if final_df.empty or final_df['Market Cap'].sum() == 0:
            st.warning("無有效數據可繪圖。")
            return
            
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