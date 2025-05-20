from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import io
import logging
from rembg import remove

app = Flask(__name__)
CORS(app, resources={r"/process": {"origins": "*"}})  # Explicit CORS config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/process', methods=['POST', 'OPTIONS'])
def handle_processing():
       try:
        logger.info("Received request with headers: %s", request.headers)
        
        if 'files' not in request.files:
            logger.error("No files part in request")
            return jsonify({"error": "No files uploaded"}), 400

        files = request.files.getlist('files')
        if len(files) != 2:
            return jsonify({"error": "Exactly 2 images required"}), 400

        # Process images
        content_file, style_file = files
        result_img = process_images(content_file, style_file)

        # Prepare response
        img_byte_arr = io.BytesIO()
        result_img.save(img_byte_arr, "JPEG")
        img_byte_arr.seek(0)
        
       response = send_file(img_byte_arr, mimetype="image/jpeg")
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        return jsonify({
            "error": "Processing failed",
            "message": str(e)
        }), 500

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
