import cv2
from utils import video_queue
import time
import sys
import os

def analyze_video(camera_index=0):
    try:
        # Check if haarcascade files exist
        face_cascade_path = 'haarcascades/haarcascade_frontalface_default.xml'
        eye_cascade_path = 'haarcascades/haarcascade_eye.xml'

        if not os.path.exists(face_cascade_path):
            print(f"Error: Face cascade file not found at {face_cascade_path}")
            return
        if not os.path.exists(eye_cascade_path):
            print(f"Error: Eye cascade file not found at {eye_cascade_path}")
            return

        cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)
        if not cap.isOpened():
            print("Error: Cannot access camera")
            return

        engagement_score = 100  # Start with full engagement
        last_update_time = time.time()

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # Resize for performance
            frame = cv2.resize(frame, (640, 480))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Face detection for posture (simple slumped check via face tilt)
            face_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            zone = "center"
            if len(faces) > 0:
                (x, y, w, h) = faces[0]  # First face
                # Simple posture: if face is tilted or low, deduct (basic approximation)
                face_center_y = y + h // 2
                frame_center_y = frame.shape[0] // 2
                if face_center_y > frame_center_y + 80:  # Less sensitive threshold
                    print("Poor posture detected")
                    engagement_score = max(0, engagement_score - 2)  # Smaller deduction

                # Zone based on face position
                if x + w // 2 < frame.shape[1] // 3:
                    zone = "left"
                elif x + w // 2 > 2 * frame.shape[1] // 3:
                    zone = "right"
                else:
                    zone = "center"

                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Eye detection for gaze - only if face is detected
            if len(faces) > 0:
                (fx, fy, fw, fh) = faces[0]
                # Focus eye detection on face region
                face_roi = gray[fy:fy+fh, fx:fx+fw]
                eye_cascade = cv2.CascadeClassifier('haarcascades/haarcascade_eye.xml')
                eyes = eye_cascade.detectMultiScale(face_roi, scaleFactor=1.1, minNeighbors=3, minSize=(20, 20))

                if len(eyes) >= 2:
                    # Adjust eye coordinates to full frame
                    left_eye = (eyes[0][0] + fx, eyes[0][1] + fy, eyes[0][2], eyes[0][3])
                    right_eye = (eyes[1][0] + fx, eyes[1][1] + fy, eyes[1][2], eyes[1][3]) if len(eyes) > 1 else left_eye

                    left_eye_center_x = left_eye[0] + left_eye[2] // 2
                    right_eye_center_x = right_eye[0] + right_eye[2] // 2
                    frame_center_x = frame.shape[1] // 2

                    gaze_deviation = abs((left_eye_center_x + right_eye_center_x) / 2 - frame_center_x)
                    print(f"Gaze deviation: {gaze_deviation:.1f}")
                    if gaze_deviation > 30:  # More sensitive threshold
                        print("Eye looking away")
                        engagement_score = max(0, engagement_score - 15)  # Larger deduction
                    else:
                        engagement_score = min(100, engagement_score + 5)  # Increase positive feedback

                    # Draw circles at eye centers instead of rectangles
                    for (ex, ey, ew, eh) in [left_eye, right_eye]:
                        eye_center_x = ex + ew // 2
                        eye_center_y = ey + eh // 2
                        cv2.circle(frame, (eye_center_x, eye_center_y), 10, (0, 255, 0), 2)
                else:
                    # If eyes not detected but face is, still give some positive feedback
                    engagement_score = min(100, engagement_score + 2)
            else:
                # No face detected - significant penalty
                engagement_score = max(0, engagement_score - 10)

            # Gradual score decay over time
            current_time = time.time()
            if current_time - last_update_time > 2.0:  # Every 2 seconds
                engagement_score = max(0, engagement_score - 1)  # Gradual decay
                last_update_time = current_time

            # Update queue
            if not video_queue.full():
                video_queue.put((engagement_score, zone))
            else:
                video_queue.get()
                video_queue.put((engagement_score, zone))

            cv2.putText(frame, f"Engagement: {engagement_score}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.imshow('Video Feed', frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
    except Exception as e:
        print(f"Error in video analysis: {e}")

