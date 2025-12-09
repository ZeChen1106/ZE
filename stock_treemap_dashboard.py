import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

# ==========================================
# 1. 準備數據 (這裡用隨機數據模擬，請替換成您的 df)
# ==========================================
# 假設有 10 個類別，跑 100 幀 (年份或時間點)
categories = ['台積電', '聯發科', '鴻海', '大立光', '中華電', '富邦金', '國泰金', '台塑', '中鋼', '南亞']
n_frames = 100

# 建立模擬數據：隨機增長
np.random.seed(42)
df = pd.DataFrame(np.random.rand(n_frames, len(categories)) * 100, columns=categories)

# 讓數據累加並平滑化 (模擬股票或營收累積)
for col in df.columns:
    df[col] = df[col].cumsum()  # 累積數值
    df[col] = df[col].interpolate()  # 插值平滑

# ==========================================
# 2. 設定畫布與參數
# ==========================================
fig, ax = plt.subplots(figsize=(12, 8))

# 定義顏色 (可選)
colors = plt.cm.tab10(range(len(categories)))
color_map = dict(zip(categories, colors))

def update(current_frame):
    """
    每一幀執行的繪圖函式
    """
    # 1. 取得當前這一幀的數據
    dff = df.iloc[current_frame]
    
    # 2. 排序：讓數值大的在上方 (Matplotlib 的 barh 預設由下往上，所以數值大排後面)
    dff = dff.sort_values(ascending=True)
    
    # ==========================================
    # [關鍵修正 1] 清除畫面，防止文字從左上角(0,0)飛入的特效
    # ==========================================
    ax.clear()
    
    # 3. 繪製水平條形圖
    # 根據索引對應顏色，確保Bar移動時顏色跟著走
    bar_colors = [color_map[name] for name in dff.index]
    bars = ax.barh(dff.index, dff.values, color=bar_colors, height=0.8)
    
    # ==========================================
    # [關鍵修正 2] 將文字固定在 Bar 的右側
    # ==========================================
    # 計算一個動態間距 (最大值的 1%)，讓文字不要貼太緊
    dx = dff.values.max() * 0.01
    
    for bar, name in zip(bars, dff.index):
        width = bar.get_width() # 取得 Bar 的長度 (數值)
        
        # ax.text(x座標, y座標, 文字內容, ...)
        # x座標 = width + dx (Bar長度 + 間距)
        # ha='left' (水平對齊左側) -> 這樣文字就會往右延伸
        ax.text(width + dx,         # x 座標
                bar.get_y() + bar.get_height()/2, # y 座標 (Bar 的中心高度)
                f'{width:,.0f}',    # 文字內容 (數值格式化)
                ha='left',          # 靠左對齊 (文字起點在 x 座標)
                va='center',        # 垂直置中
                size=12,            # 字體大小
                weight='bold')      # 粗體

        # (額外功能) 在 Bar 內部左側顯示類別名稱
        ax.text(dx, 
                bar.get_y() + bar.get_height()/2, 
                name, 
                ha='left', va='center', color='white', weight='bold')

    # 4. 裝飾圖表細節
    # 在右下角顯示當前進度/年份
    # transform=ax.transAxes 代表使用相對座標 (0~1)
    ax.text(1, 0.4, f'Frame: {current_frame}', transform=ax.transAxes, 
            color='#777777', size=46, ha='right', weight=800, alpha=0.5)
    
    # 設定標題
    ax.set_title('動態競賽圖 (Race Chart)', size=20, weight='bold', pad=20)
    
    # 設定 X 軸範圍 (隨著最大值動態調整，並多留 15% 空間給右側文字)
    ax.set_xlim(0, dff.values.max() * 1.15)
    
    # 隱藏不必要的邊框和刻度
    ax.xaxis.set_ticks_position('top') # X軸刻度移到上面
    ax.tick_params(axis='x', colors='#777777', labelsize=12)
    ax.set_yticks([]) # 隱藏 Y 軸刻度 (因為名稱已經寫在 Bar 裡面了)
    ax.grid(which='major', axis='x', linestyle='--', alpha=0.5)
    
    # 移除四邊的黑色框線
    for spine in plt.gca().spines.values():
        spine.set_visible(False)

# ==========================================
# 3. 產生動畫
# ==========================================
# interval=100 代表每 100 毫秒換一張 (速度可調)
anim = animation.FuncAnimation(fig, update, frames=range(n_frames), interval=100, repeat=False)

# 顯示動畫 (如果您在 Jupyter Notebook)
# from IPython.display import HTML
# HTML(anim.to_jshtml())

# 儲存為 GIF (需要安裝 pillow) 或 MP4 (需要 ffmpeg)
print("正在儲存動畫...")
anim.save('race_chart_fixed.gif', writer='pillow')
print("完成！檔案已儲存為 race_chart_fixed.gif")

plt.close()