from flask import Flask, request, jsonify, send_file
from PIL import Image
import numpy as np
import io
import logging
import traceback

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

def validate_image(image):
    try:
        img = Image.open(image)
        img.verify()
        image.stream.seek(0)  # Reset file pointer
        return True
    except Exception as e:
        app.logger.error(f"Invalid image file: {str(e)}")
        return False

def process_images(content_img, style_img):
    try:
        # Load and convert content image
        content_image = Image.open(content_img)
        content_array = np.array(content_image)
        
        # Handle RGBA images
        if content_array.shape[2] == 4:
            content_array = content_array[..., :3]

        # Load and convert style image
        style_image = Image.open(style_img)
        style_array = np.array(style_image)
        
        if style_array.shape[2] == 4:
            style_array = style_array[..., :3]

        # Simple alpha blending for demonstration
        result_array = (content_array * 0.7 + style_array * 0.3).astype(np.uint8)
        
        # Convert numpy array back to PIL Image
        result_img = Image.fromarray(result_array)
        return result_img

    except Exception as e:
        app.logger.error(f"Processing error: {traceback.format_exc()}")
        raise

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        if 'files' not in request.files:
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        app.logger.info(f"Files received: {[(f.filename, f.content_type) for f in files]}")

        if len(files) != 2:
            return jsonify({"error": "Exactly 2 images required"}), 400

        # Validate images
        if not all(validate_image(f) for f in files):
            return jsonify({"error": "Invalid image file(s)"}), 400

        # Process images
        content_file = files[0]
        style_file = files[1]
        result_img = process_images(content_file, style_file)

        # Prepare response
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)

        return send_file(img_byte_arr, mimetype='image/jpeg')

    except Exception as e:
        app.logger.error(f"Server error: {traceback.format_exc()}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
