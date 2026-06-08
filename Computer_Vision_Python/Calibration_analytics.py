import cv2
import numpy as np
import os
import glob

# Calibaration parameters
# Inner corners on calibration tool, (horizontal,vertical)
CHESSBOARD_SIZE = (9, 6) 
SQUARE_SIZE_MM = 5.5  #mm
IMAGE_DIR = "calibration_images"

# Stopcriteria for aub-pixel algorithm
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Prepare for real 3D points
objp = np.zeros((CHESSBOARD_SIZE[0] * CHESSBOARD_SIZE[1], 3), np.float32)
objp[:, :2] = np.mgrid[0:CHESSBOARD_SIZE[0], 0:CHESSBOARD_SIZE[1]].T.reshape(-1, 2)
objp = objp * SQUARE_SIZE_MM
objpoints = [] 
imgpoints_left = []
imgpoints_right = []

# Get calibration photos
left_images = sorted(glob.glob(os.path.join(IMAGE_DIR, 'left_*.png')))
right_images = sorted(glob.glob(os.path.join(IMAGE_DIR, 'right_*.png')))

# Start calibration
valid_pairs = 0
image_size = None

for left_path, right_path in zip(left_images, right_images):
    imgL = cv2.imread(left_path, cv2.IMREAD_GRAYSCALE)
    imgR = cv2.imread(right_path, cv2.IMREAD_GRAYSCALE)
    
    if image_size is None:
        image_size = imgL.shape[::-1] # (bredde, højde)

    # Finding corners
    retL, cornersL = cv2.findChessboardCorners(imgL, CHESSBOARD_SIZE, None)
    retR, cornersR = cv2.findChessboardCorners(imgR, CHESSBOARD_SIZE, None)

    if retL and retR:
        # Sub-pixel improovements
        corners2L = cv2.cornerSubPix(imgL, cornersL, (11, 11), (-1, -1), criteria)
        corners2R = cv2.cornerSubPix(imgR, cornersR, (11, 11), (-1, -1), criteria)

        objpoints.append(objp)
        imgpoints_left.append(corners2L)
        imgpoints_right.append(corners2R)
        valid_pairs += 1
    else:
        print(f"Could't find chessboard corners in {left_path} or {right_path}.")

print(f"\n Working pairs {valid_pairs} out of {len(left_images)}")

# Calibrating each camera by themselves
#retL: (Return value / RMS), mtxL: (Matrix Left),distL: (Distortion Coefficients),rvecsL: (Rotation Vectors),
#tvecsL: (Translation Vectors)
retL, mtxL, distL, rvecsL, tvecsL = cv2.calibrateCamera(objpoints, imgpoints_left, image_size, None, None)
retR, mtxR, distR, rvecsR, tvecsR = cv2.calibrateCamera(objpoints, imgpoints_right, image_size, None, None)
print(f"retL: {retL}, retR: {retR}")
print(f"mtxL: {mtxL}, mtxR: {mtxR}")
print(f"distL: {distL}, distR: {distR}")
print(f"rvecsL: {rvecsL}, rvecsR: {rvecsR}")
print(f"tvecsL: {tvecsL}, tvecsR: {tvecsR}")

# Stereo calibration
flags = cv2.CALIB_FIX_INTRINSIC # Trusting the calculation of the matrices calculations from above
retStereo, new_mtxL, distL, new_mtxR, distR, R, T, E, F = cv2.stereoCalibrate(
    objpoints, imgpoints_left, imgpoints_right, 
    mtxL, distL, mtxR, distR, 
    image_size, criteria=criteria, flags=flags)

print("\n--- Calibration results ---")
print(f"Reprojection Error (RMS): {retStereo:.4f} pixels")

# # Save Matrices
# np.savez("stereo_params.npz", mtxL=new_mtxL, distL=distL, mtxR=new_mtxR, distR=distR, R=R, T=T, RMS=retStereo)