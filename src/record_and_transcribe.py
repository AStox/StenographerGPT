import sys
import requests
import functools
import sounddevice as sd
import threading
import soundfile as sf
import numpy as np
from pydub import AudioSegment
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# Global variable to control the recording loop
recording = True
stop_event = threading.Event()


def transcribe_audio(audio_file, chunk_duration=60):
    audio = AudioSegment.from_wav(audio_file)
    audio_duration = audio.duration_seconds
    chunk_size = chunk_duration * 1000  # chunk_duration in milliseconds
    transcriptions = []

    for i in range(0, int(audio_duration * 1000), chunk_size):
        chunk = audio[i:i + chunk_size]
        chunk_file = 'temp_chunk.wav'
        chunk.export(chunk_file, format='wav')

        headers = {
            'Authorization': f'Bearer {API_KEY}',
        }

        with open(chunk_file, 'rb') as f:
            audio_data = f.read()
            response = requests.post(
                'https://api.openai.com/v1/audio/transcriptions',
                headers=headers,
                data={'model': 'whisper-1'},
                files={'file': ('temp_chunk.wav', audio_data, 'audio/wav')}
            )
            print(response.json())
            transcription = response.json()['text']
            transcriptions.append(transcription)

    os.remove('temp_chunk.wav')
    full_transcription = ' '.join(transcriptions)
    return full_transcription


import time

def summarize_text(text):
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }

    tokens = text.split()
    chunks = []

    while tokens:
        chunk_tokens = []
        while tokens and len(chunk_tokens) + len(tokens[0]) + 1 < 2048:
            token = tokens.pop(0)
            chunk_tokens.append(token)
        chunks.append(' '.join(chunk_tokens))

    summaries = []

    for chunk in chunks:
        messages = [
            {'role': 'system', 'content': 'You are an AI language model trained to summarize text. Please provide a detailed summary of the following transcription:'},
            {'role': 'user', 'content': chunk}
        ]

        data = {
            'model': 'gpt-3.5-turbo',
            'messages': messages
        }

        response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
        print(response.json())
        summary = response.json()['choices'][0]['message']['content']
        summaries.append(summary)

        time.sleep(1)  # Pause between API requests to avoid rate limits

    combined_summary = ' '.join(summaries)
    return combined_summary


def start_recording(output_directory):
    stop_event.clear()
    _start_recording(os.path.join(output_directory, "mic_output.wav"), MIC_DEVICE_INDEX, 1)
    _start_recording(os.path.join(output_directory, "system_output.wav"), SYSTEM_AUDIO_DEVICE_INDEX, 2)

def _start_recording(outfile, device_index, channels=1):
    global is_recording
    is_recording = True
    record_thread = threading.Thread(target=record_audio_non_blocking, args=(outfile, device_index, channels))
    record_thread.start()

def stop_recording(output_directory):
    global is_recording
    is_recording = False
    stop_event.set()
    # process_audio(output_directory, output_directory)

def record_audio_non_blocking(outfile, device_index, channels):
    with sf.SoundFile(outfile, mode='w', samplerate=48000, channels=channels) as file:
        with sd.InputStream(callback=functools.partial(callback, file), channels=channels, samplerate=48000, device=device_index):
            # print('Recording started.')
            stop_event.wait()
            # print('Recording stopped.')

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

# print('MIC_DEVICE_INDEX:', MIC_DEVICE_INDEX)
# print('SYSTEM_AUDIO_DEVICE_INDEX:', SYSTEM_AUDIO_DEVICE_INDEX)



def process_audio(input_directory, output_directory):
    mic_output = os.path.join(input_directory, "mic_output.wav")
    system_output = os.path.join(input_directory, "system_output.wav")
    merged_output = os.path.join(output_directory, "merged_output.wav")
    # Merge the recorded audio files
    merge_audio_files(mic_output, system_output, merged_output)

    # Transcribe the audio
    transcription = transcribe_audio(merged_output)
    print(transcription);
    transcript_file = os.path.join(output_directory, "transcript.txt")
    with open(transcript_file, "w") as f:
        f.write(transcription)


    # Summarize the transcription
    summary_file = os.path.join(output_directory, "summary.txt")
    summary = summarize_text(transcription)
    with open(summary_file, "w") as f:
        f.write(summary)
    print('Summary:', summary)

# stop_recording('archive/office')
# output_directory = 'archive/office'
# with open('archive/office/transcript.txt', 'r') as file:
#     transcription_text = file.read()
#     summary_file = os.path.join(output_directory, "summary.txt")
#     summary = summarize_text(transcription_text)
#     with open(summary_file, "w") as f:
#         f.write(summary)
#     print('Summary:', summary)