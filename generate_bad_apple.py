import cv2
from PIL import Image
import math
import os
import sys

# ==========================================
# CONFIGURATION
# ==========================================
VIDEO_FILE = 'bad_apple.mp4'
AUDIO_FILE = 'bad_apple.mp3'
OUTPUT_HTML = 'index.html'
OUTPUT_SPRITE = 'spritesheet.webp'

TARGET_FPS = 10        # Frames per second
FRAME_W = 80           # Frame width
FRAME_H = 60           # Frame height
COLS = 50              # Columns in the sprite sheet grid
SCALE = 8              # Video scale multiplier in CSS (80x60 * 8 = 640x480)

def main():
    if not os.path.exists(VIDEO_FILE):
        print(f"Error: {VIDEO_FILE} not found!")
        sys.exit(1)

    print("Step 1: Extracting and processing frames...")
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
            # Convert to grayscale and resize
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            resized = cv2.resize(gray, (FRAME_W, FRAME_H))
            
            # Apply strict binary threshold to make it pure black & white 
            # (Maximizes WebP compression efficiency)
            _, thresh = cv2.threshold(resized, 128, 255, cv2.THRESH_BINARY)
            
            extracted_images.append(Image.fromarray(thresh))
            
            if len(extracted_images) % 100 == 0:
                print(f"Processed {len(extracted_images)} / {target_total_frames} frames...")
                
        current_frame += 1
    
    cap.release()

    # Calculate padding to ensure the grid is a perfect rectangle
    total_extracted = len(extracted_images)
    rows = math.ceil(total_extracted / COLS)
    total_grid_spots = rows * COLS
    
    # Pad missing frames with black rectangles
    black_frame = Image.new('L', (FRAME_W, FRAME_H), 0)
    while len(extracted_images) < total_grid_spots:
        extracted_images.append(black_frame)

    print("\nStep 2: Generating massive Sprite Sheet...")
    sheet_w = COLS * FRAME_W
    sheet_h = rows * FRAME_H
    
    # 'L' mode is 8-bit pixels, black and white
    spritesheet = Image.new('L', (sheet_w, sheet_h))

    for i, img in enumerate(extracted_images):
        row = i // COLS
        col = i % COLS
        x = col * FRAME_W
        y = row * FRAME_H
        spritesheet.paste(img, (x, y))

    print("Saving highly compressed WebP (this may take a moment)...")
    spritesheet.save(OUTPUT_SPRITE, quality=80, method=6)

    print("\nStep 3: Compiling Zero-JS HTML/CSS...")
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Pure CSS Bad Apple!!</title>
    <style>
        :root {{
            --frame-w: {FRAME_W}px;
            --frame-h: {FRAME_H}px;
            --scale: {SCALE};
            --cols: {COLS};
            --rows: {rows};
            --fps: {TARGET_FPS};
            
            /* Timing Calcs */
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

        /* The UI Wrapper */
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

        /* The CSS Render Engine */
        .screen {{
            width: var(--frame-w);
            height: var(--frame-h);
            background-image: url('{OUTPUT_SPRITE}');
            background-size: calc(var(--frame-w) * var(--cols)) calc(var(--frame-h) * var(--rows));
            background-repeat: no-repeat;
            background-position: 0px 0px;
            image-rendering: pixelated; /* Keeps upscaled B&W pixels razor sharp */
            transform: scale(var(--scale));
            transform-origin: center;
            
            /* NESTED KEYFRAMES: 2D Step Matrix */
            animation: 
                animX var(--row-duration) steps(var(--cols), end) infinite,
                animY var(--total-duration) steps(var(--rows), end) infinite;
            
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

        /* ZERO-JS Logic Trick */
        #play-trigger {{ display: none; }}
        
        #play-trigger:checked ~ .tv-wrapper .screen {{
            animation-play-state: running;
        }}
        #play-trigger:checked ~ .controls .step-1 {{
            display: none;
        }}
        #play-trigger:checked ~ .controls .step-2 {{
            opacity: 1; pointer-events: auto; transform: scale(1);
        }}

        .controls {{
            margin-top: 30px;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 80px;
        }}

        .play-btn {{
            background: #e50914;
            color: white;
            padding: 16px 32px;
            font-size: 20px;
            font-weight: bold;
            cursor: pointer;
            border-radius: 6px;
            user-select: none;
            transition: all 0.2s;
            box-shadow: 0 4px 15px rgba(229, 9, 20, 0.4);
        }}
        .play-btn:hover {{ background: #f40612; transform: translateY(-2px); }}
        
        .step-2 {{
            opacity: 0; pointer-events: none; transform: scale(0.95);
            transition: all 0.3s; text-align: center;
        }}
        
        audio {{ margin-top: 10px; border-radius: 30px; outline: none; }}
        p.warning {{ font-size: 0.85em; color: #888; max-width: 600px; text-align: center; margin-top: 40px; }}

    </style>
</head>
<body>

    <h1>Pure Code Bad Apple!!</h1>

    <!-- Pure HTML/CSS State Checkbox -->
    <input type="checkbox" id="play-trigger">

    <div class="tv-wrapper">
        <div class="screen"></div>
    </div>

    <div class="controls">
        <label for="play-trigger" class="play-btn step-1">1. START CSS RENDERER</label>
        
        <div class="step-2">
            <span style="color: #0f0; font-weight: bold;">CSS ENGINE RUNNING</span><br>
            <audio id="audio" controls src="{AUDIO_FILE}"></audio>
        </div>
    </div>

    <p class="warning">
        <strong>Zero JS Constraint Notice:</strong> Because this site relies entirely on the browser's CSS compositor engine with EXACTLY ZERO JavaScript, programmatic audio sync is impossible. Hit "Start CSS Renderer" to ready the animation state, then hit "Play" on the native audio element to begin. The CSS timeline handles the math perfectly.
    </p>

</body>
</html>"""

    with open(OUTPUT_HTML, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print("\nSUCCESS! Pipeline complete.")
    print(f"Generated {OUTPUT_SPRITE} and {OUTPUT_HTML}.")
    print("Open index.html in your browser to view.")

if __name__ == '__main__':
    main()