from flask import Flask, render_template, request, jsonify
import requests
import os

app = Flask(__name__)
API_ENDPOINT = os.environ.get('API_ENDPOINT', 'http://localhost:5000')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    query = data.get('query', '')
    
    try:
        response = requests.post(
            f"{API_ENDPOINT}/chat",
            json={'query': query},
            timeout=30
        )
        return jsonify(response.json())
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
