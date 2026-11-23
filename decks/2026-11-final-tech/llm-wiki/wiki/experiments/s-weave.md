---
id: experiments/s-weave
title: 直線 S 型擺動：問題、原因分析、陀螺儀內迴圈與實車效果
status: mixed
sources:
  - raw/records/analyses/play-comp-20261105-findings.json
  - raw/records/analyses/why-s-weave-20261107-findings.json
  - raw/project/snapshot-20261123d/yaw_inner.py
  - raw/project/snapshot-20261123d/yaw_inner.json
  - raw/project/snapshot-20261123d/play_comp.json
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/records/logs/AGENTS.md
  - raw/records/logs/AGENTS_LOG_202611.md
  - raw/records/logs/AGENTS_HISTORY_until_20261119.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 直線 S 型擺動

## 一句話結論

11-07 的分析認為直線 S 型擺動是「兩次積分＋約 0.75 s 迴路延遲」造成的臨界迴路，調 kp／kd／車速／間隙補償都改不掉週期，因此加入陀螺儀內迴圈 yaw_inner（最終版仍在用，增益 k 4）[src: raw/records/analyses/why-s-weave-20261107-findings.json#L10-L14] [src: raw/project/snapshot-20261123d/yaw_inner.json#L2-L3]；但「加入 yaw_inner 前後」的實車改善幅度**無法從現存紀錄量化**，現存最乾淨的實車前後對照是 11-18 的 k 6→4（主直線車頭轉速標準差約由 8.7～22.1 降到 6.4～12.8°/s）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660]。

## 內容

### 名詞

- **S 型擺動（weave）**：車在直線上左右來回擺、路徑像 S，不是單純偏一側。
- **gz**：陀螺儀量到的車頭轉速（°/s）。紀錄中的「直線 gz 標準差」是擺動大小的主要指標；11-18 的定義為「車頭轉速扣 1 s 平均後的標準差」[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660]。
- **yaw_inner（陀螺儀內迴圈）**：把外層 PID 算出的轉向量解讀成「目標車頭轉速」，再用陀螺儀實測轉速做內層比例回授的模組；見 [[control/yaw-inner]] [src: raw/project/snapshot-20261123d/yaw_inner.py#L10-L16]。
- **轉向間隙（play）**：連桿與舵機的機械空行程，指令反向時輪子要先走完一段才動；**間隙補償 play_comp** 是在指令換方向時額外加一個固定量把空行程「跳過去」的模組；見 [[control/play-comp]]。

### 間隙與 S 型是不同機制

- 間隙是硬體空行程：11-12 地墊實測遲滯約 155 µs、間隙外增益約 0.32 deg/m per µs [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L364]。
- S 型擺動在 11-07 的分析中是迴路動態問題：舵量→車頭轉速的曲線是平滑線性的、沒有硬死區，中心也校正正確；因此排除「中心錯」「硬死區」「影像雜訊」三者為主因，且當時 play comp 40/40 讓擺動變差 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L6-L8] [src: raw/records/analyses/why-s-weave-20261107-findings.json#L18-L22]。
- 但兩者在實車上會互相作用：11-17 的出彎擺盪分析與 11-18 的直線晃動調查都指出，擺動由「硬體間隙＋間隙補償＋yaw_inner＋延遲」共同構成（模型與紀錄分析）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L603] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L642]。

### 時間線

