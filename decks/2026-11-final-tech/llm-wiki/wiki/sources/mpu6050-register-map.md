---
id: sources/mpu6050-register-map
title: InvenSense MPU-6000／MPU-6050 暫存器表（RM-MPU-6000A）
status: implemented
sources:
  - raw/official/invensense-RM-MPU-6000A-register-map.pdf
  - raw/project/imu-new-20261105/imu_logger.py
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

這是 MPU-6050 的官方暫存器說明。本車 IMU 紀錄程式寫入的暫存器 0x1B，就是文件裡的 GYRO_CONFIG（陀螺儀設定）。 [src: raw/official/invensense-RM-MPU-6000A-register-map.pdf] [src: raw/project/imu-new-20261105/imu_logger.py#L54]

## 內容

- **書目**：InvenSense，《MPU-6000 and MPU-6050 Register Map and Descriptions》，文件編號 RM-MPU-6000A，共 47 頁 [src: raw/official/invensense-RM-MPU-6000A-register-map.pdf]。
- **取得方式與限制**：TDK InvenSense 官網的 PDF 網址現在會跳到搜尋頁，下載不到。這份改從經銷商 SparkFun 的鏡像（cdn.sparkfun.com）取得，2026-11-23 下載，確認是完整的 PDF。內容是原廠文件，但取得管道不是原廠。 [src: raw/official/invensense-RM-MPU-6000A-register-map.pdf]
- **與本車的關係（確實採用）**：
  - 紀錄程式讀取位址 0x68 的 MPU6050，並對 0x1B 寫入 0x00，註解寫明陀螺儀量程為 ±250 dps [src: raw/project/imu-new-20261105/imu_logger.py#L22] [src: raw/project/imu-new-20261105/imu_logger.py#L54]。
  - 暫存器表第 4.4 節（第 14 頁）定義 Register 27（十六進位 1B）為 GYRO_CONFIG，其中 FS_SEL＝0 代表量程 ±250 °/s [src: raw/official/invensense-RM-MPU-6000A-register-map.pdf]。
  - 上述是 11-05 版紀錄程式，現役版本沒有逐檔確認，見 [[hardware/imu-mpu6050]]。

## 公式與參數

- 陀螺儀量程 ±250 °/s，由 GYRO_CONFIG 的 FS_SEL＝0 決定 [src: raw/official/invensense-RM-MPU-6000A-register-map.pdf]。

## 未確認

- 這裡只匯入暫存器表。電氣特性在另一份產品規格書（PS-MPU-6000A），官網一樣下載不到，所以沒有匯入。 [src: raw/official/invensense-RM-MPU-6000A-register-map.pdf]
- PDF 沒有行號，改用章節、頁碼與暫存器名稱定位；內容是從 PDF 文字串抽出後核對的。

## 相關條目

- [[hardware/imu-mpu6050]]
- [[synthesis/imu-roles]]
- [[sources/nvidia-carrier-board-spec]]
