import numpy as np
import pandas as pd
import cv2
import matplotlib.pyplot as plt
import os

baseline=72.99
BackboneL=250
camera_thickness=23
hole_offset=21
cameraGlass_thickness=1
height=375.5-(camera_thickness-cameraGlass_thickness)

# Loding calibration data
try:
    calib = np.load(r'ImageDetection\stereo_params.npz')
    mtxL, distL = calib['mtxL'], calib['distL']
    mtxR, distR = calib['mtxR'], calib['distR']
    R, T = calib['R'], calib['T']
    RMS = calib['RMS']
except FileNotFoundError:
    exit()

# Contruct projection matrices (P1=origo, P2=displaced)
RT_L = np.hstack((np.eye(3), np.zeros((3, 1))))
P1 = mtxL @ RT_L

RT_R = np.hstack((R, T))
P2 = mtxR @ RT_R

# Triangulation
def triangulate_3D_point(Lx, Ly, Rx, Ry):
    # Convert pixels to mm with sub-pixel and lence korrection
    # OpenCV arrays
    pixel_L = np.array([[[Lx, Ly]]], dtype=np.float32)
    pixel_R = np.array([[[Rx, Ry]]], dtype=np.float32)
    
    # Undistort
    pts_L_undist = cv2.undistortPoints(pixel_L, mtxL, distL, P=mtxL)
    pts_R_undist = cv2.undistortPoints(pixel_R, mtxR, distR, P=mtxR)
    
    # Triangulation
    pts_4D = cv2.triangulatePoints(P1, P2, pts_L_undist, pts_R_undist)
    
    # From homogene to cartesian coordinates
    pts_3D = pts_4D[:3, :] / pts_4D[3, :]
    return pts_3D.flatten() # [X, Y, Z] in mm

# Data analysis
def main():
    # Median of Soft robot results
    excel_file = r"ImageDetection\MedianResults.xlsx"
    
    try:
        df = pd.read_excel(excel_file, header=None)
        # Rename column headers
        df.columns = ['Lx2', 'Ly2', 'Lx1', 'Ly1', 'Rx2', 'Ry2', 'Rx1', 'Ry1']
    except FileNotFoundError:
        return

    results_3D = []

    for index, row in df.iterrows():
        # Check for NaN in P1
        if pd.notna(row['Lx1']) and pd.notna(row['Rx1']):
            pos1_3D = triangulate_3D_point(row['Lx1'], row['Ly1'], row['Rx1'], row['Ry1'])
        else:
            pos1_3D = [np.nan, np.nan, np.nan]

        # Check for NaN in P2
        if pd.notna(row['Lx2']) and pd.notna(row['Rx2']):
            pos2_3D = triangulate_3D_point(row['Lx2'], row['Ly2'], row['Rx2'], row['Ry2'])
        else:
            pos2_3D = [np.nan, np.nan, np.nan]

        results_3D.append({
            'P1_X': pos1_3D[0], 'P1_Y': pos1_3D[1], 'P1_Z': pos1_3D[2],
            'P2_X': pos2_3D[0], 'P2_Y': pos2_3D[1], 'P2_Z': pos2_3D[2]
        })

    # Convert to dataframe and exclude empty cells
    df_3D = pd.DataFrame(results_3D)
    df_3D = df_3D.dropna().reset_index(drop=True) 

    # Calibration length error
    focal_avg=(mtxL[0,0]+mtxR[0,0])/2
    xy_error=df_3D['P1_Z']*RMS/focal_avg
    z_error=(df_3D['P1_Z'])^2*RMS/(baseline*focal_avg)
    print(f"xy_error: {xy_error:.4f}mm\n")
    print(f"z_error: {z_error:.4f}mm")


    # Going from left camera frame to absoulte frame
    df_3D['P1_X'] = df_3D['P1_X']-baseline/2
    df_3D['P2_X'] = df_3D['P2_X']-baseline/2
    df_3D['P1_Z'] = height-df_3D['P1_Z']
    df_3D['P2_Z'] = height-df_3D['P2_Z']
    
    # Exporting deformations to excel
    origin = df_3D.iloc[0] # Initial pos

    # Deformation for P1
    df_3D['P1_dX'] = df_3D['P1_X'] - origin['P1_X']
    df_3D['P1_dY'] = df_3D['P1_Y'] - origin['P1_Y']
    df_3D['P1_dZ'] = df_3D['P1_Z'] - origin['P1_Z']
    df_3D['P1_AbsDef'] = np.sqrt(df_3D['P1_dX']**2 + df_3D['P1_dY']**2 + df_3D['P1_dZ']**2)

    # Deformation for P2
    df_3D['P2_dX'] = df_3D['P2_X'] - origin['P2_X']
    df_3D['P2_dY'] = df_3D['P2_Y'] - origin['P2_Y']
    df_3D['P2_dZ'] = df_3D['P2_Z'] - origin['P2_Z']
    df_3D['P2_AbsDef'] = np.sqrt(df_3D['P2_dX']**2 + df_3D['P2_dY']**2 + df_3D['P2_dZ']**2)

    export_file = "3D_Kinematics_Processed.xlsx"
    try:
        df_3D.to_excel(export_file, index=False)
        print(f"SUCCES: Data saved '{export_file}' with {len(df_3D)} rows.")
    except PermissionError:
        print(f"Error: Couldn't save'{export_file}'")

    # Plot functions
    plot_deformation(df_3D)
    plot_distance_p1_p2(df_3D)
    plot_3d_trajectory(df_3D)