#### 11-05：先檢查間隙補償（只分析）
- 使用者要求在拿間隙補償對付直線擺動前先檢查它；當時紀錄顯示補償是關的（backlash_enabled 0）[src: raw/records/analyses/play-comp-20261105-findings.json#L1-L2]。
- 找到三個問題：補償量被增益排程乘 15/PWM 縮小、開補償會把轉向速率限到 500～800 µs/s、保存的左右值不對；提出程式修改與「先只在起跑直線試」的建議，未做任何改動 [src: raw/records/analyses/play-comp-20261105-findings.json#L3-L5]。

#### 11-07：為什麼 S 型很難去掉（只分析）
- 資料：8 輪新連桿紀錄、平地直線 4777 筆樣本 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L4]。
- 迴路：誤差→PID→舵機→車頭轉速→航向→橫向誤差，**兩次積分**加延遲；相機→PID 0.12 s、PID→控制板 0.1、指令→車頭轉速反應 0.5～0.6 s，合計約 0.75 s [src: raw/records/analyses/why-s-weave-20261107-findings.json#L11-L12]。
- 只用 P 時，雙積分器在任何增益下相位餘裕都是 0；觀察到的 2.3～3.3 s 週期由 D 與延遲決定；kp ×0.67、kd 150→200、kd 60 都沒用或更差；車速提高時週期變短但空間波長約 1.9 m 不變 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L13-L15]。
- 迴路是「臨界但不發散」：誤差與航向都近 0 時不會被激起，所以有時一段直線很穩，整圈仍跑得完 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L17]。
- 建議方向：A 陀螺儀內迴圈、B 航向回授、C 降外迴圈增益與車速（只是權宜）、D 縮短延遲 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L23-L28]。

#### 11-07 起：yaw_inner 上車與版本演進
- 程式檔頭記載 yaw-inner-r1 依使用者 11-07 的分析加入；理由與上面分析相同（直線 S 週期 2.3～3.3 s、幅度 0.35～0.6，不隨 kp、kd、車速、間隙補償改變）[src: raw/project/snapshot-20261123d/yaw_inner.py#L1-L7]。主程式在 yaw-inner-r1 群組中呼叫它 [src: raw/project/snapshot-20261123d/live_pid.py#L950-L951]。
- 程式中的版本註記（r2～r17，各版新增的開關）：r2 依輪速調整舵量→轉速增益、r3 彎內不反向、r4 入彎保持／坡頂穩定／直線推力上限、r5 上坡獨立增益、r6 坡道分類、r7 坡頂相機限速與彎道項上限、r8 入彎預看、r9 遠處仍在彎時不反向、r12 直線航向保持、r13 未完成彎道的反向項上限、r15 項的變化率上限、r16 與相機方向相反時的上限、r17 入彎預看的變化率上限 [src: raw/project/snapshot-20261123d/yaw_inner.py#L31-L36]。最終版程式版本字串為 yaw-inner-r17 [src: raw/project/snapshot-20261123d/yaw_inner.py#L24]。
- 11-10 上車的三版：r15（term_rate_us_s 600）、r16（oppose_cap_us 30／oppose_err 0.05）、r17（入彎預看限速 300 µs/s）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L17]。r14 的「擺動模式」也是 11-10 在 10 張/s 時加的 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L643]。
- 11-07～11-10 的原始逐格紀錄已刪，r1 上車當輪的直線擺動數字不在現存紀錄中 [src: raw/records/logs/AGENTS.md#L375]。

#### 11-12：間隙補償 ±55 上車
- 地墊實測間隙後，使用者授權 play_comp ±55／門檻 30 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L365-L366]。
- 實車：直線誤差中位由 0.26～0.39 降到 0.06～0.19（固定偏一側消失）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L372]；但平直線出現新的快速微擺——車頭反轉由 0.47 次/s（週期約 4.4 s）變成 1.82 次/s（週期約 1.0 s），60～75% 的反轉發生在補償換向後 0.05～0.45 s 內，判定為門檻 30 造成 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L377]。

#### 11-13：離線動力學模型（模型，不是實車）
- 擬合出 純延遲 0.10 s＋一階 0.03 s＋間隙 140 µs；yaw_inner.json 假設的舵量→轉速增益 0.073 比實測 0.165～0.20 小 2.4～2.9 倍 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L403]。
- 模型的敏感度：kd 60→30 擺幅 −30%／−52%；關掉 yaw_inner 反而變差（1.4 m/s 達 8.8°）；把增益改成實測值也變差；結論寫「yaw_inner 是在阻尼而非成因」[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L404]。

#### 11-17：門檻 30→15
- 出彎擺盪離線分析（模型）：出彎扭動是轉向系統自持的極限環，由硬體間隙、間隙補償、yaw_inner（k 6，實際轉向反應約為其內部假設的 3 倍）共同造成，加約 0.25 s 延遲；建議先試門檻 15 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L603]。
- 實車 run-7afb（門檻 15，只一輪）：主直線 C4e+3 m 後 gz 標準差 11.8°/s、車頭擺幅 11.5°（門檻 30 的 58df／2626 為 26.1／25.9）；補償換向次數幾乎沒變，是「跳得更早」[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L609]。

