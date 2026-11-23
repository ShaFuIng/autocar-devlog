# AI 審查 1：語意忠實度查核（Workflow 節點 C）

- 審查日期：2026-11-23
- 方式：只讀。逐處打開 raw 檔的對應行或 json 鍵，與條目句子對照；狀態判定以 `raw/project/snapshot-20261123d/` 的 json 與 `live_pid.py` 層表 L2235–L2292 為準。
- 未檢查：整檔引用 run-b541 `summary.json` 的統計數字（由 tools/stats_timing.py 從 raw 以外的 pid.jsonl 算出，無法在 raw 內重算）、官方 PDF 的頁內文字（sources/nvidia-carrier-board-spec 的 3 處只確認引用的檔案存在）。

## 摘要

| 項目 | 數量 |
|---|---|
| 抽樣引用處 | 132 |
| 正確 | 118 |
| 部分正確 | 8 |
| 錯誤 | 3 |
| 引用位置不對但內容存在 | 3 |

- 狀態查核：10 個頂層 `enabled:false` 檔、4 個關閉子區塊（arc2.pre、curve_trim.c3、lap_ff.curves.c3、speed_guard.ramp_cap）、arc_lat 四彎 control false、stuck_stop mode stop、output_unify.json 不存在、i_ramp 無 land 鍵，disabled-layers 的寫法全部與 json 一致。發現 1 處把關閉子區塊寫成現役（#2），1 處一句話結論與同頁內文的現役判斷不一致（#9）。
- 公式查核：yaw_inner、cmd_comp、crossing_pass、gyro_hold、arc2 blind r4、heading_hold FOLLOW_BIAS／HEADING_ONLY、land4、arc2.c3 底限、x-band、downhill_gz、bottom_owner 遺失格、gain_schedule 的係數、正負號、上下限都與程式一致。有問題的是 lap_ff 帶狀 own 模式（#3）與 PID 的 D 項（#12）。
- 不公開資訊：wiki/ 內沒有 IP、主機名稱、Wi-Fi 名稱、信箱、金鑰路徑、/home 路徑或人名。只出現「使用者」「隊友」這類稱呼。

## 問題表

