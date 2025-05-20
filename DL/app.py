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
CORS(app, resources={r"/process": {"origins": "*"}})
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

# Configure logging
logging.basicConfig(level=logging.INFO)
app.logger.setLevel(logging.DEBUG)

def process_images(content_img, style_img):
    """Main processing pipeline"""
    try:
        # Remove background from content image
        content_clean = remove(content_img)
        content_array = np.array(content_clean)
        
        # Extract RGBA channels
        if content_array.shape[2] == 4:
            foreground = content_array[:, :, :3]
            alpha = content_array[:, :, 3]
        else:
            foreground = content_array
            alpha = np.ones_like(content_array[:, :, 0]) * 255

        # Resize style image to match content dimensions
        style_img = style_img.resize((foreground.shape[1], foreground.shape[0]))
        style_array = np.array(style_img)

        # Normalize alpha channel [0, 1]
        alpha = alpha.astype(np.float32) / 255.0
        alpha = np.expand_dims(alpha, axis=-1)

        # Blend images
        blended = (foreground * alpha) + (style_array * (1 - alpha))
        return Image.fromarray(blended.astype(np.uint8))

    except Exception as e:
        app.logger.error(f"Processing error: {str(e)}")
        raise

def image_to_base64(pil_img):
    """Convert PIL image to base64 string"""
    try:
        buffer = io.BytesIO()
        pil_img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as e:
        app.logger.error(f"Base64 conversion error: {str(e)}")
        raise

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        app.logger.debug("Incoming request headers: %s", request.headers)
        app.logger.debug("Received files: %s", request.files)

        # Validate request
        if 'content' not in request.files or 'style' not in request.files:
            return jsonify({'error': 'Missing required image files'}), 400

        content_file = request.files['content']
        style_file = request.files['style']

        # Validate file types
        if not allowed_file(content_file.filename) or not allowed_file(style_file.filename):
            return jsonify({'error': 'Invalid file type. Use JPG/PNG only'}), 400

        # Open and verify images
        content_img = Image.open(content_file.stream)
        style_img = Image.open(style_file.stream)
        
        # Convert to RGB if necessary
        if content_img.mode != 'RGB':
            content_img = content_img.convert('RGB')
        if style_img.mode != 'RGB':
            style_img = style_img.convert('RGB')

        # Process images
        result_img = process_images(content_img, style_img)

        # Generate previews
        return jsonify({
            'content_img': image_to_base64(content_img),
            'style_img': image_to_base64(style_img),
            'result_img': image_to_base64(result_img)
        })

    except Exception as e:
        app.logger.error(f"Request handling error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
