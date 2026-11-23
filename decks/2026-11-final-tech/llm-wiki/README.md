# 自走車 LLM Wiki（公開精簡版）

這是「視覺循線自走車最終競賽版」的 LLM Wiki。同一資料夾上層的 15 頁簡報，就是以這份 Wiki 為知識來源做出來的。
架構依 Karpathy 的 LLM Wiki 三層設計：

| 層 | 位置 | 說明 |
|---|---|---|
| Raw Sources | `raw/MANIFEST.tsv` | 原始資料清單：最終版程式與設定、韌體、開發紀錄，以及 7 份外部文獻。每份都記了來源、SHA256 與取得日期。**原始檔不公開**，因為開發紀錄裡含網路位址與帳號資訊；條目中的 `[src: raw/…#L行號]` 指向這些凍結檔，可以用雜湊驗證 |
| Wiki | `wiki/` | 40 頁條目，從 `wiki/index.md` 進入。每頁標示狀態：implemented＝最終版在用、used-before＝曾用、reference-only＝僅參考 |
| Schema | `AGENTS.md`、`workflow/graph.md` | Ingest、Query、Lint 規則，以及 A～H 的 Workflow Graph 與回退規則 |

## Workflow Graph

```
A 最終版資料盤點 → B 文獻 Ingest／Wiki 撰寫 → [C Lint＋AI 查核]
  → D 以 Wiki 查詢產生大綱（deck/outline.md） → [E 覆蓋率與來源檢查]
  → F 逐頁生成 HTML → [G 忠實度、功能與渲染檢查] → H 交付與統計
```

- C、E、G 是固定的檢查關卡。
- 檢查失敗時，先分類錯誤再決定回退到哪個節點，規則表在 `workflow/graph.md`。
- 同一個問題最多自動修正 3 輪。
- 型號、參數、成績互相矛盾時，記入 `wiki/conflicts.md` 等人工決定。

## 執行紀錄與統計

- `checks/loop-log.jsonl`：每次檢查一筆，欄位有節點、檢查、結果、證據、錯誤類型、回退節點、修正、重檢結果。
- `checks/loop-stats.md`：各節點的失敗次數統計，由 `tools/loop_stats.py` 產生。
- `checks/lint-*.md`：Lint 報告。`lint-20261123-225959.md` 是第一次執行時的警告，其餘是修正後的結果。
- `checks/ai-review-1.md`：獨立 AI 查核，抽查 132 處引用。
- `checks/coverage-*.md`：大綱覆蓋率檢查。
- `checks/deck-*.md`：簡報靜態檢查。

## 工具

`tools/` 是實際使用的腳本：
- `freeze_raw.py`、`ingest_external.py`：凍結原始資料、匯入外部文獻。
- `lint.py`：Wiki 檢查。
- `coverage.py`：大綱覆蓋率檢查。
- `check_deck.py`：簡報靜態檢查。
- `loop_stats.py`：統計檢查紀錄。
- `stats_*.py`、`build_*.py`：統計與產圖。

腳本裡的路徑是作者本機的路徑。公開版移除了不公開資訊比對清單中的主機與網路名稱。