def plot_deformation(df_3D):
    # Opsætning af 2x2 subplot grid
    fig, axs = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('Kinematic deformations (3D Triangulation)', fontsize=16)

    # Subplot: X-Deformation
    axs[0, 0].plot(df_3D.index, - df_3D['P1_dX'], label=r'$\Delta X$ P1', color='blue', linestyle='--')
    axs[0, 0].plot(df_3D.index, -df_3D['P2_dX'], label=r'$\Delta X$ P2', color='red')
    axs[0, 0].set_title('X-deformations')
    axs[0, 0].set_ylabel('Deformation (mm)')
    axs[0, 0].grid(True)
    axs[0, 0].legend()

    # Subplot: Y-Deformation
    axs[0, 1].plot(df_3D.index, df_3D['P1_dY'], label=r'$\Delta Y$ P1', color='blue', linestyle='--')
    axs[0, 1].plot(df_3D.index, df_3D['P2_dY'], label=r'$\Delta Y$ P2', color='red')
    axs[0, 1].set_title('Y-akse Deformation')
    axs[0, 1].set_ylabel('Y Deformation (mm)')
    axs[0, 1].grid(True)
    axs[0, 1].legend()

    # Subplot: Z-Deformation
    axs[1, 0].plot(df_3D.index, -df_3D['P1_dZ'], label=r'$\Delta Z$ P1', color='blue', linestyle='--')
    axs[1, 0].plot(df_3D.index, -df_3D['P2_dZ'], label=r'$\Delta Z$ P2', color='red')
    axs[1, 0].set_title('Z Deformation')
    axs[1, 0].set_xlabel('Sample index (Time)')
    axs[1, 0].set_ylabel('Deformation (mm)')
    axs[1, 0].grid(True)
    axs[1, 0].legend()

    # Subplot: Absolut Deformation
    axs[1, 1].plot(df_3D.index, df_3D['P1_AbsDef'], label='Absolut Bevægelse P1', color='blue', linestyle='--')
    axs[1, 1].plot(df_3D.index, df_3D['P2_AbsDef'], label='Absolut Bevægelse P2', color='red')
    axs[1, 1].set_title('Absolute Deformation')
    axs[1, 1].set_xlabel('Sample index (time)')
    axs[1, 1].set_ylabel('Distance from origo (mm)')
    axs[1, 1].grid(True)
    axs[1, 1].legend()

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Giver plads til suptitle
    plt.show()

def plot_distance_p1_p2(df_3D):
    dist_P1_P2 = np.sqrt(
        (df_3D['P2_X'] - df_3D['P1_X'])**2 + 
        (df_3D['P2_Y'] - df_3D['P1_Y'])**2 + 
        (df_3D['P2_Z'] - df_3D['P1_Z'])**2
    )

    # Mean values for noise evaluation
    mean_dist = dist_P1_P2.mean()
    std_dist = dist_P1_P2.std()

    plt.figure(figsize=(10, 5))
    plt.plot(df_3D.index, dist_P1_P2, color='purple', label='Afstand P1 $\\leftrightarrow$ P2')
    
    # Plot meanline
    plt.axhline(y=mean_dist, color='black', linestyle='--', alpha=0.7, 
                label=f'Gennemsnit: {mean_dist:.2f} mm ($\sigma$: {std_dist:.2f} mm)')

    plt.title('Distance between targets')
    plt.xlabel('Sample index (time)')
    plt.ylabel('Distance (mm)')
    
    # Scale Y-axis
    y_min, y_max = plt.ylim()
    plt.ylim(mean_dist - 10, mean_dist + 10) 
    
    plt.grid(True)
    plt.legend()
    plt.show()

def plot_3d_trajectory(df_3D):
    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(111, projection='3d')

    ax.scatter(df_3D['P1_X'], df_3D['P1_Z'], df_3D['P1_Y'], 
               c='blue', marker='o', label='P1 Trajektorie', alpha=0.6)
    
    ax.scatter(df_3D['P2_X'], df_3D['P2_Z'], df_3D['P2_Y'], 
               c='red', marker='^', label='P2 Trajektorie', alpha=0.6)

    # Startpunkterne (hvilepositionen) fremhæves med grøn
    ax.scatter(df_3D['P1_X'].iloc[0], df_3D['P1_Z'].iloc[0], df_3D['P1_Y'].iloc[0], c='green', s=100, label='Start P1')
    ax.scatter(df_3D['P2_X'].iloc[0], df_3D['P2_Z'].iloc[0], df_3D['P2_Y'].iloc[0], c='green', s=100, label='Start P2')

    ax.set_xlabel('X axis (mm)')
    ax.set_ylabel('Z axis (mm)')
    ax.set_zlabel('Y axis (mm)')
    ax.set_title('3D kinematic trajectory')
    ax.legend()
    plt.show()

if __name__ == "__main__":
    main()