| 編號 | 條目檔:行 | 類型 | 條目寫的 | raw 實際（檔:行） | 建議修正 |
|---|---|---|---|---|---|
| 1 | control/slope-downhill.md:35 | misquote | 「最終版下坡與落地前 1.2 m 的舵量由 land4…全權決定」 | land4.py:L19-L22：slope 段從第一個下坡格到落地；land 段從落地到 x_end（1.2 m）。land4.json:L629 x_end 1.2 | 改為「下坡全程與落地後最初 1.2 m」。「落地前」會被讀成坡上最後 1.2 m |
| 2 | control/command-chain.md:84 | status-wrong | 層 28 lap_ff「彎 1／2／3 依位置的帶狀前饋」 | lap_ff.json curves.c3.enabled = false；彎 3 由 arc2_flat（arc2.c3）負責（curve-band-ff.md 同樣這樣寫） | 改為「彎 1／2」 |
| 3 | control/curve-band-ff.md:115-124（公式） | formula | own 模式「上限 = tgt → a = 1 時輸出 = tgt」 | lap_ff.py:L169-L171、L279：上限 upper = max(中心+own_lo, min(prof+m_hi_us, own_up))；own_up = prof+et+gt，沒有經過 cap 夾限。m_hi_us = 140（c1、c2） | 公式補上 `upper = min(prof + m_hi_us, prof+et+gt)`。a=1 時輸出 = min(tgt, prof+140)。參數表補 m_hi_us 140。et+gt 最多 210，所以這個上限確實會作用 |
| 4 | control/curve-band-ff.md:128 | misquote | c1 κ_turn「46～100° 40.9，130° 起遞減」 | lap_ff.json curves.c1.band.kappa_turn：100° 40.9 → 113° 39.0 → 120° 35 → 130° 25 | 改為「100° 起遞減」 |
| 5 | control/curve-band-ff.md:67 | link-broken（引用錯位） | x-band「速率限制 700 µs/s」[arc2.json#L1144] | L1144 是 note，沒有寫數字；rate_us_s 700 在 arc2.json:L1027 | 改引 #L1027 或 #key=c3.xband.rate_us_s |
| 6 | control/yaw-inner.md:45 | misquote | CREST_SETTLE「剛離開陡坡 1.0 s 內」 | yaw_inner.py:L74、L77：steep_t 在俯仰 ≥ settle_pitch 5°（上坡）時記錄，之後 1.0 s 內不作用 | 改為「上坡（俯仰 ≥ 5°）結束後 1.0 s 內」 |
| 7 | control/yaw-inner.md:28 | link-broken（引用錯位） | 「gz…左轉為正」[yaw_inner.py#L10] | L10 只寫 50 Hz，沒有寫正負號。正負號寫在 yaw_inner.py:L150（+ = left）或 gyro_hold.py:L5 | 加引 L150 |
| 8 | control/yaw-inner.md:91 | misquote（輕微） | weave：1.5 s 內 gz 同時 ≥ +20 與 ≤ −20 | live_pid.py:L1205 另外要求視窗內至少 5 筆（len(w_)>=5），而且只在平地 WAIT_CLIMB 才判斷 | 補「至少 5 筆、平地」 |
| 9 | control/heading-hold.md:35 | status-wrong（輕微） | 一句話結論：「陡下坡由 down_straight 限幅或陀螺儀保持」並標【現役】 | 同頁 L81 與 land4.py:L19-L20：land4 slope 段擁有坡上每一格，down_straight 的結果不被採用 | 改為「陡下坡由 land4 全權（down_straight 只在 land4 無參考或無 IMU 時送出）」 |
| 10 | hardware/imu-mpu6050.md:57 | misquote | 「11-22 13:43 由手機頁誤校成 1.99 後更正回 1.0」 | AGENTS.md:L215：13:21 手機頁誤校成 1.99，13:43 更正為 1.0 | 時間改為「13:21 誤校、13:43 更正」 |
| 11 | comms/uart-protocol.md:80 | misquote | 「其他韌體版本目錄的同一常數為 50 或 70」 | 引用的 AGENTS.md:L119-L120 只寫前一版 70；「50」是 Orin 端上限（Config.h:L36 註解、AGENTS.md:L120）。raw 沒有其他韌體目錄可以佐證 50 | 刪掉「50」，或改寫成「Orin 端預設上限 50」 |
| 12 | control/pid-core.md（公式 D 項） | formula | `D ← D + dt/(τ_D+dt)×(Δe_near/dt − D)`；target = c + u×g | visual_pid.py:L101、L107：D 用的是傳入的控制誤差 e 的差分（e − 上一格 e），不是 e_near。target 另外還加 feedforward()（PID 內建間隙補償，最終版 backlash_enabled 0，所以是 0） | 改成 Δe/dt，並註明「feedforward 項最終版為 0」 |
| 13 | path/vision-failure-modes.md:116 | link-broken（引用錯位） | 坡頂備援「白線間距至少 24 px、至少 15 列、最多往上延伸 24 px」[crest_fallback.py#L23-L24] | MIN_GAP 24、MIN_ROWS 15、EXT_PX 24 在 crest_fallback.py:L25 | 引用範圍改為 L23-L25 |
| 14 | control/heading-hold.md:59 | misquote（輕微） | 參考航向：PRE 或 LATE，「再以相機橫向斜率修正 ±2.5°」 | arc2.py:L222-L229：相機修正（cam_ref_m）只套在 PRE，LATE 不套 | 改為「PRE 參考再以相機斜率修正」 |

另外有 2 處程式說明文字與 json 不一致。條目已經依規則處理，這裡只列出供參考：xp_anchor.json note 寫「NOT deployed」但 enabled true；stuck_stop.json note 寫「LOG mode」但 mode 是 stop。

## 讀者可讀性：第一次出現時沒有解釋的名詞

1. cps（slope-downhill.md:92「6800 cps」：編碼器每秒計數，換算寫在 speed-control.md:75，這頁沒有）
2. FLOOR／RELEASED（curve-band-ff.md curve_map 段：curve_map 的狀態名，沒有說明意思）
3. proposal（heading-hold.md:54：每格的命令提案字典）
4. 直行點（command-chain.md:138、curve-band-ff.md：車實際走直所需的舵量，與「中心」的差別沒有說明）
5. LAND8（curve-band-ff.md 彎 4 段：只有 slope-downhill 有定義）
6. C3s／C4e 的含義（curve-band-ff.md:39 只寫「由 lap_pos 判定」，沒有寫「彎 3 起點／彎 4 終點」）
7. crest_midpoint（command-chain.md:131：坡頂中點路徑來源）
8. WARMUP（command-chain.md 步驟 2：沒有說明是 PID 第一格只記錄誤差）
9. TOP+／DASHe（path/upper-dash-route.md:100 等：只在 lap-position 有定義）
10. e_c（command-chain.md 等多處：「該位置置中時的相機誤差」只在 curve-band-ff 有定義）

## 抽樣清單

以下標 ✓ 的是正確，編號是問題表的編號。

**control/yaw-inner.md**：L20 ✓、L25 ✓、L26 ✓、L27 ✓、L28 #7、L32 層序 ✓、L33 ✓、L34 ✓、L35 ±40 ✓、L38 ely 條件 ✓（live_pid L957-958、segment_ctx L52-73）、L39 ✓、L41 ✓、L42 坡頂保持 ✓、L43 down_push ✓、L44 TRANSITION ✓、L45 #6、L46 ✓、L49 下限 −20 ✓（curve_map.py L123）、L50 c4_exit ✓、L51 lock false ✓、公式 L58-61 ✓、L64 ✓、參數表 k 4／cap 120／gz_tau 0.1／max_u 400／gain_lo-hi／climb／crest／downhill／hold_far／term_rate／oppose ✓、L90 ✓、L91 #8、L92 ✓、L93 ✓、L94 ✓、L95 ✓、L96 ✓、L98 增益 0.19～0.28 ✓、L104 ✓

**control/heading-hold.md**：L35 #9、L40 ✓、L45 ✓、L46 cmd_comp 條件 ✓、L47 ✓、L50 xp_anchor ✓、L51 窗口 ✓、L52 cam_frac／release／fade ✓、L53 ✓、L55 crossing_hold ✓、L58 V 字路口窗口 ✓、L59 #14、L60 max_dev 12 ✓、L66 圓圈路口窗口 ✓、L67 地圖參考 −204.7 ✓、L69 lost_age 1.0 ✓、L70 ✓、L73 TURN_DEG 75 ✓、L74 ✓、L75 ✓、L80 down_straight ✓、L84-85 gyro_hold ✓、L88-93 關閉層 ✓、公式 cmd_comp ✓、gyro_hold ✓、blind r2／r4 律 ✓、參數表 k_psi 10／12、ki 8／10、lim／step、k_cam／trim／tau、ref_m ✓、heading_hold 公式與常數 ✓、upper_single one 參數 ✓、down_straight ✓

**control/disabled-layers.md**：A 表 10 列 ✓、B 4 項 ✓（含 arc2.py _sub L57-60、L608-612、json L1322「11 次中 7 次」）、C arc_lat／overspeed_watch／bottom_guide ✓、D dist_ff（無程式讀取）／output_unify 不存在／i_ramp 無 land／blind_c2 無 v2 ✓、E 表 curve_map.lock、yaw_inner 三項、bottom_map、bottom_owner、bottom_guide、imu_boost L9、lap_ff gate 999、release_err 9.0、upper_single 三項 ✓、F stuck_stop note 與 mode 不一致 ✓

**control/curve-band-ff.md**：L31 ✓、L35 ✓、L36 ✓、L44 層序 ✓、L49 觸發 ✓、L50 trig_head ✓、L51 c1 窗口與 START ✓、L52 c2 窗口 ✓、L53 plat ✓、L54 delay／ramp ✓、L55 結束 ✓、L56 取消 ✓、L57 gate 999 ✓、L62 c3 窗口 ✓、L63 c3 底限公式 ✓、L64 w_x 與 e_max ✓、L67 #5、L68 arc_lat→x-band ✓、L69 top 表與規則 ✓、L74-77 彎 4 ✓、L82 curve_ff ✓、L85 gain_schedule ✓、公式 #3、κ 表 #4、c2 κ ✓、e_c_turn ✓、v_ref ✓、gain_table ✓、x-band 公式與參數 ✓

**control/slope-downhill.md**：L35 #1、L40 ✓、L45 down_tail ✓、L46 down_steep −8 ✓、L47 down_level ✓、L48 downhill 0.8 s ✓、L72 imu_boost ✓、L86 slope 擁有每格 ✓、L87 ref ✓、L88 u 上限 −0.05 ✓、L89 spike 3° ✓、L91 downhill_gz ✓、L98 land_min 1.2 m／1.0 s ✓、L99 LAND 段 ✓、L102 相機項 ✓、L106 bottom_owner 範圍 ✓、L107 cap 240 等 ✓、land4 公式 ✓、參數表 slope／land ✓、bottom_owner 公式 ✓、downhill_gz 公式 ✓

**control/command-chain.md**：L39 ✓、步驟 1 max_gap ✓、步驟 2 WARMUP ✓、步驟 4 lap_pos 更新時序 ✓、層 24 ✓、層 28 #2、層 31 ✓、層 53 ✓、遺失格順序 ✓、gain_schedule 不套用的情況 ✓、steer_rate 1500 ✓、韌體 40 µs／20 ms ✓、orin_timed ✓

**control 其他**：pid-core L48 ✓、L49 ✓、L98 ✓、公式 #12；play-comp L41 ✓、L47 ✓、L48 ✓；lost-path L68 ✓、L75 ✓、L77 ✓；speed-control L52 ✓、L63 ✓、L69 ✓；lap-position L59 ✓、L71 ✓、L77 ✓

**comms**：uart-protocol L41 ✓、L49 ✓、L50 ✓、L80 #11、L117 ✓；timing-latency L34 ✓、L60 ✓、L61 ✓、L68-73 表（max_age 0.3、max_gap 0.4、uart 0.025～0.1、2 筆／0.45 s、200 ms、500 ms、40 µs）✓

**path**：mask-to-path L68 ✓、L101 ✓、L110 ✓；junction-handling L36 ✓、L55 ✓、L59 ✓；upper-dash-route L51 ✓、L96 ✓；vision-failure-modes L116 #13

**perception**：camera-capture L52 ✓、L80 ✓；yolo26-sem L60 ✓、L95 IoU 驗算 ✓、L96 ✓

**hardware**：imu-mpu6050 L57 #10、L63 ✓、L81 ✓；steering-servo L59 ✓、L62 ✓、L83 ✓；vehicle-hardware L63 ✓、L73 ✓、L89 ✓

**experiments**：final-performance L58 ✓、L67 ✓、L108 ✓；lap-progression L45 ✓、L73 ✓、L84 ✓；s-weave L61 ✓、L102 ✓、L114 ✓；failures-abandoned L47 ✓、L93 ✓、L101 ✓

**synthesis/imu-roles.md**：L27 ✓、L46 ✓、L47 梯形積分 ✓

**sources/nvidia-carrier-board-spec.md**：L20、L22、L23（只確認 PDF 檔存在，沒有核對頁內文字）
