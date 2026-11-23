---
id: overview
title: 系統總覽：一顆相機加一顆 IMU 的循線自走車
status: implemented
sources:
  - raw/project/snapshot-20261123d/README.md
  - raw/project/snapshot-20261123d/live_pid.py
  - raw/project/docs/PROTOCOL.md
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

Jetson Orin Nano 用 AI 模型從相機畫面分割出白線，算出路徑與舵量、油門，經 UART 送給 BMduino 控制板驅動舵機與馬達。相機不可靠的地方由 IMU 與編碼器補上。最終定版那一輪跑出 56.5／56.8 s，沒有失敗 [src: raw/project/snapshot-20261123d/README.md#L4]。

## 內容

**資料流**（每一格影像都走一次）：

1. **取像**：USB 相機，固定曝光。見 [[perception/camera-capture]]。
2. **辨識**：YOLO26 語意分割，逐像素判斷「白線／背景」。見 [[perception/yolo26-sem]]。
3. **路徑**：由白線遮罩配對內側邊線，求出中心路徑與近列、遠列誤差。見 [[path/mask-to-path]]、[[path/junction-handling]]、[[path/upper-dash-route]]。
4. **控制**：PID 加上依路段開關的各層（帶狀前饋、航向保持、坡道、速度表），後寫入的層生效 [src: raw/project/snapshot-20261123d/live_pid.py#L2235-L2292]。見 [[control/pid-core]]、[[control/command-chain]]。
5. **輸出**：間隙補償與速率限制後，經 UART（有序號與 CRC 校驗）送到 BMduino [src: raw/project/docs/PROTOCOL.md#L20-L34]。見 [[control/play-comp]]、[[comms/uart-protocol]]。

**相機不夠時靠什麼補**：
- IMU 提供俯仰、航向、車頭轉速，見 [[synthesis/imu-roles]]。
- 編碼器里程加地標定位，告訴車子現在在一圈中的哪裡，見 [[control/lap-position]]。
- 相機在哪些情境失效，見 [[path/vision-failure-modes]]；路徑遺失時怎麼辦，見 [[control/lost-path]]。

**時序**：最終版每格處理與控制資料年齡，見 [[comms/timing-latency]]。

**硬體**：見 [[hardware/vehicle-hardware]]、[[hardware/imu-mpu6050]]、[[hardware/steering-servo]]。

**成果與演進**：見 [[experiments/final-performance]]、[[experiments/lap-progression]]、[[experiments/s-weave]]、[[experiments/failures-abandoned]]。

**不可寫成現役的層**：見 [[control/disabled-layers]]。

## 公式與參數

各條目分列。總覽不另列公式。

## 未確認

- 封面成績與效能比的用法待人工決定，見 [[conflicts]] 的 D1、D2。

## 相關條目

- [[synthesis/imu-roles]]
- [[control/command-chain]]
- [[sources/nvidia-carrier-board-spec]]
- [[synthesis/glossary]]
