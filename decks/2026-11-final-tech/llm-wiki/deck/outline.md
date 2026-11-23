# 競賽技術簡報大綱（節點 D 產物，15 頁）

依使用者 11-23 定的 15 頁題目，以 Wiki 條目查詢後寫成。每頁欄位固定，由 `tools/coverage.py`（節點 E）檢查：
- 每頁至少連到一個存在的條目。
- 第 1～13 頁至少有一個 implemented／mixed 條目。
- 「結論」欄的每個數字，都要能在該頁連到的條目中找到。
- 「待決」欄引用的衝突編號要存在於 wiki/conflicts.md。

素材原則（待決 H-2）：
- 感知頁用 11-19 有錄影的輪次（與最終版同一份模型權重），要標明「較早控制版」。
- 控制頁用最終版 run-b541 逐格紀錄的遮罩與狀態重繪。
- 不把不同輪次拼成同一次實驗。

---

## P01 整台車如何從感知走到控制？
- 結論：一顆相機加一顆 IMU，在 Orin 上每格算出舵量與油門，經 UART 交給 BMduino 驅動舵機與馬達；最終版約每秒 23.4 格送進控制。
- 感測／演算法：USB 相機、MPU6050、編碼器、YOLO26 語意分割、PID＋分層控制。
- Wiki：[[overview]] [[hardware/vehicle-hardware]] [[comms/timing-latency]] [[control/command-chain]]
- 公式：無。
- 圖表：系統方塊圖（依原理圖重畫，不放原圖）；一格資料流時間軸。
- 待決：P-1 C-1

## P02 相機如何取得適合 AI 辨識的影像？
- 結論：固定手動曝光 30 ms 加 gamma 300，維持約 30 張/s（自動曝光時只有約 17～20 張/s），再縮成 640×360 送進模型。
- 感測／演算法：USB 相機 MJPG 1280×720。
- Wiki：[[perception/camera-capture]]
- 公式：無。
- 圖表：自動與手動曝光的張數對照。
- 待決：（兩種曝光的對照畫面尚未找到）

## P03 YOLO26 如何從影像分割出白線？
- 結論：自己標註、微調的兩類語意分割模型，逐像素判斷白線；在 Orin 上用 PyTorch 推論，模型階段中位約 20 ms。
- 感測／演算法：YOLO26n-sem（v4 權重）、輸入 640。
- Wiki：[[perception/yolo26-sem]] [[comms/timing-latency]] [[sources/ultralytics-semantic-segmentation]] [[sources/ultralytics-jetson-guide]]
- 公式：無。
- 圖表：11-19 影片的原圖、遮罩、疊合三連圖；v3 與 v4 的比較。
- 待決：H-2

## P04 白線遮罩如何轉換成可行駛路徑？
- 結論：配對內側邊線求出中心路徑；近列誤差給 PID，遠列誤差經透視正規化、低通後作預看。
- 感測／演算法：camera-pair-v2、PreviewErrorPID。
- Wiki：[[path/mask-to-path]] [[path/junction-handling]] [[control/pid-core]] [[sources/opencv-homography]]
- 公式：e = e_near + LPF(0.2·(e_far_proj − e_near))，τ 0.15 s。
- 圖表：遮罩疊路徑與取樣列（11-19 影片）。
- 待決：H-2

## P05 相機在哪些賽道情境下會失去可靠判斷？
- 結論：前輪前 27～30 cm 以內看不到；彎 1～3 幾乎只見外側線；路口、虛線離開畫面、坡頂、坡口與落地容易失準。最終版控制端只有 0.3% 的格無效，最長連續 0.13 s，低於停車門檻 0.4 s。
- 感測／演算法：有效旗標三層、lost_policy。
- Wiki：[[path/vision-failure-modes]] [[control/lost-path]]
- 公式：無。
- 圖表：賽道地圖上的各路段無效率熱度（run-b541 統計）。
- 待決：H-2

## P06 IMU 如何提供車身姿態與運動資訊？
- 結論：只用俯仰、航向、車頭轉速三個量；側傾與加速度沒有參與控制。平地基準 1.0°，資料超過 0.3 s 就不用。
- 感測／演算法：MPU6050、互補濾波（11-05 版紀錄程式）。
- Wiki：[[synthesis/imu-roles]] [[hardware/imu-mpu6050]] [[sources/nvidia-carrier-board-spec]] [[sources/mpu6050-register-map]]
- 公式：相對俯仰 = pitch − 1.0°；航向梯形積分 ψ_k = ψ_(k−1) + ½(gz_k + gz_(k−1))·Δt。
- 圖表：一圈的俯仰與 gz 曲線，標出坡道與四個彎；「IMU 量→使用的層」對照表。
- 待決：（H-1 已決：只引用 11-05 版紀錄程式並註明限制）

## P07 直線為什麼會走 S 型？陀螺儀如何壓住？路口如何保持航向？
- 結論：S 型來自相機到車頭的迴路延遲與兩次積分，調 PID 改不了週期；陀螺儀內迴圈用 gz 即時抵銷。11-18 增益由 6 降到 4 後，主直線 gz 標準差由 16.7／8.7／22.1 降到 6.4～12.8。路口則用進路口前的平均航向保持方向，航向差超過 12° 就放手。
- 感測／演算法：yaw_inner、arc2.blind／blind_c2、crossing_pass、gyro_hold；間隙補償是另一個機制。
- Wiki：[[control/yaw-inner]] [[experiments/s-weave]] [[control/heading-hold]] [[control/play-comp]]
- 公式：term = 4·(g(v)·u + gz)，上限 ±120 µs；路口：中心 + I + 10·Δψ + 1.2·gz + 相機微調。
- 圖表：run-b541 路口段的航向差、舵量、層狀態同步曲線；S 型示意（延遲迴路）。
- 待決：C-2 B-2（D3、D4 已決：不宣稱因果；兩種延遲分開列）

