---
id: perception/yolo26-sem
title: YOLO26n-sem 白線語意分割模型（v4）
status: implemented
sources:
  - raw/project/snapshot-20261123d/pid_models.json
  - raw/project/snapshot-20261123d/live_model_worker.py
  - raw/project/snapshot-20261123d/model_stage.json
  - raw/project/snapshot-20261123d/model_stage.py
  - raw/project/snapshot-20261123d/camera_pair_geometry.json
  - raw/project/model-yolo26-sem-v4/dataset/data.yaml
  - raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml
  - raw/project/model-yolo26-sem-v4/train_trial.py
  - raw/project/model-yolo26-sem-v4/training_summary.json
  - raw/project/model-yolo26-sem-v4/comparison/metrics.json
  - raw/project/model-yolo26-sem-v4/run_provenance.json
  - raw/project/model-yolo26-sem-v4/split_plan.json
  - raw/project/model-yolo26-sem-v4/quality_gate.json
  - raw/records/analyses/a1-poster-factcheck-20261103.md
  - raw/records/logs/AGENTS_HISTORY_until_20261119.md
  - raw/records/runs/run-b541-20261123/summary.json
verified_against: snapshot-20261123d
updated: 2026-11-23
---

# YOLO26n-sem 白線語意分割模型（v4）

## 一句話結論

車上只用一個模型：Ultralytics YOLO26n-sem 的語意分割版本，把每個像素分成「背景／白線邊界」兩類；部署的是 v4 微調權重（SHA256 開頭 8b802fa0），在 Orin 上以 PyTorch 推論（未用 TensorRT），輸入尺寸 640，最終實跑模型階段中位約 20 ms [src: raw/project/model-yolo26-sem-v4/dataset/data.yaml#L5-L7] [src: raw/project/snapshot-20261123d/live_model_worker.py#L38-L42] [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L15] [src: raw/records/runs/run-b541-20261123/summary.json]。

## 內容

### 名詞

- **語意分割（semantic segmentation）**：對影像每個像素給一個類別，不框出物件；本車輸出一張「哪些像素是白線」的遮罩 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L39]。
- **YOLO26n-sem**：Ultralytics YOLO26 系列中最小（n）的語意分割模型；v4 訓練設定 `task: semantic` [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L1]。

### 部署（最終版）

