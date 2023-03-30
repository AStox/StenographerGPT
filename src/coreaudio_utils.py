import objc
from Foundation import NSBundle

# Load the CoreAudioKit bundle
core_audio_kit_bundle = NSBundle.bundleWithIdentifier_(b'com.apple.audio.CoreAudioKit')
objc.loadBundleFunctions(core_audio_kit_bundle, globals(), [
    ('CACreateAggregateDevice', '@@:*')
])

def create_mod(audio_device_uids):
    # Create the multi-output device
    mod = CACreateAggregateDevice(audio_device_uids, None)

    if mod is None:
        raise RuntimeError('Failed to create multi-output device.')

    return mod

def set_system_output_device(device_uid):
    # Your implementation to set the system output device
    pass

def remove_mod(mod_uid):
    # Your implementation to remove the multi-output device
    pass

def main():
    # Add the UIDs of the devices you want to include in the Multi-Output Device
    sub_device_uids = [
        "BlackHole_UID",
        "AirPods_UID"
    ]
    create_mod(sub_device_uids)

if __name__ == "__main__":
    main()
