# StenographerGPT

StenographerGPT is a tool that uses GPT to record and transcribe meetings, interviews, or any other audio. 

## Installation

To use StenographerGPT, you need to do the following:
- Download BlackHole (a virtual audio driver for macOS) from https://existential.audio/blackhole/.
- Create a new multi-output device with your regular output device (built-in speakers, AirPods, Bluetooth speaker, etc) and BlackHole 2ch. Name it something and set `DEVICE_1_MOD` to the same name in the `.env`.
- Set `DEVICE_1_NAME` to the name of the output device (`MacBook Pro Speakers`, `Adam's AirPods`, etc) in the `.env` file.
- Install the required packages by running `pip install -r requirements.txt` in the terminal.

## Usage

To use StenographerGPT, run `python main.py` in the terminal. Then, use the menu to start a new recording. Once you stop the recording, you'll be presented with a menu of further actions, such as transcribing the recording, editing the transcription, and saving the transcription to a file.

StenographerGPT makes it easy to transcribe audio recordings quickly and accurately, saving you time and effort. Give it a try and see how it can help you with your transcription needs!
