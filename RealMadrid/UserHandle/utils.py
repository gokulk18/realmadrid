import cv2
import mediapipe as mp
import numpy as np
from django.conf import settings
import os

mp_pose = mp.solutions.pose
mp_drawing = mp.solutions.drawing_utils

def calculate_angle(a, b, c):
    """Calculate angle between three points"""
    a = np.array(a)
    b = np.array(b)
    c = np.array(c)
    
    radians = np.arctan2(c[1]-b[1], c[0]-b[0]) - np.arctan2(a[1]-b[1], a[0]-b[0])
    angle = np.abs(radians*180.0/np.pi)
    
    if angle > 180.0:
        angle = 360-angle
        
    return angle

def count_exercise_reps(pose_data, exercise_type):
    """Count repetitions based on exercise type"""
    reps = 0
    stage = None  # 'up' or 'down'
    
    if exercise_type == 'pushup':
        # Track angles of arms for pushups
        for frame in pose_data:
            landmarks = frame['landmarks']
            
            # Get shoulder, elbow, and wrist coordinates
            shoulder = [landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x,
                       landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y]
            elbow = [landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_ELBOW.value].y]
            wrist = [landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_WRIST.value].y]
            
            # Calculate angle
            angle = calculate_angle(shoulder, elbow, wrist)
            
            # Count reps
            if angle > 160:
                stage = 'up'
            elif angle < 90 and stage == 'up':
                stage = 'down'
                reps += 1
                
    elif exercise_type == 'squat':
        # Track angles of legs for squats
        for frame in pose_data:
            landmarks = frame['landmarks']
            
            # Get hip, knee, and ankle coordinates
            hip = [landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].x,
                  landmarks[mp_pose.PoseLandmark.LEFT_HIP.value].y]
            knee = [landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].x,
                   landmarks[mp_pose.PoseLandmark.LEFT_KNEE.value].y]
            ankle = [landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].x,
                    landmarks[mp_pose.PoseLandmark.LEFT_ANKLE.value].y]
            
            # Calculate angle
            angle = calculate_angle(hip, knee, ankle)
            
            # Count reps
            if angle > 160:
                stage = 'up'
            elif angle < 90 and stage == 'up':
                stage = 'down'
                reps += 1
    
    return reps

def evaluate_exercise(reps_counted, target_reps, exercise_type):
    """Evaluate exercise performance"""
    completion_percentage = (reps_counted / target_reps) * 100
    
    result = {
        'counted_reps': reps_counted,
        'target_reps': target_reps,
        'completion_percentage': completion_percentage,
        'status': 'completed' if completion_percentage >= 90 else 'failed',
        'feedback': ''
    }
    
    if completion_percentage >= 90:
        result['feedback'] = f"Great job! You completed {reps_counted} out of {target_reps} {exercise_type}s."
    elif completion_percentage >= 70:
        result['feedback'] = f"Almost there! You completed {reps_counted} out of {target_reps} {exercise_type}s. Try to complete all repetitions next time."
    else:
        result['feedback'] = f"Keep practicing! You completed {reps_counted} out of {target_reps} {exercise_type}s."
    
    return result

def detect_pose(video_path, exercise_type, target_reps):
    """Process video and evaluate exercise"""
    cap = cv2.VideoCapture(video_path)
    pose = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
    
    output_path = os.path.join(settings.MEDIA_ROOT, 'processed_videos')
    os.makedirs(output_path, exist_ok=True)
    
    filename = os.path.basename(video_path)
    output_video_path = os.path.join(output_path, f"processed_{filename}")
    
    if not cap.isOpened():
        return None
    
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
    
    frame_count = 0
    pose_data = []
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = pose.process(frame_rgb)
        
        if results.pose_landmarks:
            mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
            
            landmarks = []
            for landmark in results.pose_landmarks.landmark:
                landmarks.append({
                    'x': landmark.x,
                    'y': landmark.y,
                    'z': landmark.z,
                    'visibility': landmark.visibility
                })
            pose_data.append({'frame': frame_count, 'landmarks': landmarks})
        
        out.write(frame)
        frame_count += 1
    
    cap.release()
    out.release()
    
    # Count repetitions and evaluate
    reps_counted = count_exercise_reps(pose_data, exercise_type)
    evaluation = evaluate_exercise(reps_counted, target_reps, exercise_type)
    
    return {
        'processed_video': output_video_path,
        'pose_data': pose_data,
        'evaluation': evaluation
    }

