---
id: control/lap-position
title: 圈內位置估計（lap_pos）：編碼器里程＋航向／俯仰地標
status: implemented
sources:
  - raw/project/snapshot-20261123d/lap_pos.py
  - raw/project/snapshot-20261123d/lap_pos.json
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/lap_speed.py
  - raw/project/snapshot-20261123d/brake_zones.json
  - raw/project/snapshot-20261123d/track_pos.json
  - raw/project/firmware-pwm100_v1/Config.h
  - raw/project/firmware-pwm100_v1/Encoder.cpp
  - raw/project/firmware-pwm100_v1/Telemetry.cpp
  - raw/project/docs/track-map-01-12.webp
  - raw/records/logs/AGENTS.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 圈內位置估計（lap_pos）：編碼器里程＋航向／俯仰地標

## 一句話結論

lap_pos 不用相機，只用後輪編碼器里程（每 count 0.000222 m）與陀螺儀積分航向、IMU 俯仰，在已知 67.72 m 的一圈上找 13 個地標（彎道起訖的航向轉折、坡道起訖的俯仰轉折），每找到一個就把位置重新對齊到該地標的標稱位置；速度表、減速區與彎道前饋都以「離最近地標幾公尺」決定何時作用 [src: raw/project/snapshot-20261123d/lap_pos.py#L13-L23] [src: raw/project/snapshot-20261123d/lap_pos.json#L4-L22]。

## 內容

### 狀態：說明文字過時

lap_pos.py 檔頭寫「offline candidate, NOT deployed」「log only」[src: raw/project/snapshot-20261123d/lap_pos.py#L1]，但最終版 lap_pos.json enabled true [src: raw/project/snapshot-20261123d/lap_pos.json#key=enabled]，主程式每格呼叫它 [src: raw/project/snapshot-20261123d/live_pid.py#L2190]，且 lap_speed、brake_zones、curve_map 的彎 4 出彎判定等都讀它的狀態 [src: raw/project/snapshot-20261123d/lap_speed.py#L112-L117] [src: raw/project/snapshot-20261123d/live_pid.py#L975-L988]。依規則以 json＋呼叫為準，算現役。它本身不改命令，是其他層的位置來源。

### 輸入

每格從已有資料取得，不自行讀感測器 [src: raw/project/snapshot-20261123d/lap_pos.py#L9-L11]：

- **t**：Orin 單調時鐘；**gz**：本格陀螺儀偏航率（左正）；**pitch_rel**：imu_boost 的相對俯仰；**enc_b**：控制板回報的 B 輪編碼器 forward−reverse 累計 [src: raw/project/snapshot-20261123d/live_pid.py#L2184-L2188]。
- 呼叫位置在層表之後、送出之前，所以各層讀到的是上一格的位置 [src: raw/project/snapshot-20261123d/live_pid.py#L2183-L2190]（細節見 [[control/command-chain]]）。

### 里程與航向

- **里程 D**＝(enc_b − 起始值)×m_per_count，只取歷史最大值（不倒退）[src: raw/project/snapshot-20261123d/lap_pos.py#L216-L218]。主程式其他地方也用同一常數 2.22e-4 [src: raw/project/snapshot-20261123d/live_pid.py#L89]。
- **航向 yaw**＝gz 的梯形積分；缺 gz 時沿用上一個 gz 外插；兩格間隔超過 gap_s 0.35 s 時暫停航向走廊檢查直到下一個地標 [src: raw/project/snapshot-20261123d/lap_pos.py#L206-L213] [src: raw/project/snapshot-20261123d/lap_pos.json#key=gap_s]。這是 lap_pos 自己積分的航向，與 heading_hold 等其他模組的航向分開。陀螺儀用途總整理見 [[synthesis/imu-roles]]。

### 韌體端的編碼器

- **編碼器（encoder）**＝裝在輪軸上的 A／B 兩相方波感測器，兩相相位差可判斷正反轉。韌體對 A、B 兩腳都設 CHANGE 中斷，用 16 格狀態表判斷每個邊緣的方向，正轉、反轉各自計數——兩相的每個上升、下降邊緣都計一次，即「四倍頻」解碼 [src: raw/project/firmware-pwm100_v1/Encoder.cpp#L10-L32]。兩相同時跳變（不合法轉移）另計 invalid [src: raw/project/firmware-pwm100_v1/Encoder.cpp#L15]。
- 腳位設定：A 輪 4／5、B 輪 6／7，ENCODERS_ENABLED true；註解寫腳位由圖面推定、須上車確認 [src: raw/project/firmware-pwm100_v1/Config.h#L41-L44]。
- 計數每 TELEMETRY_MS（200 ms）快照一次，並放進狀態回報的 enc_b 欄位 [src: raw/project/firmware-pwm100_v1/Encoder.cpp#L54-L60] [src: raw/project/firmware-pwm100_v1/Config.h#L40] [src: raw/project/firmware-pwm100_v1/Telemetry.cpp#L61]。
- 硬體細節見 [[hardware/vehicle-hardware]]。

### 地標與標稱位置

- 一圈 67.72 m；13 個地標依序：C1s（彎 1 起）、C1e、C2s、C2e、C3s、RAMP（上坡起）、TOP（坡頂）、DASHs（虛線轉彎起）、DASHe、DOWN（下坡起）、LAND8（落地）、C4s、C4e；標稱位置以 C1s 為 0 [src: raw/project/snapshot-20261123d/lap_pos.json#L4-L37]。彎道編號依統一跑道圖 [src: raw/project/docs/track-map-01-12.webp]。
- **航向地標**：以「前一段直線的航向平台（odometer 視窗內 gz 積分航向的中位數）」為基準，航向越過基準 ±level_deg 10° 且持續 hold_m 0.3 m 才確認；C2s、C3s 用 hold_start_m 0.5 m；各彎總轉角門檻為 C1 −150°、C2 −205°、C3 −245°、DASH +85°、C4 −200°（右轉為負）[src: raw/project/snapshot-20261123d/lap_pos.py#L146-L179] [src: raw/project/snapshot-20261123d/lap_pos.json#L38-L47]。
- **俯仰地標**：RAMP＝俯仰高於 5° 持續 0.2 m；TOP＝回到 5° 以下持續 0.3 m；DOWN＝低於 −8° 持續 0.1 m；LAND8＝回到 −8° 以上持續 0.2 m [src: raw/project/snapshot-20261123d/lap_pos.py#L158-L171] [src: raw/project/snapshot-20261123d/lap_pos.json#key=ramp_deg] [src: raw/project/snapshot-20261123d/lap_pos.json#key=down_deg]。
- **確認點回推**：確認時以越線那一刻的里程（兩格間內插）為地標位置，所以判定延後 hold 公尺，但位置本身不落後 [src: raw/project/snapshot-20261123d/lap_pos.py#L51-L69] [src: raw/project/snapshot-20261123d/lap_pos.py#L15-L17]。
- **重新對齊**：s＝標稱位置＋(D − 越線里程)；C4s 不重新對齊（no_anchor）[src: raw/project/snapshot-20261123d/lap_pos.py#L95-L97] [src: raw/project/snapshot-20261123d/lap_pos.py#L113-L123] [src: raw/project/snapshot-20261123d/lap_pos.json#key=no_anchor]。
- **C2e 備援**：彎 2 結束若沒越過主門檻（195°），但已轉過 185° 且之後 1.5 m 內只再轉 ≤4°，就以這段平靜區起點當 C2e [src: raw/project/snapshot-20261123d/lap_pos.py#L181-L201] [src: raw/project/snapshot-20261123d/lap_pos.json#key=c2e_fallback]。

### 接受窗、跳過與遺失

- **接受窗**：越線時估計位置比標稱早超過 window_m[0]＝3 m 就忽略（例如 V 字路口的假轉角）[src: raw/project/snapshot-20261123d/lap_pos.py#L229-L233] [src: raw/project/snapshot-20261123d/lap_pos.json#key=window_m]。window_m[1]（3 m）只用在遺失後的恢復判定 [src: raw/project/snapshot-20261123d/lap_pos.py#L128-L134]。
- **跳過**：等待中的地標已晚於標稱 skip_after_m 1.5 m 仍未出現，就當作在標稱位置經過（不重新對齊）；個別地標可放寬：C2e 5.0 m、C1s 9.0 m [src: raw/project/snapshot-20261123d/lap_pos.py#L237-L248] [src: raw/project/snapshot-20261123d/lap_pos.json#key=skip_after_m] [src: raw/project/snapshot-20261123d/lap_pos.json#key=skip_after_by]。C1s 9.0 是任意起點用的保險鍵 [src: raw/records/logs/AGENTS.md#L169]。
- **遺失（lost）**：連續跳過 lost_skips 2 個地標，或在直線段航向偏離參考剖面超過 max(3×sd＋14°, 24°) 持續 0.5 m [src: raw/project/snapshot-20261123d/lap_pos.py#L253-L267] [src: raw/project/snapshot-20261123d/lap_pos.json#L86-L89]。
- **恢復**：遺失時里程推算繼續；任何上坡（RAMP）或下坡（DOWN）俯仰事件即可重新取得位置（本跑道唯一）；或連續 2 個地標落在接受窗內 [src: raw/project/snapshot-20261123d/lap_pos.py#L128-L139] [src: raw/project/snapshot-20261123d/lap_pos.json#key=lost_clear_n]。
- 說明文字提到 `lost_after_m`，但程式與 json 實際用的是 skip_after／lost_skips，說明文字未更新 [src: raw/project/snapshot-20261123d/lap_pos.py#L19-L20]。

### 起點位置

- 第 0 圈（起跑到第一次 C1s）位置＝start_s＋D，start_s −3.44 表示起點在 C1s 前 3.44 m（旗子位置）[src: raw/project/snapshot-20261123d/lap_pos.py#L85] [src: raw/project/snapshot-20261123d/lap_pos.json#key=start_s]。第 0 圈的 C1s 位置以起點加里程計算 [src: raw/project/snapshot-20261123d/lap_pos.py#L230]。
- 起點不在旗子時，以手機頁「起點位置」或同語意的產生器重寫 lap_pos／brake_zones／lap_ff／start_bias 四檔（免重啟）；往後超過 2.5 m 自動關起步左舵，可用 0～7 m [src: raw/records/logs/AGENTS.md#L167] [src: raw/records/logs/AGENTS.md#L169]。brake_zones 第 1 圈的區段以「起跑後公尺數」為錨，第 2 圈起才用 lap_pos 地標 [src: raw/project/snapshot-20261123d/brake_zones.json#key=zones]。

### 已知限制：搬車

- 系統不偵測「搬車」：車被拿起時輪子不轉、里程不變，放回不同位置後定位會錯而不自知 [src: raw/records/logs/AGENTS.md#L166]。
- 11-23 實例：彎 4 出彎後暫停並搬車再繼續，位置雖在之後的地標重新對上，但彎 1 比預期早約 2.6 m 出現，落在彎 1 帶狀前饋的觸發窗外，之後一連串失誤直到 lost(HEADING)；操作規則改為暫停後不搬車，必須搬就停止本輪重新起跑 [src: raw/records/logs/AGENTS.md#L164]。

### track_pos 只供紀錄

車上另有一個同名不同用途的 track_pos.py／track_pos.json（11-08），供 ops07 執行環境寫入紀錄；lap_pos 是另外命名的估計器 [src: raw/project/snapshot-20261123d/lap_pos.py#L3-L5] [src: raw/project/snapshot-20261123d/track_pos.json#key=enabled]。

## 公式與參數

```
D     = max(D, (enc_b − enc_b0) × m_per_count)
yaw  += ½ (gz_k + gz_{k−1}) × Δt
s     = s_nom(anchor) + (D − D_cross(anchor))      （第 0 圈未對齊前：s = start_s + D）
地標確認：sign × (x − level) > 0 持續 hold 公尺；D_cross 以前後兩格線性內插
航向走廊容差 = max(k_sd × sd + add, min)
```
[src: raw/project/snapshot-20261123d/lap_pos.py#L51-L69] [src: raw/project/snapshot-20261123d/lap_pos.py#L95-L97] [src: raw/project/snapshot-20261123d/lap_pos.py#L210-L218] [src: raw/project/snapshot-20261123d/lap_pos.py#L261]

| 參數 | 值 | 性質 | 出處 |
|---|---|---|---|
| m_per_count | 0.000222 m | 實測值（未列量測方法） | [src: raw/project/snapshot-20261123d/lap_pos.json#key=m_per_count] |
| lap_m | 67.72 m | 實測值（多圈地標平均） | [src: raw/project/snapshot-20261123d/lap_pos.json#key=lap_m] |
| nominal_m（13 地標） | C1s 0～C4e 56.98 m | 實測值（11-13 的 21～36 圈平均） | [src: raw/project/snapshot-20261123d/lap_pos.json#L5-L20] [src: raw/project/snapshot-20261123d/lap_pos.json#key=note] |
| start_s | −3.44 m | 實測值（旗子位置） | [src: raw/project/snapshot-20261123d/lap_pos.json#key=start_s] |
| level_deg／hold_m／hold_start_m | 10°／0.3 m／0.5 m | 調參值 | [src: raw/project/snapshot-20261123d/lap_pos.json#L45-L47] |
| ramp_deg／down_deg | 5°／−8° | 調參值 | [src: raw/project/snapshot-20261123d/lap_pos.json#L52-L53] |
| window_m | ±3 m | 調參值 | [src: raw/project/snapshot-20261123d/lap_pos.json#key=window_m] |
| skip_after_m／skip_after_by | 1.5 m／C2e 5.0、C1s 9.0 | 調參值 | [src: raw/project/snapshot-20261123d/lap_pos.json#L60] [src: raw/project/snapshot-20261123d/lap_pos.json#key=skip_after_by] |
| lost_skips／lost_clear_n | 2／2 | 調參值 | [src: raw/project/snapshot-20261123d/lap_pos.json#L61] [src: raw/project/snapshot-20261123d/lap_pos.json#key=lost_clear_n] |
| 走廊 k_sd／add／min／persist | 3／14°／24°／0.5 m | 調參值 | [src: raw/project/snapshot-20261123d/lap_pos.json#L86-L89] |
| 編碼器快照週期 | 200 ms | 設計假設 | [src: raw/project/firmware-pwm100_v1/Config.h#L40] |

## 未確認

- 編碼器計數每 200 ms 才快照一次，而控制每秒約 23 格（見 [[comms/timing-latency]]），推論里程在相鄰幾格間是階梯狀更新；以最高速 1.44 m/s 計，每一階約 0.29 m（推算 1.44×0.2），這對地標內插精度的影響未量測 [src: raw/project/firmware-pwm100_v1/Encoder.cpp#L54-L60]。
- Config.h 中編碼器腳位 4～7 與馬達方向腳位 4～7 數字相同，是否為不同腳位命名體系未確認，已列入衝突草稿 [src: raw/project/firmware-pwm100_v1/Config.h#L12-L13] [src: raw/project/firmware-pwm100_v1/Config.h#L43]。
- m_per_count 0.000222 的量測方式（輪徑與每轉 count 數）不在本頁來源內 [src: raw/project/snapshot-20261123d/lap_pos.json#key=m_per_count]。
- 只用 B 輪（enc_b）計里程，左右輪差（紀錄提到右輪比左輪快約 5%）對彎道里程的影響未評估 [src: raw/records/logs/AGENTS.md#L110]。

## 相關條目

- [[control/command-chain]]
- [[control/speed-control]]
- [[control/curve-band-ff]]
- [[synthesis/imu-roles]]
- [[hardware/imu-mpu6050]]
- [[hardware/vehicle-hardware]]
- [[comms/timing-latency]]
