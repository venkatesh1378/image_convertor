import os
import io
import base64
import logging
import numpy as np
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from PIL import Image
from rembg import remove

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.DEBUG)

def process_images(content_img, style_img):
    """Process images and return blended result"""
    try:
        # Remove background
        content_clean = remove(content_img)
        content_array = np.array(content_clean)
        
        # Handle RGBA channels
        if content_array.shape[2] == 4:
            foreground = content_array[:, :, :3]
            alpha = content_array[:, :, 3]
        else:
            foreground = content_array
            alpha = np.ones(content_array.shape[:2], dtype=np.uint8) * 255

        # Resize style image
        style_img = style_img.resize((foreground.shape[1], foreground.shape[0]))
        style_array = np.array(style_img)

        # Normalize alpha
        alpha = alpha.astype(np.float32) / 255.0
        alpha = np.expand_dims(alpha, axis=-1)

        # Blend images
        blended = (foreground * alpha) + (style_array * (1 - alpha))
        return Image.fromarray(blended.astype(np.uint8))

    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        raise

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        app.logger.debug("Incoming request files: %s", request.files)

        # Validate files
        if 'content' not in request.files or 'style' not in request.files:
            return jsonify({'error': 'Missing image files'}), 400

        content_file = request.files['content']
        style_file = request.files['style']

        # Validate extensions
        allowed_extensions = {'png', 'jpg', 'jpeg'}
        if not (content_file.filename.lower().endswith(tuple(allowed_extensions)) and
                style_file.filename.lower().endswith(tuple(allowed_extensions))):
            return jsonify({'error': 'Invalid file type. Use JPG/PNG only'}), 400

        # Process images
        content_img = Image.open(content_file.stream).convert('RGB')
        style_img = Image.open(style_file.stream).convert('RGB')
        result_img = process_images(content_img, style_img)

        # Convert to base64
        def img_to_base64(img):
            buff = io.BytesIO()
            img.save(buff, format="PNG")
            return base64.b64encode(buff.getvalue()).decode("utf-8")

        return jsonify({
            'content_img': img_to_base64(content_img),
            'style_img': img_to_base64(style_img),
            'result_img': img_to_base64(result_img)
        })

    except Exception as e:
        app.logger.exception("Server error during processing")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
