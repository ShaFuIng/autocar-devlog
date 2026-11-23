---
id: experiments/failures-abandoned
title: 試過但放棄或確定變差的方法，以及從未上車的提案
status: mixed
sources:
  - raw/records/logs/AGENTS.md
  - raw/records/logs/AGENTS_HISTORY_until_20261119.md
  - raw/records/analyses/why-s-weave-20261107-findings.json
  - raw/records/analyses/tracking-proposal-v1.json
  - raw/records/analyses/a1-poster-factcheck-20261103.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 試過但放棄或確定變差的方法

## 一句話結論

開發紀錄有一節「試過且確定變差，不要再試」列出約 25 項，多數是實車試過後退回，少數只有離線模型證據；另有追蹤演算法提案（Regulated Pure Pursuit、Stanley、MPC）與 TensorRT 加速只停在提案或參考階段，從未上車 [src: raw/records/logs/AGENTS.md#L377-L386] [src: raw/records/analyses/tracking-proposal-v1.json#L4-L6] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L573]。

## 內容

### 讀法

- 每項標【曾用】＝曾上車或實跑過、已退回；【僅參考】＝只有提案或離線評估、從未上車。
- 「依據」欄分開寫實車或離線（模型／重播）；只有模型證據的項目，「變差」是模型估計，不是實車觀察。
- 主清單出自 [src: raw/records/logs/AGENTS.md#L377-L386]；能找到較詳細紀錄的另附出處。

### 轉向與間隙補償

| 項目 | 想解決什麼 | 結果 | 依據 | 出處 |
|---|---|---|---|---|
| 【曾用】間隙補償門檻 60 | 降低補償換邊次數 | 擺幅變大 | 紀錄寫「門檻 60 實車變差」；11-17 模型亦變差 | [src: raw/records/logs/AGENTS.md#L379] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L612] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L603] |
| 【僅參考】補償最短停留時間 | 同上 | 11-12 評估後不採用 | 離線評估 | [src: raw/records/logs/AGENTS.md#L379] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L612] |
| 【僅參考】只用低通決定補償換邊 | 讓補償不被小抖動觸發 | 直線 ×1.14～1.43（變差） | 閉迴路模型 | [src: raw/records/logs/AGENTS.md#L379] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L617] |
| 【僅參考】內迴圈拿掉對向上限（oppose cap） | 讓陀螺儀阻尼不被相機方向壓住 | 主直線晃的圈 ×1.14、平穩圈 ×1.15（變差），「不要做」 | 閉迴路重播模型 | [src: raw/records/logs/AGENTS.md#L380] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L646] |
| 【僅參考】內迴圈轉向增益改成實測值 | 讓 yaw_inner 假設的增益（0.073）符合實測（0.165～0.20） | 模型擺幅 12.4°（變差） | 模型 | [src: raw/records/logs/AGENTS.md#L380] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L403-L404] |
| 【曾用】kd 60 以上 | 加阻尼壓直線 S 型 | 11-07 分析：kd 60 時幅度變大；模型 kd 90 在 1.4 m/s 不穩 | 實車紀錄分析＋模型 | [src: raw/records/logs/AGENTS.md#L380] [src: raw/records/analyses/why-s-weave-20261107-findings.json#L14] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L404] |

S 型擺動整體脈絡見 [[experiments/s-weave]]。

### 路口與上段

| 項目 | 想解決什麼 | 結果 | 依據 | 出處 |
|---|---|---|---|---|
| 【曾用】路口直行窗口第二／三版 | 圓圈路口直行時不被別條線帶走 | 自 C2e+0.3 m 起以固定地圖角整段接管，成敗取決於出彎角；之後改做第四版 | 實車 | [src: raw/records/logs/AGENTS.md#L381] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L641] |
| 【曾用】上段 L1（stall 修正＋車頭上限） | 虛線轉彎後快速對準虛線 | 5 次通過全部過衝 +8～+13.4° 、上段擺盪 | 實車（11-15） | [src: raw/records/logs/AGENTS.md#L382] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L477] |
| 【曾用】轉後加速＋滑行 | 上層提速 | 坡口前車速掉到 0.25～0.41 m/s、一次過衝 16° | 實車（run-2485） | [src: raw/records/logs/AGENTS.md#L384] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L485] |
| 【僅參考】拿掉備用走廊 | 簡化路口處理 | 會新增 86 段 ≥0.35 s 無路徑（共 84.8 s） | 重播統計 | [src: raw/records/logs/AGENTS.md#L386] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L649] |

### 坡道與落地

| 項目 | 想解決什麼 | 結果 | 依據 | 出處 |
|---|---|---|---|---|
| 【曾用】坡上預轉第一版 | 落地前先往右轉，避免壓外線 | 方向錯：航向基準下判成「已超前」，偏移往左 −17～−30 µs | 實車（11-18） | [src: raw/records/logs/AGENTS.md#L382] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L672] |
| 【曾用】坡上轉向律第一版（slope-law） | 坡上用單一控制律取代多層疊加 | 實車坡末偏左 | 實車（11-15 e8e1） | [src: raw/records/logs/AGENTS.md#L382] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L485] |

### 彎道

| 項目 | 想解決什麼 | 結果 | 依據 | 出處 |
|---|---|---|---|---|
| 【曾用】彎 2 目標 0.78 | 彎 2 往外移、少壓內線 | 打滿後往內甩（外移過頭） | 實車 | [src: raw/records/logs/AGENTS.md#L383] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L628] |
| 【曾用】彎 1 帶狀 own mode＋外移 4 cm | 彎 1 往外移 | 輪廓舵量不足＋外移過多，車跑到外緣（未出界但無餘裕） | 實車 | [src: raw/records/logs/AGENTS.md#L383] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L628] |

注意：11-22 起彎道改用另一版「帶狀全權」設計並留在最終版，與這裡退回的 11-17 版不同，見 [[control/curve-band-ff]] [src: raw/records/logs/AGENTS_LOG_202611.md#L1209-L1213]。

### 速度

| 項目 | 想解決什麼 | 結果 | 依據 | 出處 |
|---|---|---|---|---|
| 【曾用】主直線油門 60（當時上限 50） | 主直線更快 | 峰值車速 1.51 m/s 對 50 時 1.48／1.50＝無增益；主直線 gz 標準差 22.3（第 1 圈 7.5） | 實車（11-17） | [src: raw/records/logs/AGENTS.md#L384] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L627-L628] |
| 【曾用】全程關誤差變化率降速 | 減少油門被擋 | 列為變差 | 紀錄只有結論一句 | [src: raw/records/logs/AGENTS.md#L384] |

主直線 60 的結論與後來 11-19 韌體上限改 100、主直線油門 100 並不矛盾：後者是另一次韌體與設定變更 [src: raw/records/logs/AGENTS.md#L119] [src: raw/records/logs/AGENTS.md#L127]。

### 感知與路徑

| 項目 | 想解決什麼 | 結果 | 依據 | 出處 |
|---|---|---|---|---|
| 【僅參考】由下往上追線取代現行路徑 | 單線時保持左右身分 | 效果小或變差 | 離線原型 | [src: raw/records/logs/AGENTS.md#L385] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L578] |
| 【僅參考】以追線擋估計器翻轉 | 防止左右線認錯 | 「在現有鏡頭視野下證據不支持」 | 離線 | [src: raw/records/logs/AGENTS.md#L385] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L586] |
| 【曾用】用模型遮罩找虛線 | 上段找虛線 | 效果小或變差；車上改回 mask_dash false | 實車 | [src: raw/records/logs/AGENTS.md#L385] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L386] |
| 【僅參考】實體車道寬取代寬度比例 | 單線時推算另一側 | 效果小或變差 | 離線 | [src: raw/records/logs/AGENTS.md#L385] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L575] |
| 【僅參考】曝光自動調整 | 當晚想解決晚轉 | 離線結論：場地變亮不均勻，不建議作為晚轉解法，未上車 | 離線 | [src: raw/records/logs/AGENTS.md#L386] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L678] |

### 運算

| 項目 | 想解決什麼 | 結果 | 依據 | 出處 |
|---|---|---|---|---|
| 【曾用】多行程並行 | 提高每秒處理張數 | 遮罩重播下較快，但與真實模型一起跑反而變慢（互搶 CPU，原因未查），不採用 | Orin 上實量 | [src: raw/records/logs/AGENTS.md#L115] [src: raw/records/logs/AGENTS.md#L386] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L541-L542] |
| 【僅參考】TensorRT／FP16 推論加速 | 縮短模型推論時間 | 「會改輸出而未做」；筆電只做了 FP16 對 FP32 比較（遮罩 IoU 中位 0.99934），ONNX 與 TensorRT 沒做，Orin 建引擎腳本備妥未執行 | 離線 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L567] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L571] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L573] |

- 11-03 海報查核文件記載 Orin 實測為「PyTorch FP32，未用 TensorRT」，並把「TensorRT 加速」列為應避免的說法 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L53] [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L100]。模型本身見 [[perception/yolo26-sem]]。

### 從未上車的追蹤演算法提案

- 【僅參考】tracking-proposal-v1：mode「proposal_only」、hardware_output false，候選控制器為「adaptive_pure_pursuit_regulated_speed」（可調前視距離的 Pure Pursuit＋依曲率降速）[src: raw/records/analyses/tracking-proposal-v1.json#L4-L6]。
- 名詞：**Pure Pursuit**＝在路徑上取前方一點，算出讓車走圓弧到達該點的轉向角；**Regulated Pure Pursuit** 是 Nav2 的變體，會依曲率等條件調降車速；**Stanley** 依前軸到路徑的橫向誤差與航向誤差算轉向；**MPC**＝模型預測控制。提案列出的參考來源為 Nav2 RPP 說明與論文、Stanley 原始論文、Autoware MPC 橫向控制器、Optuna 參數搜尋 [src: raw/records/analyses/tracking-proposal-v1.json#L26-L46]。
- 提案參數：pwm 15、steer_rate 300、前視 0.8～1.2（lookahead_time 1）、near_cm 39、軸距 23 cm、間隙補償關、標定基準 20261018 [src: raw/records/analyses/tracking-proposal-v1.json#L7-L25]。
- 為何沒採用：**未找到書面放棄理由**。三份開發紀錄（規則與現況檔、十一月逐日紀錄、十一月十九日前歷史檔）中搜尋 pursuit、Stanley、MPC、lookahead 皆無相關記載（搜尋結果為空，無行可引）。
- 參考：near_cm 39 是 10 月的距離基準，後來使用者更正距離是由前輪最前緣量、現為 27 cm [src: raw/records/logs/AGENTS.md#L13-L15]。

## 公式與參數

無。

## 未確認

- 「全程關誤差變化率降速」「路口直行窗口第二／三版」等項目在紀錄中只有結論，找不到逐輪數字。
- 「間隙補償門檻 60」紀錄寫實車變差，但對應那一輪的數字在本 raw 範圍內未找到（11-10 以前原始紀錄已刪）[src: raw/records/logs/AGENTS.md#L375]。
- 追蹤演算法提案的日期與放棄原因不明；提案檔的 calibration_reference 為 20261018 [src: raw/records/analyses/tracking-proposal-v1.json#L25]。
- TensorRT 在 Orin 上的實際速度與輸出差異沒有量過 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L573]。

## 相關條目

- [[experiments/s-weave]]
- [[experiments/lap-progression]]
- [[control/yaw-inner]]
- [[control/play-comp]]
- [[control/slope-downhill]]
- [[control/curve-band-ff]]
- [[control/speed-control]]
- [[control/disabled-layers]]
- [[path/vision-failure-modes]]
- [[perception/yolo26-sem]]
- [[perception/camera-capture]]
