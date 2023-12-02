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

    return info


def get_from_buf(buf):
    data = bencoding.decode(buf)
 
    info_data = data[b'info'] if b'info' in data else data
    info_encode = bencoding.encode(info_data) 
    
    info_hash = hashlib.sha1(info_encode).hexdigest()

    #info_data = data[b'info']
    pieces = info_data[b'pieces']

    info = {
        'info_hash': info_hash,
        'info_hash_bytes': hashlib.sha1(info_encode).digest(),
        'peer_id': secrets.token_hex(20),
        'piece_length': info_data[b'piece length'],
        'pieces': info_data[b'pieces'],
        'piece_hashes': [pieces[i:i + 20] for i in range(0, len(pieces), 20)]
    }

    files = []
    #Multi file 
    if b'files' in info_data:
        root_dir = info_data[b'name'].decode()
        files = [{
            'path': f"{root_dir}/{'/'.join([f.decode() for f in file[b'path']])}",
            'length': file[b'length']
        } for file in info_data[b'files']]

        info['files'] = files
        info['length'] = sum([file['length'] for file in files])

    else:
        info['files'] = [{
            'path': info_data[b'name'].decode('utf-8'),
            'length': info_data[b'length']
        }]

        info['length'] = info_data[b'length']
        # info['name'] = info_data[b'name'].decode('utf-8')
        # info['length'] = info_data[b'length']

    if b'announce' in data:
            info['announce_list'] = []
            info['announce_list'].append(data[b'announce'].decode('utf-8'))
    if b'announce-list' in data:
        info['announce_list'].extend([url.decode('utf-8') for val in data[b'announce-list'] for url in val ])

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
        if b'announce-list' in data:
            info['announce_list'].extend([url.decode('utf-8') for val in data[b'announce-list'] for url in val ])

        return info