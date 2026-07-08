# 每日戰略新聞簡報(Daily Strategic News Briefing)

每個工作日(週一至週五)**台北時間 07:30** 自動產製的全球科技/地緣/資本市場簡報。

## 運作方式
- 由 Claude Code「Routine(排程)」在每個工作日清晨觸發一個全新 session(在 Anthropic 雲端 VM 執行,無需使用者電腦開機)。
- 該 session 依 [`SPEC.md`](./SPEC.md) 規格:讀取本資料夾近期簡報去重 → 網路研究 → 產出 A–G 結構簡報 → commit 至本資料夾 → 於 Gmail 建立完整全文草稿。
- 每日檔案:`briefings/YYYY-MM-DD.md`。

## 核心原則
極致事實準確度:區分事實與機構預測、證據導向、濾除極端值、報價附時點與層級、羅生門並列不裁決。詳見 [`SPEC.md`](./SPEC.md)。

## 分支
所有簡報 commit 至 `claude/daily-news-briefing-vh78sn`。

## 交付管道
1. **Repo 存檔**(完整版,永久紀錄與去重依據)。
2. **Gmail 草稿**(完整版)。
3. **排程完成 email 通知**至 inbox。

> 註:目前連接的 Gmail 整合僅能**建立草稿**,無法直接寄送;inbox 遞送由排程完成通知信負責。
