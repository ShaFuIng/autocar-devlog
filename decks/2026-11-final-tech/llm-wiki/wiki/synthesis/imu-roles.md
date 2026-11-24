---
id: synthesis/imu-roles
title: IMU 在最終版控制中的角色（綜合）
status: implemented
sources:
  - raw/project/snapshot-20261123d/imu_boost.json
  - raw/project/snapshot-20261123d/imu_boost.py
  - raw/project/snapshot-20261123d/heading_hold.py
  - raw/project/snapshot-20261123d/dash_route.py
  - raw/project/snapshot-20261123d/lap_pos.py
  - raw/project/imu-new-20261105/imu_logger.py
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

最終版只用 IMU 的三個量：俯仰角、航向角、車頭轉速（gz）。俯仰角判斷「現在在哪一段坡」，航向角在相機看不清時「鎖住方向」，gz 則讓轉向不必等相機慢半拍的回饋。側傾角與加速度沒有進入任何控制計算。

## 內容

**資料從哪裡來。** IMU 紀錄程式讀 MPU6050，輸出俯仰、航向與三軸角速度，寫成一個最新值檔案 [src: raw/project/imu-new-20261105/imu_logger.py#L1-L33]。控制端各層每次重讀這個檔案 [src: raw/project/snapshot-20261123d/imu_boost.json#key=latest_path]：
- 俯仰讀 `pitch_deg` [src: raw/project/snapshot-20261123d/imu_boost.py#L56]
- 航向讀 `yaw_deg` [src: raw/project/snapshot-20261123d/heading_hold.py#L117]
- 車頭轉速讀 `gyro_dps[2]` [src: raw/project/snapshot-20261123d/heading_hold.py#L145]

時間超過 0.3 s 的資料視為過期，該層跳過 [src: raw/project/snapshot-20261123d/imu_boost.json#key=max_age_s] [src: raw/project/snapshot-20261123d/dash_route.py#L764-L770]。

| IMU 量 | 名詞解釋 | 用在哪些控制 | 條目 |
|---|---|---|---|
| 俯仰角（減平地基準 1.0°） | 車頭上仰或下俯的角度 | 上坡加油門、坡頂鎖定、下坡與落地判斷、上坡積分釋放、坡道地標 RAMP／TOP／DOWN／LAND8 [src: raw/project/snapshot-20261123d/imu_boost.json#key=flat_pitch_deg] | [[control/slope-downhill]]、[[control/lap-position]] |
| 航向角 yaw | 車頭朝向，由 gz 積分而來 | 路口方向保持、虛線轉彎後保持、路徑遺失時鎖航向、下坡目標航向、彎道「已轉幾度」 | [[control/heading-hold]]、[[control/lost-path]]、[[control/curve-band-ff]] |
| 車頭轉速 gz | 每秒轉幾度 | 陀螺儀內迴圈（壓直線 S 型）、各保持層的阻尼項、下坡轉速項 | [[control/yaw-inner]]、[[control/slope-downhill]] |
| 側傾角、加速度 | — | **沒有使用**：最終版程式沒有讀取這兩個欄位 [src: raw/project/snapshot-20261123d/imu_boost.py#L56] | — |

**地標定位另外積分一份航向。** 地標定位用每格的 gz 以梯形法自行積分，不讀紀錄程式算好的 yaw [src: raw/project/snapshot-20261123d/lap_pos.py#L204-L215]。所以「彎道已轉角度」有兩種量法：帶狀前饋用 IMU 的 yaw；地標偵測與取消判斷用這份自行積分的值。詳見 [[control/curve-band-ff]] 與 [[control/lap-position]]。

**IMU 補足相機的四種情境**（相機失效的情境見 [[path/vision-failure-modes]]）：
1. **直線 S 型**：相機到舵機的整個迴路有延遲，只靠相機會來回擺動；用 gz 做內迴圈即時抵銷。見 [[control/yaw-inner]]、[[experiments/s-weave]]。
2. **路口**：白線交叉時相機路徑不可靠，改用進路口前的平均航向保持方向。見 [[control/heading-hold]]。
3. **急彎**：近處只看得到外側線。以 IMU 量到的「已轉角度」查跑道形狀表，預先給舵。見 [[control/curve-band-ff]]。
4. **坡道與落地**：坡口、落地時相機看不到正確路面。依目標航向表用陀螺儀轉向，再交還相機。見 [[control/slope-downhill]]。

## 公式與參數

- 相對俯仰＝pitch_deg−flat_pitch_deg。flat_pitch_deg＝1.0°，是調參值，依靜止讀數校正 [src: raw/project/snapshot-20261123d/imu_boost.json#key=flat_pitch_deg]。
- 地標定位的航向積分：ψ_k＝ψ_(k−1)＋½(gz_k＋gz_(k−1))·Δt（梯形法）[src: raw/project/snapshot-20261123d/lap_pos.py#L211]。
- 各層公式見對應條目：[[control/yaw-inner]]、[[control/heading-hold]]、[[control/slope-downhill]]、[[control/curve-band-ff]]。

## 未確認

- IMU 紀錄程式最近一次有紀錄的部署是 r6（11-05 18:59，只改啟動零點）；最終版實跑的資料年齡 0～24 ms 與 50 Hz 相符，但車上檔案未逐檔核對 [src: raw/project/imu-still-boot-20261105/deployment-acceptance.json]。見 [[hardware/imu-mpu6050]] 與 `wiki/conflicts.md` 的 H-1。
- 影像辨識端（worker）的地面判斷程式用自己的平地基準預設值，與控制端的 1.0° 不同（撰寫 [[hardware/imu-mpu6050]] 時發現）。它對最終版控制有沒有影響未查證。

## 相關條目

- [[hardware/imu-mpu6050]]
- [[control/yaw-inner]]
- [[control/heading-hold]]
- [[control/curve-band-ff]]
- [[control/slope-downhill]]
- [[control/lost-path]]
- [[control/lap-position]]
- [[path/vision-failure-modes]]
