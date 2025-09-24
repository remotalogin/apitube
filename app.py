from flask import Flask, request, jsonify, render_template
from seu_script_de_download import download_audio, download_video  # importe suas funções aqui

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/download_audio', methods=['POST'])
def api_download_audio():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', 128)
    if not url:
        return jsonify({'ok': False, 'msg': 'URL não fornecida'}), 400

    result = download_audio(url, quality)
    if result['ok']:
        return jsonify({
            'ok': True,
            'filename': result['filename'],
            'quality': result['quality'],
            'download_url': result['url'] if 'url' in result else None,
            # Atenção: 'buffer' não pode ser enviado via JSON, deve salvar arquivo ou enviar streaming
        })
    else:
        return jsonify({'ok': False, 'msg': result['msg']}), 400

@app.route('/api/download_video', methods=['POST'])
def api_download_video():
    data = request.json
    url = data.get('url')
    quality = data.get('quality', 360)
    if not url:
        return jsonify({'ok': False, 'msg': 'URL não fornecida'}), 400

    result = download_video(url, quality)
    if result['ok']:
        return jsonify({
            'ok': True,
            'filename': result['filename'],
            'quality': result['quality'],
            'download_url': result['url'] if 'url' in result else None,
        })
    else:
        return jsonify({'ok': False, 'msg': result['msg']}), 400

if __name__ == '__main__':
    app.run(debug=True)
