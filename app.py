from flask import Flask, request, jsonify, send_file
from io import BytesIO
import time
import requests
import base64
import json
from Crypto.Cipher import AES
from youtube_search import YoutubeSearch

app = Flask(__name__)

AUDIO_QUALITIES = [92, 128, 256, 320]
VIDEO_QUALITIES = [144, 360, 480, 720, 1080]

search_cache = {}
metadata_cache = {}

def clean_cache():
    now = time.time()
    for k in list(search_cache.keys()):
        if now - search_cache[k]['timestamp'] > 3600:
            del search_cache[k]
    for k in list(metadata_cache.keys()):
        if now - metadata_cache[k]['timestamp'] > 1800:
            del metadata_cache[k]

def get_youtube_video_id(url):
    import re
    regex = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|v\/|embed\/|user\/[^\/\n\s]+\/)?(?:watch\?v=|v%3D|embed%2F|video%2F)?|youtu\.be\/|youtube\.com\/watch\?v=|youtube\.com\/embed\/|youtube\.com\/v\/|youtube\.com\/shorts\/|youtube\.com\/playlist\?list=)([a-zA-Z0-9_-]{11})'
    match = re.search(regex, url)
    return match.group(1) if match else None

def decode(enc):
    try:
        secret_key = bytes.fromhex('C5D58EF67A7584E4A29F6C35BBC4EB12')
        data = base64.b64decode(enc)
        iv = data[:16]
        content = data[16:]
        cipher = AES.new(secret_key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(content)
        pad_len = decrypted[-1]
        decrypted = decrypted[:-pad_len]
        return json.loads(decrypted.decode('utf-8'))
    except Exception as e:
        raise RuntimeError(f'Decode error: {str(e)}')

def savetube(link, quality, type_):
    try:
        cdn_resp = requests.get('https://media.savetube.me/api/random-cdn')
        cdn = cdn_resp.json().get('cdn')
        if not cdn:
            return {'status': False, 'message': 'No CDN found'}

        infoget_resp = requests.post(f'https://{cdn}/v2/info', json={'url': link}, headers={
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://yt.savetube.me/1kejjj1?id=362796039'
        })
        infoget = infoget_resp.json()
        info = decode(infoget.get('data', ''))

        download_resp = requests.post(f'https://{cdn}/download', json={
            'downloadType': type_,
            'quality': str(quality),
            'key': info.get('key')
        }, headers={
            'Content-Type': 'application/json',
            'User-Agent': 'Mozilla/5.0',
            'Referer': 'https://yt.savetube.me/start-download?from=1kejjj1%3Fid%3D362796039'
        })

        response = download_resp.json()
        if not response.get('data') or not response['data'].get('downloadUrl'):
            return {'status': False, 'message': 'No download URL'}

        filename = f"{info.get('title')} ({quality}{'kbps' if type_ == 'audio' else 'p'}){'.mp3' if type_ == 'audio' else '.mp4'}"

        return {
            'status': True,
            'quality': f"{quality}{'kbps' if type_ == 'audio' else 'p'}",
            'availableQuality': AUDIO_QUALITIES if type_ == 'audio' else VIDEO_QUALITIES,
            'url': response['data']['downloadUrl'],
            'filename': filename
        }
    except Exception as e:
        print('SaveTube error:', str(e))
        return {'status': False, 'message': 'Converting error'}

def search(name):
    clean_cache()
    now = time.time()
    if name in search_cache and now - search_cache[name]['timestamp'] < 3600:
        return search_cache[name]['data']

    results = YoutubeSearch(name, max_results=1).to_dict()
    if not results:
        return {'ok': False, 'msg': 'Não encontrei nenhuma música.'}
    result = {'ok': True, 'criador': 'Hiudy', 'data': results[0]}
    search_cache[name] = {'data': result, 'timestamp': now}
    return result

def download_audio(url, quality=128):
    clean_cache()
    id_ = get_youtube_video_id(url)
    if not id_:
        return {'ok': False, 'msg': 'URL inválida'}
    now = time.time()

    cache_key = f"meta:{id_}"
    meta = None
    if cache_key in metadata_cache and now - metadata_cache[cache_key]['timestamp'] < 1800:
        meta = metadata_cache[cache_key]['data']

    if not meta:
        search_result = search(f'https://youtube.com/watch?v={id_}')
        if not search_result['ok']:
            return {'ok': False, 'msg': 'Erro ao buscar metadados'}
        meta = search_result['data']
        metadata_cache[cache_key] = {'data': meta, 'timestamp': now}

    if quality not in AUDIO_QUALITIES:
        quality = 128

    result = savetube(f'https://youtube.com/watch?v={id_}', quality, 'audio')
    if not result['status']:
        return {'ok': False, 'msg': result.get('message', 'Falha ao gerar link')}

    file_resp = requests.get(result['url'], timeout=60)
    buffer = file_resp.content

    return {
        'ok': True,
        'buffer': buffer,
        'filename': result['filename'],
        'quality': result['quality'],
        'availableQuality': AUDIO_QUALITIES
    }

def download_video(url, quality=360):
    clean_cache()
    id_ = get_youtube_video_id(url)
    if not id_:
        return {'ok': False, 'msg': 'URL inválida'}
    now = time.time()

    cache_key = f"meta:{id_}"
    meta = None
    if cache_key in metadata_cache and now - metadata_cache[cache_key]['timestamp'] < 1800:
        meta = metadata_cache[cache_key]['data']

    if not meta:
        search_result = search(f'https://youtube.com/watch?v={id_}')
        if not search_result['ok']:
            return {'ok': False, 'msg': 'Erro ao buscar metadados'}
        meta = search_result['data']
        metadata_cache[cache_key] = {'data': meta, 'timestamp': now}

    if quality not in VIDEO_QUALITIES:
        quality = 360

    result = savetube(f'https://youtube.com/watch?v={id_}', quality, 'video')
    if not result['status']:
        return {'ok': False, 'msg': result.get('message', 'Falha ao gerar link')}

    file_resp = requests.get(result['url'], timeout=60)
    buffer = file_resp.content

    return {
        'ok': True,
        'buffer': buffer,
        'filename': result['filename'],
        'quality': result['quality'],
        'availableQuality': VIDEO_QUALITIES
    }

# Flask routes

@app.route('/search', methods=['GET'])
def api_search():
    term = request.args.get('term')
    if not term:
        return jsonify({'ok': False, 'msg': 'Termo de busca não fornecido'}), 400
    result = search(term)
    return jsonify(result)

@app.route('/download/audio', methods=['GET'])
def api_download_audio():
    url = request.args.get('url')
    quality = int(request.args.get('quality', 128))
    if not url:
        return jsonify({'ok': False, 'msg': 'URL não fornecida'}), 400
    result = download_audio(url, quality)
    if not result['ok']:
        return jsonify(result), 400
    return send_file(BytesIO(result['buffer']), download_name=result['filename'], as_attachment=True)

@app.route('/download/video', methods=['GET'])
def api_download_video():
    url = request.args.get('url')
    quality = int(request.args.get('quality', 360))
    if not url:
        return jsonify({'ok': False, 'msg': 'URL não fornecida'}), 400
    result = download_video(url, quality)
    if not result['ok']:
        return jsonify(result), 400
    return send_file(BytesIO(result['buffer']), download_name=result['filename'], as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
