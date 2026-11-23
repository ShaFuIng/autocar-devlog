---
id: sources/regulated-pure-pursuit
title: Macenski 等（2023）Regulated Pure Pursuit 論文
status: reference-only
sources:
  - raw/papers/macenski-2023-regulated-pure-pursuit-arxiv-2305.20026.pdf
  - raw/papers/macenski-2023-regulated-pure-pursuit-arxiv-2305.20026-abs.txt
  - raw/records/analyses/tracking-proposal-v1.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

Regulated Pure Pursuit 是 Pure Pursuit 路徑追蹤法的改良版。本專案曾把它列為控制器候選，但**只停在提案，從沒上過車**。最終版用的是 PID 加上逐彎前饋。

## 內容

- **書目**：Steve Macenski 等 4 位作者，〈Regulated Pure Pursuit for Robot Path Tracking〉，arXiv:2305.20026，2023-05-31 提交 [src: raw/papers/macenski-2023-regulated-pure-pursuit-arxiv-2305.20026-abs.txt#L12-L15]。PDF 共 4 頁，已完整下載 [src: raw/papers/macenski-2023-regulated-pure-pursuit-arxiv-2305.20026.pdf]。
- **重點**：作者在工業級服務機器人上實驗這個演算法，並在 ROS 2 的 Nav2 中提供參考實作 [src: raw/papers/macenski-2023-regulated-pure-pursuit-arxiv-2305.20026-abs.txt#L18-L19]。Pure Pursuit 的做法是在路徑上選一個前方的目標點，算出開到那一點需要的圓弧。
- **與本車的關係（只當參考）**：專案的追蹤提案標記為 `mode: proposal_only`，候選控制器是 `adaptive_pure_pursuit_regulated_speed`，參考資料引用了這篇論文 [src: raw/records/analyses/tracking-proposal-v1.json#L4-L6] [src: raw/records/analyses/tracking-proposal-v1.json#L32]。紀錄中找不到書面的放棄理由，見 [[experiments/failures-abandoned]]。

## 公式與參數

- Pure Pursuit 的經典曲率公式：κ＝2·sin(α)/L_d。α 是目標點相對車頭的角度，L_d 是前視距離。這是這類方法的通用式，本車**沒有實作**。 [src: raw/papers/macenski-2023-regulated-pure-pursuit-arxiv-2305.20026.pdf]

## 未確認

- 只核對了摘要頁的文字，PDF 內文沒有逐段核對。
- 本車相機最近只看得到前輪前 27～30 cm，在這種視野下前視點要怎麼選，沒有評估過。 [src: raw/records/logs/AGENTS.md#L112]

## 相關條目

- [[experiments/failures-abandoned]]
- [[sources/stanley-2006]]
- [[control/curve-band-ff]]
