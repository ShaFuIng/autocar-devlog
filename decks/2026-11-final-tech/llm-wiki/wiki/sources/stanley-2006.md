---
id: sources/stanley-2006
title: Thrun 等（2006）Stanley：贏得 DARPA 大挑戰的車輛
status: reference-only
sources:
  - raw/papers/thrun-2006-stanley.pdf
  - raw/records/analyses/tracking-proposal-v1.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

這篇論文的轉向控制段落提出 Stanley 控制法：轉向角＝航向誤差，再加上一項依橫向誤差與車速算出的修正。本專案只在提案中引用它作比較，**從沒上過車**。

## 內容

- **書目**：S. Thrun 等，〈Stanley: The Robot that Won the DARPA Grand Challenge〉，Journal of Field Robotics，2006。從 Stanford 作者頁下載，PDF 共 32 頁，已完整下載 [src: raw/papers/thrun-2006-stanley.pdf]。
- **與本車的關係（只當參考）**：專案追蹤提案的參考清單列出這篇論文的 §9.2 [src: raw/records/analyses/tracking-proposal-v1.json#L36-L37]，而這份提案只是 proposal_only [src: raw/records/analyses/tracking-proposal-v1.json#L4]。
- **與最終版的對照**：Stanley 法同時用航向誤差和橫向誤差，所以需要知道車頭相對路徑的方向。本車最終版的做法不同：路口和下坡用 IMU 保持航向，彎道用帶狀前饋。見 [[control/heading-hold]] 與 [[control/curve-band-ff]]。

## 公式與參數

- 經典 Stanley 轉向律：δ＝ψ_e＋arctan(k·e/v)。ψ_e 是航向誤差，e 是橫向誤差，v 是車速，k 是增益。這是論文方法的通用式，本車**沒有實作**。

## 未確認

- PDF 內文沒有逐段核對；§9.2 的確切內容，是依專案提案裡的引用當線索。 [src: raw/records/analyses/tracking-proposal-v1.json#L36-L37]

## 相關條目

- [[sources/regulated-pure-pursuit]]
- [[experiments/failures-abandoned]]
