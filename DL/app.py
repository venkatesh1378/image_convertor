from flask import Flask, request, jsonify, send_file
from flask_cors import CORS  # Add CORS support
from PIL import Image
import numpy as np
import io
import logging
import traceback

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests
app.logger.setLevel(logging.DEBUG)  # Increase logging verbosity

def validate_image(image):
    try:
        img = Image.open(image)
        img.verify()
        image.stream.seek(0)  # Critical: Reset file pointer after verification
        return True, None
    except Exception as e:
        error_msg = f"Invalid image file {image.filename}: {str(e)}"
        app.logger.error(error_msg)
        return False, error_msg

def process_images(content_img, style_img):
    try:
        # Load images with explicit format handling
        content_image = Image.open(content_img).convert('RGB')
        style_image = Image.open(style_img).convert('RGB')
        
        # Convert to numpy arrays
        content_array = np.array(content_image)
        style_array = np.array(style_image)

        # Ensure same dimensions
        if content_array.shape != style_array.shape:
            content_image = content_image.resize(style_image.size)
            content_array = np.array(content_image)

        # Demo processing (replace with your actual logic)
        result_array = (content_array * 0.7 + style_array * 0.3).astype(np.uint8)
        result_img = Image.fromarray(result_array)
        
        app.logger.debug("Successfully generated result image")
        return result_img

    except Exception as e:
        app.logger.error(f"Processing failed: {traceback.format_exc()}")
        raise

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        app.logger.debug("Received request with headers: %s", request.headers)
        
        if 'files' not in request.files:
            app.logger.error("No files part in request")
            return jsonify({"status": "error", "message": "No files uploaded"}), 400

        files = request.files.getlist('files')
        app.logger.debug("Received %d files", len(files))

        if len(files) != 2:
            return jsonify({"status": "error", "message": "Exactly 2 images required"}), 400

        # Validate images with detailed feedback
        validations = [validate_image(f) for f in files]
        if not all(valid for valid, _ in validations):
            errors = [msg for _, msg in validations if msg]
            return jsonify({
                "status": "error",
                "message": "Invalid image files",
                "errors": errors
            }), 400

        # Process images
        content_file, style_file = files
        result_img = process_images(content_file, style_file)

        # Prepare response with explicit encoding
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, format='JPEG', quality=95)
        img_byte_arr.seek(0)
        app.logger.debug("Sending response with image size: %d bytes", img_byte_arr.getbuffer().nbytes)

        return send_file(img_byte_arr, mimetype='image/jpeg')

    except Exception as e:
        app.logger.error("Critical error: %s", traceback.format_exc())
        return jsonify({
            "status": "error",
            "message": "Processing failed",
            "error": str(e),
            "trace": traceback.format_exc()
        }), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
