# ----------------------------------------------------------------------
# S&P 500 股市儀表板 (CacheReplayClosureError 修正版)
# ----------------------------------------------------------------------

import streamlit as st
import plotly.express as px
import yfinance as yf
import pandas as pd
import time
from datetime import datetime

# --- 1. Streamlit 頁面設定 ---
st.set_page_config(
    page_title="S&P 500 全方位趨勢儀表板", 
    layout="wide"
)

st.markdown("""
<style>
    .block-container { padding-top: 1rem; padding-bottom: 2rem; }
    h3 { margin-top: 2rem; border-bottom: 2px solid #f0f2f6; padding-bottom: 0.5rem; font-family: 'Arial Black', sans-serif; }
    .stAlert { padding-top: 0.5rem; padding-bottom: 0.5rem; }
</style>
""", unsafe_allow_html=True)

st.title("📊 S&P 500 市場趨勢儀表板")
st.caption("自動更新機制：數據每 6 小時自動更新一次 (涵蓋美股收盤)，亦可手動刷新。")

# --- 2. 側邊欄控制 ---
st.sidebar.header("⚙️ 控制台")

if st.sidebar.button('🔄 強制更新數據', type="primary"):
    # 在清除快取前先清空狀態，避免衝突
    st.cache_data.clear()
    st.session_state.pop('last_update', None)
    st.rerun()

# 顯示上次更新時間
if 'last_update' in st.session_state:
    st.sidebar.success(f"資料時間: {st.session_state['last_update']}")


# --- 3. 數據獲取：成分股清單 (無 UI 輸出) ---
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


# --- 4. 數據獲取：市值 (無 UI 輸出) ---
@st.cache_data(ttl=24 * 3600)
def fetch_market_caps(tickers):
    """抓取市值 (純 I/O 操作)"""
    caps = {}
    
    # 注意：這裡不能有 st.progress 或 st.toast
    for ticker in tickers:
        try:
            caps[ticker] = yf.Ticker(ticker).fast_info['market_cap']
        except:
            caps[ticker] = 0
            
    return caps

# --- 5. 數據獲取：歷史價格 (無 UI 輸出) ---
@st.cache_data(ttl=21600) # 6小時自動更新一次
def fetch_price_history(tickers):
    """
    下載過去一年的股價歷史數據。
    """
    try:
        data = yf.download(
            tickers, 
            period="1y", 
            group_by='ticker', 
            auto_adjust=True, 
            threads=True, 
            progress=False
        )
        return data
    except Exception:
        return pd.DataFrame()

# --- 6. 數據處理與計算 (純 Pandas 操作) ---
def process_data_for_periods(sp500_df, history_data, market_caps):
    # 這裡的邏輯與之前保持一致 (省略重複代碼，確保純計算)
    results = []
    tickers = sp500_df['Ticker'].tolist()
    
    for ticker in tickers:
        try:
            if ticker not in history_data.columns.levels[0]:
                continue
                
            stock_df = history_data[ticker]['Close'].dropna()
            if len(stock_df) < 2: 
                continue

            last_price = stock_df.iloc[-1]
            mkt_cap = market_caps.get(ticker, 0)
            
            # 計算各週期漲跌幅
            chg_1d = stock_df.pct_change(1).iloc[-1] * 100
            chg_1w = stock_df.pct_change(5).iloc[-1] * 100 if len(stock_df) > 5 else 0
            chg_1m = stock_df.pct_change(21).iloc[-1] * 100 if len(stock_df) > 21 else 0
            chg_ytd = ((last_price - stock_df.iloc[0]) / stock_df.iloc[0]) * 100
            
            row = sp500_df[sp500_df['Ticker'] == ticker].iloc[0]
            
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
        except Exception:
            continue
            
    return pd.DataFrame(results)

# --- 7. 繪圖函數 (保持不變) ---
def plot_treemap(df, change_col, title, color_range):
    # 這裡的程式碼與前面保持一致，確保字體設定正確
    df['Label'] = df.apply(lambda x: f"{x['Ticker']}\n{x[change_col]:+.2f}%", axis=1)
    
    fig = px.treemap(
        df,
        path=[px.Constant(title), 'Sector', 'Industry', 'Ticker'],
        values='Market Cap',
        color=change_col,
        color_continuous_scale='RdYlGn', 
        color_continuous_midpoint=0,
        range_color=color_range,
        custom_data=['Name', 'Close', change_col]
    )
    
    fig.update_traces(
        textinfo="label+text",
        textfont=dict(family="Arial Black", size=15), 
        hovertemplate='<b>%{label}</b><br>股價: $%{customdata[1]:.2f}<br>漲跌幅: %{customdata[2]:.2f}%'
    )
    
    fig.update_layout(
        height=600, 
        margin=dict(t=40, l=10, r=10, b=10),
        font=dict(family="Arial", size=14),
        title_font=dict(family="Arial Black", size=20)
    )
    
    st.plotly_chart(fig, use_container_width=True)

# --- 8. 主程式 (在外部處理 Loading 狀態) ---
def main():
    
    if 'last_update' not in st.session_state:
        st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 必須使用 st.spinner 在外部包裹數據獲取過程
    with st.spinner('正在載入數據 (如果超過 6 小時未更新，會自動重新下載)...'):
        # A. 獲取資料
        sp500 = get_sp500_constituents()
        if sp500.empty:
            st.error("無法取得成分股清單。")
            return
            
        tickers_list = sp500['Ticker'].tolist()
        
        # B. 抓取數據
        market_caps = fetch_market_caps(tickers_list)
        history_data = fetch_price_history(tickers_list)
        
        # C. 處理數據
        if history_data.empty:
            st.error("無法取得股價數據，請稍後再試。")
            return
            
        final_df = process_data_for_periods(sp500, history_data, market_caps)
        
    # D. 檢查與顯示
    if final_df.empty or final_df['Market Cap'].sum() == 0:
        st.warning("數據處理完成，但無有效市值數據可繪圖。")
        return
        
    # 過濾無效資料並顯示圖表
    final_df = final_df[final_df['Market Cap'] > 0]

    # E. 顯示四張圖表
    st.subheader("🌞 1 日短期趨勢 (Daily)")
    plot_treemap(final_df, '1D Change', 'S&P 500 (1 Day)', [-4, 4])
    
    st.subheader("📅 1 週趨勢 (Weekly)")
    plot_treemap(final_df, '1W Change', 'S&P 500 (1 Week)', [-8, 8])
    
    st.subheader("🌕 1 月趨勢 (Monthly)")
    plot_treemap(final_df, '1M Change', 'S&P 500 (1 Month)', [-15, 15])
    
    st.subheader("📅 1 年/長期趨勢 (YTD)")
    plot_treemap(final_df, 'YTD Change', 'S&P 500 (1 Year)', [-40, 40])
    
    # 成功運行後更新時間
    st.session_state['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

if __name__ == '__main__':
    main()