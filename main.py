import cv2
import threading
import time
import sys
import argparse
try:
    from video_analysis import analyze_video
    from audio_analysis import analyze_audio
    from utils import video_queue, audio_queue, calculate_combined_score, log_interest
    from flask import Flask, render_template_string
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

app = Flask(__name__)

# Global for dashboard
current_score = 50
current_zone = "center"

@app.route('/')
def dashboard():
    return render_template_string("""
    <h1>Classroom Interest Monitor</h1>
    <p>Current Score: {{ score }}</p>
    <p>Zone: {{ zone }}</p>
    <meta http-equiv="refresh" content="1">  <!-- Auto-refresh -->
    """, score=current_score, zone=current_zone)

def main(camera_index=1):
    print("Starting Classroom Interest Monitor...")
    try:
        # Start threads
        video_thread = threading.Thread(target=analyze_video, args=(camera_index,), daemon=True)
        audio_thread = threading.Thread(target=analyze_audio, daemon=True)
        video_thread.start()
        audio_thread.start()
        print("Video and audio threads started. Press Ctrl+C to exit.")

        # Main loop - keep running even if threads die
        while True:
            video_data = None
            audio_data = None
            try:
                video_data = video_queue.get(timeout=1)
                audio_data = audio_queue.get(timeout=1)
            except:
                pass  # No new data

            if video_data and audio_data:
                video_score, video_zone = video_data
                audio_score, audio_zone = audio_data
                combined = calculate_combined_score(video_score, audio_score)
                zone = video_zone  # Prioritize video for spatial
                log_interest(zone, combined, time.strftime("%H:%M:%S"))
                current_score = combined
                current_zone = zone
                print(f"Combined Score: {combined}, Zone: {zone}")
            elif video_data:
                # Only video data available
                video_score, video_zone = video_data
                log_interest(video_zone, video_score, time.strftime("%H:%M:%S"))
                current_score = video_score
                current_zone = video_zone
                print(f"Video Score: {video_score}, Zone: {video_zone}")
            elif audio_data:
                # Only audio data available
                audio_score, audio_zone = audio_data
                log_interest(audio_zone, audio_score, time.strftime("%H:%M:%S"))
                current_score = audio_score
                current_zone = audio_zone
                print(f"Audio Score: {audio_score}, Zone: {audio_zone}")

            time.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted by user")
    except Exception as e:
        print(f"Error in main: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Exiting Classroom Interest Monitor.")
        cv2.destroyAllWindows()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Classroom Interest Monitor")
    parser.add_argument("--camera", type=int, help="Camera index to use")
    args = parser.parse_args()

    # If no camera specified, ask user
    camera_index = args.camera
    if camera_index is None:
        try:
            camera_index = int(input("Enter camera index to use (0 for default camera, 1 for second camera, etc.): "))
        except ValueError:
            print("Invalid input, using default camera (0)")
            camera_index = 0

    # Start Flask app in a separate thread
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False), daemon=True)
    flask_thread.start()
    print("Flask dashboard started at http://localhost:5000")
    main(camera_index=camera_index)
