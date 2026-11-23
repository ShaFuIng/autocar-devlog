---
id: control/speed-control
title: 油門決定鏈：speed_adapt、位置速度表、減速區與上限
status: implemented
sources:
  - raw/project/snapshot-20261123d/speed_policy.py
  - raw/project/snapshot-20261123d/speed_adapt.py
  - raw/project/snapshot-20261123d/speed_adapt.json
  - raw/project/snapshot-20261123d/lap_speed.py
  - raw/project/snapshot-20261123d/lap_speed.json
  - raw/project/snapshot-20261123d/brake_zones.json
  - raw/project/snapshot-20261123d/speed_guard.py
  - raw/project/snapshot-20261123d/speed_guard.json
  - raw/project/snapshot-20261123d/throttle_cap.py
  - raw/project/snapshot-20261123d/throttle_cap.json
  - raw/project/snapshot-20261123d/imu_boost.json
  - raw/project/snapshot-20261123d/speed_policy.json
  - raw/project/snapshot-20261123d/manual_drive.py
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/firmware-pwm100_v1/Config.h
  - raw/project/firmware-pwm100_v1/Drive.cpp
  - raw/project/firmware-pwm100_v1/ManualDrive.cpp
  - raw/records/logs/AGENTS.md
  - raw/records/runs/run-b541-20261123/summary.json
  - raw/project/snapshot-20261123d/lap_pos.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 油門決定鏈：speed_adapt、位置速度表、減速區與上限

## 一句話結論

