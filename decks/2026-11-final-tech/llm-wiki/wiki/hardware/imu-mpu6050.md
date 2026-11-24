---
id: hardware/imu-mpu6050
title: IMU（MPU6050）硬體、紀錄程式與校正
status: implemented
sources:
  - raw/project/imu-new-20261105/imu_logger.py
  - raw/project/imu-still-boot-20261105/candidate/imu_logger.py
  - raw/project/imu-still-boot-20261105/deployment-acceptance.json
  - raw/project/imu-new-20261105/acceptance.json
  - raw/project/snapshot-20261123d/imu_boost.json
  - raw/project/snapshot-20261123d/imu_boost.py
  - raw/project/snapshot-20261123d/ground_identity.py
  - raw/project/snapshot-20261123d/ground_identity.json
  - raw/project/snapshot-20261123d/dash_route.py
  - raw/records/analyses/a1-poster-factcheck-20261103.md
  - raw/records/logs/AGENTS.md
  - raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# IMU（MPU6050）硬體、紀錄程式與校正

## 一句話結論

車上裝一顆 MPU6050（加速度計＋陀螺儀），接在 Orin 的 I²C bus 7、位址 0x68；一支獨立的紀錄程式以 50 Hz 讀取，算出俯仰（pitch）、側傾（roll）與由陀螺儀 z 軸積分的航向（yaw），寫成 `latest.json` 給控制程式讀取；控制端以「平地基準」`flat_pitch_deg`＝1.0° 換算相對俯仰 [src: raw/project/imu-new-20261105/imu_logger.py#L1-L6] [src: raw/project/snapshot-20261123d/imu_boost.json#key=flat_pitch_deg]。注意：本頁描述的紀錄程式是 11-05 版（imu-logger-r5），最終版車上執行的是否相同未經核對。

## 內容

### 硬體與安裝

- 晶片：MPU6050，接 Orin I²C bus 7、位址 0x68 [src: raw/project/imu-new-20261105/imu_logger.py#L1] [src: raw/project/imu-new-20261105/imu_logger.py#L22]；11-03 查核文件也確認 IMU 已裝且用於航向保持與上下坡判斷 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L26]。
- 11-05 隊友因舊排線斷裂更換過一顆 MPU6050；新晶片 who_am_i 讀回 0x68 [src: raw/project/imu-new-20261105/acceptance.json#L1-L2]。
- 車體座標：X 向前、Y 向左、Z 向上；車體＝感測器的（−X, −Y, +Z）[src: raw/project/imu-new-20261105/imu_logger.py#L8-L9] [src: raw/project/imu-new-20261105/imu_logger.py#L32]。俯仰「車頭朝上為正」、側傾「左側朝上為正」[src: raw/project/imu-new-20261105/imu_logger.py#L13-L14]。
- 感測器設定：數位低通約 44 Hz（濾馬達振動）、陀螺儀量程 ±250 dps、加速度計量程 ±2 g [src: raw/project/imu-new-20261105/imu_logger.py#L53-L55]。
- 名詞：**I²C** 是兩條線（時脈、資料）的低速匯流排；Orin 40-pin 擴充排針上有兩組 I²C、電位 3.3 V [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]（官方規格書第 21 頁）。MPU6050 接在哪兩腳原始資料未記載。

### 紀錄程式 imu_logger.py

**版本更正（11-24）**：11-05 18:59 起車上換成 imu-logger-r6 [src: raw/project/imu-still-boot-20261105/deployment-acceptance.json] [src: raw/project/imu-still-boot-20261105/candidate/imu_logger.py#L1]。r6 相對 r5 只改「啟動時估零點」：最多等 120 s 直到車靜止才估，靜止失敗時改用新晶片的參考零點；取樣率、濾波、輸出格式都沒有改 [src: raw/project/imu-still-boot-20261105/candidate/imu_logger.py#L31-L35] [src: raw/project/imu-still-boot-20261105/candidate/imu_logger.py#L78-L88]。之後的紀錄沒有再更換紀錄程式的記載，所以 r6 是最近一次有紀錄的部署版本；最終版車上是否仍是 r6，沒有逐檔核對（未連線 Orin）。以下逐條引用 r5 檔，與 r6 相同的部分不受影響。

**最終版實際更新頻率的佐證**：最終版實跑 run-b541 的 2804 格中，控制端讀到的 IMU 資料年齡為 −0.007～0.024 s、中位 0.010 s、P95 0.020 s（由 tools/stats_imu_age.py 自逐格紀錄 pid.jsonl 計算）[src: raw/records/runs/run-b541-20261123/summary.json]。年齡不超過約一個 20 ms 週期，與 50 Hz 取樣相符。這是推論，不是直接讀到的設定。

1. 喚醒後先丟掉 0.3 s 的讀數（剛喚醒的值不可靠）[src: raw/project/imu-new-20261105/imu_logger.py#L72-L73]。
2. **每次啟動時用靜止的 1 秒估陀螺儀零點**：收集 1 s 讀數，若加速度大小變動 < 0.05 g 且陀螺儀標準差 < 1.0 dps 判為靜止，零點取這 1 s 平均；否則改用 10-19 的參考零點並在檔頭註明 [src: raw/project/imu-new-20261105/imu_logger.py#L74-L82] [src: raw/project/imu-new-20261105/imu_logger.py#L85]。因此「重新校準」就是讓車靜止後重啟紀錄服務 [src: raw/records/logs/AGENTS.md#L101]。
3. **互補濾波**算俯仰與側傾：以陀螺儀角速度積分為主（權重 0.98），再用加速度計算出的傾角（權重 0.02）拉回，避免積分漂移 [src: raw/project/imu-new-20261105/imu_logger.py#L33] [src: raw/project/imu-new-20261105/imu_logger.py#L100-L107]。
4. **航向 yaw**＝扣掉零點後的 gz 直接積分，左轉為正；它是相對於紀錄程式啟動時的角度，會隨殘餘零點漂移 [src: raw/project/imu-new-20261105/imu_logger.py#L35-L36] [src: raw/project/imu-new-20261105/imu_logger.py#L103]。
5. 取樣率預設 50 Hz [src: raw/project/imu-new-20261105/imu_logger.py#L67]；每 5 筆以「先寫暫存檔再改名」的方式原子更新 `latest.json`（含 t、pitch_deg、roll_deg、yaw_deg、gyro_dps）[src: raw/project/imu-new-20261105/imu_logger.py#L40] [src: raw/project/imu-new-20261105/imu_logger.py#L109-L113]，所以讀取端看到的更新率是 50 ÷ 5 ＝ 10 次/s（推算）。完整逐筆紀錄另寫入 jsonl 檔 [src: raw/project/imu-new-20261105/imu_logger.py#L114-L115]。
   - **11-10 起改為每 1 筆更新**：11-10 08:27 把 LATEST_EVERY 由 5 改成 1，`latest.json` 由 10 Hz 變成 50 Hz，當時實測每秒 50.3 次、間隔 20 ms [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L17]。最終版實跑的 IMU 資料年齡 0～24 ms 也與此相符。這個改動晚於本機凍結的 r5／r6 檔，所以兩份檔案裡的 LATEST_EVERY 仍是 5 [src: raw/project/imu-still-boot-20261105/candidate/imu_logger.py#L44]。
6. 時間戳用 `time.monotonic()`，與 PID 紀錄的 capture_at／consumed_at 同一時鐘 [src: raw/project/imu-new-20261105/imu_logger.py#L4-L6]。
7. 新晶片不套用加速度六面校正（舊晶片的值會讓靜止時 |a| 讀成 0.865 g），改由平地基準吸收零 g 偏移 [src: raw/project/imu-new-20261105/imu_logger.py#L23-L30] [src: raw/project/imu-new-20261105/acceptance.json#L3-L4]。

檔頭說明寫「never used for control」、檔頭欄位 `control_use=False` [src: raw/project/imu-new-20261105/imu_logger.py#L3-L4] [src: raw/project/imu-new-20261105/imu_logger.py#L87]：意思是「紀錄程式本身不送控制命令」。它輸出的 `latest.json` 確實被控制端讀取（r3 起）[src: raw/project/imu-new-20261105/imu_logger.py#L37-L39]，以程式為準，這段說明只對「程式本身」成立。

### 控制端怎麼讀（最終版快照）

- `imu_boost.py` 讀 `latest.json`，相對俯仰＝pitch_deg − flat_pitch_deg；讀不到、超過 max_age_s（0.3 s）未更新或數值異常，就退回不加速並記錄原因 [src: raw/project/snapshot-20261123d/imu_boost.py#L8-L14] [src: raw/project/snapshot-20261123d/imu_boost.py#L66-L74] [src: raw/project/snapshot-20261123d/imu_boost.json#key=max_age_s]。
- 高架虛線路段的路線窗（[[path/upper-dash-route]]）也經同一個讀取器取得相對俯仰 [src: raw/project/snapshot-20261123d/dash_route.py#L762-L771]。
- worker 端的地面幾何單線身分判斷（ground_identity）另外直接讀 `latest.json` 的 gz 與俯仰 [src: raw/project/snapshot-20261123d/ground_identity.py#L68-L75]。
- 各控制層如何使用 IMU（坡道判斷、航向保持、陀螺儀內迴圈）見 [[synthesis/imu-roles]]。

### 校正：平地基準 flat_pitch_deg

- 最終版 `imu_boost.json` 的 `flat_pitch_deg`＝1.0 [src: raw/project/snapshot-20261123d/imu_boost.json#key=flat_pitch_deg]。11-22 13:21 手機頁在讀數偏高處誤校成 1.99，13:43 更正回 1.0 [src: raw/records/logs/AGENTS.md#L215]；手機服務 r5 提供「平地基準放回 1.0（不量測）」[src: raw/records/logs/AGENTS.md#L197]。
- 這個值歷經多次重設（−0.7、2.6、2.05、1.1、1.0 等），原因多為 IMU 更換、鬆脫重固或後輪更換 [src: raw/project/snapshot-20261123d/imu_boost.json#key=note] [src: raw/records/logs/AGENTS.md#L281]。

### 已知風險

- **凍結**：摔車後 IMU 可能凍結——數值不變但時間戳照常更新，紀錄服務仍顯示 active；車上沒有防護，需重啟紀錄服務並在車靜止時重新校準 [src: raw/records/logs/AGENTS.md#L101]。11-21 曾發生（加速度全 0、陀螺儀固定），整輪無地標、無上坡加速 [src: raw/records/logs/AGENTS.md#L255]。之後手機服務 r2 加了 IMU 健康檢查（凍結或無資料→IMU_FAULT、不能起跑）[src: raw/records/logs/AGENTS.md#L248]。因為「時間戳照常更新」，控制端的 max_age_s 檢查擋不住這種凍結（推論：凍結時 t 仍在前進，`age` 不會超過 0.3 s）。
- **鬆脫／被撞動**：11-19 中午鬆脫重固（靜止俯仰約 1.4°、側傾約 3.0°）[src: raw/records/logs/AGENTS.md#L336]；11-21 重新加固後靜止值改以俯仰 0.95／側傾 1.90 為準 [src: raw/records/logs/AGENTS.md#L281]；11-19 晚撞後按緊，靜止值改以俯仰 0.84／側傾 0.36 為準 [src: raw/records/logs/AGENTS.md#L134]。
- 最終定版當天 Orin 17:45 重開機過，之後 IMU 靜止值未核對 [src: raw/records/logs/AGENTS.md#L136]。

## 公式與參數

- 互補濾波（每筆，dt 為兩筆間隔）：
  - pitch ← α·(pitch − g_y·dt) + (1−α)·pitch_acc，其中 pitch_acc ＝ atan2(a_x, √(a_y²+a_z²)) [src: raw/project/imu-new-20261105/imu_logger.py#L100] [src: raw/project/imu-new-20261105/imu_logger.py#L106]
  - roll ← α·(roll + g_x·dt) + (1−α)·atan2(a_y, a_z) [src: raw/project/imu-new-20261105/imu_logger.py#L101] [src: raw/project/imu-new-20261105/imu_logger.py#L107]
  - α ＝ 0.98（設計假設，註解稱「陀螺儀路徑權重」）[src: raw/project/imu-new-20261105/imu_logger.py#L33]
- yaw ← yaw + g_z·dt（扣零點後的 gz，左轉為正）[src: raw/project/imu-new-20261105/imu_logger.py#L103]
- 換算：加速度原始值 ÷ 16384（±2 g）、陀螺儀原始值 ÷ 131（±250 dps）、溫度 ÷ 340 + 36.53（晶片規格換算常數，設計值）[src: raw/project/imu-new-20261105/imu_logger.py#L61-L63]
- 靜止判定：|a| 變動 < 0.05 g 且 gyro 標準差 < 1.0 dps（設計假設）[src: raw/project/imu-new-20261105/imu_logger.py#L81]
- 相對俯仰 pitch_rel ＝ pitch_deg − flat_pitch_deg；flat_pitch_deg ＝ 1.0（實測後設定的校正值）[src: raw/project/snapshot-20261123d/imu_boost.py#L70] [src: raw/project/snapshot-20261123d/imu_boost.json#key=flat_pitch_deg]
- 讀取有效期 max_age_s ＝ 0.3 s（調參值）[src: raw/project/snapshot-20261123d/imu_boost.json#key=max_age_s]

## 未確認

- 最終版車上執行的紀錄程式版本：最近一次有紀錄的部署是 r6（11-05 18:59），快照不含紀錄程式，未逐檔核對（使用者 11-23 決定不連線 Orin）[src: raw/project/imu-still-boot-20261105/deployment-acceptance.json]。systemd 啟動參數（是否帶 --rate）沒有本機副本；r6 預設 50 Hz [src: raw/project/imu-still-boot-20261105/candidate/imu_logger.py#L71]。
- 【程式事實，影響未評估】worker 端 ground_identity 的平地基準不是 1.0：`ground_identity.json` 沒有設定 `flat_pitch_deg`，因此用程式預設 2.6 [src: raw/project/snapshot-20261123d/ground_identity.py#L23-L24] [src: raw/project/snapshot-20261123d/ground_identity.json]；它只在 |pitch−2.6| ≤ pitch_max_deg 4.0 時啟用地面比對 [src: raw/project/snapshot-20261123d/ground_identity.json#key=pitch_max_deg] [src: raw/project/snapshot-20261123d/ground_identity.py#L74] [src: raw/project/snapshot-20261123d/ground_identity.py#L202]。與控制端 1.0 相差 1.6°，對單線身分判斷的實際影響原始資料沒有評估。
- IMU 的水平軸方向「從未以車輛運動驗證」是 10-19 版的說明 [src: raw/project/imu-new-20261105/imu_logger.py#L14-L15]；11-05 驗收時也寫軸向檢查（車頭朝上→pitch +、左轉→yaw +）尚未做 [src: raw/project/imu-new-20261105/acceptance.json#L7]。r4 註解另寫實測左轉積分 +90° [src: raw/project/imu-new-20261105/imu_logger.py#L35]，可視為 yaw 方向的部分驗證。
- 下坡落地衝擊每次頂到加速度計量程 [src: raw/records/logs/AGENTS.md#L113]；量程 ±2 g 下對落地後俯仰的影響未量化。

## 相關條目

- [[synthesis/imu-roles]]（IMU 在各控制層的用途）
- [[control/slope-downhill]]、[[control/heading-hold]]、[[control/yaw-inner]]
- [[path/upper-dash-route]]、[[path/junction-handling]]
- [[hardware/vehicle-hardware]]
