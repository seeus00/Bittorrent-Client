import struct
import urllib
import socket
import bencoding
import random
import peer_helper


def get_peers(payload, udp_url, vpn_ip=None):
    url_info = urllib.parse.urlparse(udp_url)
    try:
        #Connect
        #Magic num, action, transaction_id
        rand_transaction_id = 5
        connect_data = struct.pack('>qii', int('0x41727101980', 16), 0, rand_transaction_id)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind((vpn_ip, 0))
        sock.settimeout(2)
        sock.connect((url_info.hostname, int(url_info.port)))
        sock.send(connect_data)
        
        data = sock.recv(1024)

        if len(data) < 16:
            print("ERR: Announce packet not 16 bytes")
            return None
        action, transaction_id, connection_id = struct.unpack_from('>iiq', data)
        if transaction_id != rand_transaction_id:
            print("Transaction ids don't match!")
            return None

        #announce
        announce_data = struct.pack('>qii20s20sqqqiiiii', connection_id, 1, transaction_id, payload['info_hash'], payload['peer_id'],
            0, 0, 0, 0, 0, 8, -1, 6347)
        sock.send(announce_data)
        data = sock.recv(1024)
        
        announce, transaction_id, interval, leechers, seeders = struct.unpack_from('>iiiii', data)
        peers = data[20:]

        return peer_helper.parse_ips(peers)
    except Exception as e:
        return None
    