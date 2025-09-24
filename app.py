from flask import Flask, request, jsonify, render_template
from your_code import search, download_audio, download_video  # seu código com funções
import base64

app = Flask(__name__)

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/api/youtube/audio', methods=['POST'])
def api_download_audio():
    data = request.get_json()
    url = data.get('url')
    quality = int(data.get('quality', 128))

    if not url:
        return jsonify({'error': 'URL é obrigatória'}), 400

    result = download_audio(url, quality)

    if not result['ok']:
        return jsonify({'error': result.get('msg')}), 500

    # Retorna link de download base64 ou buffer se preferir
    audio_base64 = base64.b64encode(result['buffer']).decode('utf-8')
    return jsonify({
        'filename': result['filename'],
        'quality': result['quality'],
        'availableQuality': result['availableQuality'],
        'file_base64': audio_base64
    })

@app.route('/api/youtube/video', methods=['POST'])
def api_download_video():
    data = request.get_json()
    url = data.get('url')
    quality = int(data.get('quality', 360))

    if not url:
        return jsonify({'error': 'URL é obrigatória'}), 400

    result = download_video(url, quality)

    if not result['ok']:
        return jsonify({'error': result.get('msg')}), 500

    video_base64 = base64.b64encode(result['buffer']).decode('utf-8')
    return jsonify({
        'filename': result['filename'],
        'quality': result['quality'],
        'availableQuality': result['availableQuality'],
        'file_base64': video_base64
    })

@app.route('/api/youtube/search', methods=['GET'])
def api_search():
    term = request.args.get('q')
    if not term:
        return jsonify({'error': 'Termo de busca é obrigatório'}), 400

    result = search(term)
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)