每格油門（PWM 百分比）先由 IMU 上坡提升與 speed_adapt（依路徑穩定度與彎道，最高 50）決定，再由 lap_speed 依圈內位置往上拉（直線與坡道前段可到 100），然後依序被上層上限、brake_zones 減速區、上層轉彎上限與下坡超速防護往下壓；全車上限由 throttle_cap 100 與韌體 MAX_THROTTLE_PERCENT 100 把關 [src: raw/project/snapshot-20261123d/speed_policy.py#L114-L122] [src: raw/project/snapshot-20261123d/throttle_cap.json] [src: raw/project/firmware-pwm100_v1/Config.h#L36]。

## 內容

### 決定順序（有效格）

`speed_policy.py` 把所有油門決策集中成固定順序 [src: raw/project/snapshot-20261123d/speed_policy.py#L7-L15]：

1. **imu_boost**（層表第 4 列）：依俯仰判斷上坡，上坡時油門至少 uphill_pwm 25；進入門檻 5°、離開 3°、需持續 0.2 s，油門變化率 10/s [src: raw/project/snapshot-20261123d/speed_policy.py#L65-L69] [src: raw/project/snapshot-20261123d/imu_boost.json#key=uphill_pwm] [src: raw/project/snapshot-20261123d/imu_boost.json#key=on_deg] [src: raw/project/snapshot-20261123d/imu_boost.json#key=pwm_rate]。IMU 在各處的用途見 [[synthesis/imu-roles]]。
2. **speed_adapt**（速度群組最後一層）：依路徑穩定度分 LOW／MID／HIGH 三級，誤差、誤差變化率、轉向偏移超過門檻就降級，穩定 stable_s 後升級，升降速率各 30/s [src: raw/project/snapshot-20261123d/speed_adapt.py#L1-L20] [src: raw/project/snapshot-20261123d/speed_adapt.json#key=up_rate]。最終版等級為 24／30／50，硬上限 hard_cap 50 [src: raw/project/snapshot-20261123d/speed_adapt.json#key=min_pwm] [src: raw/project/snapshot-20261123d/speed_adapt.json#key=mid_pwm] [src: raw/project/snapshot-20261123d/speed_adapt.json#key=max_pwm] [src: raw/project/snapshot-20261123d/speed_adapt.json#key=hard_cap]。
   - **curve_pwm_by**：在 curve_map 判定的彎道內，以各彎專用油門取代 LOW／MID：彎 1 44、彎 2 36、彎 3 36、彎 4 48 [src: raw/project/snapshot-20261123d/speed_adapt.json#key=curve_pwm_by] [src: raw/project/snapshot-20261123d/speed_adapt.py#L203-L207]。彎道 key 由 curve_map 的路段與序號對照 [src: raw/project/snapshot-20261123d/speed_policy.py#L99-L111]。
   - 其他情境值：落地後 landing_pwm 50、上層轉彎前／後 40／36、上層 upper_pwm 27、下坡 downhill_pwm 10 [src: raw/project/snapshot-20261123d/speed_adapt.json#key=landing_pwm] [src: raw/project/snapshot-20261123d/speed_adapt.json#key=upper_pwm_pre_turn] [src: raw/project/snapshot-20261123d/speed_adapt.json#key=upper_pwm_post_turn] [src: raw/project/snapshot-20261123d/speed_adapt.json#key=upper_pwm] [src: raw/project/snapshot-20261123d/speed_adapt.json#key=downhill_pwm]。
3. **speed_caps**（層表第 36 列）內部依序 [src: raw/project/snapshot-20261123d/speed_policy.py#L114-L122]：
   1. **lap_speed**（位置速度表）：只往上拉，見下節 [src: raw/project/snapshot-20261123d/speed_policy.py#L117]。
   2. **lane_cap**：上層（route OPEN 或 lane_segment 作用）時的上限 [src: raw/project/snapshot-20261123d/speed_policy.py#L164-L172]。
   3. **brake_zones**：依里程的減速區上限；壓下時同時把 speed_adapt 的內部油門拉低 [src: raw/project/snapshot-20261123d/speed_policy.py#L180-L188]。
   4. **upper_cap**：上層虛線轉彎時的上限 [src: raw/project/snapshot-20261123d/speed_policy.py#L120]。
   5. **w_coast**（upper_wide，下坡前的滑行上限）[src: raw/project/snapshot-20261123d/speed_policy.py#L121]。
   6. **speed_guard**：本格最後一個油門決定 [src: raw/project/snapshot-20261123d/speed_policy.py#L122]。

遺失格則用 speed_adapt 的 hold_pwm，之後同樣經 speed_guard [src: raw/project/snapshot-20261123d/speed_policy.py#L15]。

### lap_speed：位置速度表

- **位置速度表**＝以 lap_pos 的地標為錨，「錨點後 from_m～to_m 公尺內把油門往上拉到 pwm」的區段清單；第一個包含目前位置的區段生效 [src: raw/project/snapshot-20261123d/lap_speed.py#L81-L89]。位置本身見 [[control/lap-position]]。
- 一般區段（r1）：不在被擋的狀況下（WARMUP、上層、坡道、誤差超過 err_guard、轉向偏移超過 steer_guard_us、speed_adapt 為 LOW 等），以 rate_pwm_s 往目標爬升；全域 rate 60 PWM/s、err_guard 0.30、steer_guard 250 µs [src: raw/project/snapshot-20261123d/lap_speed.py#L91-L110] [src: raw/project/snapshot-20261123d/lap_speed.py#L122-L154] [src: raw/project/snapshot-20261123d/lap_speed.json#L4-L6]。
- **兩段制（two_level，r3）**：三條直線的 100 區不看誤差變化率與 speed_adapt 的 LOW／MID，只分兩狀態——NORMAL 給區段油門 100；TROUBLE（|誤差|>0.4，回到 0.3 以下才解除；或轉向偏移 >300 µs；或低通 |gz|>25°/s）給 min(100, 70)；上升 200 PWM/s、下降 120 PWM/s [src: raw/project/snapshot-20261123d/lap_speed.py#L23-L38] [src: raw/project/snapshot-20261123d/lap_speed.py#L157-L204] [src: raw/project/snapshot-20261123d/lap_speed.json#L9-L27]。檔頭說明此機制是因為 100 區內 41 次掉速中有 36 次來自一兩格的誤差變化率觸發 [src: raw/project/snapshot-20261123d/lap_speed.py#L27-L29]。
- **坡道區**（RAMP+0.3～1.9 m，油門 100、allow_climb）：最終版此區 err_guard 0.4、rate_pwm_s 70 [src: raw/project/snapshot-20261123d/lap_speed.json#L64-L71]；這是 11-23 定版前最後一項改動（lap_speed.json 3d6806c5）[src: raw/records/logs/AGENTS.md#L136]。
- 區段往下切換到較低區段時，以 down_rate_pwm_s 80 逐步下降，不是瞬間掉 [src: raw/project/snapshot-20261123d/lap_speed.py#L139-L141] [src: raw/project/snapshot-20261123d/lap_speed.json#key=down_rate_pwm_s]。
- 區段目標不得超過 throttle_cap；speed_adapt 的內部油門最多被拉到 hard_cap 50，超過 50 的部分只由區段本身延續 [src: raw/project/snapshot-20261123d/lap_speed.py#L130-L150]。
- 最終版區段：主直線／斜線／圓圈直線 100（兩段制）、坡道 100、彎 4 後半 64、三條直線的 50 後備區、坡頂 33、彎 3 前段 48、左彎到彎 3 入口 38、彎 1 入口銜接 42、彎 2 入口銜接 33 [src: raw/project/snapshot-20261123d/lap_speed.json#key=zones]。「彎 4 後半」區段名稱寫 58，實際 pwm 為 64，以數值為準 [src: raw/project/snapshot-20261123d/lap_speed.json#L72-L80]。

### brake_zones：減速區

- 以里程或 lap_pos 地標為錨的油門上限區段，壓在 lap_speed 之後，所以減速區一定贏過提速區 [src: raw/project/snapshot-20261123d/lap_speed.py#L10-L11] [src: raw/project/snapshot-20261123d/brake_zones.json#key=zones]。
- 每區可有兩種錨：第 1 圈用「起跑後公尺數」（anchor start），第 2 圈起用 lap_pos 地標（lap_anchor）[src: raw/project/snapshot-20261123d/brake_zones.json#key=zones]。例：彎 1 入口上限 42、彎 2 入口 33、彎 3 入口 38、彎 3 尾段 31、坡道最後一公尺 50、坡底到彎 4 36 [src: raw/project/snapshot-20261123d/brake_zones.json#key=zones]。

### speed_guard：下坡超速防護

- 說明文字寫「NOT deployed」，但最終版 json 的 downhill_guard 與 overspeed_watch 為 enabled true、get() 只要有一個開關開就回傳物件，依規則算現役 [src: raw/project/snapshot-20261123d/speed_guard.py#L1-L12] [src: raw/project/snapshot-20261123d/speed_guard.py#L326-L334] [src: raw/project/snapshot-20261123d/speed_guard.json#key=downhill_guard.enabled]。
- downhill_guard：下坡窗口內較快的後輪達 6800 cps 時把油門壓到 5，直到兩輪都低於 4500 cps（最多 3 s）[src: raw/project/snapshot-20261123d/speed_guard.json#L10-L20]。overspeed_watch 只記錄、不改油門 [src: raw/project/snapshot-20261123d/speed_guard.py#L12]。ramp_cap 關閉 [src: raw/project/snapshot-20261123d/speed_guard.json#key=ramp_cap.enabled]。
- 換算：6800 cps × 0.000222 m/count ≈ 1.51 m/s（推算；json 附註亦寫 1.51 m/s）[src: raw/project/snapshot-20261123d/speed_guard.json#L85]。

### 全車上限與起跑上限

- throttle_cap.json max_pct 100：Orin 端唯一允許超過 50 的開關；也受韌體回報的 throttle_limit_pct 限制 [src: raw/project/snapshot-20261123d/throttle_cap.py#L1-L15] [src: raw/project/snapshot-20261123d/throttle_cap.py#L42-L50]。檔頭「NOT deployed」已過時，json 存在且 FIRMWARE_MAX 為 100 [src: raw/project/snapshot-20261123d/throttle_cap.py#L24]。
- 起跑時 speed_adapt 把本輪上限提高到 max_pct，manual_drive 拒絕任何超過本輪起跑值的油門 [src: raw/project/snapshot-20261123d/speed_adapt.py#L129-L134] [src: raw/project/snapshot-20261123d/manual_drive.py#L174]；最終實跑 run-b541 的起跑上限為左右 100 [src: raw/records/runs/run-b541-20261123/summary.json#L9-L10]。
- 本輪 accel_seconds／decel_seconds 為 0，Orin 端不再加斜坡 [src: raw/records/runs/run-b541-20261123/summary.json#L13-L14]。

### 韌體端

- MAX_THROTTLE_PERCENT 100（11-19 由 70 改為 100，用於量全油門落地車速）[src: raw/project/firmware-pwm100_v1/Config.h#L36]；MANUAL 指令的左右油門超過此值即拒絕（錯誤碼名稱仍叫 PWM_LIMIT_50，為舊名）[src: raw/project/firmware-pwm100_v1/ManualDrive.cpp#L33]。
- 油門百分比換成 0～255 的 PWM，每 5 ms 最多變化 5 [src: raw/project/firmware-pwm100_v1/Drive.cpp#L282-L294] [src: raw/project/firmware-pwm100_v1/Config.h#L37] [src: raw/project/firmware-pwm100_v1/Config.h#L40]。

### 最高速 1.44 m/s

11-19 落地全油門 100% 實測 6492 cps≈1.44 m/s≈367 rpm（run-436d）；比賽「效能比」以平均速度相對此最高速計算 [src: raw/records/logs/AGENTS.md#L127]。換算：6492×0.000222≈1.441 m/s（推算）[src: raw/project/snapshot-20261123d/lap_pos.json#key=m_per_count]。最終成績見 [[experiments/final-performance]]。

## 公式與參數

```
pwm ← imu_boost(pwm)
pwm ← speed_adapt(pwm; LOW 24 / MID 30 / HIGH 50, curve_pwm_by)
pwm ← max(pwm, lap_speed 區段爬升值)            （只升不降）
pwm ← min(pwm, lane_cap, brake_zone, upper_cap, w_coast)
pwm ← speed_guard(pwm)                           （下坡超速 → 5）
韌體: duty = |pwm| × 255 / 100；每 5 ms 向目標移動 5
```
[src: raw/project/snapshot-20261123d/speed_policy.py#L114-L122] [src: raw/project/firmware-pwm100_v1/Drive.cpp#L266-L270]

| 參數 | 值 | 性質 | 出處 |
|---|---|---|---|
| speed_adapt min／mid／max／hard_cap | 24／30／50／50 | 調參值 | [src: raw/project/snapshot-20261123d/speed_adapt.json#key=max_pwm] |
| curve_pwm_by c1／c2／c3／c4 | 44／36／36／48 | 調參值 | [src: raw/project/snapshot-20261123d/speed_adapt.json#key=curve_pwm_by] |
| lap_speed 全域 rate／err_guard／steer_guard | 60 PWM/s／0.30／250 µs | 調參值 | [src: raw/project/snapshot-20261123d/lap_speed.json#L4-L6] |
| 兩段制 e_trouble／e_ok／mid_pwm | 0.4／0.3／70 | 調參值 | [src: raw/project/snapshot-20261123d/lap_speed.json#L16-L25] |
| 兩段制上升／下降速率 | 200／120 PWM/s | 調參值 | [src: raw/project/snapshot-20261123d/lap_speed.json#L23-L24] |
| 坡道區 err_guard／rate | 0.4／70 PWM/s | 調參值 | [src: raw/project/snapshot-20261123d/lap_speed.json#L70] |
| imu_boost uphill_pwm／on／off | 25／5°／3° | 調參值 | [src: raw/project/snapshot-20261123d/imu_boost.json#key=uphill_pwm] |
| speed_guard 觸發／放開 | 6800／4500 cps | 調參值 | [src: raw/project/snapshot-20261123d/speed_guard.json#L12-L13] |
| throttle_cap max_pct | 100 | 設計假設 | [src: raw/project/snapshot-20261123d/throttle_cap.json] |
| 韌體 MAX_THROTTLE_PERCENT | 100 | 設計假設（「Experiment ceiling; not a hardware rating」） | [src: raw/project/firmware-pwm100_v1/Config.h#L36] |
| 韌體斜坡 RAMP_STEP／RAMP_MS | 5／5 ms（0→255 約 255 ms，推算 255÷5×5） | 設計假設 | [src: raw/project/firmware-pwm100_v1/Config.h#L37] [src: raw/project/firmware-pwm100_v1/Config.h#L40] |
| 最高速 | 1.44 m/s（6492 cps） | 實測值 | [src: raw/records/logs/AGENTS.md#L127] |

## 未確認

- 本頁未逐格統計 run-b541 中每段油門實際由哪一層決定；各區段對圈速的貢獻見 [[experiments/final-performance]]。
- speed_policy.json 的 turn_pwm 18 與 lane_segment.LOCK_PWM 在上層的實際作用範圍未展開 [src: raw/project/snapshot-20261123d/speed_policy.json]。
- 最高速 1.44 m/s 只有 run-436d 一次落地量測；架空 100% 為 382／364 rpm [src: raw/records/logs/AGENTS.md#L127]。
- PWM 與車速的關係會隨電池電量改變（紀錄提到電量明顯影響圈速），本頁未量化。

## 相關條目

- [[control/command-chain]]
- [[control/lap-position]]
- [[control/slope-downhill]]
- [[synthesis/imu-roles]]
- [[hardware/vehicle-hardware]]
- [[experiments/final-performance]]
- [[comms/uart-protocol]]
