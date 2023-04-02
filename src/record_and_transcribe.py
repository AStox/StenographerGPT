import sys
import requests
import json
import functools
import sounddevice as sd
import threading
import keyboard
import soundfile as sf
import numpy as np
from scipy.io import wavfile
from pydub import AudioSegment
from queue import Queue
from dotenv import load_dotenv
# from create_mod import create_multi_output_device
import os

# create_multi_output_device()

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# Global variable to control the recording loop
recording = True
stop_event = threading.Event()


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
        'prompt': f'Summarize the following transcript in english:\n{text}',
        'max_tokens': 2048,
        # 'temperature': 0.5,
    }

    response = requests.post(
        'https://api.openai.com/v1/completions',
        headers=headers,
        json=data
    )

    return response.json()['choices'][0]['text'].strip()

def start_recording(outfile, device_index, channels=1):
    global is_recording
    is_recording = True
    record_thread = threading.Thread(target=record_audio_non_blocking, args=(outfile, device_index, channels))
    record_thread.start()

def stop_recording():
    global is_recording
    is_recording = False
    stop_event.set()

def record_audio_non_blocking(outfile, device_index, channels):
    with sf.SoundFile(outfile, mode='w', samplerate=48000, channels=channels) as file:
        with sd.InputStream(callback=functools.partial(callback, file), channels=channels, samplerate=48000, device=device_index):
            print('Recording started.')
            stop_event.wait()
            print('Recording stopped.')

# def record_audio_non_blocking(outfile, device_index, seconds=None, channels=1):
#     def record(outfile, device_index, seconds, channels):
#         with sf.SoundFile(outfile, mode='w', samplerate=48000, channels=channels) as file:
#             with sd.InputStream(callback=functools.partial(callback, file), channels=channels, samplerate=48000, device=device_index):
#                 print('Recording started.')
#                 while True:
#                     sd.sleep(500)
#                     if keyboard.is_pressed('s'):
#                         break
#                     if seconds is not None:
#                         sd.sleep(seconds * 1000)
#                         break
#         print('Recording stopped.')

#     record_thread = threading.Thread(target=record, args=(outfile, device_index, seconds, channels))
#     record_thread.start()
#     return record_thread

def stop_audio_recording():
    global recording
    recording = False

def callback(file, indata, frames, time, status):
    if status:
        print(status, file=sys.stderr)
    file.write(indata)

def file_exists_and_not_empty(file_path):
    return os.path.exists(file_path) and os.path.getsize(file_path) > 0

def print_audio_duration(file_path):
    with sf.SoundFile(file_path) as audio_file:
        duration = len(audio_file) / audio_file.samplerate
        print(f"{file_path} duration: {duration} seconds")




def merge_audio_files(file1, file2, output_file):
    # Read the input files
    audio1_data, samplerate1 = sf.read(file1)
    audio2_data, samplerate2 = sf.read(file2)

    # Ensure both audio arrays are 2D (channels x samples)
    if audio1_data.ndim == 1:
        audio1_data = audio1_data[:, np.newaxis]
    if audio2_data.ndim == 1:
        audio2_data = audio2_data[:, np.newaxis]

    # Upmix the audio files to the same number of channels
    max_channels = max(audio1_data.shape[1], audio2_data.shape[1])
    if audio1_data.shape[1] < max_channels:
        audio1_data = np.tile(audio1_data, (1, max_channels // audio1_data.shape[1]))
    if audio2_data.shape[1] < max_channels:
        audio2_data = np.tile(audio2_data, (1, max_channels // audio2_data.shape[1]))

    # Check if the input files have the same sample rate
    if samplerate1 != samplerate2:
        raise ValueError("Input files must have the same sample rate")

    # Make sure the input files have the same length
    if audio1_data.shape[0] < audio2_data.shape[0]:
        pad = np.zeros((audio2_data.shape[0] - audio1_data.shape[0], audio1_data.shape[1]), dtype=audio1_data.dtype)
        audio1_data = np.vstack((audio1_data, pad))
    else:
        pad = np.zeros((audio1_data.shape[0] - audio2_data.shape[0], audio2_data.shape[1]), dtype=audio2_data.dtype)
        audio2_data = np.vstack((audio2_data, pad))

    # Merge the audio data
    merged_data = audio1_data + audio2_data

    # Write the output file
    sf.write(output_file, merged_data, samplerate1)



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
# devices = sd.query_devices()
# for index, device in enumerate(devices):
#     # print index name and max input channels and max output channels
#     print(f"Device Index: {index}, Device Name: {device['name']}, Max Input Channels: {device['max_input_channels']}," +
#           f" Max Output Channels: {device['max_output_channels']}")

# Find the device indices
# ternary operator to handle the case where the AirPods Pro are not connected
MIC_DEVICE_INDEX = find_device_index('Stox’s AirPods Pro', 'input') if find_device_index('Stox’s AirPods Pro', 'input') >= 0 else find_device_index('MacBook Pro Microphone', 'input')
SYSTEM_AUDIO_DEVICE_INDEX = find_device_index('BlackHole 2ch', 'output')

print('MIC_DEVICE_INDEX:', MIC_DEVICE_INDEX)
print('SYSTEM_AUDIO_DEVICE_INDEX:', SYSTEM_AUDIO_DEVICE_INDEX)

# # Start the non-blocking recording for microphone and system audio
# mic_thread = record_audio_non_blocking('mic_output.wav', MIC_DEVICE_INDEX, channels=1)
# system_audio_thread = record_audio_non_blocking('system_output.wav', SYSTEM_AUDIO_DEVICE_INDEX, channels=2)

# # Wait for the 's' key to stop the recording
# keyboard.wait('s')
# stop_audio_recording()

# # Merge the recorded audio files
# merge_audio_files('mic_output.wav', 'system_output.wav', 'merged_output.wav')

# # Transcribe the audio
# transcription = transcribe_audio('merged_output.wav')
# print('Transcription:', transcription)

# # Summarize the transcription
# summary = summarize_text(transcription)
# print('Summary:', summary)

def process_audio(mic_output, system_output, merged_output):
    # Merge the recorded audio files
    merge_audio_files(mic_output, system_output, merged_output)

    # Transcribe the audio
    transcription = transcribe_audio(merged_output)
    print('Transcription:', transcription)

    # Summarize the transcription
    summary = summarize_text(transcription)
    print('Summary:', summary)

# start_recording('mic_output.wav', MIC_DEVICE_INDEX, 1)
# start_recording('system_output.wav', SYSTEM_AUDIO_DEVICE_INDEX, 2)
# keyboard.wait('s')
# stop_recording()
# process_audio('mic_output.wav', 'system_output.wav', 'merged_output.wav')