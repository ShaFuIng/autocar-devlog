# 自走車 LLM Wiki：Schema 與維護規則

本專案依 Karpathy「LLM Wiki」的三層架構，整理視覺循線自走車最終競賽版的技術知識，供競賽技術簡報（autocar-devlog）查詢。
使用繁體中文。AI 開始任何工作前先讀完本檔。

## 1. 三層架構

| 層 | 位置 | 誰寫 | 規則 |
|---|---|---|---|
| Raw Sources | `raw/` | `tools/freeze_raw.py` 凍結複製；外部文獻經使用者授權下載 | **只加不改**。每檔在 `raw/MANIFEST.tsv` 有原路徑、SHA256、取得日期。來源更新時另存新版本，不覆寫舊檔 |
| Wiki | `wiki/` | LLM 撰寫與維護，人審 | 依第 3～4 節格式；每項技術敘述可追溯到 raw |
| Schema | 本檔、`workflow/` | 人與 AI 共同維護 | 規則變更寫在這裡並記入 `wiki/log.md` |

- 自走車原始專案 `D:\OneDrive\Desktop\自走車` **永遠唯讀**：不修改控制程式、模型、設定、測試資料；不連線車輛做任何動作。
- 「最終版」＝使用者 11-23 定版的車上快照 `raw/project/snapshot-20261123d/`（與車上逐檔核對過）＋現役韌體 `raw/project/firmware-pwm100_v1/`。

## 2. 資料衝突的優先順序

1. 實作內容：最終版原始碼與設定 ＞ 程式內說明文字（docstring、json 的 note）＞ 開發紀錄 ＞ 舊查核文件。
   - 例：檔頭寫「NOT deployed」但 json `enabled: true` 且主程式有呼叫 → 以程式為準算現役，並在條目註明說明文字過時。
2. 實測成績：原始測試紀錄（run 的 summary／逐格紀錄、紀錄檔中逐輪數字）為準。
3. 無法依以上規則判定的衝突（模型、硬體型號、參數、成績、來源互相矛盾）→ 寫入 `wiki/conflicts.md`，狀態 `open`，**不自行選答案**，等人工決定。

## 3. 條目格式

每個條目是一個 Markdown 檔，開頭有 frontmatter：

```
---
id: control/yaw-inner            # 與檔案路徑相同（不含 .md）
title: 陀螺儀內迴圈壓住直線 S 型
status: implemented              # implemented | used-before | reference-only | mixed
sources:                         # 本頁引用的 raw 檔（相對 Wiki 根目錄）
  - raw/project/snapshot-20261123d/yaw_inner.py
verified_against: snapshot-20261123d
updated: 2026-11-23
---
```

- `status`
  - `implemented`＝最終版確實在用（json 開啟且主程式有呼叫）。
  - `used-before`＝曾上車或曾用過，最終版已關閉或已替換。
  - `reference-only`＝僅研究參考、提案、比較，從未上車。
  - `mixed`＝同一頁有多種狀態，每段要個別標出（用 `【現役】【曾用】【僅參考】`）。
- 每頁固定段落：`## 一句話結論`、`## 內容`、`## 公式與參數`（沒有就寫「無」）、`## 未確認`、`## 相關條目`。

## 4. 引用格式（Lint 會自動檢查）

- 引用 raw：`[src: raw/<路徑>#L<起>-L<迄>]`、`[src: raw/<路徑>#L<行>]`，或 json 鍵 `[src: raw/<路徑>#key=<鍵名>]`，或整檔 `[src: raw/<路徑>]`。
- 引用其他條目：`[[control/pid-core]]`（不加 .md）。
- **含數字的技術敘述行（段落或條列）必須至少有一個 `[src: …]`**。數字照原始資料寫，不四捨五入成更好看的數字；推算值要寫「推算」並列出算式。
- 紀錄檔（AGENTS 系列）要引用到行號。
- 每個係數註明性質：實測值／調參值／設計假設。

## 5. 資料夾

```
raw/            Raw Sources（MANIFEST.tsv）
  project/      最終版程式、韌體、協定、模型設定
  records/      開發紀錄、分析、實跑摘要
  official/     官方文件、規格書
  papers/       論文
wiki/
  index.md      全部條目目錄（Lint 檢查完整性）
  log.md        Wiki 更新紀錄（只往下加）
  overview.md   系統總覽
  conflicts.md  未決衝突
  hardware/ perception/ path/ control/ comms/ experiments/ sources/ synthesis/
workflow/       Workflow Graph 與 Loop 規則
deck/           簡報大綱（節點 D 產物；tools/coverage.py 檢查）
checks/         Lint 報告、loop-log.jsonl、統計
tools/          freeze_raw.py、lint.py、coverage.py、loop_stats.py、stats_timing.py、stats_vision_validity.py
```

## 6. 操作

### Ingest（加入新來源）
1. 來源放進 `raw/` 適當子資料夾（外部文件需使用者授權下載），更新 `MANIFEST.tsv`。
2. 在 `wiki/sources/` 寫一頁來源摘要：書目資訊、重點、與本車的關係（確實採用／曾用／僅參考）、不適用之處。
3. 更新受影響的條目與交叉連結、`index.md`、`log.md`。

### Query（查詢，例如做簡報大綱）
- 只用 Wiki 條目回答，回答附條目 id；Wiki 沒有的內容標「Wiki 缺」，回到 Ingest 補，不從記憶補。

### Lint（檢查）
- `python tools/lint.py` → `checks/lint-<時間>.md`。
- 自動檢查：frontmatter、status 值、引用檔存在於 MANIFEST 且雜湊相符、行號範圍有效、json 鍵存在、條目連結有效、孤立頁、index 完整、含數字的敘述有引用、不公開資訊。
- AI 審查：敘述是否忠於來源、狀態標記是否正確、專有名詞第一次出現有無解釋。

## 7. 不公開資訊

Wiki 不公開，但仍不寫入條目：IP 位址、主機名稱、帳號、金鑰路徑、Wi-Fi 名稱與密碼、個人姓名與信箱。raw 的原始紀錄可能含這些資訊，不得引用原文到條目中。

## 8. Workflow 與 Loop

見 `workflow/graph.md`。每次檢查都寫一筆 `checks/loop-log.jsonl`。
