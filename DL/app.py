import os
from flask import Flask, render_template, request, send_file
import cv2
import numpy as np
from rembg import remove
from flask import jsonify
from PIL import Image
import io
import base64

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB limit

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process', methods=['POST'])
def process():
    if 'content' not in request.files or 'style' not in request.files:
        return "Please upload both images", 400

    content_file = request.files['content']
    style_file = request.files['style']

    # Process images
    try:
        # Read and process content image
        content_img = np.array(Image.open(content_file.stream))
        output = remove(content_img)
        foreground = output[:, :, :3]
        mask = output[:, :, 3]

        # Process style image
        style_img = np.array(Image.open(style_file.stream))
        styled_bg = cv2.resize(style_img, (foreground.shape[1], foreground.shape[0]))

        # Blend images
        mask = mask.astype(np.float32) / 255.0
        mask = np.expand_dims(mask, axis=-1)
        result = (foreground * mask) + (styled_bg * (1 - mask))
        result = result.astype(np.uint8)

        # Convert images to base64 for display
        def img_to_base64(img):
            pil_img = Image.fromarray(img)
            buff = io.BytesIO()
            pil_img.save(buff, format="PNG")
            return base64.b64encode(buff.getvalue()).decode("utf-8")

        content_b64 = img_to_base64(cv2.cvtColor(content_img, cv2.COLOR_RGB2BGR))
        style_b64 = img_to_base64(styled_bg)
        result_b64 = img_to_base64(result)

        # Create download link
        result_bytes = io.BytesIO()
        Image.fromarray(result).save(result_bytes, format='PNG')
        result_bytes.seek(0)
        return jsonify({
            'content_img': content_b64,
            'style_img': style_b64,
            'result_img': result_b64
        })
        

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
