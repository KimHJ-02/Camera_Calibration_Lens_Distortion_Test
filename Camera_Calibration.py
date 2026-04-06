import cv2 as cv
import numpy as np
import os

# ============================================================
# Camera Calibration using Chessboard Pattern
# ============================================================

# --- 체스보드 설정 ---
# 체스보드 내부 코너 수 (가로 x 세로)
# 예: 9x7 체스보드이면 내부 코너는 8x6
BOARD_W = 8
BOARD_H = 6
SQUARE_SIZE = 35.0  # 체스보드 한 칸의 실제 크기 (mm)

# --- 입력 설정 ---
# 동영상 파일 경로 (체스보드를 다양한 각도로 촬영한 영상)
VIDEO_PATH = "data/chessboard.avi"
# 또는 이미지 폴더 사용 시:
# IMAGE_DIR = "data/chessboard_images/*.jpg"

# --- 3D 월드 좌표 생성 (체스보드는 z=0 평면) ---
objp = np.zeros((BOARD_H * BOARD_W, 3), np.float32)
objp[:, :2] = np.mgrid[0:BOARD_W, 0:BOARD_H].T.reshape(-1, 2)
objp *= SQUARE_SIZE  # 실제 크기 반영

# 모든 이미지의 3D/2D 포인트 저장 리스트
obj_points = []  # 3D 월드 좌표
img_points = []  # 2D 이미지 좌표

# --- 동영상에서 프레임 추출하며 코너 검출 ---
cap = cv.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"Error: '{VIDEO_PATH}' 파일을 열 수 없습니다.")
    exit(1)

frame_count = 0
used_count = 0
FRAME_INTERVAL = 15  # 매 N 프레임마다 검출 시도 (너무 비슷한 프레임 방지)

print(f"동영상 로드: {VIDEO_PATH}")
print(f"체스보드 코너: {BOARD_W}x{BOARD_H}, 칸 크기: {SQUARE_SIZE}mm")
print("코너 검출 중...")

while True:
    ret, frame = cap.read()
    if not ret:
        break

    frame_count += 1

    # 일정 간격으로만 검출 시도
    if frame_count % FRAME_INTERVAL != 0:
        continue

    gray = cv.cvtColor(frame, cv.COLOR_BGR2GRAY)

    # 체스보드 코너 검출
    found, corners = cv.findChessboardCorners(gray, (BOARD_W, BOARD_H), None)

    if found:
        # 서브픽셀 정밀도로 코너 위치 보정
        criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)
        corners = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)

        obj_points.append(objp)
        img_points.append(corners)
        used_count += 1

        # 코너 검출 결과 표시
        cv.drawChessboardCorners(frame, (BOARD_W, BOARD_H), corners, found)
        cv.putText(frame, f"Detected ({used_count})", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
    else:
        cv.putText(frame, "Not detected", (10, 30),
                   cv.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    cv.imshow("Chessboard Detection", frame)
    if cv.waitKey(1) == 27:  # ESC 종료
        break

cap.release()
cv.destroyAllWindows()

img_size = (gray.shape[1], gray.shape[0])  # (width, height)

print(f"\n총 프레임: {frame_count}, 검출 성공: {used_count}장")

if used_count < 3:
    print("Error: 최소 3장 이상의 검출 결과가 필요합니다.")
    exit(1)

# --- 카메라 캘리브레이션 ---
print("\n캘리브레이션 수행 중...")
ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv.calibrateCamera(
    obj_points, img_points, img_size, None, None
)

# --- 결과 출력 ---
fx = camera_matrix[0, 0]
fy = camera_matrix[1, 1]
cx = camera_matrix[0, 2]
cy = camera_matrix[1, 2]

print("\n===== 캘리브레이션 결과 =====")
print(f"RMSE (Re-projection Error): {ret:.4f}")
print(f"\nCamera Matrix:")
print(f"  fx = {fx:.2f}")
print(f"  fy = {fy:.2f}")
print(f"  cx = {cx:.2f}")
print(f"  cy = {cy:.2f}")
print(f"\n  Full Matrix:\n{camera_matrix}")
print(f"\nDistortion Coefficients (k1, k2, p1, p2, k3):")
print(f"  {dist_coeffs.ravel()}")

os.makedirs("Saved", exist_ok=True)

# --- 결과를 이미지로 저장 (README용) ---
k1, k2, p1, p2, k3 = dist_coeffs.ravel()
lines = [
    "===== Camera Calibration Result =====",
    "",
    f"RMSE (Re-projection Error): {ret:.4f}",
    "",
    "Camera Matrix:",
    f"  fx = {fx:.2f}",
    f"  fy = {fy:.2f}",
    f"  cx = {cx:.2f}",
    f"  cy = {cy:.2f}",
    "",
    "Distortion Coefficients:",
    f"  k1 = {k1:.6f}",
    f"  k2 = {k2:.6f}",
    f"  p1 = {p1:.6f}",
    f"  p2 = {p2:.6f}",
    f"  k3 = {k3:.6f}",
    "",
    f"Image Size: {img_size[0]} x {img_size[1]}",
    f"Used Images: {used_count}",
]

# 이미지 크기 계산
font = cv.FONT_HERSHEY_SIMPLEX
font_scale = 0.7
thickness = 2
line_height = 35
margin = 30
img_w = 500
img_h = margin + line_height * len(lines) + margin

# 흰 배경 이미지 생성
result_img = np.ones((img_h, img_w, 3), dtype=np.uint8) * 255

for i, line in enumerate(lines):
    y = margin + (i + 1) * line_height
    color = (0, 0, 200) if "RMSE" in line else (0, 0, 0)
    cv.putText(result_img, line, (margin, y), font, font_scale, color, thickness)

result_img_path = os.path.join("Saved", "calibration_result.png")
cv.imwrite(result_img_path, result_img)
print(f"\n결과 이미지 저장: {result_img_path}")

# --- 결과 저장 (NumPy - Distortion_Correction용) ---
np_path = os.path.join("Saved", "calibration_result.npz")
np.savez(np_path,
         camera_matrix=camera_matrix,
         dist_coeffs=dist_coeffs,
         rvecs=np.array(rvecs, dtype=object),
         tvecs=np.array(tvecs, dtype=object))
print(f"NumPy 저장: {np_path}")
