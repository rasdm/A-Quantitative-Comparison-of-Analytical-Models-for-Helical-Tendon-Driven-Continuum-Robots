import cv2
import depthai as dai
import os

SAVE_DIR = "calibration_images"
xpixels = 840
ypixels = 600

# Making folder
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Pipeline Setup
pipeline = dai.Pipeline()

camLeft = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
camRight = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)

leftOut = camLeft.requestOutput((xpixels, ypixels), type=dai.ImgFrame.Type.GRAY8)
rightOut = camRight.requestOutput((xpixels, ypixels), type=dai.ImgFrame.Type.GRAY8)

qLeft = leftOut.createOutputQueue(maxSize=4, blocking=False)
qRight = rightOut.createOutputQueue(maxSize=4, blocking=False)

pipeline.start()
print("Press s to save photo pair, q to quit")

img_count = 0

try:
    while pipeline.isRunning():
        fLeft = qLeft.get()
        fRight = qRight.get()

        if fLeft is not None and fRight is not None:
            imgL = fLeft.getCvFrame()
            imgR = fRight.getCvFrame()

            # Vis billederne side om side
            combined = cv2.hconcat([imgL, imgR])
            cv2.imshow("Collecting for Stereo calibrering", combined)

            key = cv2.waitKey(1)
            if key == ord('q'):
                break
            elif key == ord('s'):
                left_path = os.path.join(SAVE_DIR, f"left_{img_count:02d}.png")
                right_path = os.path.join(SAVE_DIR, f"right_{img_count:02d}.png")
                cv2.imwrite(left_path, imgL)
                cv2.imwrite(right_path, imgR)
                print(f"Gemt billedpar {img_count}")
                img_count += 1

except Exception as e:
    print(f"Error: {e}")
finally:
    cv2.destroyAllWindows()
    print(f"Datacollection finished. {img_count} Photo pairs.")