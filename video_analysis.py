import cv2
from utils import video_queue
import time
import sys

def analyze_video(camera_index=1):
    try:
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            print("Error: Cannot access camera")
            return

        engagement_score = 100  # Start with full engagement

        while True:
            ret, frame = cap.read()
            if not ret:
                break
            # Resize for performance
            frame = cv2.resize(frame, (640, 480))
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            # Face detection for posture (simple slumped check via face tilt)
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            zone = "center"
            if len(faces) > 0:
                (x, y, w, h) = faces[0]  # First face
                # Simple posture: if face is tilted or low, deduct (basic approximation)
                face_center_y = y + h // 2
                frame_center_y = frame.shape[0] // 2
                if face_center_y > frame_center_y + 80:  # Increased threshold for less sensitivity
                    engagement_score = max(0, engagement_score - 5)  # Reduced deduction

                # Zone based on face position
                if x + w // 2 < frame.shape[1] // 3:
                    zone = "left"
                elif x + w // 2 > 2 * frame.shape[1] // 3:
                    zone = "right"
                else:
                    zone = "center"

                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)

            # Eye detection for gaze
            eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
            eyes = eye_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

            if len(eyes) >= 2:
                left_eye = eyes[0]
                right_eye = eyes[1] if len(eyes) > 1 else eyes[0]

                left_eye_center_x = left_eye[0] + left_eye[2] // 2
                right_eye_center_x = right_eye[0] + right_eye[2] // 2
                frame_center_x = frame.shape[1] // 2

                gaze_deviation = abs((left_eye_center_x + right_eye_center_x) / 2 - frame_center_x)
                print(f"Gaze deviation: {gaze_deviation:.1f}")
                if gaze_deviation > 80:  # Increased threshold for less sensitivity
                    print("Eye looking away")
                    engagement_score = max(0, engagement_score - 20)  # Reduced deduction
                else:
                    engagement_score = min(100, engagement_score + 2)  # Smaller addition

                # Draw circles at eye centers instead of rectangles
                for (ex, ey, ew, eh) in eyes:
                    eye_center_x = ex + ew // 2
                    eye_center_y = ey + eh // 2
                    cv2.circle(frame, (eye_center_x, eye_center_y), 10, (0, 255, 0), 2)

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
        sys.exit(1)

