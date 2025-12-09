# ----------------------------------------------------------------------
# 股市戰情室 - 絲滑競賽圖終極修正版 (Fixed KeyError)
# ----------------------------------------------------------------------

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import yfinance as yf
import pandas as pd
import numpy as np
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

# --- 5. 歷史數據處理：插補與排名 (修復 Bug 版) ---

@st.cache_data
def get_processed_race_data():
    """
    生成 2000-2025 的平滑插補數據，並鎖定 Top 10
    """
    # 1. 原始數據
    raw_data = []
    
    def add_year(year, *companies):
        for comp in companies:
            raw_data.append({"Year": year, "Company": comp[0], "Market Cap": comp[1], "Sector": comp[2]})

    # 2000
    add_year(2000, 
             ("Microsoft", 586, "Technology"), ("GE", 477, "Industrial"), ("Cisco", 366, "Technology"),
             ("ExxonMobil", 272, "Energy"), ("Intel", 275, "Technology"), ("Walmart", 230, "Consumer"))
    # 2002
    add_year(2002, 
             ("Microsoft", 276, "Technology"), ("GE", 240, "Industrial"), ("ExxonMobil", 235, "Energy"),
             ("Walmart", 220, "Consumer"), ("Pfizer", 190, "Health"), ("Citi", 180, "Finance"))
    # 2005
    add_year(2005, 
             ("ExxonMobil", 360, "Energy"), ("GE", 350, "Industrial"), ("Microsoft", 270, "Technology"),
             ("Citi", 240, "Finance"), ("BP", 230, "Energy"), ("Walmart", 200, "Consumer"))
    # 2008
    add_year(2008, 
             ("ExxonMobil", 406, "Energy"), ("Walmart", 218, "Consumer"), ("Procter & Gamble", 185, "Consumer"),
             ("Microsoft", 170, "Technology"), ("ICBC", 175, "Finance"), ("Johnson & Johnson", 160, "Health"))
    # 2011
    add_year(2011, 
             ("ExxonMobil", 400, "Energy"), ("Apple", 376, "Technology"), ("PetroChina", 270, "Energy"),
             ("Shell", 230, "Energy"), ("Microsoft", 220, "Technology"), ("ICBC", 210, "Finance"))
    # 2014
    add_year(2014, 
             ("Apple", 600, "Technology"), ("ExxonMobil", 420, "Energy"), ("Google", 360, "Technology"),
             ("Microsoft", 340, "Technology"), ("Berkshire", 300, "Finance"), ("Johnson & Johnson", 280, "Health"))
    # 2017
    add_year(2017, 
             ("Apple", 860, "Technology"), ("Alphabet", 720, "Technology"), ("Microsoft", 650, "Technology"),
             ("Amazon", 560, "Technology"), ("Facebook", 500, "Technology"), ("Berkshire", 480, "Finance"))
    # 2020
    add_year(2020, 
             ("Apple", 2250, "Technology"), ("Saudi Aramco", 2000, "Energy"), ("Microsoft", 1680, "Technology"),
             ("Amazon", 1600, "Technology"), ("Alphabet", 1180, "Technology"), ("Facebook", 750, "Technology"))
    # 2022
    add_year(2022, 
             ("Apple", 2100, "Technology"), ("Saudi Aramco", 1900, "Energy"), ("Microsoft", 1780, "Technology"),
             ("Alphabet", 1100, "Technology"), ("Amazon", 850, "Technology"), ("Nvidia", 400, "Technology"))
    # 2024
    add_year(2024, 
             ("Apple", 3300, "Technology"), ("Microsoft", 3200, "Technology"), ("Nvidia", 2900, "Technology"),
             ("Alphabet", 2100, "Technology"), ("Amazon", 1900, "Technology"), ("Saudi Aramco", 1800, "Energy"))
    # 2025 (Forecast)
    add_year(2025, 
             ("Apple", 3550, "Technology"), ("Nvidia", 3450, "Technology"), ("Microsoft", 3350, "Technology"),
             ("Alphabet", 2250, "Technology"), ("Amazon", 2300, "Technology"), ("Meta", 1200, "Technology"))

    df = pd.DataFrame(raw_data)

    # 2. 數據插補 (Interpolation)
    # 轉置
    df_pivot = df.pivot_table(index='Year', columns='Company', values='Market Cap')
    
    # 建立 Sector 對照表
    sector_map = df.drop_duplicates('Company').set_index('Company')['Sector']

    # 擴展年份索引
    new_index = np.arange(2000, 2025.2, 0.2) 
    df_interp = df_pivot.reindex(df_pivot.index.union(new_index)).interpolate(method='linear')
    df_interp = df_interp.reindex(new_index)
    df_interp = df_interp.fillna(0) 

    # 確保 Index 名稱為 'Year'，避免 reset_index 出錯
    df_interp.index.name = 'Year'

    # 轉回長表格 (修正：id_vars 改為 'Year')
    df_melt = df_interp.reset_index().melt(id_vars='Year', var_name='Company', value_name='Market Cap')
    
    # 3. 每一幀重新計算排名
    df_melt['Rank'] = df_melt.groupby('Year')['Market Cap'].rank(method='first', ascending=False)
    
    # 4. 只保留 Top 10
    df_final = df_melt[df_melt['Rank'] <= 10].copy()
    
    # 補回 Sector 資訊
    df_final['Sector'] = df_final['Company'].map(sector_map)
    
    # 格式化顯示文字
    df_final['Label'] = df_final.apply(lambda x: f" {x['Company']} (${int(x['Market Cap'])}B)", axis=1)

    return df_final.sort_values(['Year', 'Rank'])

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
    with tab2:  # 請確認這裡的 tab 變數名稱是否對應您的設定 (例如 tab2 或 tab3)
    st.header("全球市值霸主競賽")
    st.caption("動態展示全球頂尖企業的市值消長")
    
    # 加入按鈕，避免網頁一開啟就自動運算卡住
    if st.button('▶️ 開始競賽', key='btn_race'):
        
        # 顯示進度提示
        with st.spinner('正在計算數據並繪製動畫，請稍候...'):
            
            # 1. 準備數據 (假設使用全域變數 df_history，若無請確保有讀取數據)
            # 這裡進行插值讓動畫更順暢
            df_race = df_history.copy()
            
            # 2. 設定畫布
            fig, ax = plt.subplots(figsize=(10, 6))
            
            # 定義顏色 (固定每間公司的顏色)
            unique_stocks = df_race.columns
            colors = plt.cm.tab10(np.linspace(0, 1, len(unique_stocks)))
            color_map = dict(zip(unique_stocks, colors))

            def update(current_frame):
                # -------------------------------------------------------
                # [關鍵修正 1] 清除上一幀畫面
                # 這行指令是拿掉「飛入特效」的關鍵，確保每一幀都是乾淨重畫
                # -------------------------------------------------------
                ax.clear()
                
                # A. 取得當前幀數據並排序 (數值大的在下面，Matplotlib barh 預設由下往上畫)
                dff = df_race.iloc[current_frame].sort_values(ascending=True)
                
                # B. 繪製 Bar
                bar_colors = [color_map[name] for name in dff.index]
                bars = ax.barh(dff.index, dff.values, color=bar_colors, height=0.8)
                
                # -------------------------------------------------------
                # [關鍵修正 2] 將文字固定在 Bar 的右側
                # -------------------------------------------------------
                # 設定文字與 Bar 的間距 (動態計算：最大值的 1%)
                dx = dff.values.max() * 0.01
                
                for bar, name in zip(bars, dff.index):
                    width = bar.get_width() # 取得 Bar 長度
                    
                    # --- 數值文字 (固定在右側) ---
                    # x 座標 = width + dx
                    # ha='left' 讓文字向右延伸
                    ax.text(width + dx, 
                            bar.get_y() + bar.get_height()/2, 
                            f'{width:,.0f}', 
                            ha='left', va='center', size=12, weight='bold')
                    
                    # --- 公司名稱 (固定在 Bar 內部左側) ---
                    ax.text(dx, 
                            bar.get_y() + bar.get_height()/2, 
                            name, 
                            ha='left', va='center', color='white', weight='bold', size=10)

                # C. 調整樣式與座標軸
                # 顯示當前時間/幀數
                ax.text(1, 0.4, f'Day: {current_frame}', transform=ax.transAxes, 
                        color='#777777', size=40, ha='right', weight=800, alpha=0.3)
                
                # [重要] 設定 X 軸範圍，確保右邊文字不會被切掉
                # 必須比最大值大一點 (例如 1.2 倍)
                ax.set_xlim(0, dff.values.max() * 1.2)
                
                ax.set_title('Global Market Cap Race', size=16, weight='bold', loc='left')
                ax.xaxis.set_ticks_position('top')
                ax.tick_params(axis='x', colors='#777777')
                ax.set_yticks([]) # 隱藏 Y 軸標籤 (因為已寫在 Bar 內)
                ax.grid(which='major', axis='x', linestyle='--', alpha=0.5)
                
                # 移除邊框
                plt.box(False)

            # 3. 建立動畫
            # interval=100 代表每 0.1 秒換一張
            anim = animation.FuncAnimation(fig, update, frames=len(df_race), interval=100)
            
            # 4. 輸出到 Streamlit
            components.html(anim.to_jshtml(), height=600)
            
            # 關閉圖表釋放記憶體
            plt.close(fig)

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