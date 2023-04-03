import subprocess

AudioTypes = {
    'speakers': 'MacBook Pro Speakers',
    'headphones': 'Stox’s AirPods Pro',
    'blackhole': 'BlackHole 2ch',
    'speakers_BH': 'Speakers + Blackhole',
    'headphones_BH': 'AirPods + Blackhole',
}

previous_audio_device = None

def get_audio_devices():
    output = subprocess.check_output(['SwitchAudioSource', '-a']).decode('utf-8')
    devices = [line.strip() for line in output.split('\n') if line]
    return devices

def get_current_audio_device():
    output = subprocess.check_output(['SwitchAudioSource', '-c']).decode('utf-8')
    return output.strip()

def set_audio_output_device(device_name):
    subprocess.check_call(['SwitchAudioSource', '-s', device_name])

def switch_to_blackhole():
    previous_audio_device = get_current_audio_device()
    if (previous_audio_device == AudioTypes['speakers']):
        set_audio_output_device(AudioTypes['speakers_BH'])
    elif (previous_audio_device == AudioTypes['headphones']):
        set_audio_output_device(AudioTypes['headphones_BH'])

def switch_to_previous_device():
    if (previous_audio_device == AudioTypes['speakers']):
        set_audio_output_device(AudioTypes['speakers'])
    elif (previous_audio_device == AudioTypes['headphones']):
        set_audio_output_device(AudioTypes['headphones'])