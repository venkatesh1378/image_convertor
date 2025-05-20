from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import numpy as np
import io
import logging
import traceback
from rembg import remove

app = Flask(__name__)
CORS(app, resources={r"/process": {"origins": "*"}})
app.logger.setLevel(logging.INFO)

MAX_SIZE = 1024  # Maximum dimension for resizing

def process_images(content_img, style_img):
    try:
        # Process content image (remove background)
        content_image = Image.open(content_img).convert("RGBA")
        content_image.thumbnail((MAX_SIZE, MAX_SIZE))
        content_clean = remove(content_image)

        # Process style image (resize to match content)
        style_image = Image.open(style_img).convert("RGBA")
        style_image = style_image.resize(content_clean.size)

        # Combine images
        composite = Image.alpha_composite(style_image, content_clean)
        return composite.convert("RGB")

    except Exception as e:
        app.logger.error(f"Processing error: {traceback.format_exc()}")
        raise

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        if len(files) != 2:
            return jsonify({"error": "Exactly 2 images required"}), 400

        # Process images
        content_file, style_file = files
        result_img = process_images(content_file, style_file)

        # Prepare response
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, "JPEG", quality=90)
        img_byte_arr.seek(0)

        response = send_file(img_byte_arr, mimetype="image/jpeg")
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        app.logger.error(f"Server error: {traceback.format_exc()}")
        return jsonify({
            "error": "Processing failed",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
