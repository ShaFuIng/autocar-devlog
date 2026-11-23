---
id: control/disabled-layers
title: 已關閉、只記錄或說明文字過時的控制層清單
status: mixed
sources:
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/auto_centre.json
  - raw/project/snapshot-20261123d/bottom_commit.json
  - raw/project/snapshot-20261123d/curve_hold.json
  - raw/project/snapshot-20261123d/diff_assist.json
  - raw/project/snapshot-20261123d/exit_damp.json
  - raw/project/snapshot-20261123d/gyro_damp.json
  - raw/project/snapshot-20261123d/heading_term.json
  - raw/project/snapshot-20261123d/standalone_line.json
  - raw/project/snapshot-20261123d/standalone_line_path.py
  - raw/project/snapshot-20261123d/straight_slew.json
  - raw/project/snapshot-20261123d/xp_corridor.json
  - raw/project/snapshot-20261123d/arc2.json
  - raw/project/snapshot-20261123d/arc2.py
  - raw/project/snapshot-20261123d/curve_trim.json
  - raw/project/snapshot-20261123d/lap_ff.json
  - raw/project/snapshot-20261123d/speed_guard.json
  - raw/project/snapshot-20261123d/speed_guard.py
  - raw/project/snapshot-20261123d/arc_lat.json
  - raw/project/snapshot-20261123d/arc_lat.py
  - raw/project/snapshot-20261123d/dist_ff.json.enabled-backup
  - raw/project/snapshot-20261123d/output_unify.py
  - raw/project/snapshot-20261123d/curve_map.json
  - raw/project/snapshot-20261123d/yaw_inner.json
  - raw/project/snapshot-20261123d/crossings_ctl.json
  - raw/project/snapshot-20261123d/bottom_map.json
  - raw/project/snapshot-20261123d/bottom_owner.json
  - raw/project/snapshot-20261123d/bottom_guide.json
  - raw/project/snapshot-20261123d/imu_boost.json
  - raw/project/snapshot-20261123d/i_ramp.py
  - raw/project/snapshot-20261123d/i_ramp.json
  - raw/project/snapshot-20261123d/upper_single.json
  - raw/project/snapshot-20261123d/stuck_stop.json
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/project/snapshot-20261123d/MANIFEST.sha256
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 已關閉與只記錄的控制層

## 一句話結論

