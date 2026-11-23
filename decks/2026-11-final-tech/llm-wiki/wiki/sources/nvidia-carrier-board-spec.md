---
id: sources/nvidia-carrier-board-spec
title: NVIDIA Jetson Orin Nano 開發套件載板規格書（SP-11324-001 v1.3）
status: implemented
sources:
  - raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf
  - raw/project/imu-new-20261105/imu_logger.py
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

這份 NVIDIA 官方規格書是本車接線的依據。IMU 接在 40-pin 擴充排針（J12）的 I²C #1，控制板則接 UART #1。 [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]

## 內容

- **書目**：NVIDIA，《Jetson Orin Nano Developer Kit Carrier Board Specification》，文件編號 SP-11324-001，版本 v1.3。專案內原本就保存這份 PDF，凍結於 [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]。
- **與本車的關係**：確實採用。專案依據這份文件決定 IMU 與控制板 UART 接在哪幾支腳。
- **本車用到的部分**（PDF 第 22 頁，Table 3-3 Expansion Header Pin Description – J12）[src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]：
  - 第 3 腳 I2C1_SDA、第 5 腳 I2C1_SCL：I²C #1 的資料線與時脈線，模組上已有 2.2 kΩ 上拉電阻。I²C 是一種用兩條線串接多個感測器的序列匯流排。 [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]
  - 第 8 腳 UART1_TXD、第 10 腳 UART1_RXD：UART #1 的傳送與接收。UART 是兩條線的非同步序列通訊。 [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]
  - 第 1 腳是 3.3 V、第 2／4 腳是 5.0 V，各標 1 A。 [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]
- **第 3 頁概述**：擴充排針是 40-pin（2×20），提供 I²C ×2、SPI ×2、UART、I2S、GPIO、PWM [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]。
- **本車端的對應**：IMU 紀錄程式從 Linux 的 I²C bus 7、位址 0x68 讀 MPU6050 [src: raw/project/imu-new-20261105/imu_logger.py#L1-L30]。「J12 第 3／5 腳在 Linux 對應 bus 7」這件事，規格書沒有寫，是從專案程式推得的對應，不是規格書內容。

## 公式與參數

無。

## 未確認

- 規格書沒有寫 Linux 端的 I²C 匯流排編號與 UART 裝置名稱。專案程式用的是 bus 7 與 `/dev/ttyTHS1`（見 [[comms/uart-protocol]]）。兩者和接腳的對應只有程式佐證，沒有官方文件佐證。
- 這份 PDF 沒有可用的行號。引用時以頁碼與表號定位，文字是用 PDF 內文字串抽出後核對的。

## 相關條目

- [[hardware/imu-mpu6050]]
- [[hardware/vehicle-hardware]]
- [[comms/uart-protocol]]
