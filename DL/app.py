import os
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
import cv2
import numpy as np
from rembg import remove
from PIL import Image
import io
import base64
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

def process_image(content_file, style_file):
    # Process content image
    content_img = np.array(Image.open(content_file))
    output = remove(content_img)
    foreground = output[:, :, :3]
    mask = output[:, :, 3]

    # Process style image
    style_img = np.array(Image.open(style_file))
    styled_bg = cv2.resize(style_img, (foreground.shape[1], foreground.shape[0]))

    # Blend images
    mask = mask.astype(np.float32) / 255.0
    mask = np.expand_dims(mask, axis=-1)
    result = (foreground * mask) + (styled_bg * (1 - mask))
    return result.astype(np.uint8)

def image_to_base64(img_array):
    img = Image.fromarray(img_array)
    buff = io.BytesIO()
    img.save(buff, format="PNG")
    return base64.b64encode(buff.getvalue()).decode("utf-8")

@app.route('/process', methods=['POST'])
def process():
    try:
        if 'content' not in request.files or 'style' not in request.files:
            return jsonify({'error': 'Missing files'}), 400

        content_file = request.files['content']
        style_file = request.files['style']

        # Validate file extensions
        if not (content_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')) or \
           not (style_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')))):
            return jsonify({'error': 'Invalid file format'}), 400

        # Process images
        result_array = process_image(content_file, style_file)
        
        # Convert original images to base64
        content_img = np.array(Image.open(content_file))
        style_img = np.array(Image.open(style_file))

        return jsonify({
            'content_img': image_to_base64(content_img),
            'style_img': image_to_base64(cv2.resize(style_img, (content_img.shape[1], content_img.shape[0]))),
            'result_img': image_to_base64(result_array)
        })

    except Exception as e:
        app.logger.error(f'Error processing image: {str(e)}')
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
