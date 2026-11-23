---
id: control/play-comp
title: 轉向間隙補償（play_comp）
status: implemented
sources:
  - raw/project/snapshot-20261123d/play_comp.py
  - raw/project/snapshot-20261123d/play_comp.json
  - raw/project/snapshot-20261123d/output_stage.py
  - raw/project/snapshot-20261123d/output_stage.json
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/_extra/start_params.json
  - raw/records/analyses/play-comp-20261105-findings.json
  - raw/records/analyses/why-s-weave-20261107-findings.json
  - raw/records/logs/AGENTS.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 轉向間隙補償（play_comp）

## 一句話結論

最終版在每一筆命令送出前，依「命令上一次往哪個方向移動」加上固定偏移：往右移過就 +15 µs、往左移過就 −15 µs，換向門檻 15 µs，用來吃掉轉向連桿的空行程；它處理的是機構間隙，和直線 S 型擺動（迴路延遲造成，由陀螺儀內迴圈處理）是不同的問題 [src: raw/project/snapshot-20261123d/play_comp.json#L1-L7] [src: raw/project/snapshot-20261123d/play_comp.py#L38-L55]。

## 內容

### 什麼是轉向間隙

**轉向間隙（play／backlash）**＝舵機轉了、輪子卻還沒跟著轉的那一段空行程，來自連桿與舵機臂的鬆動。命令換方向時，舵機要先走完這段空行程，輪子才開始動，所以同一個命令值「從左邊來」與「從右邊來」對應的輪角不同。

### 11-05 的量測背景

- 說明文字記載：11-05 實測命令 1340～1490 µs 之間車子幾乎不產生偏航；只記錄的中心估計器得到「從左邊來的直行點約 1500 µs、從右邊來約 1360 µs」，當時保存的中心 1390，估計間隙約 140 µs，中心落在間隙內 [src: raw/project/snapshot-20261123d/play_comp.py#L3-L7]。
- 同日的分析指出控制器內建補償（visual_pid backlash，當時關閉）有兩個問題：補償量在控制器內部，之後會被 gain_schedule 依速度縮小，但機械間隙不會隨速度變；而且開啟後控制器把輸出速率限在 500～800 µs/s，比正常 1500 µs/s 慢 [src: raw/records/analyses/play-comp-20261105-findings.json#L3]。
- 因此改在**輸出階段、最終命令送出前**做補償，不受 gain_schedule 縮放，也不加速率上限 [src: raw/project/snapshot-20261123d/play_comp.py#L8-L13]。控制器內建補償在最終版仍關閉 [src: raw/project/snapshot-20261123d/_extra/start_params.json#L21-L30]。

### 演算法

1. 記住「上一次移動方向」direction（初始 0）與該方向上的極值 extreme（初始為中心）[src: raw/project/snapshot-20261123d/play_comp.py#L33] [src: raw/project/snapshot-20261123d/play_comp.py#L43]。
2. 原始命令比極值多走 threshold_us 以上才算換向；同方向繼續走則更新極值（遲滯式換向偵測）[src: raw/project/snapshot-20261123d/play_comp.py#L45-L53]。
3. 方向為右加 +right_us、為左加 −left_us，再夾在 min_us～max_us [src: raw/project/snapshot-20261123d/play_comp.py#L54-L55]。
4. 位置：output_stage.send 的第 3 步，在記錄 cmd_comp 在途命令之後、交給 manual_drive 之前；設定檔名由 output_stage.json 指定為 play_comp.json，每輪起跑讀一次，免重啟 [src: raw/project/snapshot-20261123d/output_stage.py#L3-L9] [src: raw/project/snapshot-20261123d/output_stage.json]。
5. 起跑回中的格與中心 WARMUP 格不補償、也不推進補償狀態 [src: raw/project/snapshot-20261123d/live_pid.py#L658-L661]；play_comp 開啟時，上層 lane_segment 自己的間隙補償會被關掉，避免兩個補償疊加 [src: raw/project/snapshot-20261123d/live_pid.py#L648-L655]。

### 數值演變（新舵機）

- 舊舵機時期設定為 ±55、門檻 15 [src: raw/records/logs/AGENTS.md#L335]。
- 11-23 下午舊舵機損壞換新；新舵機三輪實跑估得間隙約 60（原 130）、直行點 1435～1444，因此中心改 1445、補償先改 ±25 [src: raw/records/logs/AGENTS.md#L151]。
- 11-23 17:19 再改為 ±15（退回值 585cd447）[src: raw/records/logs/AGENTS.md#L144]，並成為定版設定 [src: raw/records/logs/AGENTS.md#L136]。
- play_comp.json 的附註仍寫「55 → 25」，是 16:5x 那一步的說明，實際數值已是 15 [src: raw/project/snapshot-20261123d/play_comp.json#L2-L6]。

### 與 S 型擺動的區別

- **間隙**：機構空行程，造成換向瞬間「命令有、輪角沒有」的固定落差；補償方式是換向時加一個固定偏移。
- **直線 S 型**：11-07 的分析認為主要來自迴路本身——誤差→舵機→偏航率→航向→橫向位置是兩次積分，加上約 0.75 s 的迴路延遲，使相位裕度不足；中心校準與硬性死區都被排除為主因，且當時試 ±40 的間隙補償反而更差 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L10-L21]。對策方向是陀螺儀偏航率內迴圈 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L24]，見 [[control/yaw-inner]] 與 [[experiments/s-weave]]。
- 因此兩者在最終版同時存在、各管各的：play_comp 在最末端改命令，yaw_inner 在層表中段改命令（見 [[control/command-chain]]）。紀錄也提醒：若鎖緊間隙，補償必須同步調小或關 [src: raw/records/logs/AGENTS.md#L108]。

## 公式與參數

```
若 direction = 0：raw − extreme ≥ th → direction = +1；extreme − raw ≥ th → direction = −1
若 direction = +1：raw ≥ extreme → extreme = raw；extreme − raw ≥ th → direction = −1, extreme = raw
若 direction = −1：raw ≤ extreme → extreme = raw；raw − extreme ≥ th → direction = +1, extreme = raw
out = clamp( raw + (direction>0 ? +right_us : direction<0 ? −left_us : 0), min_us, max_us )
```
[src: raw/project/snapshot-20261123d/play_comp.py#L42-L55]

| 參數 | 值 | 性質 | 出處 |
|---|---|---|---|
| right_us／left_us | 15／15 µs | 調參值（依新舵機間隙約 60 的估計逐步調小） | [src: raw/project/snapshot-20261123d/play_comp.json#key=right_us] [src: raw/project/snapshot-20261123d/play_comp.json#key=left_us] |
| threshold_us | 15 µs | 調參值 | [src: raw/project/snapshot-20261123d/play_comp.json#key=threshold_us] |
| 程式預設值（json 缺時） | 關、110／30／30 | 設計假設 | [src: raw/project/snapshot-20261123d/play_comp.py#L20] |
| 新舵機間隙估計 | 約 60 µs | 實測值（三輪擬合） | [src: raw/records/logs/AGENTS.md#L151] |
| 舊舵機間隙估計 | 約 130 µs（跑圈擬合 110～130） | 實測值 | [src: raw/records/logs/AGENTS.md#L108] |

## 未確認

- 間隙 60 µs 是由跑圈資料擬合，不是架空直接量測；補償只取到 15（約間隙的四分之一），是否最佳未驗證 [src: raw/records/logs/AGENTS.md#L151] [src: raw/project/snapshot-20261123d/play_comp.json#key=right_us]。
- 說明文字自承「Experiment values, not a measured mechanical play」[src: raw/project/snapshot-20261123d/play_comp.py#L13]。
- 補償換邊頻率對舵機磨耗與直線擺動的影響，最終版只有 run-ce19 一輪「直線 gz 標準差變小」的紀錄 [src: raw/records/logs/AGENTS.md#L143]。

## 相關條目

- [[control/command-chain]]
- [[control/pid-core]]
- [[control/yaw-inner]]
- [[experiments/s-weave]]
- [[hardware/steering-servo]]
- [[hardware/vehicle-hardware]]
