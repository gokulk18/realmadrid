import mediapipe as mp
import cv2
import numpy as np
from django.shortcuts import get_object_or_404
from django.core.files import File
from django.utils import timezone
import tempfile
from .models import PlayerVideo

def analyze_video(video_id):
    try:
        video = PlayerVideo.objects.get(id=video_id)
        video.status = 'processing'
        video.save()

        # Initialize MediaPipe Pose
        mp_pose = mp.solutions.pose
        mp_drawing = mp.solutions.drawing_utils
        pose = mp_pose.Pose(
            static_image_mode=False,
            model_complexity=2,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )

        # Open video file
        cap = cv2.VideoCapture(video.video.path)
        
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        # Create temporary file for processed video
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_output.name, fourcc, fps, (frame_width, frame_height))

            frame_count = 0
            pose_detected_frames = 0
            exercise_reps = 0
            last_position = None

            # Get exercise type from task
            exercise_type = video.task.exercise_type

            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break

                # Convert BGR to RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Process frame with MediaPipe
                results = pose.process(frame_rgb)

                if results.pose_landmarks:
                    pose_detected_frames += 1

                    # Draw pose landmarks
                    mp_drawing.draw_landmarks(
                        frame,
                        results.pose_landmarks,
                        mp_pose.POSE_CONNECTIONS
                    )

                    # Count exercise repetitions based on exercise type
                    if exercise_type == 'pushup':
                        exercise_reps += count_pushups(results.pose_landmarks, last_position)
                    elif exercise_type == 'squat':
                        exercise_reps += count_squats(results.pose_landmarks, last_position)
                    
                    last_position = results.pose_landmarks

                # Write frame to output video
                out.write(frame)
                
                # Update progress
                frame_count += 1
                progress = (frame_count / total_frames) * 100
                video.processing_progress = progress
                video.save()

            # Release resources
            cap.release()
            out.release()
            pose.close()

            # Save processed video
            with open(temp_output.name, 'rb') as processed_file:
                video.processed_video.save(
                    f'processed_{video.video.name}',
                    File(processed_file)
                )

            # Calculate metrics
            detection_rate = (pose_detected_frames / frame_count) * 100
            target_reps = video.task.repetitions
            accuracy = min(100, (exercise_reps / target_reps) * 100) if target_reps > 0 else 0

            # Save analysis results
            video.evaluation_data = {
                'Pose Detection Rate': f'{detection_rate:.1f}%',
                'Completed Repetitions': exercise_reps,
                'Target Repetitions': target_reps,
                'Exercise Accuracy': f'{accuracy:.1f}%',
                'Frames Analyzed': frame_count
            }
            video.status = 'completed'
            video.processed_at = timezone.now()
            video.save()

            # Update task status if exercise completed successfully
            if exercise_reps >= target_reps:
                video.task.status = 'completed'
                video.task.save()

    except Exception as e:
        video.status = 'failed'
        video.error_message = str(e)
        video.save()
        raise

def count_pushups(landmarks, last_position):
    if not last_position:
        return 0
    
    shoulder = landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER].y
    last_shoulder = last_position.landmark[mp.solutions.pose.PoseLandmark.LEFT_SHOULDER].y
    
    if last_shoulder < 0.6 and shoulder >= 0.6:
        return 1
    return 0

def count_squats(landmarks, last_position):
    if not last_position:
        return 0
    
    hip = landmarks.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP].y
    last_hip = last_position.landmark[mp.solutions.pose.PoseLandmark.LEFT_HIP].y
    
    if last_hip < 0.7 and hip >= 0.7:
        return 1
    return 0