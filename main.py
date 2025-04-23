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

UPLOAD_TEST = 'test'
app.config['UPLOAD_TEST'] = UPLOAD_TEST 

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_TEST, exist_ok=True)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    print("Request files:", request.files)
    print("Request form:", request.form)

    
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image_file = request.files['image']
    try:
        bbox = json.loads(request.form['bbox'])  # Expected to be dict
        message = request.form['message']
        print(message)

        print(bbox)
        # Load image and get dimensions
        image = Image.open(io.BytesIO(image_file.read())).convert("RGB")
        width, height = image.size

        image.save(f"{app.config['UPLOAD_TEST']}/{uuid4()}.png")

        # Calculate pixel coordinates for bbox (lat/lng to pixel)
        # Assumes you know the map center, zoom, and image size used in static map
        def latlng_to_pixel(lat, lng, center_lat, center_lng, zoom, img_width, img_height):
            import math
            TILE_SIZE = 256
            scale = 2 ** zoom
            def latlng_to_world(lat, lng):
                siny = math.sin(lat * math.pi / 180)
                siny = min(max(siny, -0.9999), 0.9999)
                x = TILE_SIZE * (0.5 + lng / 360)
                y = TILE_SIZE * (0.5 - math.log((1 + siny) / (1 - siny)) / (4 * math.pi))
                return x * scale, y * scale
            center_x, center_y = latlng_to_world(center_lat, center_lng)
            world_x, world_y = latlng_to_world(lat, lng)
            dx = world_x - center_x
            dy = world_y - center_y
            px = img_width // 2 + int(dx)
            py = img_height // 2 + int(dy)
            return px, py

        # These should match the frontend static map params
        zoom = 15
        img_width = 600
        img_height = 400
        center_lat = (bbox["north"] + bbox["south"]) / 2
        center_lng = (bbox["east"] + bbox["west"]) / 2

        # Get pixel coordinates for bbox corners
        left, top = latlng_to_pixel(bbox["north"], bbox["west"], center_lat, center_lng, zoom, img_width, img_height)
        right, bottom = latlng_to_pixel(bbox["south"], bbox["east"], center_lat, center_lng, zoom, img_width, img_height)

        # Clamp values to image bounds
        top = max(0, min(top, height))
        bottom = max(0, min(bottom, height))
        left = max(0, min(left, width))
        right = max(0, min(right, width))

        # Crop the bbox region
        cropped_image = image.crop((left, top, right, bottom))
        cropped_path = f"{app.config['UPLOAD_FOLDER']}/cropped_{uuid4()}.png"
        cropped_image.save(cropped_path)
        print(f"Cropped bbox saved to {cropped_path}")

        if bottom <= top or right <= left:
            return jsonify({"error": "Invalid bbox after clamping."}), 400

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid bounding box format: {e}"}), 400

    except (KeyError, TypeError, ValueError) as e:
        return jsonify({"error": f"Invalid bounding box format: {e}"}), 400

    # Crop and process the image
    cropped_image = image.crop((left, top, right, bottom))

    # Convert to base64
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")  # This line caused the crash if bbox was out of bounds
    img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
    base64_string = f"data:image/png;base64,{img_base64}"

    # Send to external API
    api_url = "https://8001-01js3j9z7whtnaqyt11jpqb69r.cloudspaces.litng.ai/predict"
    

    # Prepare payload with base64 image
    payload = {"image": base64_string}

    # Send POST request to the server
    response = requests.post(api_url, json=payload)

    # Print the response from the server
    print(response.json())
    
    response_text = "hi recived response"
    if response.status_code != 200:
        return jsonify({"error": "Failed to get response from model API", "details": response.text}), 500

    return jsonify({
        "message": message,
        "response": response.json()
    })


if __name__ == "__main__":
    # public_url = ngrok.connect(5000)
    # print(f'PUBLIC URL :{public_url}')
    app.run(host='0.0.0.0', port=5000)

