---
id: synthesis/glossary
title: 名詞與地標代號對照
status: implemented
sources:
  - raw/project/snapshot-20261123d/lap_pos.json
  - raw/project/snapshot-20261123d/lap_pos.py
  - raw/project/snapshot-20261123d/curve_map.py
  - raw/project/snapshot-20261123d/visual_pid.py
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/snapshot-20261123d/speed_guard.py
  - raw/project/snapshot-20261123d/single_centre.py
  - raw/project/snapshot-20261123d/lap_ff.py
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

條目中常見的程式代號都在這裡用一句話解釋。寫簡報時要改成一般用語，不能直接把代號放上投影片。

## 內容

**地標代號**：地標定位用的賽道特徵點。後面數字是從彎 1 起點算起的名義位置（公尺）[src: raw/project/snapshot-20261123d/lap_pos.json#L4-L19]。

| 代號 | 意思 | 名義位置 |
|---|---|---|
| C1s／C1e | 彎 1 起點／終點（s＝start、e＝end） | 0.0／3.33 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |
| C2s／C2e | 彎 2 起點／終點 | 15.27／19.77 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |
| C3s／C3e | 彎 3 起點／終點 | 30.21／37.33 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |
| RAMP | 上坡開始（俯仰角超過門檻） | 36.97 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |
| TOP | 坡頂 | 39.86 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |
| DASHs／DASHe | 高架上層虛線轉彎開始／結束 | 42.82／43.68 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |
| DOWN | 下坡開始 | 47.05 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |
| LAND8 | 下坡落地點（俯仰回到 −8° 以上） | 49.37 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |
| C4s／C4e | 彎 4 起點／終點 | 49.54／56.98 [src: raw/project/snapshot-20261123d/lap_pos.json#key=nominal_m] |

- 寫法如「C2e+x m」表示彎 2 終點之後 x 公尺；「TOP+」「DASHe+」同理（見 [[control/lap-position]]）。
- 地標之間的路段名稱（curve1、diagonal_v、circle_straight…）見 [src: raw/project/snapshot-20261123d/lap_pos.py#L34-L37]，對應關係見 [[control/lap-position]]。

**其他名詞**：

| 名詞 | 一句話解釋 | 出處 |
|---|---|---|
| µs（舵量） | 舵機脈衝寬度，單位微秒；中心 1445 µs 是直行，數字越大越往右 | [[hardware/steering-servo]] |
| 直行點 | 實際讓車走直線的舵量；因為轉向有間隙，它不一定等於設定的中心。最終版用一個共用中心代替各處寫死的直行點 [src: raw/project/snapshot-20261123d/single_centre.py#L1-L9] | [[control/play-comp]] |
| cps | 編碼器每秒計數（counts per second），用來表示輪速 [src: raw/project/snapshot-20261123d/speed_guard.py#L9-L11] | [[control/speed-control]] |
| WARMUP | PID 第一格還沒有前一格可算微分，先不輸出 [src: raw/project/snapshot-20261123d/visual_pid.py#L98-L100] | [[control/pid-core]] |
| FLOOR／RELEASED | 彎道地圖的兩種狀態：還沒轉完時給內迴圈一個「至少要轉這麼快」的下限（FLOOR），轉完就放開（RELEASED）[src: raw/project/snapshot-20261123d/curve_map.py#L122-L123] | [[control/curve-band-ff]] |
| crest_midpoint | 坡頂看不到完整車道時的備用路徑來源 [src: raw/project/snapshot-20261123d/live_pid.py#L1997] | [[path/vision-failure-modes]] |
| proposal | 控制程式每格算出、準備送出的命令與各層診斷資料；紀錄檔以此欄位保存 | [[control/command-chain]] |
| e_c（置中誤差） | 車在彎道內正好置中時，相機誤差應有的值；帶狀前饋用「誤差減 e_c」修正，而不是要求誤差為 0 [src: raw/project/snapshot-20261123d/lap_ff.py#L194] | [[control/curve-band-ff]] |
| 帶狀（band）前饋 | 依「已轉角度」查跑道曲率表，先給出應有的舵量，再用相機誤差微調 | [[control/curve-band-ff]] |
| 全權（own） | 某一層在它的範圍內完全決定舵量，取代前面的 PID 結果 | [[control/command-chain]] |

## 公式與參數

無。

## 未確認

- 名義位置是設定值，實際每圈會依地標重新對齊，見 [[control/lap-position]]。

## 相關條目

- [[overview]]
- [[control/lap-position]]
- [[control/command-chain]]
