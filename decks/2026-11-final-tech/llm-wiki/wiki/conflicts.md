# 未決衝突（conflicts）

依 AGENTS.md 第 2 節無法自動判定的衝突。狀態 `open` 的項目**只能由人工關閉**；關閉時寫下決定、決定者與日期，並更新受影響條目。

| 編號 | 主題 | 狀態 | 影響簡報頁 |
|---|---|---|---|
| D1 | 封面成績用哪個圈速 | 已決 | 13 |
| D2 | 效能比是否用推算值、圈長取哪個 | 已決 | 13 |
| D3 | yaw_inner 角色兩次模型結論相反 | 已決（寫法） | 7 |
| D4 | 迴路延遲數字 | 已決（分開列） | 7、11 |
| D5 | run 編號重號 | open | 14 |
| B-1 | curve_map 彎角表與說明檔彎角 | open | 8 |
| B-2 | 路口窗口位置（說明檔為舊版） | open | 7 |
| B-3 | arc2.c3.top 上限表未隨中心平移 | open | 8 |
| C-1 | 編碼器與馬達腳位編號相同 | open | 1、10 |
| C-2 | 命令→車頭延遲兩個估計（併 D4） | open | 7 |
| C-3 | 影像年齡經驗值與最終輪實測 | open（低） | 1、13 |
| P-1 | 馬達驅動器型號 XY160D／DRV1011 | open | 1 |
| P-2 | 舊舵機延遲數值 | open（低） | 7 |
| H-1 | 現役 IMU 紀錄程式未凍結（只有 11-05 版） | 已決（註明限制） | 6 |
| H-2 | 最終版無原始影像，素材要用 11-19 影片＋b541 重繪 | 已決 | 3～10、13 |

---

# 來源：experiments/_conflicts-draft-D.md

以下各條狀態皆為 open，不自行選答案，等人工決定後再併入 `wiki/conflicts.md`。

## D1 封面成績（已決）

- **決定（使用者 2026-11-23 決定）**：用最終版 run-b541 的 56.5 s，明確標示為「賽前實測」，不是正式比賽成績。55.4 s 只在歷史演進需要時提及，並註明是舊舵機。


