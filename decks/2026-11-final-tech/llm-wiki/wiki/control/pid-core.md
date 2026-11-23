---
id: control/pid-core
title: 視覺 PID 核心：誤差定義、PID 形式與參數
status: implemented
sources:
  - raw/project/snapshot-20261123d/visual_pid.py
  - raw/project/snapshot-20261123d/preview_error.py
  - raw/project/snapshot-20261123d/camera_pair.py
  - raw/project/snapshot-20261123d/offscreen_center.py
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/project/snapshot-20261123d/_extra/servo_profile.json
  - raw/records/analyses/play-comp-20261105-findings.json
  - raw/records/runs/run-b541-20261123/summary.json
  - raw/project/snapshot-20261123d/single_centre.py
  - raw/records/logs/AGENTS.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 視覺 PID 核心：誤差定義、PID 形式與參數

## 一句話結論

最終版每一格的基礎轉向命令，是由「相機路徑在固定前視列的橫向誤差（加一點遠列預視）」經一個帶條件式積分、近列微分低通與輸出速率限制的 PID 算出的舵機脈寬；參數為 kp 220／ki 40／kd 30、左右增益 1.5／1.45、中心 1445 µs，之後才交給命令鏈上的其他層修正 [src: raw/project/snapshot-20261123d/_extra/start_params.json#L31-L48]。

## 內容

### 這個 PID 在整條鏈中的位置

- **PID（比例－積分－微分控制器）**：依誤差本身（P）、誤差累積（I）、誤差變化率（D）算出修正量的回授控制器。本車用它把「路徑偏離畫面中心多少」換成舵機脈寬（µs，數字越大越往右）。
- 最終版路徑演算法名稱是 `camera-pair-v2-junction-flag`，在主程式裡被當成 `camera-pair-v2-junction` 處理 [src: raw/project/snapshot-20261123d/live_pid.py#L199]，因此控制器類別是 `OffscreenPID` [src: raw/project/snapshot-20261123d/live_pid.py#L567]。
- 類別繼承鏈為 OffscreenPID → CameraPairPID → PreviewErrorPID，PreviewErrorPID 內部再呼叫 NearDerivativePID（visual_pid.PID 的子類）[src: raw/project/snapshot-20261123d/offscreen_center.py#L75-L84] [src: raw/project/snapshot-20261123d/camera_pair.py#L95-L99] [src: raw/project/snapshot-20261123d/preview_error.py#L25-L54]。11-05 的分析也記錄了同一條呼叫鏈 [src: raw/records/analyses/play-comp-20261105-findings.json#L2]。
- 最終實跑 run-b541 的紀錄中，控制器版本欄位為 `offscreen-center-r2`，路徑演算法為 `camera-pair-v2-junction` [src: raw/records/runs/run-b541-20261123/summary.json#L52-L54]。
- PID 的輸出只是「提案」（reason `PROPOSAL_ONLY`，hardware_output false）[src: raw/project/snapshot-20261123d/visual_pid.py#L116-L118]；之後還要經過命令鏈的各層與輸出階段，見 [[control/command-chain]]。

### 誤差從哪裡來

誤差來自相機畫面的路徑點（YOLO 遮罩轉成路徑的過程見 [[path/mask-to-path]]）。

1. **近列誤差**：在固定前視列（row_ratio 0.6，即畫面第 0.6×719 列）找路徑通過的 x，換成相對畫面中心的比例，範圍夾在 ±1 [src: raw/project/snapshot-20261123d/offscreen_center.py#L20-L28]。中心另加一個視覺中心偏移 `visual_center_offset_px_640` 18（以 640 寬計）[src: raw/project/snapshot-20261123d/_extra/start_params.json#L45]。OffscreenPID 固定使用這一列（fixed_row），不像 PreviewErrorPID 會自動往下找可用列 [src: raw/project/snapshot-20261123d/offscreen_center.py#L78-L88]。
2. **遠列預視**：再取遠列（preview_far_row 0.45）的誤差，依兩列的車道寬先驗做透視正規化，避免「平行但偏移的車道」被誤當成方向誤差 [src: raw/project/snapshot-20261123d/preview_error.py#L56-L66]。遠近差乘上 preview_far_weight（最終版 0.2）後，經時間常數 0.15 s 的低通濾波，加到近列誤差上，成為送進 PID 的控制誤差 [src: raw/project/snapshot-20261123d/preview_error.py#L94-L102] [src: raw/project/snapshot-20261123d/_extra/start_params.json#L47-L48]。
3. **D 用近列**：NearDerivativePID 在呼叫父類前改寫上一格誤差，使 D 項實際微分的是「近列誤差的變化」，而不是含遠列的控制誤差；程式註解說明微分遠列會放大岔路與短線段的抖動 [src: raw/project/snapshot-20261123d/preview_error.py#L25-L35]。

### PID 形式（visual_pid.py）

- 時間間隔 dt 超過 max_gap 0.4 s、誤差缺失或超出 ±1 時，控制器重設並回傳無效；第一格只記錄誤差（WARMUP）[src: raw/project/snapshot-20261123d/visual_pid.py#L88-L100] [src: raw/project/snapshot-20261123d/_extra/start_params.json#L44]。
- D 項是一階低通的誤差變化率，時間常數 derivative_tau 0.15 s [src: raw/project/snapshot-20261123d/visual_pid.py#L101] [src: raw/project/snapshot-20261123d/_extra/start_params.json#L42]。
- 積分候選值夾在 ±integral_limit（1.0）[src: raw/project/snapshot-20261123d/visual_pid.py#L102] [src: raw/project/snapshot-20261123d/_extra/start_params.json#L43]。
- **條件式積分（anti-windup，防積分飽和）**：先用候選積分算一次輸出；只有在「輸出沒有被行程或速率限制卡住，或卡住的方向與誤差相反」時（(target−limited)×error ≤ 0）才接受新積分，否則保留舊值 [src: raw/project/snapshot-20261123d/visual_pid.py#L110-L114]。
- 輸出 u＝kp·e＋ki·I＋kd·D；u≥0 乘 right_gain、u<0 乘 left_gain，加上中心；先夾在 min_us～max_us，再限制每格變化不超過 steer_rate×dt [src: raw/project/snapshot-20261123d/visual_pid.py#L103-L109]。

### 中心與行程

- 中心 1445 µs、左限 780、右限 2050 來自舵機保存設定 rev44 [src: raw/project/snapshot-20261123d/_extra/servo_profile.json#L1-L6]；起跑參數（PID 文件 rev155）裡的值相同 [src: raw/project/snapshot-20261123d/_extra/start_params.json#L3] [src: raw/project/snapshot-20261123d/_extra/start_params.json#L37-L41]。
- 起跑時主程式檢查 PID 中心必須等於保存的共用中心，限位不得超出保存設定 [src: raw/project/snapshot-20261123d/live_pid.py#L563-L565]；手機服務起跑時也以車上舵機設定覆蓋 center／min／max [src: raw/project/snapshot-20261123d/_extra/start_params.json#L2]。
- `single_centre.json` 開啟，起跑時會把其他層裡以絕對值寫的「直行點」改成共用中心、把絕對上限改成「中心＋（原值−1480）」，詳見 [[control/command-chain]] [src: raw/project/snapshot-20261123d/single_centre.py#L6-L15]。

### 關閉的內建功能

- `direction_enabled` 0、`backlash_enabled` 0、`backlash_initial_enabled` 0：控制器內建的方向預視與間隙補償都關閉 [src: raw/project/snapshot-20261123d/_extra/start_params.json#L18-L30]。PreviewErrorPID 甚至要求 direction 必須為 0 才能建立 [src: raw/project/snapshot-20261123d/preview_error.py#L44-L45]。間隙改在輸出階段補償，見 [[control/play-comp]]。
- PID 參數裡的 `pwm` 15 只是基礎值，實際油門由速度層決定，見 [[control/speed-control]] [src: raw/project/snapshot-20261123d/_extra/start_params.json#L34]。

## 公式與參數

近列誤差（畫面寬 1280、高 720；row＝row_ratio×719）[src: raw/project/snapshot-20261123d/offscreen_center.py#L20-L28]：

```
e_near = clamp( (x_row − 639.5 − offset_640 × 1280/640) / 639.5 , −1, 1 )
```

控制誤差（遠列預視）[src: raw/project/snapshot-20261123d/preview_error.py#L56-L66] [src: raw/project/snapshot-20261123d/preview_error.py#L94-L100]：

```
e_far_proj = e_far × W(near) / W(far)
dir ← dir + dt/(τ_dir+dt) × ( w_far×(e_far_proj − e_near) − dir )
e = clamp( e_near + dir , −1, 1 )
```

PID（每格）[src: raw/project/snapshot-20261123d/visual_pid.py#L101-L115]：

```
D  ← D + dt/(τ_D+dt) × ( Δe_near/dt − D )
I* = clamp( I + e·dt , −I_lim, I_lim )
u  = kp·e + ki·I + kd·D
（指令另加 feedforward() 項；基礎 PID 類別為 0，最終版控制器未覆寫）
target  = c + u × (u ≥ 0 ? g_R : g_L)
bounded = clamp(target, min_us, max_us)
steer   = clamp(bounded, last − rate·dt, last + rate·dt)
若 (target − steer)·e ≤ 0 則 I = I*，否則 I 不變
```

| 參數 | 值 | 性質 | 出處 |
|---|---|---|---|
| kp／ki／kd | 220／40／30 | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L31-L33] |
| right_gain／left_gain | 1.45／1.5 | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L38-L39] |
| steer_rate | 1500 µs/s | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L35] |
| center／min／max | 1445／780／2050 µs | 實測值（舵機校準，rev44） | [src: raw/project/snapshot-20261123d/_extra/servo_profile.json#L1-L6] |
| derivative_tau | 0.15 s | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L42] |
| integral_limit | 1.0 | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L43] |
| max_gap | 0.4 s | 設計假設 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L44] |
| row_ratio／preview_far_row | 0.6／0.45 | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L36] [src: raw/project/snapshot-20261123d/_extra/start_params.json#L48] |
| preview_far_weight | 0.2 | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L47] |
| τ_dir（遠近差低通） | 0.15 s | 設計假設（程式內固定） | [src: raw/project/snapshot-20261123d/preview_error.py#L53-L54] |
| visual_center_offset_px_640 | 18 px | 調參值 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#L45] |
| 參數合法範圍（如 kp 0～600、steer_rate 50～1500） | — | 設計假設 | [src: raw/project/snapshot-20261123d/visual_pid.py#L27-L30] |

## 未確認

- PID 參數表 rev155 的完整調參歷程（kp 220 何時定案）不在本頁來源內；只有「rev150 已是 kp 220／ki 40／kd 30」的紀錄 [src: raw/records/logs/AGENTS.md#L335]。
- W(near)／W(far) 的車道寬先驗來自 `line_width_prior.prior_width`，本頁未展開其數值。
- steer_rate 1500 µs/s 在 PID 內限制一次，manual_drive 與韌體又各有一層速率限制（見 [[control/command-chain]]），三者哪一個實際起作用未逐格核對。

## 相關條目

- [[control/command-chain]]：PID 之後的各層與輸出階段。
- [[path/mask-to-path]]：路徑點如何產生。
- [[path/vision-failure-modes]]：誤差無效、丟線時的情況。
- [[control/play-comp]]：輸出階段的轉向間隙補償。
- [[control/yaw-inner]]：疊加在 PID 輸出上的陀螺儀內迴圈。
- [[hardware/steering-servo]]：舵機與中心校準。
- [[overview]]
