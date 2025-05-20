from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image
import numpy as np
import io
import logging

app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        # Check for files with correct field name
        if 'files' not in request.files:
            app.logger.error("Missing 'files' field in request")
            return jsonify({"error": "Field 'files' required"}), 400

        files = request.files.getlist('files')
        
        if len(files) != 2:
            return jsonify({"error": "Exactly 2 files required"}), 400

        # Process images
        content_img = Image.open(files[0]).convert('RGB')
        style_img = Image.open(files[1]).convert('RGB')
        
        # Simple blending demo
        content = np.array(content_img)
        style = np.array(style_img)
        result = (content * 0.7 + style * 0.3).astype(np.uint8)
        result_img = Image.fromarray(result)

        # Return image
        img_bytes = io.BytesIO()
        result_img.save(img_bytes, 'JPEG')
        img_bytes.seek(0)
        
        return send_file(img_bytes, mimetype='image/jpeg')

    except Exception as e:
        app.logger.error(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
