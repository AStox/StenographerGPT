import sys
import requests
import json
import functools
import sounddevice as sd
import threading
import keyboard
import soundfile as sf
from pydub import AudioSegment
from queue import Queue
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# Global variable to control the recording loop
recording = True

def transcribe_audio(audio_file):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        # 'Content-Type': 'multipart/form-data',
    }
    with open(audio_file, 'rb') as f:
        audio_data = f.read()
        response = requests.post(
            'https://api.openai.com/v1/audio/transcriptions',
            headers=headers,
            data={'model': 'whisper-1'},
            files={'file': ('output.wav', audio_data, 'audio/wav')}
        )
        print(response.json())
        return response.json()['text']

def summarize_text(text):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }

    data = {
        'model': 'text-davinci-003',
        'prompt': f'Summarize the following text:\n{text}',
        'max_tokens': 50,
        'temperature': 0.5,
    }

    response = requests.post(
        'https://api.openai.com/v1/completions',
        headers=headers,
        json=data
    )

    return response.json()['choices'][0]['text'].strip()

def record_audio_non_blocking(outfile, device_index, seconds=None, channels=1):
    def record(outfile, device_index, seconds, channels):
        with sf.SoundFile(outfile, mode='w', samplerate=48000, channels=channels) as file:
            with sd.InputStream(callback=functools.partial(callback, file), channels=channels, samplerate=48000, device=device_index):
                print('Recording started.')
                while True:
                    sd.sleep(500)
                    if keyboard.is_pressed('s'):
                        break
                    if seconds is not None:
                        sd.sleep(seconds * 1000)
                        break
        print('Recording stopped.')

    record_thread = threading.Thread(target=record, args=(outfile, device_index, seconds, channels))
    record_thread.start()
    return record_thread

def stop_audio_recording():
    global recording
    recording = False

def callback(file, indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    file.write(indata)

def merge_audio_files(file1, file2, output_file):
    audio1 = AudioSegment.from_wav(file1)
    audio2 = AudioSegment.from_wav(file2)
    combined = audio1.overlay(audio2)
    combined.export(output_file, format='wav')

def find_device_index(device_label, direction):
    if direction not in ['input', 'output']:
        raise ValueError("Invalid direction. It must be 'input' or 'output'.")

    devices = sd.query_devices()
    for index, device in enumerate(devices):
        if device['name'] == device_label:
            if (direction == 'input' and device['max_input_channels'] > 0) or (direction == 'output' and device['max_output_channels'] > 0):
                return index
    return -1


# print the available devices
devices = sd.query_devices()
for index, device in enumerate(devices):
    # print index name and max input channels and max output channels
    print(f"Device Index: {index}, Device Name: {device['name']}, Max Input Channels: {device['max_input_channels']}," +
          f" Max Output Channels: {device['max_output_channels']}")


# Find the device indices
# ternary operator to handle the case where the AirPods Pro are not connected
MIC_DEVICE_INDEX = find_device_index('Stox’s AirPods Pro', 'input') if find_device_index('Stox’s AirPods Pro', 'input') >= 0 else find_device_index('MacBook Pro Microphone', 'input')
SYSTEM_AUDIO_DEVICE_INDEX = find_device_index('BlackHole 2ch', 'output')
# SPEAKER_DEVICE_INDEX = find_device_index('Stox’s AirPods Pro', 'output') if find_device_index('Stox’s AirPods Pro', 'output') >= 0 else find_device_index('MacBook Pro Speakers', 'output')

print('MIC_DEVICE_INDEX:', MIC_DEVICE_INDEX)
print('SYSTEM_AUDIO_DEVICE_INDEX:', SYSTEM_AUDIO_DEVICE_INDEX)
# print('SPEAKER_DEVICE_INDEX:', SPEAKER_DEVICE_INDEX)

# Start the non-blocking recording for microphone and system audio
mic_thread = record_audio_non_blocking('mic_output.wav', MIC_DEVICE_INDEX, channels=1)
system_audio_thread = record_audio_non_blocking('system_output.wav', SYSTEM_AUDIO_DEVICE_INDEX, channels=2)

# Wait for the 's' key to stop the recording
keyboard.wait('s')
stop_audio_recording()

# Merge the recorded audio files
merge_audio_files('mic_output.wav', 'system_output.wav', 'merged_output.wav')

# Transcribe the audio
transcription = transcribe_audio('merged_output.wav')
print('Transcription:', transcription)

# Summarize the transcription
summary = summarize_text(transcription)
print('Summary:', summary)