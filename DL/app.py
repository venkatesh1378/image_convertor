from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import numpy as np
import io
import logging
from rembg import remove

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)

MAX_SIZE = 1024  # Max dimension for processing

def process_images(content_img, style_img):
    try:
        # Process content image (remove background)
        content_image = Image.open(content_img).convert("RGBA")
        content_image.thumbnail((MAX_SIZE, MAX_SIZE))
        content_clean = remove(content_image)  # Background removal
        
        # Process style image (new background)
        style_image = Image.open(style_img).convert("RGBA")
        style_image = style_image.resize(content_clean.size)
        
        # Combine images
        composite = Image.alpha_composite(style_image, content_clean)
        
        return composite.convert("RGB")

    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        raise

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        if len(files) != 2:
            return jsonify({"error": "Exactly 2 images required"}), 400

        # First file: content (foreground), Second file: style (background)
        content_file, style_file = files
        result_img = process_images(content_file, style_file)

        # Return result
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, "JPEG")
        img_byte_arr.seek(0)
        
        return send_file(img_byte_arr, mimetype="image/jpeg")

    except Exception as e:
        return jsonify({
            "error": "Processing failed",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
