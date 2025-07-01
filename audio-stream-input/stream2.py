import subprocess
import pyaudio
import sys
from os import environ as env
from pydub import AudioSegment

def check_silent(raw_data):
    """
    Check if audio data is silent by calculating RMS directly from raw PCM data.
    More efficient than using AudioSegment.
    """
    if len(raw_data) < 2:
        return True
    
    try:
        import struct
        import math
        
        # Convert bytes to 16-bit signed integers
        samples = struct.unpack(f'<{len(raw_data)//2}h', raw_data)
        
        # Calculate RMS (Root Mean Square)
        sum_squares = sum(sample * sample for sample in samples)
        rms = math.sqrt(sum_squares / len(samples))
        
        # Convert to approximate dBFS
        if rms == 0:
            return True
        
        # 32767 is max value for 16-bit signed
        db_fs = 20 * math.log10(rms / 32767.0)
        
        # Return True if silent (below -50 dBFS threshold)
        return db_fs < -50.0
        
    except Exception as e:
        print(f"Error in check_silent: {e}")
        return False  # Assume not silent if we can't determine

def stream_audio(input_url, chunk_size=4096):
    """
    Stream audio from a given URL using ffmpeg and yield chunks of raw PCM data.
    """
    command = [
        "ffmpeg",
        "-i", input_url,
        "-f", "s16le",
        "-ac", "1",  # Mono output
        "-ar", "48000",
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
    # Fixed: Match the mono output from ffmpeg
    stream = p.open(
        format=pyaudio.paInt16,
        channels=1,  # Changed to mono to match ffmpeg output
        rate=48000,
        output=True,
        frames_per_buffer=2048  # Adjusted buffer size
    )

    audio_chunks = []
    processing_queue = []

    try:
        for audio_chunk in stream_audio(url):
            print(f"Received chunk of {len(audio_chunk)} bytes")
            if check_silent(audio_chunk) == False:
                print("Non-silent audio chunk detected, saving to audio_chunks")
                audio_chunks.append(audio_chunk)
            else:
                print("Silent audio chunk detected, processing current chunks")
                if len(audio_chunks) >= 1:  # Fixed condition
                    print("Added audio chunk to processing queue")
                    processing_queue.append({
                        "timestamp": "timestamp",
                        "audio_chunks": audio_chunks
                    })
                    audio_chunks = []
            
            # Always write to stream for playback
            stream.write(audio_chunk)
            
    except Exception as e:
        print(f"Error during streaming: {e}")
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
    #example_url = env['STREAM_URL']
    example_url = "http://stream.live.vc.bbcmedia.co.uk/bbc_world_service"
    #example_url = "http://192.168.1.166:8100/public/audio-stream?rate=48000"
    play_stream(example_url)