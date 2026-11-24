# Wiki 更新紀錄

每筆一個標題（`grep "^## \["` 可列出）。類型：建立、Ingest、更新、檢查、規則。

## [2026-11-23] 規則 | 建立 Wiki
- 建立 AGENTS.md（Schema）、workflow/graph.md（Workflow Graph 與 Loop 規則）、tools/lint.py、tools/loop_stats.py。

## [2026-11-23] Ingest | 最終版原始資料（節點 A）
- tools/freeze_raw.py 凍結 251 筆：最終版快照 20261123d 全部檔案（先與其 MANIFEST.sha256 逐檔核對）、現役韌體 pwm100_v1、協定與硬體說明、11-05 版 IMU 紀錄程式、模型 v4 設定與指標、分析檔、三份開發紀錄、run-b541 摘要、NVIDIA 載板規格書；run-b541 逐格紀錄只記雜湊不複製。

## [2026-11-23] 建立 | 第一批條目（節點 B）
- 29 頁：hardware 3、perception 2、path 4、control 11、comms 2、experiments 4、sources 1、synthesis 1、overview。
- Ingest 來源摘要：sources/nvidia-carrier-board-spec。其他外部文獻待使用者授權下載。
- 未決衝突 16 條整理於 conflicts.md。
- 統計腳本：tools/stats_vision_validity.py、tools/stats_timing.py（讀 run-b541 逐格紀錄）。

## [2026-11-23] 檢查 | 節點 C 第 1 輪
- 自動 Lint：第 1 次 5 個警告（未引用的數字行），修正後 0 錯誤 0 警告。
- AI 獨立抽查 132 處引用：正確 118、部分正確 8、錯誤 3、錯位 3（checks/ai-review-1.md）。主對話逐項對照 raw 後修正 13 項；其中「PID D 項用控制誤差」一項經查 NearDerivativePID 確實改寫前一格誤差，條目原文正確，不改，只補 feedforward 項說明。
- 新增 synthesis/glossary（名詞與地標代號），處理抽查指出的未解釋名詞。

## [2026-11-23] 檢查 | 節點 D／E
- deck/outline.md：15 頁大綱，每頁連到 Wiki 條目、公式、圖表與待決衝突。
- tools/coverage.py：0 問題（checks/coverage-20261123-230922.md）；以故意寫錯的暫存大綱做負向測試，6 個問題全抓到。
- 外部文獻 Ingest 只完成 1 份（NVIDIA 規格書），其餘待使用者授權下載。

## [2026-11-23] Ingest | 外部文獻 6 份（使用者授權下載）
- Ultralytics 語意分割文件（另存實例分割頁對照）、Ultralytics Jetson 指南、OpenCV 4.13.0 單應性教學、InvenSense MPU-6000/6050 暫存器表（官網連結失效，改用經銷商鏡像）、Macenski 2023 Regulated Pure Pursuit（arXiv）、Thrun 2006 Stanley。
- tools/ingest_external.py：HTML 另轉純文字檔供行號引用；全部記入 MANIFEST（來源網址、SHA256、取得日、版本說明）。
- 連同既有的 NVIDIA 載板規格書，獨立外部來源共 7 份；其中 Pure Pursuit、Stanley 標 reference-only。

## [2026-11-23] 更新 | 衝突決策
- 依使用者決定關閉 D1、D2、D3（寫法）、D4（分開列）、H-1（註明限制）、H-2；P-1 與其他項維持 open。

## [2026-11-23] 檢查 | 節點 F／G
- HTML 草稿 autocar-devlog/decks/2026-11-final-tech（15 頁）。G：靜態檢查 0 問題；1280×720 有 6 頁超出，追加 .slide.dense 緊湊樣式後全部通過；375 px 無水平捲軸；換頁、圖片正常。未 commit、未發布。

## [2026-11-23] 更新 | 簡報補圖（F／G）
- P02 曝光對照（11-17 隧道口靜態比對，背景模糊；來源凍結為 raw/records/analyses/expo-20261117）、P11 一格命令計算鏈（run-b541 兩格實例）、P14 圈速時間線（依 experiments/lap-progression）。產生腳本 tools/build_missing_figs.py。
- G：加圖後 P02、P11 超出一屏，次要清單移到講者備註後通過。

## [2026-11-24] 更新 | IMU 紀錄程式版本更正
- 使用者提問「為什麼用 11-05 版」後查出：11-05 18:59 已換成 r6（啟動等靜止再估零點），先前只凍結 r5。已補凍結 r6 與上車驗收紀錄，更新 hardware/imu-mpu6050、synthesis/imu-roles、conflicts H-1；新增 tools/stats_imu_age.py（最終版 IMU 資料年齡 0～24 ms，與 50 Hz 相符）。
