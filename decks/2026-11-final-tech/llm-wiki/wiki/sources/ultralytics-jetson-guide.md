---
id: sources/ultralytics-jetson-guide
title: Ultralytics NVIDIA Jetson 部署指南
status: reference-only
sources:
  - raw/official/ultralytics-docs-guides-nvidia-jetson.html
  - raw/official/ultralytics-docs-guides-nvidia-jetson.txt
  - raw/records/analyses/a1-poster-factcheck-20261103.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

這份 Ultralytics 指南說明如何在 Jetson 上部署 YOLO，包括用 TensorRT 加速。本車只把它當參考基準，**最終版沒有使用 TensorRT**，推論仍用 PyTorch。

## 內容

- **書目**：Ultralytics，〈NVIDIA Jetson〉部署指南，網址 https://docs.ultralytics.com/guides/nvidia-jetson/，2026-11-23 擷取 [src: raw/official/ultralytics-docs-guides-nvidia-jetson.html]。
- **版本差異**：今天擷取的版本是在 JetPack 7.2 上測試的 [src: raw/official/ultralytics-docs-guides-nvidia-jetson.txt#L65]。本車用的是 JetPack 6.2，見 [[hardware/vehicle-hardware]]。專案 10 月讀到的版本已經取不回來，所以內容可能和今天的不同。
- **相關段落**：
  - JetPack 4、5、6 的映像檔，指南都指向「在 Jetson 上使用 TensorRT」一節 [src: raw/official/ultralytics-docs-guides-nvidia-jetson.txt#L108]。
  - 支援裝置清單裡有 Orin Nano Super [src: raw/official/ultralytics-docs-guides-nvidia-jetson.txt#L70]。
- **與本車的關係（只當參考）**：11-03 的查核紀錄寫明，實車推論用 PyTorch FP32，沒有用 TensorRT [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L53]。為什麼沒有導入，見 [[experiments/failures-abandoned]]。

## 公式與參數

無。

## 未確認

- 專案當時讀的指南版本和今天擷取的不同，不能拿今天的內容去推論當時的判斷依據。

## 相關條目

- [[perception/yolo26-sem]]
- [[experiments/failures-abandoned]]
- [[comms/timing-latency]]