#### 11-18：直線晃動根因與 k 6→4
- 紀錄分析：晃的圈實送指令擺動主要來自 yaw_inner 項 20～44 µs，鏡頭 P+D 只有 8～18 µs；晃不晃主要看進直線時已帶多大擺動（多數來自彎 4 放手那一格）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L642]。
- 閉迴路重播模型：真正維持晃動的是 yaw_inner 本身（項落後約 85°，加指令→gz 約 97°，合計約 182°＝負阻尼）；k 6→4 估計主直線晃的圈 ×0.66；拿掉對向上限（oppose cap）會變差 ×1.14 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L646]。
- 上車：yaw_inner.json k_us_per_dps 6→4 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L652]。

### 上車後實際效果（實車數字）

**A. k 6→4（run-7a70 對 run-6c1e，同日）——現存最乾淨的前後對照** [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660]

| 路段 | 改前 | 改後 | 出處 |
|---|---|---|---|
| 主直線 gz 標準差（°/s，逐圈） | 16.7／8.7／22.1 | 6.4／7.0／6.5／10.5／12.8 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660] |
| 斜線 | 4.0～11.3 | 3.9～4.5 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660] |
| 圓圈直線 | 3.4～8.7 | 2.5～4.7 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660] |
| 上坡 | 12.8～20.6 | 6.9～9.9 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660] |
| 下坡 | 6.4～24.1 | 4.9～8.7 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660] |
| yaw_inner 項標準差，主直線（µs） | 23～47 | 13～22 | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660] |
| 主直線擺動偵測（no_hold）比例 | 12～70% | 0／0／0／14／36% | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660] |

紀錄的判讀是「k 4 達到預期，保留；剩餘擺動由彎 4 出彎帶進來、之後會衰減（不再自持）」；使用者回饋「直線變穩後很多有問題的地方都順利通過；直線偶爾仍擺」[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660]。

**B. 間隙補償門檻 15（run-7afb，只一輪）**：主直線 gz 標準差 11.8°/s；車頭擺幅 11.5° 對門檻 30 時 26.1／25.9° [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L609]。

