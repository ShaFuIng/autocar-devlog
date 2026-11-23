---
id: hardware/vehicle-hardware
title: 整車硬體與分工
status: implemented
sources:
  - raw/project/docs/Orin_Interface_v1-README.md
  - raw/project/docs/jetson-environment-handoff.md
  - raw/project/firmware-pwm100_v1/Config.h
  - raw/project/firmware-pwm100_v1/Drive.cpp
  - raw/project/snapshot-20261123d/server.py
  - raw/project/snapshot-20261123d/lap_pos.json
  - raw/project/snapshot-20261123d/throttle_cap.json
  - raw/project/imu-new-20261105/imu_logger.py
  - raw/records/analyses/a1-poster-factcheck-20261103.md
  - raw/records/logs/AGENTS.md
  - raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 整車硬體與分工

## 一句話結論

車上分成兩台電腦：Jetson Orin Nano 負責「看」與「算」（相機取像、YOLO26 白線分割、路徑、PID 與各控制層），BMduino-UNO（BM53A367A）控制板負責「動」與「保護」（經 PCA9685 送出舵機與後輪馬達訊號、讀編碼器、急停與逾時鎖定），兩者以 UART 序列通訊相連 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L18-L21] [src: raw/project/docs/Orin_Interface_v1-README.md#L24-L29]。

## 內容

### 分工總表

| 元件 | 角色 | 依據 |
|---|---|---|
| Jetson Orin Nano Developer Kit（8 GB LPDDR5、ARM64） | 車上主電腦：取像、模型推論、路徑、控制計算、紀錄 | [src: raw/project/docs/jetson-environment-handoff.md#L5-L12] |
| BMduino-UNO，編譯板型 BM53A367A（HT32F52367） | 控制板：解析 Orin 命令、急停／啟動按鈕、馬達斜坡、舵機輸出、編碼器計數 | [src: raw/project/docs/Orin_Interface_v1-README.md#L73] [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L28] |
| PCA9685 16 通道 PWM 模組（I²C 位址 0x40） | 由控制板經 I²C 控制，產生舵機脈波（CH0）與馬達 PWM（CH4～CH7） | [src: raw/project/firmware-pwm100_v1/Config.h#L10-L15] [src: raw/project/docs/Orin_Interface_v1-README.md#L50-L52] |
| 馬達驅動器 | 驅動兩顆後輪直流馬達；型號有兩種說法，見「未確認」與衝突草稿 | [src: raw/project/docs/Orin_Interface_v1-README.md#L38-L40] [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L33] |
| 後輪：左右各一顆直流減速馬達（含編碼器） | 動力；不是四輪驅動，也沒有做差速轉向 | [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L21] [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L27] |
| 前輪：舵機＋連桿轉向 | 轉向，見 [[hardware/steering-servo]] | [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L27] |
| 編碼器（AB 兩相） | 數輪子轉動的脈衝，給車速與里程（地標定位） | [src: raw/project/docs/Orin_Interface_v1-README.md#L58] [src: raw/project/snapshot-20261123d/lap_pos.json#key=m_per_count] |
| 實體啟動鈕 D10、實體急停鈕 D11、啟動燈 D12 | 急停為軟體停止，不切斷電池 | [src: raw/project/firmware-pwm100_v1/Config.h#L8-L9] [src: raw/project/docs/Orin_Interface_v1-README.md#L36] |
| USB 單眼相機 | 前方取像，見 [[perception/camera-capture]] | [src: raw/project/snapshot-20261123d/server.py#L471-L482] |
| MPU6050 IMU（Orin I²C bus 7、位址 0x68） | 量俯仰、側傾與轉動角速度，見 [[hardware/imu-mpu6050]] | [src: raw/project/imu-new-20261105/imu_logger.py#L1] |

名詞說明：
- **PCA9685**：一顆用 I²C 介面設定、能同時輸出 16 路 PWM 脈波的晶片；舵機的角度由脈波寬度（µs）決定 [src: raw/project/firmware-pwm100_v1/Drive.cpp#L183-L184]。
- **編碼器**：裝在馬達上的感測器，輪子轉動時輸出 A、B 兩相方波；控制板以 AB 雙邊緣「四倍頻」解碼計數 [src: raw/project/docs/Orin_Interface_v1-README.md#L58]。
- **UART**：兩台裝置之間的序列通訊線。Orin 端用 Serial1、115200 bps、8N1 [src: raw/project/docs/Orin_Interface_v1-README.md#L24]；協定細節見 [[comms/uart-protocol]]。

### 接線（控制板側）

| 功能 | 設定 | 依據 |
|---|---|---|
| 馬達 A PWM | 致能 D8；PCA9685 CH4／CH5，極性反轉 | [src: raw/project/docs/Orin_Interface_v1-README.md#L50] [src: raw/project/firmware-pwm100_v1/Config.h#L10-L14] |
| 馬達 B PWM | 致能 D9；PCA9685 CH6／CH7，極性正常 | [src: raw/project/docs/Orin_Interface_v1-README.md#L51] [src: raw/project/firmware-pwm100_v1/Config.h#L10-L14] |
| 舵機 | PCA9685 CH0，50 Hz | [src: raw/project/firmware-pwm100_v1/Config.h#L15] [src: raw/project/firmware-pwm100_v1/Drive.cpp#L184] |
| 編碼器 | 控制板 GPIO D4～D7（與 PCA9685 的 CH4～CH7 是不同硬體） | [src: raw/project/firmware-pwm100_v1/Config.h#L41-L44] [src: raw/project/docs/Orin_Interface_v1-README.md#L61] |
| Orin UART | 控制板 Serial1（D20/RX1、D21/TX1） | [src: raw/project/docs/Orin_Interface_v1-README.md#L53] |

Config.h 裡 `MOTOR_A_IN1 = 4` 等數字是 PCA9685 通道，`ENC_A_A = 4` 等是控制板腳位，數字相同但不是同一個東西 [src: raw/project/firmware-pwm100_v1/Config.h#L12-L13] [src: raw/project/firmware-pwm100_v1/Config.h#L43] [src: raw/project/docs/Orin_Interface_v1-README.md#L61]。原理圖上另有 74LS14（反相器）與 74HC125（UART 電位轉換） [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L32]；Orin 的 40-pin 擴充排針所有訊號都是 3.3 V 電位、含 2 組 I²C 與 UART1 [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]（官方規格書第 21 頁「3.3 40-Pin Expansion Header」）。

### 安全與限幅（最終版韌體 pwm100_v1）

- 行車指令逾時 500 ms 即鎖定 [src: raw/project/firmware-pwm100_v1/Config.h#L35]；急停腳 D11 需連續低電位 10 ms（10000 µs）才成立，較短視為雜訊 [src: raw/project/firmware-pwm100_v1/Config.h#L9]。
- 韌體油門上限常數 100（%），註解寫明這是實驗上限、不是硬體額定值；Orin 端另有 `throttle_cap.json`，最終版為 100 [src: raw/project/firmware-pwm100_v1/Config.h#L36] [src: raw/project/snapshot-20261123d/throttle_cap.json#key=max_pct]。
- 急停是軟體停止，不會切斷電池；控制板當機或電源異常時無法靠韌體保證停車 [src: raw/project/docs/Orin_Interface_v1-README.md#L36-L37]。

### 電腦軟體環境（Orin）

Ubuntu 22.04、L4T R36.4.3（JetPack 6.2 系列）、CUDA 12.6、cuDNN 9.3.0、TensorRT 10.3.0、OpenCV 4.8.0 [src: raw/project/docs/jetson-environment-handoff.md#L16-L22]。這份交接文件寫「PyTorch 尚未安裝」，是早期狀態 [src: raw/project/docs/jetson-environment-handoff.md#L23]；之後模型以 Ultralytics 8.4.174、torch 2.10.0 在 Docker 容器內執行，未使用 TensorRT [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L40] [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L53]，見 [[perception/yolo26-sem]]。

### 已過時的說明（不要照抄）

- Orin_Interface_v1 README 寫「編碼器是診斷用途，不參與速度閉迴路」[src: raw/project/docs/Orin_Interface_v1-README.md#L63]，以及「電池電壓、電流、真實車速固定回報 null」[src: raw/project/docs/Orin_Interface_v1-README.md#L67]，是 10 月的狀態。最終版控制端以編碼器累計換算里程（每計數 0.000222 m）做地標定位 [src: raw/project/snapshot-20261123d/lap_pos.json#key=m_per_count]，見 [[control/lap-position]]、[[control/speed-control]]。
- README 的舵機中心 1340 µs、範圍 ±700 µs 是第一版數值 [src: raw/project/docs/Orin_Interface_v1-README.md#L52]，最終版見 [[hardware/steering-servo]]。

## 公式與參數

- 輪速換算：車速（m/s）＝ 每秒編碼器計數 × 0.000222 m（`m_per_count`，調參／標定值，標定方法原始資料未在本頁所引檔案內說明）[src: raw/project/snapshot-20261123d/lap_pos.json#key=m_per_count]。
  - 推算檢查：落地全油門實測 6492 cps ≈ 1.44 m/s [src: raw/records/logs/AGENTS.md#L127]；6492 × 0.000222 ＝ 1.441 m/s（推算），兩者一致。
- 舵機 PWM 頻率 50 Hz（設計值）、PCA9685 振盪器設定 25,880,000 Hz（調參值，用來校正晶片時脈）[src: raw/project/firmware-pwm100_v1/Config.h#L19] [src: raw/project/firmware-pwm100_v1/Drive.cpp#L183-L184]。
- 指令逾時 500 ms、急停確認 10 ms、油門上限 100%（皆為設計／實驗值，非安全認證值）[src: raw/project/firmware-pwm100_v1/Config.h#L9] [src: raw/project/firmware-pwm100_v1/Config.h#L35-L36]。

## 未確認

- 馬達驅動器型號：README 寫「已由使用者確認為 XY160D，圖面標示 DRV1011」[src: raw/project/docs/Orin_Interface_v1-README.md#L40]，11-03 查核文件則寫「使用者曾稱 XY160D，現場型號待確認」[src: raw/records/analyses/a1-poster-factcheck-20261103.md#L33]。已記入衝突草稿 `wiki/path/_conflicts-draft.md`，本頁不選答案。
- 馬達料號：原理圖標 PK32K5SP284HE12T-027BB0（含編碼器），現場料號待確認 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L34]。
- 相機型號、電池規格：照片可見「HD WEBCAM」與「18V 6.0Ah」字樣，品牌型號未確認 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L87]；環境文件只寫「Full HD USB Webcam」[src: raw/project/docs/jetson-environment-handoff.md#L12]。型號原始資料未記載。
- 輪徑：後輪 11-02 換成 9 cm、前輪約 7.5 cm（暫估）[src: raw/records/analyses/a1-poster-factcheck-20261103.md#L35]；之後是否再換未見紀錄。
- IMU 接在 Orin 40-pin 哪兩腳：原始資料只寫 bus 7，未記載腳位；官方規格書第 21 頁列有 I2C0／I2C1 兩組，但規格書沒有 Linux bus 編號對照。 [src: raw/project/imu-new-20261105/imu_logger.py#L1] [src: raw/official/nvidia-jetson-orin-nano-carrier-board-SP-11324-001-v1.3.pdf]

## 相關條目

- [[overview]]
- [[hardware/steering-servo]]、[[hardware/imu-mpu6050]]、[[perception/camera-capture]]
- [[comms/uart-protocol]]、[[control/command-chain]]、[[control/speed-control]]、[[control/lap-position]]
