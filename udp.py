import struct
import urllib
import socket
import bencoding
import random
import peer_helper
import time
import random
import traceback

def get_peers(payload, udp_url, vpn_ip=None):
    url_info = urllib.parse.urlparse(udp_url)
    try:
        #Connect
        #Magic num, action, transaction_id
        rand_transaction_id = random.randint(0, 100000)
        connect_data = struct.pack('>qii', int('0x41727101980', 16), 0, rand_transaction_id)

        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        if vpn_ip:
            sock.bind((vpn_ip, 0))

        sock.connect((url_info.hostname, int(url_info.port)))
        sock.send(connect_data)
        
        data = sock.recv(16)
       
        if len(data) < 16:
            print("ERR: Announce packet not 16 bytes")
            return None
        action, transaction_id, connection_id = struct.unpack_from('>iiq', data)
        if transaction_id != rand_transaction_id:
            print("Transaction ids don't match!")
            return None

        #announce
        announce_data = struct.pack('>qii20s20sqqqiiiii', connection_id, 1, transaction_id, payload['info_hash'], payload['peer_id'],
            0, 0, 0, 0, 0, 0, -1, 6881)
        sock.send(announce_data)
        data = sock.recv(1024)

        if len(data) < 20:
            return None

        announce, transaction_id, interval, leechers, seeders = struct.unpack_from('>iiiii', data)
        peers = data[20:]

        return peer_helper.parse_ips(peers)
    except Exception as e:
        print("UDP ERROR: " + traceback.format_exc())

    