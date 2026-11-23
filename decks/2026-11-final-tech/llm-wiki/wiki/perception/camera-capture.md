---
id: perception/camera-capture
title: 相機取像（USB 相機、MJPG 1280×720、手動曝光）
status: implemented
sources:
  - raw/project/snapshot-20261123d/server.py
  - raw/project/snapshot-20261123d/live_model_worker.py
  - raw/project/snapshot-20261123d/standalone_line_path.py
  - raw/project/snapshot-20261123d/warm_color_candidate.py
  - raw/project/snapshot-20261123d/model_stage.json
  - raw/project/snapshot-20261123d/worker_overlap.json
  - raw/project/docs/jetson-environment-handoff.md
  - raw/records/analyses/a1-poster-factcheck-20261103.md
  - raw/records/logs/AGENTS.md
  - raw/records/logs/AGENTS_HISTORY_until_20261119.md
  - raw/records/runs/run-b541-20261123/summary.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# 相機取像（USB 相機、MJPG 1280×720、手動曝光）

## 一句話結論

車頭一顆 USB 相機以 MJPG 格式、1280×720、要求 30 張/s、緩衝 2 張取像 [src: raw/project/snapshot-20261123d/server.py#L476-L482]；相機固定手動曝光 30 ms＋gamma 300，實際約 30 張/s [src: raw/records/logs/AGENTS.md#L100]（自動曝光時只有約 17～20 張/s [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L551]）；影像進模型前縮成 640×360 [src: raw/project/snapshot-20261123d/standalone_line_path.py#L250-L251]。

## 內容

### 取像程式（server.py camera_worker）

- 以 OpenCV 的 V4L2 介面開啟固定的 USB 裝置路徑（by-id 名稱含「USB_Camera」）[src: raw/project/snapshot-20261123d/server.py#L474-L476]。
- 設定：MJPG（相機端壓縮的 JPEG 串流）、寬 1280、高 720、FPS 30、BUFFERSIZE 2 [src: raw/project/snapshot-20261123d/server.py#L478-L482]。緩衝只留 2 張是為了不讓舊影格堆積（推論：緩衝越大，讀到的影格越舊）。
- 每讀到一張就記錄取像時間 `capture_at`（Orin 的 monotonic 時鐘）、序號，並以最近 2 秒的影格數算 `capture_fps`，再交給處理管線 [src: raw/project/snapshot-20261123d/server.py#L485-L499]。
- 讀取失敗時丟出錯誤、釋放相機，2 秒後重開 [src: raw/project/snapshot-20261123d/server.py#L488-L489] [src: raw/project/snapshot-20261123d/server.py#L502-L504]。

### 曝光：為什麼固定手動 30 ms＋gamma 300

1. 11-17 唯讀查詢：驅動回報每格 1/30 s，但自動曝光（光圈優先）下，車停在起點時實際只有 16.6～16.7 張/s、每次讀取約 60 ms；前一天跑道上約 20 張/s——判讀為自動曝光在光線不足時拉長每格時間（當時標為推論）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L544]。
2. 靜態測試：手動 30 ms（exposure_absolute 300，單位 100 µs）可到 29.8 張/s 但畫面太暗（平均亮度 18、左線消失）；加相機內建 gamma 300 後亮度 122、白線遮罩與自動曝光的重疊 IoU 0.855，鏡頭核對通過 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L545]。
3. 多位置比對：隧道口手動較好（自動漏掉左線近處）、坡底相當（近處重疊 97.9%）、上層相當或略好、上坡有天花板燈處相當（94%），四處手動皆 29.7～29.9 張/s [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L546-L549]。
4. 11-17 授權改為手動後，capture_fps 29.7～29.9、每次讀取約 32 ms；註明「每秒張數由約 17～20 變 30，屬整圈變更」[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L551]。
5. 之後成為開機服務，固定手動 30 ms＋gamma 300，以 capture_fps ≈ 30 為準 [src: raw/records/logs/AGENTS.md#L100]。

注意：相機斷電或重插會回到自動曝光（11-17 紀錄）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L551]；最終版由開機服務重設 [src: raw/records/logs/AGENTS.md#L100]。

### 進入模型前的處理

1. 把 JPEG 解碼後縮成 640×360 [src: raw/project/snapshot-20261123d/standalone_line_path.py#L250-L251]。
2. 「暖色修正」（WarmColor）：在畫面第 190～335 列找亮且低飽和的像素，若紅／藍比 > 1.15（偏暖光）就逐通道調整增益，增益每秒最多變 0.65；沒偵測到時 0.3 s 後回到 1 [src: raw/project/snapshot-20261123d/warm_color_candidate.py#L31-L49]。最終版以 `warm_fast` 開啟等值的快速版 [src: raw/project/snapshot-20261123d/model_stage.json#key=warm_fast] [src: raw/project/snapshot-20261123d/warm_color_candidate.py#L5-L12]。
3. 修正後的 640×360 影像送進 YOLO26 分割模型 [src: raw/project/snapshot-20261123d/live_model_worker.py#L198-L200]，見 [[perception/yolo26-sem]]。

worker 以兩段流水線執行（A：解碼＋前處理＋模型；B：路徑計算），`worker_overlap.json` 開啟並把執行緒綁在 CPU 0～3 [src: raw/project/snapshot-20261123d/worker_overlap.json#key=enabled] [src: raw/project/snapshot-20261123d/worker_overlap.json#key=cpus] [src: raw/project/snapshot-20261123d/live_model_worker.py#L135-L140]。

### 實際張數與延遲（最終版實跑 run-b541）

以 `tools/stats_vision_validity.py` 自逐格紀錄 pid.jsonl（MANIFEST external 項）計算 [src: raw/records/runs/run-b541-20261123/summary.json]：

| 項目 | 中位數 | P90 [src: raw/records/runs/run-b541-20261123/summary.json] |
|---|---|---|
| 相鄰兩筆控制紀錄的取像間隔 | 35.4 ms | 68.5 ms [src: raw/records/runs/run-b541-20261123/summary.json] |
| 取像→控制端消費（control_age） | 87.4 ms | 106.1 ms [src: raw/records/runs/run-b541-20261123/summary.json] |

本輪 119.8 s 內有 2804 筆控制紀錄，約 23.4 筆/s（推算：2804 ÷ 119.8）[src: raw/records/runs/run-b541-20261123/summary.json]。這是「被控制端消費的影格數」，不等於相機的 30 張/s；中間沒被消費的影格不在紀錄內。AGENTS 的車輛事實寫「全場約 30 張/s、影像年齡中位約 60～85 ms」[src: raw/records/logs/AGENTS.md#L114]，與本輪的 87.4 ms 量法與時期不同，僅供參考。延遲的三段定義見 [[comms/timing-latency]]。

### 鏡頭姿態核對

每次到場以靜態快照核對、每輪以起跑格複核：基準車道寬 47.6 cm、地平線 90.4 px，門檻 1.5 cm／4 px；鏡頭硬體（鏡頭、角度、位置）不更換 [src: raw/records/logs/AGENTS.md#L99]。姿態若變，地面單應性（像素→公分）就不再準，見 [[path/mask-to-path]]。

## 公式與參數

- 解析度 1280×720、要求 30 張/s、緩衝 2（設計值）[src: raw/project/snapshot-20261123d/server.py#L479-L482]
- 曝光 30 ms（exposure_absolute 300 × 100 µs）、gamma 300（實測比對後選定的調參值）[src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L545]
- capture_fps ＝（最近 2 s 內影格數 − 1）÷（最新時間 − 最早時間）[src: raw/project/snapshot-20261123d/server.py#L492] [src: raw/project/snapshot-20261123d/server.py#L497]
- 暖色修正：偵測條件 V > 160 且 S < 150 的像素數 > 150、紅／藍中位比 > 1.15；目標增益 ＝ clip(各通道中位平均 ÷ 各通道中位, 0.8, 1.55)；變化率 0.65/s（皆為實驗值）[src: raw/project/snapshot-20261123d/warm_color_candidate.py#L36-L46]

## 未確認

- 相機型號：環境文件寫「Full HD USB Webcam」[src: raw/project/docs/jetson-environment-handoff.md#L12]，舊照片可見「HD WEBCAM」字樣，品牌型號未確認 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L87]。型號原始資料未記載。
- 相機內參、鏡頭畸變：快照內的地面單應性只用平面對應，原始資料未見內參標定。
- 連續自動對焦在 11-17 查詢時是開著的（預設 0、當時 1），之後是否關閉未見紀錄 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L545]。
- 手動曝光在行進中、一天中光線變化下的表現，11-17 的比對只有靜止單張 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L549]。

## 相關條目

- [[perception/yolo26-sem]]、[[path/mask-to-path]]、[[path/vision-failure-modes]]
- [[comms/timing-latency]]、[[hardware/vehicle-hardware]]
