---
id: sources/ultralytics-semantic-segmentation
title: Ultralytics YOLO 語意分割官方文件（tasks/semantic、tasks/segment）
status: implemented
sources:
  - raw/official/ultralytics-docs-tasks-semantic.html
  - raw/official/ultralytics-docs-tasks-semantic.txt
  - raw/official/ultralytics-docs-tasks-segment.txt
  - raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

這份 Ultralytics 官方文件說明「語意分割」：模型替影像中每個像素標一個類別。本車的 YOLO26 白線模型就是這種任務。 [src: raw/official/ultralytics-docs-tasks-semantic.txt#L42-L44] [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L1]

## 內容

- **書目**：Ultralytics，〈Semantic Segmentation with Ultralytics YOLO〉，網址 https://docs.ultralytics.com/tasks/semantic/。線上文件沒有版本號，以擷取日 2026-11-23 為準 [src: raw/official/ultralytics-docs-tasks-semantic.html]。
- **完整性**：HTML 完整下載，另轉出純文字檔，方便用行號引用 [src: raw/official/ultralytics-docs-tasks-semantic.txt]。
- **重點**：
  - 語意分割替每個像素標類別，輸出一張「高×寬」的類別圖。它和實例分割（instance segmentation）不同：實例分割要把每個物體個別分開 [src: raw/official/ultralytics-docs-tasks-semantic.txt#L42-L44]。
  - YOLO26 的語意分割模型檔名帶 `-sem` 字尾，例如 yolo26n-sem.pt [src: raw/official/ultralytics-docs-tasks-semantic.txt#L48-L49]。
- **與本車的關係（確實採用）**：本車模型的訓練設定，任務欄位就是 `semantic` [src: raw/project/model-yolo26-sem-v4/runs/trial01/args.yaml#L1]。分類只有背景與白線邊界兩類，見 [[perception/yolo26-sem]]。
- **另存的 tasks/segment 頁**：那一頁講實例分割 [src: raw/official/ultralytics-docs-tasks-segment.txt]。本車沒有部署實例分割，這頁只拿來對照。

## 公式與參數

無。

## 未確認

- 文件中的預訓練模型是用 Cityscapes 資料集訓練的 [src: raw/official/ultralytics-docs-tasks-semantic.txt#L52]。本車的模型是自行標註後再微調，所以文件裡的指標不能當成本車的成績。

## 相關條目

- [[perception/yolo26-sem]]
- [[sources/ultralytics-jetson-guide]]
