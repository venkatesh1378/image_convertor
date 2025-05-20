from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import numpy as np
import io
import logging
import traceback

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)

MAX_SIZE = 1024  # Maximum dimension for either width or height

def resize_image(img):
    img.thumbnail((MAX_SIZE, MAX_SIZE))
    return img

def process_images(content_img, style_img):
    try:
        # Open and resize images
        content_image = Image.open(content_img).convert('RGB')
        style_image = Image.open(style_img).convert('RGB')
        
        # Resize both images to match dimensions
        content_image = resize_image(content_image)
        style_image = resize_image(style_image)
        
        # Ensure same size by resizing style to match content
        if content_image.size != style_image.size:
            style_image = style_image.resize(content_image.size)

        # Convert to arrays
        content_array = np.array(content_image)
        style_array = np.array(style_image)

        # Your processing logic (replace with actual style transfer)
        result_array = (content_array * 0.7 + style_array * 0.3).astype(np.uint8)
        
        return Image.fromarray(result_array)

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

        # Return result
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, 'JPG')
        img_byte_arr.seek(0)
        
        return send_file(img_byte_arr, mimetype='image/jpg')

    except Exception as e:
        return jsonify({
            "error": "Processing failed",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