- 主題：簡報封面／最終表現頁要放哪一個圈速。
- 候選：
  1. 56.5 s：最終定版快照 20261123d 的 run-b541（56.5／56.8 s，無失敗）[src: raw/records/logs/AGENTS_LOG_202611.md#L1730] [src: raw/project/snapshot-20261123d/README.md#L4]。上午 run-5b69（舊舵機、不同設定）也是 56.5 s [src: raw/records/logs/AGENTS_LOG_202611.md#L1452]。
  2. 56.0 s：新舵機時期最快單圈 run-5f69（快照 20261123c，比最終版少兩檔改動）[src: raw/records/logs/AGENTS_LOG_202611.md#L1703]。
  3. 55.4 s：全期最快單圈 run-9729（舊舵機，舵機故障更換前；下一輪即撞隧道）[src: raw/records/logs/AGENTS_LOG_202611.md#L1603] [src: raw/records/logs/AGENTS_LOG_202611.md#L1622-L1632]。
  4. 55.7 s：run-d380（舊舵機）[src: raw/records/logs/AGENTS_LOG_202611.md#L1584]。
- 附註：11-23 圈速是「各段加總」，與更早的「彎 1 入→彎 1 入」「彎 1 計圈」定義不同 [src: raw/records/logs/AGENTS_LOG_202611.md#L1452] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L367]。
- 需人決定：封面用哪個、是否註明「最終版」或「舊舵機」。

## D2 效能比是否使用推算值（已決）

- **決定（使用者 2026-11-23 決定）**：簡報加入約 83% 的推算效能比，並列出算式 67.6 m ÷ 56.5 s ÷ 1.44 m/s，標「推算」。


- 有紀錄的效能比只到 run-5b69：「67.6 m÷56.5 s÷1.44＝83%」[src: raw/records/logs/AGENTS_LOG_202611.md#L1452]。最終版 run-b541 沒有效能比紀錄 [src: raw/records/logs/AGENTS_LOG_202611.md#L1730-L1734]。
- 推算（未經紀錄）：67.6 ÷ 56.5 ÷ 1.44 ≈ 0.831（約 83%）；第二圈 56.8 s 則 ≈ 0.826。
- 圈長紀錄值不一：67.71±0.24 m（11-13）、67.5～67.7 m（11-22）、67.6 m（11-23 計算用）、67.1 m（11-20 計算用）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L403] [src: raw/records/logs/AGENTS_LOG_202611.md#L1401] [src: raw/records/logs/AGENTS_LOG_202611.md#L1452] [src: raw/records/logs/AGENTS_LOG_202611.md#L334]。更正（主對話複核）：67.72 m 有出處，是最終版地標定位的設定值 lap_m [src: raw/project/snapshot-20261123d/lap_pos.json#key=lap_m]，屬設定而非量測；量測值最接近的是 67.71±0.24 m。
- 需人決定：是否在簡報使用推算值；用哪個圈長。

## D3 yaw_inner 角色的兩次模型結論相反（已決：寫法）

- **決定（使用者 2026-11-23 決定）**：可以介紹實際機制、啟動範圍與增益調整紀錄；不宣稱沒有實驗證據的改善幅度，也不把相關性說成因果。兩次模型結論的分歧仍保留為未解。


- 11-13 動力學模型：「yaw_inner 是在阻尼而非成因」，關掉在 1.4 m/s 擺幅達 8.8°（變差）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L404]。
- 11-18 閉迴路重播模型：「真正維持晃動的是 yaw_inner 本身」，關掉時晃的圈 ×0.32 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L646]。
- 兩者皆模型、條件不同（張數、間隙補償門檻），都沒有實車關閉 yaw_inner 的驗證；使用者 11-18 決定不加測關閉組 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L655]。
- 需人決定：簡報第 7 頁（直線 S 型）如何描述 yaw_inner 的效果。

## D4 迴路延遲數字（已決：分開列）

- **決定（使用者 2026-11-23 決定）**：兩種延遲先確認量測定義，不能混用；無法確認就只列證據明確的量測值與條件。
- **處理**：11-07 的數字是「命令→車頭轉速反應的互相關峰值 0.5～0.6 s，加上相機→PID、PID→控制板，合計約 0.75 s 的迴路延遲」（舊連桿、約 10 張/s 時期）；車輛事實的 0.24～0.30 s 是「指令→車頭」，與張數無關，量法紀錄沒有寫明。兩者定義不同，簡報分開寫並各附條件，不比較、不換算。


- 11-07 分析：指令→車頭轉速反應 0.5～0.6 s，迴路延遲合計約 0.75 s [src: raw/records/analyses/why-s-weave-20261107-findings.json#L12]。yaw_inner 程式檔頭沿用此說法 [src: raw/project/snapshot-20261123d/yaw_inner.py#L3-L4]。
- 11-13 擬合：純延遲 0.10 s＋一階 0.03 s [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L403]。
- 車輛事實（現行）：指令→車頭延遲約 0.24～0.30 s [src: raw/records/logs/AGENTS.md#L108]。
- 紀錄未說明差異原因（連桿、張數、量法皆不同）。需人決定簡報引用哪個延遲。

## D5 run 編號重號（open，影響引用）

- 11-12 的 run-a674：完整一圈 83.8 s [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L372]。
- 11-19 的 run-a674：彎 1 計圈 64.8 s [src: raw/records/logs/AGENTS.md#L326]。
- 兩者是不同輪（4 碼前綴相同）。需人決定簡報引用時是否加日期區分。

---

# 來源：control/_conflicts-draft-B.md

以下各項依 AGENTS.md 第 2 節無法完全自行判定，狀態 open，待人工決定後併入 `wiki/conflicts.md`。條目內已依「程式＞說明」寫出程式實際行為，未替人工選答案。

## B-1 curve_map 彎角表與專案說明的彎角（open）
- 專案說明檔：「控制器 curve_map 對應：seg=start idx0／1／2＝彎1／彎2／彎3（150°／210°／268°）」[src: raw/records/logs/AGENTS.md#L7]；同檔另記彎 1 實量 150°、彎 2 210° [src: raw/records/logs/AGENTS.md#L111]。
- 最終版 curve_map.json：map_start 140／195／268、map_after_down 145／140／195／268 [src: raw/project/snapshot-20261123d/curve_map.json#L1]；程式說明記 9 輪實測 130～145／180～212／252～278° [src: raw/project/snapshot-20261123d/curve_map.py#L11-L13]。
- 疑點：說明檔的 150／210 可能是跑道幾何彎角，json 是地圖「預期轉角」設定值（另有 margin 25°），兩者未必是同一量。條目採 json 值；需人工確認說明檔該句是否要改寫。

## B-2 路口窗口位置（open）
- 專案說明檔：crossing_pass window0＝彎 2 結束後 0.4～2.2 m；window1＝彎 1 結束後 3.0～4.6 m [src: raw/records/logs/AGENTS.md#L8]。
- 最終版：crossing_pass.json 只有一個窗口，end_m 3.5 [src: raw/project/snapshot-20261123d/crossing_pass.json#key=end_m]；xp_anchor 開啟，錨點＝lap_pos C2e＋2.8 m（curve_map 里程）[src: raw/project/snapshot-20261123d/xp_anchor.json#key=k_m] [src: raw/project/snapshot-20261123d/live_pid.py#L1011-L1021]；程式預設 end_m 2.2 [src: raw/project/snapshot-20261123d/live_pid.py#L1139]。V 字路口改由 arc2.blind r2（C1e+4.8～7.5 m）處理 [src: raw/project/snapshot-20261123d/arc2.json#L257-L259]。
- 條目採最終版設定；說明檔描述的是舊版，是否更正由人工決定。

## B-3 arc2.c3.top 絕對上限表未隨共用中心平移（open）
- single_centre.py 說明：列舉的絕對值會改成「中心＋(值−1480)」，「其他一切已相對於 center_us」[src: raw/project/snapshot-20261123d/single_centre.py#L10-L16]。
- 實作：apply_arc2 對 c3 只改 _c_eff_us、cap_us、band.cap_us，沒有處理 c3.top.table [src: raw/project/snapshot-20261123d/single_centre.py#L97-L117]；top 表為絕對值 1760／1640／1600 µs [src: raw/project/snapshot-20261123d/arc2.json#L556-L573]，程式直接以表值比較 [src: raw/project/snapshot-20261123d/lap_ff.py#L448]。
- 以最終中心 1445 計，1600＝中心＋155（推算）；該表 11-19 寫入時的中心不同。是刻意（以舵機實際位置為準）還是遺漏，資料無法判定。

## 附註：已依規則判定、只在條目註明的說明文字過時（非 open）
- yaw_inner.py 說明「Only on normal flat-path frames」、k 8：程式 r6 起各俯仰都進入、json k 4 [src: raw/project/snapshot-20261123d/yaw_inner.py#L16-L17] [src: raw/project/snapshot-20261123d/yaw_inner.json#key=k_us_per_dps]。
- stuck_stop.json note「LOG mode … never stops」vs mode stop [src: raw/project/snapshot-20261123d/stuck_stop.json#L3-L5]。
- 多支程式說明「NOT deployed」但 json 開啟且被呼叫，清單見 control/disabled-layers 第 F 節。

---

# 來源：comms/_conflicts-draft-C.md

待合併進 `wiki/conflicts.md`。狀態皆為 `open`，未自行選答案。

## C-1 編碼器腳位與馬達腳位編號相同（open）

- 來源 A：`raw/project/firmware-pwm100_v1/Config.h#L12-L13` 馬達方向腳位 MOTOR_A_IN1 4、IN2 5、MOTOR_B_IN1 6、IN2 7。
- 來源 B：`raw/project/firmware-pwm100_v1/Config.h#L43` 編碼器腳位 ENC_A_A 4、ENC_A_B 5、ENC_B_A 6、ENC_B_B 7；同檔 L41 註解「Inferred from drawing; wheel identity and polarity MUST be checked on vehicle」。
- 矛盾：同一個數字腳位不可能同時當馬達輸出與編碼器中斷輸入；可能是 BMduino 不同腳位命名體系，也可能註解過時。編碼器實際有計數（lap_pos 依賴 enc_b），所以實車接線可用，但腳位對應無法從 raw 判定。
- 影響條目：control/lap-position、hardware/vehicle-hardware。

## C-2 命令→車頭（偏航）反應延遲兩個估計差一倍（open）

- 來源 A：`raw/records/analyses/why-s-weave-20261107-findings.json#L12`（11-07）：命令→偏航反應 0.5～0.6 s（相關峰值），迴路總延遲約 0.75 s。
- 來源 B：`raw/records/logs/AGENTS.md#L108`：指令→車頭延遲約 0.24～0.30 s，與每秒張數無關。
- 可能原因：11-08 韌體舵機追蹤速率 1000→2000 µs/s（`raw/project/firmware-pwm100_v1/Config.h#L39` 註解）、或兩者定義不同（互相關峰值 vs 擬合延遲）、或連桿更換。raw 內沒有能判定的資料。
- 影響條目：comms/timing-latency、control/yaw-inner、experiments/s-weave。

## C-3 影像年齡的經驗值與最終輪實測略有出入（open，低優先）

- 來源 A：`raw/records/logs/AGENTS.md#L114`：worker 每格約 49～55 ms、影像年齡中位約 60～85 ms。
- 來源 B：run-b541 逐格紀錄（tools/stats_timing.py，引用 `raw/records/runs/run-b541-20261123/summary.json`）：inference_ms 中位 57.4 ms、consumed_at−capture_at 中位 87.4 ms。
- 說明：不同輪次、紀錄未註明「影像年齡」的計算欄位，無法判定是車況變化還是定義不同。簡報引用最終版數字時建議用 run-b541 的值並註明輪次。
- 影響條目：comms/timing-latency。

## 已依優先順序處理、不列為衝突（供審查）

- PROTOCOL.md 的 MANUAL 油門 ±25%、MOVE ±25%、舵機每 120 ms 10 µs（`raw/project/docs/PROTOCOL.md#L8`、`#L11`、`#L43`）與現役韌體 100%、40 µs／20 ms 不同 → 以程式為準，條目已註明文件過時。
- lap_pos.py、throttle_cap.py、speed_guard.py、single_centre.py 檔頭寫「NOT deployed」，但 json 開啟且主程式有呼叫 → 依規則算現役，條目已註明。
- play_comp.json 附註寫「55 → 25」，數值為 15 → 以數值為準。
- lap_speed.json 區段名稱「c4 back half 58」實際 pwm 64 → 以數值為準。
- lap_pos.py 說明文字的 `lost_after_m` 在程式與 json 中不存在，實際為 skip_after_m／lost_skips。

---

# 來源：path/_conflicts-draft.md

狀態皆為 open；撰寫者未選答案。

## P-1 馬達驅動器型號（open）

- **使用者 2026-11-23 指示**：型號暫不標示，保留未決。


- 說法 A：README 寫「實車驅動器已由使用者確認為 XY160D；圖面標示 `DRV1011`」，並以 XY160D 描述零輸出行為的驗證對象 [src: raw/project/docs/Orin_Interface_v1-README.md#L38-L40]。
- 說法 B：11-03 A1 海報查核寫「馬達驅動器圖面標 DRV1011；使用者曾稱 XY160D，現場型號待確認」，並在第 5 節列為需補充資料 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L33] [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L108]。
- 無法判定原因：兩者都是說明文件，沒有最終版程式或設定能決定硬體型號；README（10 月）說已確認，較晚的查核文件（11-03）卻說待確認。AGENTS.md 第 2 節規則 1 的「說明文字＞開發紀錄＞舊查核文件」排序只適用於實作內容，型號屬硬體事實，需要人看實物或照片決定。
- 影響條目：hardware/vehicle-hardware（目前兩說並列）。

## P-2 舊舵機「指令→車頭延遲」數值

- 說法 A：AGENTS.md 車輛事實段（舊舵機）「指令→車頭延遲約 0.24～0.30 s，與每秒張數無關」[src: raw/records/logs/AGENTS.md#L108]。
- 說法 B：11-23 換舵機紀錄寫新舵機「延遲 0.26 s（舊 0.20）」[src: raw/records/logs/AGENTS_LOG_202611.md#L1646]。
- 補充：同一天改中心後新舵機又量到「延遲 0.20」[src: raw/records/logs/AGENTS_LOG_202611.md#L1661]。
- 無法判定原因：兩者都是原始紀錄中的量測數字，但很可能量法不同（車輛事實段為 11-12 地墊實測與跑圈擬合；11-23 為 play_now 擬合），紀錄未說明是否同一定義；依第 2 節規則 2 都屬「原始測試紀錄」，無法自動擇一。
- 影響條目：hardware/steering-servo（目前並列並註明量法可能不同）。

---

# 主對話追加

## H-1 現役 IMU 紀錄程式未凍結（已決：註明限制）

- **決定（使用者 2026-11-23 決定）**：暫不連線 Orin，使用已能驗證的最終設定與程式證據；凡是只能從 11-05 版紀錄程式得知的內容（濾波係數、頻率），都要註明限制。

- 最終版快照只含車上 `web/`，IMU 紀錄程式在另一處。Wiki 只凍結 11-05 版 [src: raw/project/imu-new-20261105/imu_logger.py]。現役是否相同需唯讀連線 Orin 比對雜湊（未授權）。
- 影響：hardware/imu-mpu6050 的濾波係數、頻率只能寫「11-05 版」。

## H-2 最終版沒有原始影像（已決）

- **決定（使用者 2026-11-23 決定）**：可以使用 11-19 的實際影片、遮罩與圖片，但要標明「控制版本較早、模型權重相同」，不可稱為 11-23 最終版錄影。

- run-b541 的 summary 記錄 `recording: false` [src: raw/records/runs/run-b541-20261123/summary.json#key=recording]；逐格紀錄有語意遮罩與路徑，沒有相機原圖。
- 有影片的最近輪次是 11-18／11-19（與最終版同一份模型權重），但控制設定與舵機不同。
- 需人決定：感知頁用 11-19 影片（標明較早控制版）、控制頁用 b541 遮罩重繪，或另外安排一次錄影（需實車授權）。
