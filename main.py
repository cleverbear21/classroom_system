import threading
import time
import sys
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

def main():
    print("Starting Classroom Interest Monitor...")
    try:
        # Start threads
        video_thread = threading.Thread(target=analyze_video, daemon=True)
        audio_thread = threading.Thread(target=analyze_audio, daemon=True)
        video_thread.start()
        audio_thread.start()
        print("Video and audio threads started. Close the video window to exit.")

        # Main loop
        while video_thread.is_alive() or audio_thread.is_alive():
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

            time.sleep(1)
    except Exception as e:
        print(f"Error in main: {e}")
    finally:
        print("Exiting Classroom Interest Monitor.")
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
