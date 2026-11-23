# Workflow Graph 與動態 Loop

```
A 最終版資料盤點 ─→ B 文獻 Ingest 與 Wiki 更新 ─→ [C Wiki Lint／技術查核]
                                                        │通過
                                                        ▼
                         D Wiki 查詢與簡報大綱 ─→ [E 覆蓋率與來源檢查]
                                                        │通過
                                                        ▼
                         F 逐頁生成 HTML ─→ [G 技術忠實度、功能與渲染檢查] ─→ H 最終交付與檢查報告
```

C、E、G 是固定的檢查關卡。任何節點都可能因檢查失敗而回退。

## 失敗分類與回退節點

| 錯誤類型（type） | 說明 | 回退到 |
|---|---|---|
| `raw-missing` | 需要的原始資料沒凍結、引用檔不在 MANIFEST、雜湊不符 | A |
| `uncited` | 含數字或技術敘述沒有 `[src:]` | B |
| `misquote` | 敘述與來源內容不符（數字、條件、狀態） | B |
| `status-wrong` | 現役／曾用／僅參考標錯（例如把已關閉的層寫成現役） | B |
| `link-broken` | 條目連結、行號範圍、json 鍵無效 | B |
| `coverage-gap-wiki` | 大綱主題在 Wiki 沒有條目 | B（左移：在 E 攔下） |
| `coverage-gap-outline` | Wiki 有條目但大綱沒引用／引用錯頁 | D |
| `html-mismatch` | HTML 內容與 Wiki 不符 | F（若 Wiki 本身錯 → B） |
| `render` | 溢出、換頁、圖片、連結、手機寬度 | F |
| `privacy` | 不公開資訊出現 | 出現處（B 或 F） |
| `human-conflict` | 模型、硬體型號、參數、成績、來源互相矛盾且規則無法判定 | **停止**，寫入 `wiki/conflicts.md` 等人工 |

## 規則

- 同一個問題（issue）最多自動修正 3 輪；第 3 輪仍失敗 → 標 `needs-human`，停止該問題，其他問題繼續。
- 每次檢查都寫一筆 `checks/loop-log.jsonl`，通過也要寫。不刻意製造錯誤。
- H 節點以 `tools/loop_stats.py` 統計各節點失敗次數、錯誤類型、平均輪數，反思用這些數字。

## loop-log.jsonl 欄位

| 欄位 | 說明 |
|---|---|
| `ts` | 時間 |
| `issue` | 問題編號（同一問題跨輪相同） |
| `round` | 第幾輪（1 起） |
| `node` | 發生檢查的節點（A～H） |
| `check` | 執行哪種檢查（auto-lint／ai-review／human／render…） |
| `result` | Pass／Fail |
| `type` | 錯誤類型（通過時為空） |
| `evidence` | 對應檔案、頁面、來源 |
| `retry_target` | 回退到哪個節點（通過時為空） |
| `fix` | 實際修正內容 |
| `recheck` | 再次驗證結果（Pass／Fail／pending） |
