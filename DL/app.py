import os
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from PIL import Image
import io
import base64
import numpy as np
from rembg import remove

app = Flask(__name__)
CORS(app)  # Enable CORS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

def process_image(content_img, style_img):
    # Remove background from content image
    content = remove(content_img)
    content_array = np.array(content)
    
    # Extract foreground and mask
    foreground = content_array[:, :, :3]
    mask = content_array[:, :, 3]
    
    # Process style image
    style = style_img.resize((foreground.shape[1], foreground.shape[0]))
    style_array = np.array(style)
    
    # Normalize mask
    mask = mask.astype(np.float32) / 255.0
    mask = np.expand_dims(mask, axis=-1)
    
    # Blend images
    result = (foreground * mask) + (style_array * (1 - mask))
    return Image.fromarray(result.astype(np.uint8))

def image_to_base64(img):
    buff = io.BytesIO()
    img.save(buff, format="PNG")
    return base64.b64encode(buff.getvalue()).decode("utf-8")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def handle_processing():
    try:
        if 'content' not in request.files or 'style' not in request.files:
            return jsonify({'error': 'Missing image files'}), 400

        content_file = request.files['content']
        style_file = request.files['style']

        # Open images
        content_img = Image.open(content_file.stream)
        style_img = Image.open(style_file.stream)

        # Validate image formats
        if content_img.format not in ('PNG', 'JPEG') or style_img.format not in ('PNG', 'JPEG'):
            return jsonify({'error': 'Invalid image format. Use JPEG/PNG'}), 400

        # Process images
        result_img = process_image(content_img, style_img)

        # Prepare response
        return jsonify({
            'content_img': image_to_base64(content_img),
            'style_img': image_to_base64(style_img),
            'result_img': image_to_base64(result_img)
        })

    except Exception as e:
        app.logger.error(f'Error processing images: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
