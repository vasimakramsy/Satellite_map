from flask import Flask,render_template,request, jsonify
from uuid import uuid4
import os
import requests
import json
import io

import base64

from PIL import Image




app = Flask(__name__, template_folder='templete')

UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files['image']
    bbox = json.loads(request.form['bbox'])  # [x1, y1, x2, y2]
    message = request.form['message']

    # Load the image
    image = Image.open(io.BytesIO(image_file.read())).convert("RGB")

    # Crop using bbox
    x1, y1, x2, y2 = map(int, bbox)
    cropped_image = image.crop((x1, y1, x2, y2))

    # Optional image processing (e.g., resize or enhance)
    processed_image = cropped_image  # or add image processing logic here

    # Encode cropped image as base64
    buffered = io.BytesIO()
    processed_image.save(buffered, format="PNG")
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    base64_string = f"data:image/png;base64,{img_base64}"

    # Send POST request to the remote LitServe API
    api_url = "https://8001-01js3j9z7whtnaqyt11jpqb69r.cloudspaces.litng.ai/predict"
    response = requests.post(api_url, json={"image": base64_string})

    if response.status_code != 200:
        return jsonify({"error": "Failed to get response from model API", "details": response.text}), 500

    result = response.json()

    return jsonify({
        "message": message,
        "model_response": result
    })


if __name__ == "__main__":
    # public_url = ngrok.connect(5000)
    # print(f'PUBLIC URL :{public_url}')
    app.run(host='0.0.0.0', port=5000)

