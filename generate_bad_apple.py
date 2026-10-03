import cv2
from PIL import Image
import math
import os
import sys

# ==========================================
# MAX QUALITY CONFIGURATION
# ==========================================
VIDEO_FILE = 'bad_apple.mp4'
AUDIO_FILE = 'bad_apple.mp3'
OUTPUT_HTML = 'index.html'
OUTPUT_SPRITE = 'spritesheet.webp'

TARGET_FPS = 30        # Full 30 FPS for buttery smooth motion
FRAME_W = 160          # 2x Width
FRAME_H = 120          # 2x Height
COLS = 100             # GRID MAXED: 100 cols * 160px = 16,000px width (WebP limit is 16383px)
SCALE = 6              # Outputs a massive 960x720 video player in the browser

def main():
    if not os.path.exists(VIDEO_FILE):
        print(f"Error: {VIDEO_FILE} not found!")
        sys.exit(1)

    print("Step 1: Extracting frames at 30 FPS... (This will take a moment)")
    cap = cv2.VideoCapture(VIDEO_FILE)
    orig_fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    video_duration = total_frames / orig_fps

    target_total_frames = int(video_duration * TARGET_FPS)
    frames_to_extract = [int((i / TARGET_FPS) * orig_fps) for i in range(target_total_frames)]
    
    extracted_images = []
    current_frame = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: 
            break
        
        if current_frame in frames_to_extract:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (FRAME_W, FRAME_H))
            
            # Keeps smooth, anti-aliased grayscale edges for superior visual quality
            extracted_images.append(Image.fromarray(resized))
            
            if len(extracted_images) % 500 == 0:
                print(f"Processed {len(extracted_images)} / {target_total_frames} frames...")
                
        current_frame += 1
    
    cap.release()

    total_extracted = len(extracted_images)
    rows = math.ceil(total_extracted / COLS)
    total_grid_spots = rows * COLS
    
    black_frame = Image.new('L', (FRAME_W, FRAME_H), 0)
    while len(extracted_images) < total_grid_spots:
        extracted_images.append(black_frame)

    print("\nStep 2: Generating massive 125-Megapixel Sprite Sheet...")
    sheet_w = COLS * FRAME_W
    sheet_h = rows * FRAME_H
    
    spritesheet = Image.new('L', (sheet_w, sheet_h))

    for i, img in enumerate(extracted_images):
        row = i // COLS
        col = i % COLS
        x = col * FRAME_W
        y = row * FRAME_H
        spritesheet.paste(img, (x, y))

    print(f"Saving {sheet_w}x{sheet_h} WebP (This will take some time and RAM)...")
    spritesheet.save(OUTPUT_SPRITE, quality=90, method=6)

    print("\nStep 3: Compiling strict iteration HTML/CSS...")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSS Bad Apple!!</title>
    <style>
        :root {{
            --frame-w: {FRAME_W}px;
            --frame-h: {FRAME_H}px;
            --scale: {SCALE};
            --cols: {COLS};
            --rows: {rows};
            --fps: {TARGET_FPS};
            
            --row-duration: calc(var(--cols) / var(--fps) * 1s);
            --total-duration: calc(var(--rows) * var(--row-duration));
        }}

        body {{
            background-color: #0a0a0a;
            color: #ffffff;
            display: flex;
            flex-direction: column;
            align-items: center;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin-top: 40px;
        }}

        .tv-wrapper {{
            width: calc(var(--frame-w) * var(--scale));
            height: calc(var(--frame-h) * var(--scale));
            border: 12px solid #222;
            border-radius: 8px;
            background: #000;
            box-shadow: 0 20px 50px rgba(0,0,0,0.9), inset 0 0 20px rgba(255,255,255,0.05);
            overflow: hidden;
            display: flex;
            justify-content: center;
            align-items: center;
        }}

        .screen {{
            width: var(--frame-w);
            height: var(--frame-h);
            background-image: url('{OUTPUT_SPRITE}');
            background-size: calc(var(--frame-w) * var(--cols)) calc(var(--frame-h) * var(--rows));
            background-repeat: no-repeat;
            background-position: 0px 0px;
            
            image-rendering: auto; 
            
            transform: scale(var(--scale));
            transform-origin: center;
            
            /* 
               FIX APPLIED: 
               - animX runs exactly var(--rows) times, then stops (forwards).
               - animY runs exactly 1 time over the total duration, then stops (forwards).
            */
            animation: 
                animX var(--row-duration) steps(var(--cols), end) var(--rows) forwards,
                animY var(--total-duration) steps(var(--rows), end) 1 forwards;
            
            animation-play-state: paused;
        }}

        @keyframes animX {{
            0% {{ background-position-x: 0px; }}
            100% {{ background-position-x: calc(-1 * var(--frame-w) * var(--cols)); }}
        }}
        @keyframes animY {{
            0% {{ background-position-y: 0px; }}
            100% {{ background-position-y: calc(-1 * var(--frame-h) * var(--rows)); }}
        }}

        #play-trigger {{ display: none; }}
        
        #play-trigger:checked ~ .tv-wrapper .screen {{
            animation-play-state: running;
        }}

        .controls {{
            margin-top: 30px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }}

        audio {{
            width: 320px;
            border-radius: 30px;
            outline: none;
            box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
        }}

    </style>
</head>
<body>

    <h1>CSS Bad Apple!!</h1>

    <input type="checkbox" id="play-trigger">

    <div class="tv-wrapper">
        <div class="screen"></div>
    </div>

    <div class="controls">
        <audio id="audio" controls src="{AUDIO_FILE}" 
               onplay="document.getElementById('play-trigger').checked = true;" 
               onpause="document.getElementById('play-trigger').checked = false;">
        </audio>
    </div>

</body>
</html>"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("\nSUCCESS! Pipeline complete.")
    print(f"Generated {OUTPUT_SPRITE} and {OUTPUT_HTML}.")

if __name__ == '__main__':
    main()