**C. 新舵機時期（11-23，實車）**：換新舵機後間隙由約 130 變約 60 µs，起初補償仍 ±55，直線擺動約 2～4 倍；之後補償調到 ±25、±15 [src: raw/records/logs/AGENTS_LOG_202611.md#L1639-L1640]。

| 時期 | run | 直線 gz 標準差 | 出處 |
|---|---|---|---|
| 舊舵機（換前參考） | 9729 等 | 起跑直線／斜線／圓圈直線／主直線 14.7／5.7／8.9／6.3 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1640] |
| 新舵機、補償 ±55、中心 1475 | b3ab | 12.9／21.4／17.2／19.4 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1640] |
| 補償 ±25、中心 1445 | ca16／6b39 | 7～13 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1662] |
| 同上 | a216／ec90 | 8.4～10.2 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1673] |
| 同上 | 2395 | 9.1～9.6 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1682] |
| 同上、上限 100 | 21fe／8ce6 | 7.6～9.5 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1691] |
| 補償 ±15 | ce19 | 6.1～7.0 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1699] |
| 補償 ±15 | 5f69 | 6.4～6.8 | [src: raw/records/logs/AGENTS_LOG_202611.md#L1704] |

- 補償換邊次數：±25 時 2.8～4.0、2.4～4.2 次/s；±15 時 2.3～3.1 次/s [src: raw/records/logs/AGENTS_LOG_202611.md#L1673] [src: raw/records/logs/AGENTS_LOG_202611.md#L1691] [src: raw/records/logs/AGENTS_LOG_202611.md#L1699]。
- 11-23 紀錄常以「舊舵機 run-9729 5.7～8.9」作比較基準（不含起跑直線）[src: raw/records/logs/AGENTS_LOG_202611.md#L1699]。

### 最終版的設定（現役）

- 【現役】yaw_inner：enabled true、k_us_per_dps 4.0、gain_dps_per_us 0.073、cap_us 120、term_rate_us_s 600、oppose_cap_us 30／oppose_err 0.05、pv_rate_us_s 300、擺動模式 weave_unhold_dps 20／1.5 s [src: raw/project/snapshot-20261123d/yaw_inner.json#L2-L5] [src: raw/project/snapshot-20261123d/yaw_inner.json#L54-L61]。
- 【現役】play_comp：±15 µs、門檻 15 µs [src: raw/project/snapshot-20261123d/play_comp.json#L2-L5]。
- 【曾用】play_comp ±55／門檻 30（11-12）、±55／門檻 15（11-17）、±25（11-23 16:46）；yaw_inner k 6（11-18 前）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L366] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L607] [src: raw/records/logs/AGENTS_LOG_202611.md#L1655] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L652]。

### 仍未解

- 上坡擺動（坡腳彎點著內迴圈，gz 標準差 4～16）、彎 4 出彎偶爾把擺動帶進主直線，列在已知未解問題 [src: raw/records/logs/AGENTS.md#L371]。
- 最終版坡道後段 gz 標準差 20／21（放寬坡道油門門檻後在還擺時就加到 100）[src: raw/records/logs/AGENTS_LOG_202611.md#L1731] [src: raw/records/logs/AGENTS_LOG_202611.md#L1724]。

## 公式與參數

- yaw_inner 項（程式註解寫法）：term = k × (gain × u + gz)，u＝PID 與增益排程後相對中心的舵量；項限制在 ±cap_us，gz 經 gz_tau_s 低通 [src: raw/project/snapshot-20261123d/yaw_inner.py#L10-L16]。
- k_us_per_dps 4.0：調參值（11-18 由 6 改 4）[src: raw/project/snapshot-20261123d/yaw_inner.json#L3] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L652]。
- gain_dps_per_us 0.073：11-07 舊連桿的實測值，後來模型指出比 11-13 的實測 0.165～0.20 小 2.4～2.9 倍，但「改成實測值」在模型與紀錄中都列為變差 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L6] [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L403-L404] [src: raw/records/logs/AGENTS.md#L380]。
- 11-07 的迴路延遲約 0.75 s 是當時估計 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L12]；之後的量測為「指令→車頭延遲約 0.24～0.30 s」[src: raw/records/logs/AGENTS.md#L108]（見未確認）。

## 未確認

- **實車改善幅度（yaw_inner 加入前後）未能從現存紀錄量化**：11-07～11-10 原始逐格紀錄已刪，紀錄檔也沒有寫下 r1 上車前後的直線擺動數字 [src: raw/records/logs/AGENTS.md#L375]。本頁的前後對照只有 k 6→4、門檻 30→15 與新舵機補償調整。
- 兩次離線模型對 yaw_inner 角色的結論相反：11-13「是阻尼、關掉變差」[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L404]；11-18「是維持晃動者、關掉 ×0.32」[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L646]。兩者條件不同（張數、補償門檻），皆未以實車關閉 yaw_inner 驗證；使用者 11-18 表示不加測關閉組 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L655]。已記入衝突草稿。
- 迴路延遲 0.75 s（11-07）與後來 0.24～0.30 s 的量測差異未見書面解釋；已記入衝突草稿 [src: raw/records/analyses/why-s-weave-20261107-findings.json#L12] [src: raw/records/logs/AGENTS.md#L108]。
- 各時期「直線 gz 標準差」的量法是否完全一致（窗長、路段範圍）未逐一核對；k 6→4 對照兩輪之間還有落地油門等其他改動 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L652]。
- 11-18 對照中改前列出 3 圈、改後 5 圈的數字，為單日各一輪的對照 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L660]。

## 相關條目

- [[control/yaw-inner]]
- [[control/play-comp]]
- [[control/pid-core]]
- [[control/heading-hold]]
- [[comms/timing-latency]]
- [[hardware/steering-servo]]
- [[hardware/imu-mpu6050]]
- [[experiments/lap-progression]]
- [[experiments/failures-abandoned]]
