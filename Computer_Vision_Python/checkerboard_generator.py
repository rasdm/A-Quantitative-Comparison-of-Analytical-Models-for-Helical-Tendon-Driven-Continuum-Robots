import numpy as np
import cv2

# --- iPhone 13 Specifikationer ---
# Skærmopløsning i landscape
screen_width = 2532
screen_height = 1170
ppi = 460  # Pixels per inch
px_per_mm = ppi / 25.4

# --- Skakbræt Design ---
# Vi designer for 5.5 mm for at det passer på telefonens fysiske bredde
target_square_size_mm = 5.5
square_size_px = int(round(target_square_size_mm * px_per_mm)) # Ca. 100 pixels pr kvadrat

cols = 10
rows = 7

# Opret et rent hvidt billede der matcher skærmens opløsning
board = np.ones((screen_height, screen_width), dtype=np.uint8) * 255

# Beregn offset for at centrere skakbrættet præcist
board_w = cols * square_size_px
board_h = rows * square_size_px
x_offset = (screen_width - board_w) // 2
y_offset = (screen_height - board_h) // 2

# Tegn de sorte kvadrater
for r in range(rows):
    for c in range(cols):
        if (r + c) % 2 == 0:  # Skiftende sort/hvid
            start_x = x_offset + c * square_size_px
            start_y = y_offset + r * square_size_px
            # Sæt farven til sort (0)
            board[start_y:start_y + square_size_px, start_x:start_x + square_size_px] = 0

# Gem billedet
filename = "iphone13_calibration_board.png"
cv2.imwrite(filename, board)

print("--- SKAKBRÆT GENERERET ---")
print(f"Fil gemt som: {filename}")
print(f"Opløsning: {screen_width}x{screen_height} (Passer til iPhone 13 skærm)")
print(f"Forventet kvadratstørrelse: {target_square_size_mm} mm ({square_size_px} pixels pr. kvadrat)")
print("Indre hjørner til kalibreringsscriptet: CHESSBOARD_SIZE = (9, 6)")