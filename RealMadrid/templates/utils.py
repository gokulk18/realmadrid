import cv2
import mediapipe as mp
import os
from django.conf import settings

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def detect_pose(video_path):
    cap = cv2.VideoCapture(video_path)
    pose = mp_pose.Pose()
    
    # Create output directory for processed video
    output_path = os.path.join(settings.MEDIA_ROOT, 'processed_videos')
    os.makedirs(output_path, exist_ok=True)
    
    # Get the filename from the original path
    filename = os.path.basename(video_path)
    output_video_path = os.path.join(output_path, f"processed_{filename}")
    
    # Prepare video writer
    if cap.isOpened():
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # or 'XVID'
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        frame_count = 0
        pose_data = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Convert to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = pose.process(frame_rgb)

            # Draw landmarks on the frame
            if results.pose_landmarks:
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # Store pose data for analysis
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility
                    })
                pose_data.append({'frame': frame_count, 'landmarks': landmarks})
            
            # Write the frame to output video
            out.write(frame)
            frame_count += 1

        cap.release()
        out.release()
        
        return {
            'processed_video': output_video_path,
            'pose_data': pose_data
        }
    
    return None