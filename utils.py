import queue
import time

# Global queues for scores
video_queue = queue.Queue(maxsize=1)
audio_queue = queue.Queue(maxsize=1)

def calculate_combined_score(video_score, audio_score, weights=(0.6, 0.4)):
    """Fuse scores: e.g., 60% video, 40% audio."""
    if video_score is None or audio_score is None:
        return 50  # Default neutral
    return (video_score * weights[0]) + (audio_score * weights[1])

def log_interest(zone, score, timestamp):
    """Simple logging to console/file."""
    log_entry = f"{timestamp}: Zone {zone} - Interest {score:.2f}"
    print(log_entry)
    with open("interest_log.txt", "a") as f:
        f.write(log_entry + "\n")
