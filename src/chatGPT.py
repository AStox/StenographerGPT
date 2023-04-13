import requests
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")
messages = []

def chunk_transcript(transcript, max_characters=2048):
    words = transcript.split()
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk + word) < max_characters:
            current_chunk += f" {word}"
        else:
            chunks.append(current_chunk.strip())
            current_chunk = word

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def prime(transcription, max_characters=2048):
    global messages
    chunks = chunk_transcript(transcription, max_characters)

    # Prime the ChatGPT instance with an explainer
    messages = [
        {"role": "system", "content": "You are an AI trained to answer questions about a given text."}
    ]

    # Send the transcript chunks as multiple prompts
    for chunk in chunks:
        messages.append({"role": "user", "content": f"Transcription chunk:\n\n{chunk}"})

    # Add the user's question
    # messages.append({"role": "user", "content": f"My question is: {question}"})

    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': messages
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    answer = response.json()['choices'][0]['message']['content'].strip()
    return answer

def ask(question, max_characters=2048):
    global messages
    messages.append({"role": "user", "content": f"My question is: {question}"})
    get_completion()

def get_completion():
    global messages
    headers = {
        'Authorization': f'Bearer {API_KEY}',
        'Content-Type': 'application/json',
    }
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': messages
    }
    response = requests.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data)
    print(response.json())
    answer = response.json()['choices'][0]['message']['content'].strip()
    messages.append({"role": "assistant", "content": answer})
    return answer
