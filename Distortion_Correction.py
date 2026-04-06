import cv2 as cv
import numpy as np
import sys
import os

# ============================================================
# Lens Distortion Correction
# 캘리브레이션 결과를 이용한 렌즈 왜곡 보정
# ============================================================

# --- 캘리브레이션 결과 불러오기 ---
calib_path = os.path.join("Saved", "calibration_result.npz")
if not os.path.exists(calib_path):
    print(f"Error: '{calib_path}' 파일을 찾을 수 없습니다.")
    print("먼저 Camera_Calibration.py를 실행하세요.")
    sys.exit(1)

data = np.load(calib_path, allow_pickle=True)
camera_matrix = data["camera_matrix"]
dist_coeffs = data["dist_coeffs"]

print("캘리브레이션 데이터 로드 완료")
print(f"Camera Matrix:\n{camera_matrix}")
print(f"Distortion Coefficients: {dist_coeffs.ravel()}")

# --- 입력 (이미지 또는 동영상) ---
input_path = sys.argv[1] if len(sys.argv) > 1 else "data/chessboard.avi"

if not os.path.exists(input_path):
    print(f"Error: '{input_path}' 파일을 찾을 수 없습니다.")
    sys.exit(1)

os.makedirs("Saved", exist_ok=True)

# 이미지 파일인지 동영상인지 판별
img_ext = (".jpg", ".jpeg", ".png", ".bmp", ".tif")
is_image = input_path.lower().endswith(img_ext)

if is_image:
    # --- 이미지 왜곡 보정 ---
    img = cv.imread(input_path)
    if img is None:
        print(f"Error: 이미지를 읽을 수 없습니다.")
        sys.exit(1)

    h, w = img.shape[:2]

    # 최적 카메라 매트릭스 (왜곡 보정 후 잘리는 영역 조절)
    new_matrix, roi = cv.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, (w, h), 1, (w, h)
    )

    # 왜곡 보정
    undistorted = cv.undistort(img, camera_matrix, dist_coeffs, None, new_matrix)

    # ROI로 크롭 (검은 테두리 제거)
    x, y, rw, rh = roi
    if rw > 0 and rh > 0:
        undistorted = undistorted[y:y+rh, x:x+rw]

    # 결과 저장
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join("Saved", f"{base_name}_undistorted.png")
    cv.imwrite(out_path, undistorted)
    print(f"결과 저장: {out_path}")

    # 비교 표시
    cv.imshow("Original", img)
    cv.imshow("Undistorted", undistorted)
    cv.waitKey(0)
    cv.destroyAllWindows()

else:
    # --- 동영상 왜곡 보정 ---
    cap = cv.VideoCapture(input_path)
    if not cap.isOpened():
        print(f"Error: 동영상을 열 수 없습니다.")
        sys.exit(1)

    w = int(cap.get(cv.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv.CAP_PROP_FPS) or 30

    # 최적 카메라 매트릭스
    new_matrix, roi = cv.getOptimalNewCameraMatrix(
        camera_matrix, dist_coeffs, (w, h), 1, (w, h)
    )

    # undistort용 맵 미리 계산 (속도 향상)
    mapx, mapy = cv.initUndistortRectifyMap(
        camera_matrix, dist_coeffs, None, new_matrix, (w, h), cv.CV_32FC1
    )

    # 결과 동영상 저장
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    out_path = os.path.join("Saved", f"{base_name}_undistorted.avi")
    fourcc = cv.VideoWriter_fourcc(*"XVID")
    out = cv.VideoWriter(out_path, fourcc, fps, (w, h))

    print(f"동영상 왜곡 보정 중... ({w}x{h} @ {fps:.0f}fps)")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # remap으로 왜곡 보정 (undistort보다 빠름)
        undistorted = cv.remap(frame, mapx, mapy, cv.INTER_LINEAR)
        out.write(undistorted)

        # 원본/보정 나란히 표시
        combined = np.hstack([frame, undistorted])
        combined = cv.resize(combined, (0, 0), fx=0.5, fy=0.5)
        cv.putText(combined, "Original", (10, 25),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        cv.putText(combined, "Undistorted", (combined.shape[1]//2 + 10, 25),
                   cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        cv.imshow("Distortion Correction", combined)

        if cv.waitKey(1) == 27:
            break

    cap.release()
    out.release()
    cv.destroyAllWindows()
    print(f"결과 저장: {out_path}")
