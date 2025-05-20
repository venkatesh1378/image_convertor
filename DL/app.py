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
        return True, None
    except Exception as e:
        error_msg = f"Invalid image file {image.filename}: {str(e)}"
        app.logger.error(error_msg)
        return False, error_msg

def process_images(content_img, style_img):
    try:
        # Load and convert images
        content_image = Image.open(content_img)
        style_image = Image.open(style_img)
        
        # Convert to arrays
        content_array = np.array(content_image)
        style_array = np.array(style_image)

        # Handle alpha channels
        if content_array.shape[2] == 4:
            content_array = content_array[..., :3]
        if style_array.shape[2] == 4:
            style_array = style_array[..., :3]

        # Check image sizes
        if content_array.shape != style_array.shape:
            raise ValueError(
                f"Image size mismatch. Content: {content_array.shape}, Style: {style_array.shape}"
            )

        # Demo processing (replace with your actual logic)
        result_array = (content_array * 0.7 + style_array * 0.3).astype(np.uint8)
        return Image.fromarray(result_array)

    except Exception as e:
        app.logger.error(f"Processing error: {traceback.format_exc()}")
        raise

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        if 'files' not in request.files:
            return jsonify({
                "status": "error",
                "message": "No files uploaded"
            }), 400

        files = request.files.getlist('files')
        app.logger.info(f"Files received: {[(f.filename, f.content_type) for f in files]}")

        if len(files) != 2:
            return jsonify({
                "status": "error",
                "message": "Exactly 2 images required"
            }), 400

        # Validate images
        validations = [validate_image(f) for f in files]
        if not all(valid for valid, _ in validations):
            errors = [msg for _, msg in validations if msg is not None]
            return jsonify({
                "status": "error",
                "message": "Invalid image files",
                "errors": errors
            }), 400

        # Process images
        content_file, style_file = files
        result_img = process_images(content_file, style_file)

        # Return result
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, format='JPEG')
        img_byte_arr.seek(0)
        
        return send_file(img_byte_arr, mimetype='image/jpeg')

    except Exception as e:
        app.logger.error(f"Server error: {traceback.format_exc()}")
        return jsonify({
            "status": "error",
            "message": "Internal server error",
            "error_details": str(e)
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=False)
