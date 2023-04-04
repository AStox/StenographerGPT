import os
import datetime

def create_timestamped_directory(base_path):
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    new_directory = os.path.join(base_path, timestamp)
    os.makedirs(new_directory, exist_ok=True)
    return new_directory
