---
id: comms/uart-protocol
title: Orin 與 BMduino 的 UART 協定與分工
status: implemented
sources:
  - raw/project/docs/PROTOCOL.md
  - raw/project/firmware-pwm100_v1/Config.h
  - raw/project/firmware-pwm100_v1/OrinProtocol.cpp
  - raw/project/firmware-pwm100_v1/ManualDrive.cpp
  - raw/project/firmware-pwm100_v1/Safety.cpp
  - raw/project/firmware-pwm100_v1/Drive.cpp
  - raw/project/firmware-pwm100_v1/Telemetry.cpp
  - raw/project/firmware-pwm100_v1/Orin_Interface_v1.ino
  - raw/project/snapshot-20261123d/server.py
  - raw/project/snapshot-20261123d/manual_drive.py
  - raw/project/snapshot-20261123d/uart_nonblock.json
  - raw/project/imu-new-20261105/imu_logger.py
  - raw/records/logs/AGENTS.md
  - raw/records/runs/run-b541-20261123/summary.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# Orin 與 BMduino 的 UART 協定與分工

## 一句話結論

Jetson Orin（主電腦）經 UART（115200 baud、8N1）以 `$SEQ,命令,參數*CRC16\n` 的文字框架把每格的「左右油門百分比＋舵機脈寬」送給 BMduino 控制板；控制板以 CRC、遞增序號與 generation 排除舊命令，每筆有效命令續 500 ms 租期，逾時、急停（低電位持續 10 ms）或 STOP 即撤除動力，並約每 200 ms 回報一次 JSON 狀態（含編碼器計數）[src: raw/project/docs/PROTOCOL.md#L17-L36] [src: raw/project/firmware-pwm100_v1/Config.h#L9] [src: raw/project/firmware-pwm100_v1/Config.h#L35] [src: raw/project/firmware-pwm100_v1/Config.h#L40]。

## 內容

### 分工

| 項目 | Jetson Orin | BMduino 控制板 | 出處 |
|---|---|---|---|
| 相機、YOLO 推論、路徑、PID 與所有控制層、油門決策 | ✓ | — | [src: raw/records/logs/AGENTS.md#L47] |
| IMU（陀螺儀／加速度計）讀取 | ✓（獨立紀錄程序，I²C） | — | [src: raw/project/imu-new-20261105/imu_logger.py#L1-L17] |
| 馬達 PWM 輸出與斜坡 | — | ✓（每 5 ms 變化 5／255） | [src: raw/project/firmware-pwm100_v1/Drive.cpp#L282-L294] |
| 舵機輸出（PCA9685，位址 0x40，通道 0） | — | ✓（每 20 ms 最多 40 µs） | [src: raw/project/firmware-pwm100_v1/Config.h#L15] [src: raw/project/firmware-pwm100_v1/Drive.cpp#L314-L321] |
| 編碼器四倍頻計數 | — | ✓（200 ms 快照） | [src: raw/project/firmware-pwm100_v1/Config.h#L42-L44] |
| 急停、起動按鈕（D11、D10）與指示燈（D12） | — | ✓ | [src: raw/project/firmware-pwm100_v1/Config.h#L8] |
| 命令租期、逾時停車 | 送命令方 | ✓（500 ms） | [src: raw/project/firmware-pwm100_v1/ManualDrive.cpp#L50-L52] |
| UART 主控與 ACK 追蹤 | ✓（/dev/ttyTHS1） | 回覆方 | [src: raw/project/snapshot-20261123d/server.py#L313] |

硬體型號見 [[hardware/vehicle-hardware]]、[[hardware/steering-servo]]、[[hardware/imu-mpu6050]]。

### 框架格式

- Serial1 115200 baud、8N1、無流量控制，ASCII、指令大寫 [src: raw/project/docs/PROTOCOL.md#L20]；韌體 setup 中 Serial 與 Serial1 皆為 115200 [src: raw/project/firmware-pwm100_v1/Orin_Interface_v1.ino#L13-L14]。
- 格式 `$SEQ,COMMAND[,ARG...]*CCCC\n`：`$` 起始（收到新 `$` 重新收包）、SEQ 為十進位 uint32、CCCC 為四位十六進位 CRC [src: raw/project/docs/PROTOCOL.md#L24-L32]。
- **CRC16／CCITT-FALSE**＝多項式 0x1021、初值 0xFFFF、不反射、不異或的 16 位元檢查碼；範圍是 `$` 之後到 `*` 之前 [src: raw/project/docs/PROTOCOL.md#L30-L31]。韌體逐位元實作 [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L14-L21]；Orin 端用 `binascii.crc_hqx(body, 0xffff)` 產生 [src: raw/project/snapshot-20261123d/server.py#L163-L166]。
- 自 `$` 起 100 ms 內須收完，內文最多 127 字元；格式或 CRC 錯誤直接丟棄並計 rx_bad，不回 ACK [src: raw/project/docs/PROTOCOL.md#L33-L34]。韌體對應：RX_FRAME_TIMEOUT_MS 100、接收緩衝 128 位元組 [src: raw/project/firmware-pwm100_v1/Config.h#L45] [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L10] [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L115-L136]。

### 序號、generation 與 ACK

- **SYNC**：只在 LOCKED／READY／FAULT 接受，建立序號起點並把 generation 加一 [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L60-L62]。之後序號必須遞增（允許繞回），否則回 STALE_SEQUENCE [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L63-L66]。
- **generation**＝本次開機內的授權版本號，從 ACK／狀態取得，不能跨重開機沿用；每次 STOP 也會更新 [src: raw/project/docs/PROTOCOL.md#L52-L56]。
- **STOP**：CRC 正確即接受，不要求 SYNC 或新序號，重複也有效 [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L55-L59]。
- 每筆框架都回一行 JSON ACK，例如 `{"type":"ack","seq":1,"ok":true,"reason":"OK","generation":1}`；ok 只代表命令被接受，不代表馬達已轉、輪角已到位 [src: raw/project/docs/PROTOCOL.md#L61-L68] [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L112-L113]。

### 指令集（最終版實際使用）

| 指令 | 作用 | 出處 |
|---|---|---|
| `SEQ,SYNC` | 建立序號會話 | [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L56] |
| `SEQ,STATUS` | 立即回報狀態 | [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L67] |
| `SEQ,PROFILE,GEN,REV,MIN,CENTER,MAX` | 同步舵機中心與限位（rev44：780／1445／2050）| [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L98-L102] [src: raw/project/snapshot-20261123d/server.py#L343-L357] |
| `SEQ,MANUAL_ARM,GEN` | 進入 MANUAL，馬達零輸出 | [src: raw/project/firmware-pwm100_v1/ManualDrive.cpp#L13-L26] |
| `SEQ,MANUAL,GEN,R,L,US` | 左右油門百分比與舵機脈寬；每筆有效命令續租期 | [src: raw/project/firmware-pwm100_v1/ManualDrive.cpp#L27-L44] |
| `SEQ,MANUAL_END,GEN` | 結束並鎖定 | [src: raw/project/firmware-pwm100_v1/ManualDrive.cpp#L45-L49] |
| `SEQ,STOP` | 撤除動力、鎖定 | [src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L57-L59] |

- PID 行車走 MANUAL 指令：Orin 的 manual_drive 每次送出 `manual_action move`，server.py 轉成 `MANUAL,{gen},{right},{left},{pulse}` [src: raw/project/snapshot-20261123d/manual_drive.py#L404-L406] [src: raw/project/snapshot-20261123d/server.py#L279]。舊的 ARM／MOVE 仍在韌體中，但協定文件說明部署版本禁止使用 [src: raw/project/docs/PROTOCOL.md#L3] [src: raw/project/docs/PROTOCOL.md#L15]。
- MANUAL 的檢查：generation 相符、狀態為 MANUAL、急停未按、PCA 正常且舵機設定已同步、|R|、|L| ≤ MAX_THROTTLE_PERCENT、脈寬在限位內；首包必須 0,0 且脈寬為中心；單一輪換方向前須停 500 ms 且無編碼器計數 [src: raw/project/firmware-pwm100_v1/ManualDrive.cpp#L27-L44]。

### 安全機制（韌體）

- **命令租期**：MANUAL 狀態下距最後一筆有效命令超過 COMMAND_TIMEOUT_MS 500 ms 即停車（COMMAND_TIMEOUT）[src: raw/project/firmware-pwm100_v1/ManualDrive.cpp#L50-L52] [src: raw/project/firmware-pwm100_v1/Config.h#L35]。
- **急停去彈跳**：D11 低電位須連續 ESTOP_CONFIRM_US 10 ms 才成立，較短的記為 ESTOP_GLITCH 事件 [src: raw/project/firmware-pwm100_v1/Config.h#L9] [src: raw/project/firmware-pwm100_v1/Safety.cpp#L66-L90]。
- **油門上限**：現役韌體 pwm100_v1 的 MAX_THROTTLE_PERCENT 為 100 [src: raw/project/firmware-pwm100_v1/Config.h#L36] [src: raw/records/logs/AGENTS.md#L119]。前一版 pwm70_v1 的同一常數為 70，屬於舊版，不是現役值[src: raw/records/logs/AGENTS.md#L120]。

### 狀態回報（控制板→Orin）

- 每行一個 JSON，無 CRC [src: raw/project/docs/PROTOCOL.md#L61]。每 TELEMETRY_MS 200 ms 自動送一次（傳送緩衝不足時丟棄並計 tx_dropped）[src: raw/project/firmware-pwm100_v1/Telemetry.cpp#L93-L97]；文件寫「約 5 Hz 廣播」[src: raw/project/docs/PROTOCOL.md#L41]。
- 主要欄位：mode／state／reason／generation、cmd_age_ms、pins、motor_a／motor_b、steer_us_command、pca_ok／i2c_errors、enc_a／enc_b、rx_good／rx_bad／rx_rejected／tx_dropped／max_loop_us [src: raw/project/docs/PROTOCOL.md#L70-L80]。enc_b 含 forward、reverse、delta、edges、invalid 等 [src: raw/project/firmware-pwm100_v1/Telemetry.cpp#L61]，供 lap_pos 計里程（見 [[control/lap-position]]）。

### Orin 端

- server.py 的 uart_worker 以獨占方式開 `/dev/ttyTHS1`（115200，寫入逾時 0.2 s）[src: raw/project/snapshot-20261123d/server.py#L302-L313]。
- 開啟 2 s 後，只有在韌體狀態新鮮（<1 s）且為 LOCKED／READY 時才送 SYNC，「不對正在行駛的韌體同步」[src: raw/project/snapshot-20261123d/server.py#L331-L340]。
- 每筆送出的命令登記在待確認清單，ACK 期限 1.5 s；任一筆逾期就盡力送 STOP 並以「UART command ACK timeout」重開連線 [src: raw/project/snapshot-20261123d/server.py#L323-L328] [src: raw/project/snapshot-20261123d/server.py#L145-L146]。
- 開啟 3 s 後若超過 2 s 沒收到任何回報，視為斷線（UART status timeout）[src: raw/project/snapshot-20261123d/server.py#L329-L330]。
- **非阻塞模式**（uart_nonblock.json 開啟）：最多 2 筆未確認、讀取逾時 0.01 s、manual_drive 送出間隔 0.025～0.1 s、manual_drive 層的 ACK 逾時 1.0 s、0.45 s 未確認即記為連線遺失，較新 move 的 ACK 可同時確認較舊的 move（ack_supersede）[src: raw/project/snapshot-20261123d/uart_nonblock.json] [src: raw/project/snapshot-20261123d/server.py#L122-L161]。最終實跑 run-b541 的紀錄中 superseded 0、link_loss null [src: raw/records/runs/run-b541-20261123/summary.json#L62-L67]。
- 時序上的意義見 [[comms/timing-latency]]。

### 文件與程式不一致處（以程式為準）

- PROTOCOL.md 寫 MANUAL 的 R／L 為「±25%」、MOVE 的 T「限幅到 ±25%」、舵機「每 120 ms 最多改 10 µs」[src: raw/project/docs/PROTOCOL.md#L8] [src: raw/project/docs/PROTOCOL.md#L11] [src: raw/project/docs/PROTOCOL.md#L43]；現役韌體則是上限 100% 與每 20 ms 40 µs（2000 µs/s；11-08 steer-slew-r1 由 1000 µs/s 調高）[src: raw/project/firmware-pwm100_v1/Config.h#L36] [src: raw/project/firmware-pwm100_v1/Drive.cpp#L317]。文件為 10 月版本，未隨韌體更新。
- MANUAL 超過油門上限時的錯誤碼字串仍是 `PWM_LIMIT_50`，但判斷條件已是 MAX_THROTTLE_PERCENT [src: raw/project/firmware-pwm100_v1/ManualDrive.cpp#L33]。

## 公式與參數

```
frame = "$" + body + "*" + HEX4( CRC16_CCITT_FALSE(body) ) + "\n"      body = "SEQ,CMD[,ARG...]"
CRC: crc = 0xFFFF；每位元組 crc ^= b<<8；8 次 { crc = (crc & 0x8000) ? (crc<<1) ^ 0x1021 : crc<<1 }
韌體油門: duty = |pct| × 255 / 100
```
[src: raw/project/firmware-pwm100_v1/OrinProtocol.cpp#L14-L21] [src: raw/project/snapshot-20261123d/server.py#L163-L166] [src: raw/project/firmware-pwm100_v1/Drive.cpp#L269]

| 參數 | 值 | 性質 | 出處 |
|---|---|---|---|
| 鮑率 | 115200 | 設計假設 | [src: raw/project/firmware-pwm100_v1/Orin_Interface_v1.ino#L14] |
| 收框逾時／內文上限 | 100 ms／127 字元 | 設計假設 | [src: raw/project/firmware-pwm100_v1/Config.h#L45] [src: raw/project/docs/PROTOCOL.md#L33] |
| 命令租期 COMMAND_TIMEOUT_MS | 500 ms | 設計假設 | [src: raw/project/firmware-pwm100_v1/Config.h#L35] |
| 急停確認 ESTOP_CONFIRM_US | 10 ms | 調參值 | [src: raw/project/firmware-pwm100_v1/Config.h#L9] |
| 狀態週期 TELEMETRY_MS | 200 ms | 設計假設 | [src: raw/project/firmware-pwm100_v1/Config.h#L40] |
| MAX_THROTTLE_PERCENT | 100 | 設計假設 | [src: raw/project/firmware-pwm100_v1/Config.h#L36] |
| 舵機追蹤 | 40 µs／20 ms | 調參值 | [src: raw/project/firmware-pwm100_v1/Config.h#L38] |
| server ACK 期限／狀態斷線 | 1.5 s／2 s | 設計假設 | [src: raw/project/snapshot-20261123d/server.py#L340] [src: raw/project/snapshot-20261123d/server.py#L329-L330] |
| 非阻塞 max_outstanding／min_period／max_period | 2／0.025 s／0.1 s | 調參值 | [src: raw/project/snapshot-20261123d/uart_nonblock.json] |
| manual_drive ack_timeout／ack_link_loss | 1.0 s／0.45 s | 調參值 | [src: raw/project/snapshot-20261123d/uart_nonblock.json] |

## 未確認

- 非阻塞模式下 manual_drive 實際送出頻率的分布（介於 10～40 筆/s）未從逐格紀錄統計；PID 每秒約 23 格（見 [[comms/timing-latency]]），推論大多數 move 由新 PID 目標觸發。
- 協定 PDF（team-uart-protocol.pdf）為廠商版本，本專案文件明言不宣稱相容 [src: raw/project/docs/PROTOCOL.md#L19]；兩者差異未整理。
- 「舵機大動作時 UART 回覆偶有損壞」列為硬體待查項目，原因未明 [src: raw/records/logs/AGENTS.md#L374]。

## 相關條目

- [[comms/timing-latency]]
- [[control/command-chain]]
- [[control/speed-control]]
- [[control/lap-position]]
- [[hardware/vehicle-hardware]]
- [[hardware/steering-servo]]
- [[hardware/imu-mpu6050]]
- [[overview]]
