from celery import shared_task
from .video_processor import analyze_video

@shared_task
def process_video_task(video_id):
    analyze_video(video_id)