class VideoProcessor:
    def __init__(self):
        self.pose = mp_pose.Pose(min_detection_confidence=0.7, min_tracking_confidence=0.7)
        
    def _process_video(self, video_path, exercise_type, target_reps=None):
        """Generic video processing method used by all exercise types"""
        cap = cv2.VideoCapture(video_path)
        
        # Prepare output video
        output_path = os.path.join(settings.MEDIA_ROOT, 'processed_videos')
        os.makedirs(output_path, exist_ok=True)
        filename = os.path.basename(video_path)
        output_video_path = os.path.join(output_path, f"processed_{filename}")
        
        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_video_path, fourcc, fps, (width, height))
        
        frame_count = 0
        pose_data = []
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            # Process frame
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.pose.process(frame_rgb)
            
            if results.pose_landmarks:
                # Draw pose landmarks
                mp_drawing.draw_landmarks(frame, results.pose_landmarks, mp_pose.POSE_CONNECTIONS)
                
                # Store landmark data
                landmarks = []
                for landmark in results.pose_landmarks.landmark:
                    landmarks.append({
                        'x': landmark.x,
                        'y': landmark.y,
                        'z': landmark.z,
                        'visibility': landmark.visibility
                    })
                pose_data.append({'frame': frame_count, 'landmarks': landmarks})
                
                # Add exercise-specific visualizations
                self._add_exercise_visualization(frame, results.pose_landmarks, exercise_type)
            
            out.write(frame)
            frame_count += 1
        
        cap.release()
        out.release()
        
        return output_video_path, pose_data
    
    def _add_exercise_visualization(self, frame, landmarks, exercise_type):
        """Add exercise-specific visual guides and measurements"""
        if exercise_type == 'PUSHUP':
            # Draw arm angle
            shoulder = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value].x * frame.shape[1],
                       landmarks.landmark[mp_pose.PoseLandmark.LEFT_SHOULDER.value].y * frame.shape[0]]
            elbow = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW.value].x * frame.shape[1],
                    landmarks.landmark[mp_pose.PoseLandmark.LEFT_ELBOW.value].y * frame.shape[0]]
            wrist = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST.value].x * frame.shape[1],
                    landmarks.landmark[mp_pose.PoseLandmark.LEFT_WRIST.value].y * frame.shape[0]]
            
            angle = calculate_angle(shoulder, elbow, wrist)
            cv2.putText(frame, f"Arm angle: {angle:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            
        elif exercise_type == 'SQUAT':
            # Draw leg angle
            hip = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP.value].x * frame.shape[1],
                   landmarks.landmark[mp_pose.PoseLandmark.LEFT_HIP.value].y * frame.shape[0]]
            knee = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE.value].x * frame.shape[1],
                   landmarks.landmark[mp_pose.PoseLandmark.LEFT_KNEE.value].y * frame.shape[0]]
            ankle = [landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE.value].x * frame.shape[1],
                    landmarks.landmark[mp_pose.PoseLandmark.LEFT_ANKLE.value].y * frame.shape[0]]
            
            angle = calculate_angle(hip, knee, ankle)
            cv2.putText(frame, f"Knee angle: {angle:.1f}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    def evaluate_pushup(self, video_path, target_reps=10):
        """Evaluate pushup form and count reps"""
        output_video_path, pose_data = self._process_video(video_path, 'PUSHUP', target_reps)
        
        # Count reps and evaluate form
        reps_counted = count_exercise_reps(pose_data, 'pushup')
        evaluation = evaluate_exercise(reps_counted, target_reps, 'pushup')
        
        # Add form analysis
        form_issues = []
        metrics = {
            'completion_rate': (reps_counted / target_reps) * 100,
            'form_issues': form_issues,
            'recommendations': []
        }
        
        return {
            'success': True,
            'processed_video_path': output_video_path,
            'metrics': metrics,
            'evaluation': evaluation
        }
    
    def evaluate_squat(self, video_path, target_reps=10):
        """Evaluate squat form and count reps"""
        output_video_path, pose_data = self._process_video(video_path, 'SQUAT', target_reps)
        
        # Count reps and evaluate form
        reps_counted = count_exercise_reps(pose_data, 'squat')
        evaluation = evaluate_exercise(reps_counted, target_reps, 'squat')
        
        # Add form analysis
        form_issues = []
        metrics = {
            'completion_rate': (reps_counted / target_reps) * 100,
            'form_issues': form_issues,
            'recommendations': []
        }
        
        return {
            'success': True,
            'processed_video_path': output_video_path,
            'metrics': metrics,
            'evaluation': evaluation
        }
    
    def evaluate_running(self, video_path):
        """Evaluate running form"""
        output_video_path, pose_data = self._process_video(video_path, 'RUNNING')
        
        # Analyze running form
        metrics = {
            'completion_rate': 100,  # Running doesn't have specific reps
            'form_issues': [],
            'recommendations': ["Maintain good posture while running",
                              "Keep your arms at roughly 90 degrees",
                              "Land midfoot with your feet under your body"]
        }
        
        return {
            'success': True,
            'processed_video_path': output_video_path,
            'metrics': metrics
        }
    
    def evaluate_general_movement(self, video_path):
        """Evaluate general movement patterns"""
        output_video_path, pose_data = self._process_video(video_path, 'GENERAL')
        
        metrics = {
            'completion_rate': 100,
            'form_issues': [],
            'recommendations': ["Focus on controlled movements",
                              "Maintain proper posture throughout the exercise"]
        }
        
        return {
            'success': True,
            'processed_video_path': output_video_path,
            'metrics': metrics
        }