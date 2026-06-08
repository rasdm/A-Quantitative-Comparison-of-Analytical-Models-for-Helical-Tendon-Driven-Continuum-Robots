import cv2
import depthai as dai
import numpy as np
import pandas as pd
import time

# --- Tuning Parameters ---
WHITE_THRESHOLD = 215 
MIN_AREA = 150         
MAX_AREA = 600       
xpixels = 840
ypixels = 600

# --- Logistik Parametre ---
LOG_INTERVAL = 0.2  # Log hvert 0.2 sekund
START_DELAY = 5.0   # Vent 2 sekunder før start
data_list = []      # Liste til at gemme rækkerne i

# 1. Pipeline Setup
pipeline = dai.Pipeline()

camLeft = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_B)
camRight = pipeline.create(dai.node.Camera).build(dai.CameraBoardSocket.CAM_C)

leftOut = camLeft.requestOutput((xpixels, ypixels), type=dai.ImgFrame.Type.GRAY8)
rightOut = camRight.requestOutput((xpixels, ypixels), type=dai.ImgFrame.Type.GRAY8)

qLeft = leftOut.createOutputQueue(maxSize=4, blocking=False)
qRight = rightOut.createOutputQueue(maxSize=4, blocking=False)

def track_object(frame):
    blurred = cv2.GaussianBlur(frame, (5, 5), 0)
    _, mask = cv2.threshold(blurred, WHITE_THRESHOLD, 255, cv2.THRESH_BINARY)
    
    kernel = np.ones((3,3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    valid_cnts = [c for c in contours if MIN_AREA < cv2.contourArea(c) < MAX_AREA]
    valid_cnts = sorted(valid_cnts, key=cv2.contourArea, reverse=True)[:2]
    
    centers = []
    for c in valid_cnts:
        c_mask = np.zeros(mask.shape, dtype=np.uint8)
        cv2.drawContours(c_mask, [c], -1, 255, -1)
        dist_trans = cv2.distanceTransform(c_mask, cv2.DIST_L2, 5)
        _, _, _, maxLoc = cv2.minMaxLoc(dist_trans)
        centers.append(maxLoc)

    # VIGTIG REGEL: P1 er altid punktet med den LAVESTE Y-værdi
    # Vi sorterer centers listen baseret på index 1 (Y-koordinaten)
    centers = sorted(centers, key=lambda p: p[1]) 

    # Visualisering
    for i, (cX, cY) in enumerate(centers):
        label = f"P{i+1}"
        cv2.circle(frame, (cX, cY), 5, (255, 255, 255), -1)
        cv2.putText(frame, f"{label}: {cX},{cY}", (cX+10, cY), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)

    return frame, centers

pipeline.start()
print(f"Program startet. Venter {START_DELAY} sekunder...")

start_time = time.time()
last_log_time = 0

try:
    while pipeline.isRunning():
        fLeft = qLeft.get()
        fRight = qRight.get()
        
        current_time = time.time() - start_time

        if fLeft is not None and fRight is not None:
            imgL, posL = track_object(fLeft.getCvFrame())
            imgR, posR = track_object(fRight.getCvFrame())

            # Logik for at gemme data (hvis der er gået 2 sekunder og vi rammer intervallet)
            if current_time >= START_DELAY:
                if (current_time - last_log_time) >= LOG_INTERVAL:
                    
                    # Forbered data-række (standard er None/NaN hvis punkt ikke findes)
                    row = {
                        'Lx1': posL[0][0] if len(posL) > 0 else None,
                        'Ly1': posL[0][1] if len(posL) > 0 else None,
                        'Lx2': posL[1][0] if len(posL) > 1 else None,
                        'Ly2': posL[1][1] if len(posL) > 1 else None,
                        'Rx1': posR[0][0] if len(posR) > 0 else None,
                        'Ry1': posR[0][1] if len(posR) > 0 else None,
                        'Rx2': posR[1][0] if len(posR) > 1 else None,
                        'Ry2': posR[1][1] if len(posR) > 1 else None
                    }
                    data_list.append(row)
                    last_log_time = current_time
                    print(f"\rData logget ved {current_time:.2f}s", end="")

            # Vis billeder
            combined = np.hstack((imgL, imgR))
            cv2.imshow("Tracking (P1 = Min Y)", combined)

        if cv2.waitKey(1) == ord('q'):
            break

except Exception as e:
    print(f"\nFejl: {e}")

finally:
    # Gem til Excel
    if data_list:
        df = pd.DataFrame(data_list)
        filename = "tracking_results.xlsx"
        df.to_excel(filename, index=False)
        print(f"\nData gemt til {filename} ({len(data_list)} rækker)")
    else:
        print("\nIngen data blev opsamlet.")

    cv2.destroyAllWindows()
    print("Cleanup complete.")