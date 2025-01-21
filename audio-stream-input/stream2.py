import subprocess
import pyaudio
import sys
from os import environ as env
from pydub import AudioSegment

def check_silent(raw_data):
    sample_rate = 44100  # Sample rate of the audio (adjust as needed)
    sample_width = 2     # 2 bytes per sample for 16-bit audio
    channels = 1         # Number of channels (1 for mono, 2 for stereo)

    audio_segment = AudioSegment.from_raw(
        raw_data,
        sample_rate=sample_rate,
        sample_width=sample_width,
        channels=channels,
        frame_rate=sample_rate  # For s16le, frame_rate is the same as sample_rate
    )
    loudness = audio_segment.dBFS
    if float(loudness) > -50.0:
        return False
    return True

def stream_audio(input_url, chunk_size=4096):
    """
    Stream audio from a given URL using ffmpeg and yield chunks of raw PCM data.
    """
    command = [
        "ffmpeg",
        "-i", input_url,
        "-f", "s16le",
        "-ac", "1",
        "-ar", "44100",
        "-hide_banner",
        "-loglevel", "error",
        "pipe:1"
    ]
    
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=10**6)
    
    try:
        while True:
            chunk = process.stdout.read(chunk_size)
            if not chunk:
                break
            yield chunk
    finally:
        process.terminate()
        process.wait()

def play_stream(url):
    p = pyaudio.PyAudio()
    stream = p.open(
        format=pyaudio.paInt16,
        channels=2,
        rate=44100,
        output=True,
        frames_per_buffer=1024
    )

    audio_chunks = []
    processing_queue = [
        # {
        #     "timestamp": "timestamp",
        #    "audio_chunks": [ ... ],
        # }
    ]


    try:
        for audio_chunk in stream_audio(url):
            if check_silent(audio_chunk) == False: 
                audio_chunks.append(audio_chunk)
                print("Saved audio chunk")
            else:
                if len(audio_chunks) < 1:
                    continue
                else:
                    print("Added audio chunk to processing queue")
                    processing_queue.append({
                        "timestamp": "timestamp",
                        "audio_chunks": audio_chunks
                    })
                    audio_chunks = []
            stream.write(audio_chunk)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Stream stopped")
        print("Processing queue: %d" % len(processing_queue))
        print("Audio chunks: %d" % len(audio_chunks))

if __name__ == "__main__":
    if 'STREAM_URL' not in env:
        print("Please provide a stream URL in the STREAM_URL environment variable")
        sys.exit(1)
    example_url = env['STREAM_URL']
    example_url = "http://appserver-docker1.home.arpa:8100/public/audio-stream?rate=48000"
    play_stream(example_url)