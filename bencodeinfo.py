import bencoding
import hashlib
import secrets

def generate_rand_peerid():
    return secrets.token_hex(20)

def get_info_from_buf(buf):
    data = bencoding.decode(buf)
    info_encode = bencoding.encode(data)
    
    info_hash = hashlib.sha1(info_encode).hexdigest()

    pieces = data[b'pieces']
    info = {
        'info_hash': info_hash,
        'info_hash_bytes': hashlib.sha1(info_encode).digest(),
        'peer_id': secrets.token_hex(20),
        'file_name': data[b'name'],
        'length': data[b'length'],
        'name': data[b'name'].decode('utf-8'),
        'piece_length': data[b'piece length'],
        'pieces': pieces,
        'piece_hashes': [pieces[i:i + 20] for i in range(0, len(pieces), 20)]
    }

    if b'announce' in data:
        info['announce_list'] = []
        info['announce_list'].append(data[b'announce'].decode('utf-8'))
    elif b'announce-list' in data:
        info['announce_list'] = [url.decode('utf-8') for url in data[b'announce-list']]

    return info

def get_info(torrent_file):
    with open(torrent_file, 'rb') as f:
        byte_str = f.read()

        data = bencoding.decode(byte_str)
        info_encode = bencoding.encode(data[b'info'])
        
        info_hash = hashlib.sha1(info_encode).hexdigest()

        pieces = data[b'info'][b'pieces']
        info = {
            'info_hash': info_hash,
            'info_hash_bytes': hashlib.sha1(info_encode).digest(),
            'peer_id': secrets.token_hex(20),
            'file_name': data[b'info'][b'name'],
            'length': data[b'info'][b'length'],
            'name': data[b'info'][b'name'].decode('utf-8'),
            'piece_length': data[b'info'][b'piece length'],
            'pieces': pieces,
            'piece_hashes': [pieces[i:i + 20] for i in range(0, len(pieces), 20)]
        }

        if b'announce' in data:
            info['announce_list'] = []
            info['announce_list'].append(data[b'announce'].decode('utf-8'))
        elif b'announce-list' in data:
            info['announce_list'] = [url.decode('utf-8') for url in data[b'announce-list']]

        return info