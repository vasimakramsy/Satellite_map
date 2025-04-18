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
    bbox = json.loads(request.form['bbox'])  # Expected to be dict
    message = request.form['message']

    # Load image and get dimensions
    image = Image.open(io.BytesIO(image_file.read())).convert("RGB")
    width, height = image.size

    # Extract and convert bbox to pixel coordinates
    try:
        top = int(bbox["north"] * height)
        bottom = int(bbox["south"] * height)
        left = int(bbox["west"] * width)
        right = int(bbox["east"] * width)

        # Clamp values to image bounds
        top = max(0, min(top, height))
        bottom = max(0, min(bottom, height))
        left = max(0, min(left, width))
        right = max(0, min(right, width))

        if bottom <= top or right <= left:
            return jsonify({"error": "Invalid bbox after clamping."}), 400

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid bounding box format: {e}"}), 400

    # Crop and process the image
    cropped_image = image.crop((left, top, right, bottom))

    # Convert to base64
    buffered = io.BytesIO()
    cropped_image.save(buffered, format="PNG")  # This line caused the crash if bbox was out of bounds
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    base64_string = f"data:image/png;base64,{img_base64}"

    # Send to external API
    api_url = "https://8001-01js3j9z7whtnaqyt11jpqb69r.cloudspaces.litng.ai/predict"
    response = requests.post(api_url, json={"image": base64_string})

    if response.status_code != 200:
        return jsonify({"error": "Failed to get response from model API", "details": response.text}), 500

    return jsonify({
        "message": message,
        "model_response": response.json()
    })


if __name__ == "__main__":
    # public_url = ngrok.connect(5000)
    # print(f'PUBLIC URL :{public_url}')
    app.run(host='0.0.0.0', port=5000)