- 模型表只有一筆 `v4-default`，轉接器 `v4`，權重為 v4 trial01 的 best.pt [src: raw/project/snapshot-20261123d/pid_models.json#L2-L6]。worker 啟動時計算權重 SHA256，並把它附在每一筆控制輸出裡，控制端若發現雜湊變了會拒絕 [src: raw/project/snapshot-20261123d/live_model_worker.py#L244] [src: raw/project/snapshot-20261123d/live_model_worker.py#L256]。最終實跑紀錄中的權重雜湊為 8b802fa03d34fa73…（由 stats 腳本讀取 pid.jsonl 的 `vision.weights_sha256` 得到）[src: raw/records/runs/run-b541-20261123/summary.json]；11-03 查核也確認部署權重 SHA256 `8b802fa0…` 與 v4 best.pt 一致 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L15]。
- 推論：`YOLO(best.pt).predict(image, imgsz=640, device=0)`，取 `semantic_mask` 中類別 1（boundary）的像素，再以最近鄰縮放回輸入大小 [src: raw/project/snapshot-20261123d/live_model_worker.py#L38-L42]。輸入是 640×360 的影像（相機 1280×720 先縮小），見 [[perception/camera-capture]]。
- 啟動時用一張全黑 720×1280 影像暖機，之後才回報 ready [src: raw/project/snapshot-20261123d/live_model_worker.py#L246-L249] [src: raw/project/snapshot-20261123d/live_model_worker.py#L256]。
- **CUDA graph 加速**（model_stage.json：`cuda_graph` true）[src: raw/project/snapshot-20261123d/model_stage.json#key=cuda_graph]：對固定輸入形狀 360×640×3 錄一次 CUDA graph（把整串 GPU 運算錄成一張圖，之後每格只要重播一次，省去逐個核心的 CPU 啟動成本）；前處理與後處理以等值的複製實作；啟動時以合成影像和原本的 `model.predict()` 逐位比對，有差異就自動退回原路徑 [src: raw/project/snapshot-20261123d/model_stage.py#L1-L25]。註解記錄 11-17 Orin 診斷：模型階段是 CPU 瓶頸（主執行緒 0.93 CPU、約 27 ms）[src: raw/project/snapshot-20261123d/model_stage.py#L14-L15]。
- 不是 TensorRT：11-03 查核明確寫「PyTorch FP32，未用 TensorRT」[src: raw/records/analyses/a1-poster-factcheck-20261103.md#L53]，海報應避免寫「TensorRT 加速」[src: raw/records/analyses/a1-poster-factcheck-20261103.md#L100]。

### 類別與資料

- 兩類：0 background、1 boundary [src: raw/project/model-yolo26-sem-v4/dataset/data.yaml#L5-L7]。
- 標註：沿白色膠帶畫多邊形，像素標為背景或邊界 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L42]。
- v4 資料：訓練 63 張、新驗證 15 張、間隔（gap）6 張、排除 0 [src: raw/project/model-yolo26-sem-v4/split_plan.json#L2-L7]；另有 10 張舊 v3 驗證集分開保留 [src: raw/project/model-yolo26-sem-v4/run_provenance.json#L3-L5]。切分是「同一路線、按時間分塊」，不是隨機相鄰幀切分，也不是獨立的泛化測試 [src: raw/project/model-yolo26-sem-v4/split_plan.json#L9]。
- 使用者選擇保留全部 84 張；其中一張未找出的影像可能有部分模糊區域未標，未標像素算背景 [src: raw/project/model-yolo26-sem-v4/quality_gate.json#L1-L7]。

### 訓練設定（v4 trial01）

| 項目 | 值 | 依據 |
|---|---|---|
| 起點 | 上一版（v3）的 best.pt，父權重 SHA256 79253ba0… | [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L3] [src: raw/project/model-yolo26-sem-v4/run_provenance.json#L2] |
| epochs／patience | 30／10 | [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L5-L7] |
| batch／imgsz | 2／640 | [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L8-L9] |
| optimizer／lr0 | AdamW／0.001 | [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L20] [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L73] |
| amp（混合精度） | false | [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L29] |
| seed／deterministic | 42／true | [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L22-L23] |
| 資料增強 | degrees 3、translate 0.05、scale 0.15、fliplr 0.5、mosaic 0、mixup 0 | [src: raw/project/model-yolo26-sem-v4/train_trial.py#L20-L21] |
| 訓練耗時 | 948.3 s | [src: raw/project/model-yolo26-sem-v4/training_summary.json#L2] |

訓練在 Orin 上、Docker 容器內進行；v3 由預訓練權重 yolo26n-sem.pt 開始，v4 由 v3 再微調 30 epoch；Ultralytics 8.4.174、torch 2.10.0 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L40-L41]。

### 辨識指標

以原始解析度、imgsz 640 FP32 評估 [src: raw/project/model-yolo26-sem-v4/run_provenance.json#L7]：

| 驗證集 | 模型 | 張數 | 邊界 IoU | Precision | Recall | Dice | 依據 |
|---|---|---|---|---|---|---|---|
| 新驗證（v4 切分） | v3 | 15 | 0.7935 | 0.8789 | 0.8908 | 0.8848 | [src: raw/project/model-yolo26-sem-v4/comparison/metrics.json#L5-L16] |
| 新驗證（v4 切分） | v4 | 15 | 0.8623 | 0.9014 | 0.9521 | 0.9261 | [src: raw/project/model-yolo26-sem-v4/comparison/metrics.json#L185-L196] |
| 舊 v3 驗證 | v3 | 10 | 0.7113 | 0.8260 | 0.8366 | 0.8313 | [src: raw/project/model-yolo26-sem-v4/comparison/metrics.json#L372-L384] |
| 舊 v3 驗證 | v4 | 10 | 0.8578 | 0.8936 | 0.9554 | 0.9235 | [src: raw/project/model-yolo26-sem-v4/comparison/metrics.json#L498-L510] |

- **限制**：metrics.json 自己註明這是「同路線開發驗證，不是獨立測試」[src: raw/project/model-yolo26-sem-v4/comparison/metrics.json#L2]。
- 訓練結束時 Ultralytics 報 mIoU 0.928、像素準確率 0.992 [src: raw/project/model-yolo26-sem-v4/training_summary.json#L4-L8]；但背景占大部分像素，這兩個數字被灌高，不適合當主要指標 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L63]。語意分割也沒有 mAP。

### 推論耗時

| 時期 | 模型階段 | 推論＋路徑 | 取像→控制採用 | 依據 |
|---|---|---|---|---|
| 11-02（e5639ab0，1129 格） | 中位 26 ms／P95 32 ms | 中位 94 ms／P95 110 ms | 中位 132 ms／P95 170 ms | [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L53-L59] |
| 11-16（7af0，2672 格） | 27 ms（P90 30） | 合計 88 ms（P90 102） | 中位 127 ms | [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L532] |
| 11-23 最終版（run-b541，2804 格） | 中位 20.2 ms／P90 23.9 ms | inference_ms 中位 57.4 ms／P90 67.5 ms（路徑 33.0／39.5 ms） | 中位 87.4 ms／P90 106.1 ms | [src: raw/records/runs/run-b541-20261123/summary.json] |

最終版一列由 `tools/stats_vision_validity.py` 自逐格紀錄 pid.jsonl（MANIFEST external 項）計算；`inference_ms` 是 worker 從讀到請求到送出控制封包的時間，因 worker 兩段流水線並行，它不等於每格間隔 [src: raw/project/snapshot-20261123d/live_model_worker.py#L132]。11-16 的紀錄指出當時每秒約 10 張的瓶頸是路徑計算而不是模型 [src: raw/records/logs/AGENTS_HISTORY_until_20261119.md#L532]。

## 公式與參數

- 邊界 IoU ＝ TP ÷ (TP + FP + FN)；Dice ＝ 2TP ÷ (2TP + FP + FN)（只算 boundary 類）。驗算（推算）：v4 新驗證集 TP 745855、FP 81557、FN 37503 → IoU ＝ 745855 ÷ 864915 ＝ 0.8623，與檔內一致 [src: raw/project/model-yolo26-sem-v4/comparison/metrics.json#L188-L192]。
- 推論輸入 imgsz 640（設計值，與訓練相同）[src: raw/project/snapshot-20261123d/live_model_worker.py#L39]；輸出遮罩 ＝（semantic_mask ＝＝ 1）[src: raw/project/snapshot-20261123d/live_model_worker.py#L40-L41]。

## 未確認

- 模型推論精度：訓練 amp false、評估 FP32 [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L29] [src: raw/project/model-yolo26-sem-v4/run_provenance.json#L7]；CUDA graph 路徑依模型的 fp16 旗標選 half 或 float [src: raw/project/snapshot-20261123d/model_stage.py#L121]，最終版該旗標的值原始資料未直接記載（11-03 時為 FP32）。
- 「v3 由 yolo26n-sem.pt 開始」只有 11-03 查核文件的轉述 [src: raw/records/analyses/a1-poster-factcheck-20261103.md#L41]，v3 的 args.yaml 未收進 raw。
- 沒有獨立測試集；遮罩品質在比賽場地其他光線、其他路段的表現未量化。

## 相關條目

- [[perception/camera-capture]]、[[path/mask-to-path]]、[[path/vision-failure-modes]]
- [[comms/timing-latency]]、[[overview]]
