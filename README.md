# 컴퓨터 비전 과제

## 목차
1. [Cartoon Rendering (만화 스타일 변환)](#1-cartoon-rendering)
2. [Camera Calibration (카메라 캘리브레이션)](#2-camera-calibration)
3. [Lens Distortion Correction (렌즈 왜곡 보정)](#3-lens-distortion-correction)

---

## 1. Cartoon Rendering

### 개요
OpenCV 이미지 처리 기법을 활용하여 일반 사진을 만화(cartoon) 스타일로 변환합니다.

### 사용 기법

| 단계 | 기법 | 역할 |
|------|------|------|
| 1 | Bilateral Filter | 엣지를 보존하면서 색상 평탄화 |
| 2 | Median Blur | 노이즈 제거 |
| 3 | Adaptive Thresholding | 윤곽선(엣지) 마스크 생성 |
| 4 | Morphological Closing | 엣지 끊김 정리 |
| 5 | bitwise_and | 윤곽선 + 색상 이미지 합성 |

### 파이프라인
```
원본 이미지
  ├─ [1] Bilateral Filter        → 색상 평탄화
  ├─ [2] Grayscale + Median Blur → 노이즈 제거
  ├─ [3] Adaptive Thresholding   → 윤곽선 마스크
  ├─ [4] Morphological Closing   → 엣지 정리
  └─ [5] bitwise_and 합성        → 만화 결과
```

### 사용법
```bash
python Cartoon_Rendering_KHJ.py [이미지 경로]
```

### 데모 — 잘 표현되는 이미지
**특징:** 윤곽이 뚜렷하고 배경이 단순한 이미지

| 원본 | 만화 변환 |
|------|-----------|
| ![원본](Saved/good_example.png) | ![만화](Saved/good_example_cartoon.png) |

- 건물, 간판 등 **색상 경계가 명확한** 이미지에서 만화 느낌이 잘 나옴

### 데모 — 잘 표현되지 않는 이미지
**특징:** 세밀한 텍스처가 많은 이미지

| 원본 | 만화 변환 |
|------|-----------|
| ![원본](Saved/bad_example.png) | ![만화](Saved/bad_example_cartoon.png) |

- 풀밭, 머리카락 등 **반복 텍스처** 영역에서 엣지가 과도하게 검출됨

### 한계점
1. **고정 파라미터** — `blockSize=9`, `C=5` 등이 모든 이미지에 동일하게 적용되어, 밝기/대비에 따라 결과 품질 차이가 큼
2. **텍스처 처리 한계** — 풀밭, 머리카락 같은 세밀한 텍스처에서 과도한 엣지가 생성되어 노이즈처럼 보임
3. **색상 단순화 부족** — Bilateral Filter 1회만 적용하여 색상이 충분히 평탄화되지 않을 수 있음
4. **처리 속도** — Bilateral Filter는 계산량이 많아 고해상도 이미지에서 느릴 수 있음
5. **의미론적 이해 부재** — 얼굴/배경 등 객체를 구분하지 못하고 모든 영역에 동일한 필터가 적용됨

---

## 2. Camera Calibration

### 개요
A4 용지에 출력한 체스보드 패턴을 다양한 각도에서 촬영한 동영상을 이용하여 카메라 내부 파라미터를 추정합니다.

### 사용 기법

| 단계 | 함수 | 역할 |
|------|------|------|
| 1 | `findChessboardCorners` | 체스보드 코너 검출 |
| 2 | `cornerSubPix` | 서브픽셀 정밀도 보정 |
| 3 | `calibrateCamera` | 카메라 행렬 + 왜곡 계수 추정 |

### 사용법
```bash
python Camera_Calibration.py
```
- 입력: `data/chessboard.avi` (체스보드 동영상)
- 출력: `Saved/calibration_result.png` (결과 이미지), `Saved/calibration_result.npz`

### 캘리브레이션 결과

![캘리브레이션 결과](Saved/calibration_result.png)

| 파라미터 | 설명 |
|----------|------|
| fx, fy | 초점 거리 (focal length, pixel 단위) |
| cx, cy | 주점 (principal point) |
| k1, k2, k3 | 방사 왜곡 계수 (radial distortion) |
| p1, p2 | 접선 왜곡 계수 (tangential distortion) |
| RMSE | 재투영 오차 (낮을수록 정확) |

### 촬영 시 주의사항
1. 체스보드는 **평평한 면에 부착** (구부러지면 3D 좌표 오류)
2. 촬영 중 **카메라/보드 정지** (모션 블러 방지)
3. **10장 이상**, 다양한 각도와 위치에서 촬영
4. 체스보드가 **화면의 큰 비율**을 차지하도록
5. 카메라와 보드가 **완전히 평행한 각도만 피할 것**

---

## 3. Lens Distortion Correction

### 개요
Camera Calibration에서 구한 카메라 행렬과 왜곡 계수를 이용하여 렌즈 왜곡을 보정합니다.

### 사용 기법

| 함수 | 역할 |
|------|------|
| `getOptimalNewCameraMatrix` | 보정 후 최적 카메라 행렬 계산 |
| `undistort` | 이미지 왜곡 보정 |
| `initUndistortRectifyMap` + `remap` | 동영상 왜곡 보정 (속도 최적화) |

### 사용법
```bash
# 이미지 왜곡 보정
python Distortion_Correction.py test_photo.jpg

# 동영상 왜곡 보정
python Distortion_Correction.py data/chessboard.avi
```
- 출력: `Saved/{파일명}_undistorted.png` 또는 `Saved/{파일명}_undistorted.avi`

### 왜곡 보정 데모

| 보정 전 (Original) | 보정 후 (Undistorted) |
|---------------------|----------------------|
| ![보정 전](Saved/distortion_before.png) | ![보정 후](Saved/distortion_after.png) |

---

## 파일 구조
```
├── Cartoon_Rendering_KHJ.py   # 만화 스타일 변환
├── Camera_Calibration.py      # 카메라 캘리브레이션
├── Distortion_Correction.py   # 렌즈 왜곡 보정
├── README.md                  # 본 문서
├── data/
│   └── chessboard.avi         # 체스보드 촬영 동영상
└── Saved/                     # 결과 저장 폴더
    ├── calibration_result.png # 캘리브레이션 결과 이미지
    ├── calibration_result.npz # 캘리브레이션 데이터
    ├── good_example.png       # 만화 변환 잘 되는 원본
    ├── good_example_cartoon.png
    ├── bad_example.png        # 만화 변환 안 되는 원본
    ├── bad_example_cartoon.png
    ├── distortion_before.png  # 왜곡 보정 전
    └── distortion_after.png   # 왜곡 보정 후
```
