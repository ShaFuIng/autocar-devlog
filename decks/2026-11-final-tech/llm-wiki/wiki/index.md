# Wiki 目錄

狀態：implemented＝最終版確實在用；used-before＝曾用；reference-only＝僅參考；mixed＝頁內分段標示。
另見 [[conflicts]]（未決衝突）、[[log]]（更新紀錄）。

## 總覽與綜合

| 條目 | 標題 | 狀態 |
|---|---|---|
| [[overview]] | 系統總覽：一顆相機加一顆 IMU 的循線自走車 | implemented |
| [[synthesis/imu-roles]] | IMU 在最終版控制中的角色（綜合） | implemented |
| [[synthesis/glossary]] | 名詞與地標代號對照 | implemented |

## 硬體

| 條目 | 標題 | 狀態 |
|---|---|---|
| [[hardware/imu-mpu6050]] | IMU（MPU6050）硬體、紀錄程式與校正 | implemented |
| [[hardware/steering-servo]] | 轉向舵機、保存設定與轉向量測事實 | implemented |
| [[hardware/vehicle-hardware]] | 整車硬體與分工 | implemented |

## 感知

| 條目 | 標題 | 狀態 |
|---|---|---|
| [[perception/camera-capture]] | 相機取像（USB 相機、MJPG 1280×720、手動曝光） | implemented |
| [[perception/yolo26-sem]] | YOLO26n-sem 白線語意分割模型（v4） | implemented |

## 路徑

| 條目 | 標題 | 狀態 |
|---|---|---|
| [[path/junction-handling]] | 路口與交叉處的路徑選擇（透視走廊＋切換器） | implemented |
| [[path/mask-to-path]] | 白線遮罩→行駛路徑→影像誤差（camera-pair-v2） | implemented |
| [[path/upper-dash-route]] | 高架上層虛線路段（DashRoute 狀態機與虛線轉彎觸發） | implemented |
| [[path/vision-failure-modes]] | 相機失去可靠判斷的情境與有效路徑旗標 | implemented |

## 控制

| 條目 | 標題 | 狀態 |
|---|---|---|
| [[control/command-chain]] | 一格命令的計算鏈：層表順序、遺失格、輸出階段 | mixed |
| [[control/curve-band-ff]] | 急彎控制：位置觸發的帶狀前饋（彎 1～彎 4） | implemented |
| [[control/disabled-layers]] | 已關閉、只記錄或說明文字過時的控制層清單 | mixed |
| [[control/heading-hold]] | 直線與路口的航向保持（多層並存） | mixed |
| [[control/lap-position]] | 圈內位置估計（lap_pos）：編碼器里程＋航向／俯仰地標 | implemented |
| [[control/lost-path]] | 路徑遺失時的處理（遺失表與各段專屬保持） | implemented |
| [[control/pid-core]] | 視覺 PID 核心：誤差定義、PID 形式與參數 | implemented |
| [[control/play-comp]] | 轉向間隙補償（play_comp） | implemented |
| [[control/slope-downhill]] | 上坡、坡頂、下坡與落地的控制 | implemented |
| [[control/speed-control]] | 油門決定鏈：speed_adapt、位置速度表、減速區與上限 | implemented |
| [[control/yaw-inner]] | 陀螺儀內迴圈（yaw_inner）壓住直線 S 型 | implemented |

## 通訊與時序

| 條目 | 標題 | 狀態 |
|---|---|---|
| [[comms/timing-latency]] | 時序與延遲：控制資料年齡、推論耗時、命令頻率 | implemented |
| [[comms/uart-protocol]] | Orin 與 BMduino 的 UART 協定與分工 | implemented |

## 實驗與歷史

| 條目 | 標題 | 狀態 |
|---|---|---|
| [[experiments/failures-abandoned]] | 試過但放棄或確定變差的方法，以及從未上車的提案 | mixed |
| [[experiments/final-performance]] | 最終版（快照 20261123d）的實測表現 | implemented |
| [[experiments/lap-progression]] | 圈速演進時間線（11-07 109.9 s → 11-23 56.5 s） | used-before |
| [[experiments/s-weave]] | 直線 S 型擺動：問題、原因分析、陀螺儀內迴圈與實車效果 | mixed |

## 來源摘要（Ingest）

| 條目 | 標題 | 狀態 |
|---|---|---|
| [[sources/nvidia-carrier-board-spec]] | NVIDIA Jetson Orin Nano 開發套件載板規格書（SP-11324-001 v1.3） | implemented |
| [[sources/ultralytics-semantic-segmentation]] | Ultralytics YOLO 語意分割官方文件（tasks/semantic、tasks/segment） | implemented |
| [[sources/ultralytics-jetson-guide]] | Ultralytics NVIDIA Jetson 部署指南 | reference-only |
| [[sources/opencv-homography]] | OpenCV 單應性（Homography）官方教學 | mixed |
| [[sources/mpu6050-register-map]] | InvenSense MPU-6000／MPU-6050 暫存器表（RM-MPU-6000A） | implemented |
| [[sources/regulated-pure-pursuit]] | Macenski 等（2023）Regulated Pure Pursuit 論文 | reference-only |
| [[sources/stanley-2006]] | Thrun 等（2006）Stanley：贏得 DARPA 大挑戰的車輛 | reference-only |