最終版快照裡有 10 個頂層 `enabled: false` 的設定檔、4 個關閉的子區塊、四彎只記錄的 arc_lat、一個不被任何程式讀取的備份檔與一個不存在的設定檔；這些都**不可**寫成現役。反過來，至少 15 支程式的說明文字寫「NOT deployed」，但 json 開啟且主程式有呼叫，依規則算現役 [src: raw/project/snapshot-20261123d/live_pid.py#L84-L86]。

## 內容

判定規則：json `enabled` 為 true 且主程式有呼叫＝現役；說明文字與此不符時以 json＋呼叫為準。本清單由腳本掃描快照內全部 `*.json` 的 `enabled`／`control`／`mode` 鍵後逐項核對程式而得（快照頂層 71 個 json 加 _extra 2 個）[src: raw/project/snapshot-20261123d/MANIFEST.sha256]。

### A. 頂層 enabled false 的設定檔【曾用】
| 檔案 | 原本作用 | 最終版狀態 | 來源 |
|---|---|---|---|
| auto_centre.json | 每輪後依中心估計器自動移動共用中心 | 關；程式已移除（b1-dead-layers），說明：估計器偏高約 1454 對直行點約 1410 | [src: raw/project/snapshot-20261123d/auto_centre.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L564] |
| bottom_commit.json | 坡底轉向承諾 | 關；程式已移除 | [src: raw/project/snapshot-20261123d/bottom_commit.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L84] |
| curve_hold.json | 彎 2 15～120° 舵量下限 1700 | 關；11-11 過度轉向後停用，程式已移除 | [src: raw/project/snapshot-20261123d/curve_hold.json#key=enabled] [src: raw/project/snapshot-20261123d/curve_hold.json#key=note] [src: raw/project/snapshot-20261123d/live_pid.py#L84] |
| diff_assist.json | 左右輪差速輔助轉向 | 關；程式已移除，兩輪同 PWM | [src: raw/project/snapshot-20261123d/diff_assist.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L1640-L1641] |
| exit_damp.json | 出彎後阻尼 | 關；cleanup-r1 移除 | [src: raw/project/snapshot-20261123d/exit_damp.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L85] |
| gyro_damp.json | 陀螺儀轉速阻尼（yaw 模式 K 18、±90 µs） | 關；程式步驟已移除，概念由 yaw_inner 取代 | [src: raw/project/snapshot-20261123d/gyro_damp.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L84] |
| heading_term.json | 路徑方向角加項 | 關；程式已移除 | [src: raw/project/snapshot-20261123d/heading_term.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L84] |
| standalone_line.json | 路徑側「遺失右線重新標記」（lost-right-r2） | 關；函式讀到 enabled false 即返回 | [src: raw/project/snapshot-20261123d/standalone_line.json#L1] [src: raw/project/snapshot-20261123d/standalone_line_path.py#L12-L19] |
| straight_slew.json | 直線舵量限速＋上限 | 關；限速步驟已移除，**但 mean_gz_max 12 仍被 weave 旗標讀取**（判斷 2 s 平均轉速是否算「在轉」）| [src: raw/project/snapshot-20261123d/straight_slew.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L995] [src: raw/project/snapshot-20261123d/live_pid.py#L1218-L1219] |
| xp_corridor.json | 圓圈路口航向走廊 | 關；物件每輪仍建立但不作用；因與 blind_c2 範圍重疊而關 | [src: raw/project/snapshot-20261123d/xp_corridor.json#L1] [src: raw/project/snapshot-20261123d/live_pid.py#L1160-L1162] |

### B. 關閉的子區塊【曾用】
- arc2.pre（坡上預先右轉）：pre.enabled false；雖然 pre.r2.enabled true，`_sub` 先檢查父層，物件不建立，arc2_pre 層不執行 [src: raw/project/snapshot-20261123d/arc2.json#L1213-L1214] [src: raw/project/snapshot-20261123d/arc2.json#L1272-L1273] [src: raw/project/snapshot-20261123d/arc2.py#L57-L60] [src: raw/project/snapshot-20261123d/arc2.py#L608-L612]。關閉理由：11 次落地中 7 次出外線 [src: raw/project/snapshot-20261123d/arc2.json#L1322]。
- curve_trim.curves.c3：enabled false（只開 c1）[src: raw/project/snapshot-20261123d/curve_trim.json#key=curves.c3.enabled]。
- lap_ff.curves.c3：enabled false，彎 3 由 arc2.c3 取代 [src: raw/project/snapshot-20261123d/lap_ff.json#key=curves.c3.enabled]。
- speed_guard.ramp_cap：enabled false（使用者 11-13 決定上坡不改）[src: raw/project/snapshot-20261123d/speed_guard.json#key=ramp_cap] [src: raw/project/snapshot-20261123d/speed_guard.py#L6-L8]。

### C. 只記錄（不出命令）【僅參考】
- arc_lat 四彎：zones.c1～c4 enabled true 但 control false＝只記錄橫向位置（LOG_ONLY）[src: raw/project/snapshot-20261123d/arc_lat.json#L6-L33] [src: raw/project/snapshot-20261123d/arc_lat.py#L34] [src: raw/project/snapshot-20261123d/arc_lat.py#L356-L361]。注意：它量到的 y 仍被彎 3 的 x-band 讀取，見 [[control/curve-band-ff]] [src: raw/project/snapshot-20261123d/live_pid.py#L1526]。
- speed_guard.overspeed_watch：程式說明為「LOG ONLY」，不改 PWM 或舵量 [src: raw/project/snapshot-20261123d/speed_guard.py#L12]。
- bottom_guide 有效格：只記錄距離（TRACK），不改命令（cap_lag null）[src: raw/project/snapshot-20261123d/live_pid.py#L1775-L1779] [src: raw/project/snapshot-20261123d/bottom_guide.json#key=cap_lag]。

### D. 死檔與不存在的設定檔
- dist_ff.json.enabled-backup：內容 enabled true，但快照內沒有任何程式讀取 dist_ff（全文搜尋無結果），檔名也不是 .json，屬死檔 [src: raw/project/snapshot-20261123d/dist_ff.json.enabled-backup#L1]。
- output_unify.json：快照內不存在；output_unify.load_config 讀不到檔即回傳 None，輸出端統一層不建立 [src: raw/project/snapshot-20261123d/output_unify.py#L25-L27] [src: raw/project/snapshot-20261123d/output_unify.py#L39-L43] [src: raw/project/snapshot-20261123d/live_pid.py#L577]。
- i_ramp 的 land（落地積分釋放）：i_ramp.json 沒有 land 鍵＝不作用 [src: raw/project/snapshot-20261123d/i_ramp.py#L32-L35] [src: raw/project/snapshot-20261123d/i_ramp.json#L1]。
- arc2 blind_c2 的 v2 控制律：json 無 v2 區塊，r4 優先 [src: raw/project/snapshot-20261123d/arc2.py#L500-L503]。

### E. 參數層面關閉（模組現役，但其中一項功能關）
| 鍵 | 值 | 效果 | 來源 |
|---|---|---|---|
| curve_map.lock | false | 不用地圖轉速鎖，只給轉速下限 | [src: raw/project/snapshot-20261123d/curve_map.json#key=lock] |
| yaw_inner.heading_hold | false | 內迴圈的直線航向保持模式關 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=heading_hold] |
| yaw_inner.pv_k | null | 入彎遠方預覽項關 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=pv_k] |
| yaw_inner.curve_cap_us | null | 彎內修正項上限關 | [src: raw/project/snapshot-20261123d/yaw_inner.json#key=curve_cap_us] |
| PID direction_enabled | 0 | 遠方列方向項關 | [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=direction_enabled] |
| PID backlash_enabled／backlash_initial_enabled | 0／0 | PID 內建間隙補償關（改由輸出端 play_comp，見 [[control/play-comp]]） | [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=backlash_enabled] [src: raw/project/snapshot-20261123d/_extra/start_params.json#key=backlash_initial_enabled] |
| crossings_ctl.xp1_hold | null | V 字路口遺失陀螺儀保持關，程式已移除 | [src: raw/project/snapshot-20261123d/crossings_ctl.json#key=xp1_hold] [src: raw/project/snapshot-20261123d/live_pid.py#L85-L86] |
| bottom_map.left_floor_us／pre_right_us | null／0 | 坡底左限與坡上預右轉關 | [src: raw/project/snapshot-20261123d/bottom_map.json#key=left_floor_us] [src: raw/project/snapshot-20261123d/bottom_map.json#key=pre_right_us] |
| bottom_owner.left_cap_us | null | 落地左側保護關 | [src: raw/project/snapshot-20261123d/bottom_owner.json#L1] |
| bottom_guide.cap_lag／hold_pwm | null／null | 不放開右上限、保持格不另限 PWM | [src: raw/project/snapshot-20261123d/bottom_guide.json#key=hold_pwm] |
| imu_boost.downhill_pwm | null | 下坡專用 PWM 關 | [src: raw/project/snapshot-20261123d/imu_boost.json#L9] |
| lap_ff.gate_after_deg | 999 | 彎內相機閘門實際不啟用 | [src: raw/project/snapshot-20261123d/lap_ff.json#key=gate_after_deg] |
| crossing_pass.release_err | 9.0 | 路口窗口實際不交還相機 | [src: raw/project/snapshot-20261123d/crossing_pass.json#key=release_err] |
| upper_single.mask_dash／normal_fallback／edge_follow | false／false／false | 上層遮罩虛線來源、一般路徑備援、邊線跟隨關 | [src: raw/project/snapshot-20261123d/upper_single.json#key=mask_dash] [src: raw/project/snapshot-20261123d/upper_single.json#key=edge_follow] |

### F. 說明文字寫「NOT deployed」但實際現役（json 開啟＋主程式呼叫）
以下檔案的程式說明或 json note 寫 offline candidate／NOT deployed，但最終版 json 開啟且主程式有呼叫，依規則算現役、說明文字過時：
- arc2.py（land／blind／c3、blind-r4、landing-r2、pulse、land lost）[src: raw/project/snapshot-20261123d/arc2.py#L1] [src: raw/project/snapshot-20261123d/arc2.json#L3]
- arc_lat.py（模組現役，但四彎只記錄）[src: raw/project/snapshot-20261123d/arc_lat.py#L1] [src: raw/project/snapshot-20261123d/arc_lat.json#L3]
- bottom_guide.py [src: raw/project/snapshot-20261123d/bottom_guide.py#L1] [src: raw/project/snapshot-20261123d/bottom_guide.json#key=enabled]
- curve_trim.py [src: raw/project/snapshot-20261123d/curve_trim.py#L1] [src: raw/project/snapshot-20261123d/curve_trim.json#key=enabled]
- i_ramp.py（ramp／exit／preload 現役；land 不在 json）[src: raw/project/snapshot-20261123d/i_ramp.py#L1] [src: raw/project/snapshot-20261123d/i_ramp.json#L1]
- land4.py [src: raw/project/snapshot-20261123d/land4.py#L1]
- lap_ff.py（含 c2-band、lap-ff-r2、c3-tail、c4-band 各段說明）[src: raw/project/snapshot-20261123d/lap_ff.py#L1] [src: raw/project/snapshot-20261123d/lap_ff.json#key=enabled]
- lap_pos.py、lap_speed.py、single_centre.py、speed_guard.py、speed_policy.py、stuck_stop.py、throttle_cap.py、upper_wide.py：各自說明首行寫 NOT deployed，最終版的 json（lap_pos.json、lap_speed.json、single_centre.json、speed_guard.json 子區塊、stuck_stop.json、throttle_cap.json、upper_wide.json）皆開啟或存在 [src: raw/project/snapshot-20261123d/single_centre.py#L1] [src: raw/project/snapshot-20261123d/speed_guard.py#L1] [src: raw/project/snapshot-20261123d/stuck_stop.json#L4-L5]
- json note 也寫 NOT deployed 者：arc2.json（blind_c2、pulse、landing_r2）、curve_trim.json、land4.json、lap_ff.json、xp_anchor.json [src: raw/project/snapshot-20261123d/arc2.json#L1175] [src: raw/project/snapshot-20261123d/arc2.json#L245]
- stuck_stop.json 的 note 寫「LOG mode … never stops」，但 mode 鍵為 stop，程式依 mode 停車，note 過時 [src: raw/project/snapshot-20261123d/stuck_stop.json#L3-L5]。

## 公式與參數

無。

## 未確認

- 本清單的掃描只看 `enabled`／`control`／`mode` 鍵；沒有這些鍵的 json（例如 jump_guard.json、gyro_hold.json）是否有「以 null 關閉」的子功能，只核對了本頁列出的幾項。
- lap_pos.py、lap_speed.py、speed_policy.py、throttle_cap.py、upper_wide.py 的現役細節由其他條目負責（[[control/lap-position]]、[[control/speed-control]]），本頁只核對 json 存在與開啟。
- 快照逐檔雜湊清單見 [src: raw/project/snapshot-20261123d/MANIFEST.sha256]。

## 相關條目

- [[control/command-chain]]、[[control/pid-core]]
- [[control/yaw-inner]]、[[control/heading-hold]]、[[control/curve-band-ff]]、[[control/slope-downhill]]、[[control/lost-path]]
- [[control/play-comp]]、[[control/speed-control]]、[[control/lap-position]]
- [[experiments/s-weave]]、[[overview]]
