import cv2

def check_cameras():
    """Check available camera indices"""
    print("Checking available cameras...")
    available_cameras = []

    for i in range(10):  # Check first 10 indices
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                print(f"Camera {i}: Available")
                available_cameras.append(i)
            else:
                print(f"Camera {i}: Opened but no frame")
            cap.release()
        else:
            print(f"Camera {i}: Not available")

    if available_cameras:
        print(f"\nAvailable camera indices: {available_cameras}")
        print("Use: python main.py --camera <index>")
    else:
        print("\nNo cameras found.")

if __name__ == "__main__":
    check_cameras()