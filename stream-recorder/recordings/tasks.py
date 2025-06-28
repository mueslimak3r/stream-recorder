# streams/tasks.py
import os
import signal
import shutil
import subprocess
import time
from django.conf import settings
from django_tasks import task
from .models import RecordingSource
from datetime import datetime
from pathlib import Path

@task()
def continuous_rebroadcast(stream_id):
    """
    Start (and maintain) an ffmpeg process that pulls from `StreamSource.url`
    and writes an HLS stream to `MEDIA_ROOT/hls/stream_<id>`.
    This task will block until it is manually terminated (or if ffmpeg fails).
    """
    print('starting continuous_rebroadcast')
    stream = RecordingSource.objects.get(pk=stream_id)

    # Mark the stream as active in DB
    stream.rebroadcast_active = True
    # We'll store HLS in e.g. /path/to/media/hls/stream_<id>/
    stream_dir = os.path.join(settings.MEDIA_ROOT, 'hls', f"stream_{stream_id}")
    os.makedirs(stream_dir, exist_ok=True)
    stream.hls_url = os.path.join(settings.MEDIA_URL, 'hls', f"stream_{stream_id}", 'index.m3u8')
    stream.save()

    # e.g. ffmpeg command for HLS
    # -i stream.url : input
    # -c:v copy, -c:a copy : no transcoding (pass-through)
    # -hls_time 6  : each segment is ~6 seconds
    # -hls_list_size 5 : keep 5 segments in the live playlist
    # -hls_flags delete_segments : delete older segments
    # -f hls : output format is HLS
    # Use '-y' to overwrite existing .m3u8 if present
    print("source url: ", stream.source_url)
    command = [
        'ffmpeg', '-i', stream.source_url,
        #'-c:v', 'copy', '-c:a', 'copy',
        '-vf', 'drawbox=color=black:t=fill',
        '-acodec', 'libmp3lame',
        '-ar', '44100',
        '-b:a', '128k',

        #'-c:a', 'copy',
        '-hls_time', '6',
        '-hls_list_size', '6',
        '-hls_flags', 'delete_segments',
        '-f', 'hls',
        '-y',  # overwrite existing files
        os.path.join(stream_dir, 'index.m3u8')
    ]

    # Spawn ffmpeg as a subprocess
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    try:
        # Continuously read from the ffmpeg process to avoid pipe blocking
        while True:
            # If ffmpeg stops, process.poll() != None
            if process.poll() is not None:
                # Possibly we try to restart it or just break
                print(f"[continuous_rebroadcast] FFmpeg stopped for stream {stream.title}")
                break
            time.sleep(1)
    finally:
        # Mark as inactive if the process ends or we get signaled
        stream = RecordingSource.objects.get(pk=stream_id)
        stream.rebroadcast_active = False
        stream.save()
        if process.poll() is None:
            # If still running, terminate
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print(f"[continuous_rebroadcast] Cleaned up for stream {stream.title}")
        shutil.rmtree(stream_dir, ignore_errors=True)

@task()
def record_source(stream_id):
    """
    Start (and maintain) an ffmpeg process that pulls from `StreamSource.url`
    and writes an HLS stream to `MEDIA_ROOT/hls/stream_<id>`.
    This task will block until it is manually terminated (or if ffmpeg fails).
    """
    print('starting record_source')
    stream = RecordingSource.objects.get(pk=stream_id)

    if stream.stream_type == RecordingSource.RECORDINGTYPE_UNKNOWN:
        print(f"[record_source] Stream type unknown for {stream.title}")
        return 1

    session_timestamp = datetime.now().strftime("%Y_%m_%d-%I_%M_%S_%p")
    stream_dir = Path(Path(settings.MEDIA_ROOT) / Path('hls') / Path(session_timestamp) / Path('stream_%s' % stream_id)).absolute()
    recording_dir = Path(Path(settings.MEDIA_ROOT) / Path('recordings') / Path(session_timestamp) / Path('stream_%s' % stream_id)).absolute()
    # Mark the stream as active in DB
    #stream.rebroadcast_active = True
    # We'll store HLS in e.g. /path/to/media/hls/stream_<id>/
    Path(recording_dir).mkdir(parents=True, exist_ok=True)
    stream.recording_active = True
    #stream.hls_url = os.path.join(settings.MEDIA_URL, 'hls', f"stream_{stream_id}", 'index.m3u8')
    stream.save()

    # e.g. ffmpeg command for HLS
    # -i stream.url : input
    # -c:v copy, -c:a copy : no transcoding (pass-through)
    # -hls_time 6  : each segment is ~6 seconds
    # -hls_list_size 5 : keep 5 segments in the live playlist
    # -hls_flags delete_segments : delete older segments
    # -f hls : output format is HLS
    # Use '-y' to overwrite existing .m3u8 if present
    print("source url: ", stream.source_url)
    print("stream type: ", stream.stream_type)

    if stream.stream_type == RecordingSource.RECORDINGTYPE_AUDIO:
        print("Recording audio")
        command = [
            'ffmpeg', '-i', stream.source_url,
            '-acodec', 'libmp3lame',
            '-ar', '44100',
            '-b:a', '128k',
            '-f', 'segment',
            '-segment_time', '10',
            '-segment_format', 'mp3',
            '-y',
            os.path.join(recording_dir, 'segment_%03d.mp3')
        ]
    elif stream.stream_type == RecordingSource.RECORDINGTYPE_VIDEO:
        command = [
            'ffmpeg', '-i', stream.source_url,
            #'-c:v', 'copy', '-c:a', 'copy',
            '-vf', 'drawbox=color=black:t=fill',
            '-acodec', 'libmp3lame',
            '-ar', '44100',
            '-b:a', '128k',

            #'-c:a', 'copy',
            '-hls_time', '6',
            '-hls_list_size', '6',
            '-hls_flags', 'delete_segments',
            '-f', 'hls',
            '-y',  # overwrite existing files
            os.path.join(stream_dir, 'index.m3u8')
        ]
    else:
        print(f"[record_source] Stream type unknown for {stream.title}")
        return 1

    # Spawn ffmpeg as a subprocess
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True
    )

    try:
        # Continuously read from the ffmpeg process to avoid pipe blocking
        while True:
            
            # If ffmpeg stops, process.poll() != None
            if process.poll() is not None:
                # Possibly we try to restart it or just break
                print(f"[record_source] FFmpeg stopped for stream {stream.title}")
                break
            time.sleep(1)
    finally:
        # Mark as inactive if the process ends or we get signaled
        stream = RecordingSource.objects.get(pk=stream_id)
        stream.recording_active = False
        stream.save()
        if process.poll() is None:
            # If still running, terminate
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        print(f"[continuous_rebroadcast] Cleaned up for stream {stream.title}")
        shutil.rmtree(stream_dir, ignore_errors=True)