## P08 急彎時相機視野不足，車輛如何完成轉向？
- 結論：以 IMU 量到的已轉角度查跑道曲率表，預先給舵（帶狀前饋）；進入後由前饋全權控制，PID 只修正「誤差減置中值」。
- 感測／演算法：lap_ff 帶狀前饋（彎 1、2）、arc2.c3（彎 3）、lap_ff4（彎 4）、curve_ff、yaw_inner。
- Wiki：[[control/curve-band-ff]] [[synthesis/imu-roles]] [[control/lap-position]]
- 公式：舵量 = 中心 + κ(θ)/g(v) + clip(220·(e_near − e_c(θ))) + clip(1.5·(gz + v·κ), ±60)。
- 圖表：彎 2 一次的已轉角度、前饋目標、實送命令、近誤差；四彎觸發與結束條件表。
- 待決：B-1 B-3

## P09 上坡、坡頂與下坡如何切換控制策略？
- 結論：俯仰 ≥5° 判上坡並加油門；坡頂由坡頂鎖定處理；坡上全程與落地後最初 1.2 m 由陀螺儀依目標航向表轉向，落地需離坡口 ≥1.2 m 或坡上 ≥1.0 s 才成立。
- 感測／演算法：imu_boost、crest_latch、land4、bottom_owner。
- Wiki：[[control/slope-downhill]] [[synthesis/imu-roles]]
- 公式：舵量 = 中心 + κ/g + clip(10·(ψ − θ(u)), ±120) + clip(1.5·(gz + κv), ±60)。
- 圖表：坡道狀態流程圖；run-b541 一趟的俯仰、航向誤差、舵量對距離。
- 待決：（坡腳回擺變大原因未查）

## P10 編碼器與地標如何輔助賽道位置判斷？
- 結論：編碼器累計里程（每計數 0.000222 m），在航向與俯仰的特徵點重新對齊，一圈設定 67.72 m；位置決定各層的開窗與速度表。
- 感測／演算法：編碼器、lap_pos 地標狀態機。
- Wiki：[[control/lap-position]] [[synthesis/glossary]]
- 公式：里程 = 計數 × 0.000222 m。
- 圖表：賽道地圖標出地標。
- 待決：C-1

## P11 PID、前饋、速度表與舵機補償如何計算控制命令？
- 結論：路徑誤差 → PID（kp 220、ki 40、kd 30）→ 各層修正（後寫者生效）→ 間隙補償 ±15 µs → 速率上限 1500 µs/s → UART；油門由位置速度表、煞車區與上限 100 決定。
- 感測／演算法：PID、層表、play_comp、lap_speed、brake_zones。
- Wiki：[[control/pid-core]] [[control/command-chain]] [[control/play-comp]] [[control/speed-control]] [[control/disabled-layers]]
- 公式：u = kp·e + ki·I + kd·D；k = max(0.57, 19.6/PWM)；間隙補償 ±15。
- 圖表：命令計算管線圖；取 run-b541 一格的實例。
- 待決：（無）

## P12 Jetson 如何透過 UART 與 BMduino 完成安全控制？
- 結論：115200 bps，每包有序號與 CRC16 校驗；指令有效期 500 ms；Orin 端待確認逾期 1.5 s 就送 STOP；實體急停需連續低電位 10 ms。
- 感測／演算法：UART 協定、BMduino 韌體 pwm100_v1。
- Wiki：[[comms/uart-protocol]] [[sources/nvidia-carrier-board-spec]]
- 公式：CRC16/CCITT-FALSE（多項式 0x1021、初值 0xFFFF）。
- 圖表：封包格式圖；送出→ACK→逾時處理時序圖。
- 待決：（無）

## P13 最終版的實際辨識與行駛表現
- 結論：最終定版 run-b541 兩圈 56.5／56.8 s、無失敗（賽前實測，非正式比賽成績；推算效能比約 83%）；模型驗證 IoU 0.862（15 張，與訓練同路線，不是獨立測試）；控制資料年齡中位 87.4 ms。
- 感測／演算法：—
- Wiki：[[experiments/final-performance]] [[perception/yolo26-sem]] [[comms/timing-latency]] [[path/vision-failure-modes]]
- 公式：無（效能比是否放推算值待決）。
- 圖表：圈速表、推論耗時分布、各路段有效率。
- 待決：C-3（D1、D2 已決）

## P14 從早期版本到最終版，做了哪些有效改進？
- 結論：有紀錄的單圈由 11-07 的 109.9 s 降到最終版 56.5 s；每個轉折只列有紀錄的改變，不把圈速差歸因給單一改動。
- 感測／演算法：—
- Wiki：[[experiments/lap-progression]] [[experiments/s-weave]] [[control/play-comp]]
- 公式：無。
- 圖表：圈速時間線，標出改進項目。
- 待決：D5

## P15 曾經失敗或放棄哪些方法？為什麼最終選用現在的架構？
- 結論：放棄的方法依實車或離線證據列出；Pure Pursuit／Stanley 只有提案，沒有找到書面放棄理由；TensorRT 因會改變輸出而未導入。
- 感測／演算法：—
- Wiki：[[experiments/failures-abandoned]] [[control/disabled-layers]] [[experiments/lap-progression]] [[sources/regulated-pure-pursuit]] [[sources/stanley-2006]] [[sources/ultralytics-jetson-guide]]
- 公式：無。
- 圖表：方法比較表（想解決什麼、結果、依據）。
- 待決：（無；Pure Pursuit、Stanley 只作 reference-only 比較）
