---
id: sources/opencv-homography
title: OpenCV 單應性（Homography）官方教學
status: mixed
sources:
  - raw/official/opencv-4.13.0-tutorial-homography.html
  - raw/official/opencv-4.13.0-tutorial-homography.txt
  - raw/project/snapshot-20261123d/ground_road.py
verified_against: snapshot-20261123d
updated: 2026-11-23
---

## 一句話結論

單應性（homography）是一個 3×3 矩陣，描述兩個平面之間的點怎麼互相對應。本車用它把相機的像素位置換算成地面座標，也就是「地面標定」。 [src: raw/official/opencv-4.13.0-tutorial-homography.txt#L36-L60] [src: raw/project/snapshot-20261123d/ground_road.py#L91]

## 內容

- **書目**：OpenCV，〈Basic concepts of the homography explained with code〉，OpenCV 4.13.0 文件（從 4.x 網址轉到這一版），2026-11-23 擷取 [src: raw/official/opencv-4.13.0-tutorial-homography.html]。
- **重點**：
  - 平面單應性描述兩個平面之間的轉換，最多差一個比例因子 [src: raw/official/opencv-4.13.0-tutorial-homography.txt#L36]。
  - 單應性矩陣是 3×3 [src: raw/official/opencv-4.13.0-tutorial-homography.txt#L60]。
  - 一個典型例子是「平面物體」與「影像平面」之間的對應 [src: raw/official/opencv-4.13.0-tutorial-homography.txt#L62-L63]。
  - 可以用直接線性轉換（DLT）從多組對應點估算 [src: raw/official/opencv-4.13.0-tutorial-homography.txt#L73]。
- **與本車的關係**：
  - 【現役】專案的地面模組用 `cv2.findHomography`，把像素點對到地面點 [src: raw/project/snapshot-20261123d/ground_road.py#L91]。
  - 最終版哪些層真的用到地面標定、哪些標定檔已經不作用，見 [[path/mask-to-path]]。主線路徑的左右線配對寬度，用的是影像中逐列擬合的結果，不是單應性。

## 公式與參數

- 齊次座標下：s·[x′, y′, 1]ᵀ＝H·[x, y, 1]ᵀ。H 是 3×3 矩陣，s 是比例因子 [src: raw/official/opencv-4.13.0-tutorial-homography.txt#L36-L60]。這是文件中的定義，不是本車的參數。

## 未確認

- 單應性假設地面是一個平面，這在坡道上不成立。坡道段換算出的地面座標誤差有多大，沒有量化過。

## 相關條目

- [[path/mask-to-path]]
- [[path/vision-failure-modes]]
