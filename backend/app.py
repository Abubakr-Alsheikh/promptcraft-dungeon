# backend/app.py
from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
import json

app = Flask(__name__)
CORS(app)  # VERY IMPORTANT for cross-origin requests

def query_ollama(prompt, system_prompt=None):
    try:
        data = {
            "prompt": prompt,
            "model": "deepseek-r1:1.5B",
            "stream": False
        }
        if system_prompt:
            data["system"] = system_prompt

        response = requests.post("http://localhost:11434/api/generate", json=data, timeout=60)  # Add a timeout
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        return json.loads(response.text)['response']

    except requests.exceptions.RequestException as e:
        print(f"Request Exception: {e}")  # Log the exception
        return "Error: Could not connect to Ollama or model error."
    except (KeyError, json.JSONDecodeError) as e:
        print(f"JSON Parsing Error: {e}")
        return "Error: Invalid response from Ollama."
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return "Error: An unexpected error occurred."

@app.route('/api/generate', methods=['POST'])
def generate_text():
    data = request.get_json()
    prompt = data.get('prompt')
    system_prompt = data.get('system_prompt')

    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    response_text = query_ollama(prompt, system_prompt)
    return jsonify({'response': response_text})

if __name__ == '__main__':
    app.run(debug=True, port=5001)  # Run in debug mode for development