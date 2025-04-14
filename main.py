from flask import Flask,render_template,request, jsonify
from uuid import uuid4
import os
import requests

from PIL import Image
import io
import json


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

    image = request.files['image']
    bbox = json.loads(request.form['bbox'])
    message = request.form['message']

    image = Image.open(io.BytesIO(image.read()))
    # Save image
    image_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{'UPLOADED'}.png")
    image.save(image_path)

    # Placeholder response - Replace with actual model processing
    response_text = f"Processed image with BBox: {bbox} and message: {message}"

    return jsonify({"message": message, "response": response_text})


if __name__ == "__main__":
    # public_url = ngrok.connect(5000)
    # print(f'PUBLIC URL :{public_url}')
    app.run(host='0.0.0.0', port=5000)

