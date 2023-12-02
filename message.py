import struct
import socket
import binascii
import time
import math
import bencoding

class Messages:
    MSG_CHOKE = 0
    MSG_UNCHOKE = 1
    MSG_INTERESTED = 2
    MSG_NOT_INTERESTED = 3
    MSG_HAVE = 4
    MSG_BITFIELD = 5
    MSG_REQUEST = 6
    MSG_PIECE = 7
    MSG_CANCEL = 8

    MSG_HAVE_ALL = 14
    MSG_HAVE_NONE = 15
    MSG_ALLOWED_FAST_PIECE = 17

    EXTENDED = 20

    def __init__(self):
        self.curr_buff = b''

    def read_piece(self, ind, buf, piece_data):
        parsed_ind = piece_data['index']

        if parsed_ind != ind:
            print("Correct ind: ", ind)
            print("Incorrect piece index!")

            return 0

        beg = piece_data['begin']
        if beg >= len(buf):
            print("Beginning offset is too high!")
            return 0

        data = piece_data['block']

        if beg + len(data) > len(buf):
            print("Data too long!")
            return 0

        for i in range(len(data)):
            buf[i + beg] = data[i]
        
        return len(data)

    def read_metadata_piece(self, index, buf, data, total_size):
        bencode_obj = {
            'msg_type': 1,
            'piece': index,
            'total_size': total_size
        }

        encoded = bencoding.encode(bencode_obj)
        bencode_info = bencoding.decode(data[:len(encoded)])

        if bencode_info[b'piece'] != index:
            print("INVALID INDEX")
            return 0

        data = data[len(encoded):]
        
        #If last piece is smaller than 16 kb, the last piece must've been 16 kb
        beg = len(data)
        if len(data) < 16384:
            beg = 16384
        
        for i in range(len(data)):
            buf[i + (beg * index)] = data[i]

        return len(data)


    def send_metadata_request(self, sock, bencode_data, ext_id):
        encoded = bencoding.encode(bencode_data)
        msg_len = 1 + 1 + len(encoded)
        bytes_data = struct.pack(f">Ibb{len(encoded)}s", msg_len, Messages.EXTENDED, ext_id, encoded)

        sock.sendall(bytes_data)

    def send_keep_alive(self, sock):
        bytes_data = struct.pack('>I', 0)
        sock.sendall(bytes_data)


    def send_have_none(self, sock):
        bytes_data = struct.pack('>Ib', 1, Messages.MSG_HAVE_NONE)
        sock.sendall(bytes_data)

    def send_have(self, sock, ind):
        bytes_data = struct.pack('>IbI', 5, Messages.MSG_HAVE, ind)
        sock.sendall(bytes_data)

    def send_request(self, sock, ind, beg, length):
        bytes_data = struct.pack('>IbIII', 13, Messages.MSG_REQUEST, ind, beg, length)
        sock.sendall(bytes_data)

    def create_metadata_handshake(self, info):
        handshake_msg = {
            'm': info[b'm'],
            'metadata_size': info[b'metadata_size'],
            'p': 6881,
            'v': 'qbittorrent 1.0'
        }

        encoded = bencoding.encode(handshake_msg)
        msg_len = 1 + 1 + len(encoded)
        
        return struct.pack(f">Ibb{len(encoded)}s", msg_len, Messages.EXTENDED, 0, encoded)


    def create_handshake(self, info_hash, peer_id):
        reserved = bytearray(8)
        reserved[5] |= 0x10 #Set reserved byte for metadata

        pstrlen = b'\x13'
        pstr = b"BitTorrent protocol"
        info_hash_str = bytes.fromhex(info_hash)
        peer_id = bytes.fromhex(peer_id)
        handshake = pstrlen + pstr + reserved + info_hash_str + peer_id

        return handshake

    def read_handshake(self, buffer_data):
        data = struct.unpack_from('>b19s8s20s20s', buffer_data)
        return data

    def send_handshake(self, sock_conn, torrent_info, reserved):
        # reserved = bytearray(8)
    
        # # reserved[5] |= 0x10 #Set reserved byte for metadata
        # reserved[7] |= 0x04 #Set reserved by for fast extension 

        pstrlen = b'\x13'
        pstr = b"BitTorrent protocol"
        info_hash_str = bytes.fromhex(torrent_info['info_hash'])
        peer_id = bytes.fromhex(torrent_info['peer_id'])
        handshake = pstrlen + pstr + reserved + info_hash_str + peer_id

        try:
            sock_conn.sendall(handshake)
            data = sock_conn.recv(len(handshake))
            return data
        except Exception as e:
            #print("HANDSHAKE FAILED TO SEND!")
            return None
        

    def create_conn(self, ip, port, default_timeout=20, vpn_ip=None):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if vpn_ip:
                s.bind((vpn_ip, 0))

            # s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.settimeout(default_timeout)
        
            s.connect((ip, port))
            return s
        except socket.error as e:
            return None
            #print(e)
        return None

            
           

    def handle_choke(self, sock):
        sock.close()

    def recieve_data(self, sock):
        try:
            msg_len_buffer = sock.recv(4)
            msg_len = struct.unpack('>I', msg_len_buffer)[0]

            if msg_len == 0:
                return b''
            

            msg_buffer = sock.recv(msg_len)
            while len(msg_buffer) < msg_len:
                if len(msg_buffer) == 0:
                    break
                msg_buffer += sock.recv(1)

            
            msg_id = msg_buffer[0]
            obj = {
                'id': msg_buffer[0],
                'len': msg_len,
                'payload': msg_buffer[1:]
            }

            payload = obj['payload']
            
            if msg_id == Messages.MSG_PIECE:
                index, begin = struct.unpack('>II', obj['payload'][:8])
                payload = {
                    'index': index,
                    'begin': begin,
                    'block': obj['payload'][8:]
                }
            elif msg_id == Messages.MSG_REQUEST or msg_id == Messages.MSG_CANCEL:
                index, begin, length = struct.unpack('>III', obj['payload'])
                payload = {
                    'index': index,
                    'begin': begin,
                    'length': length
                }
            elif msg_id == Messages.EXTENDED:
                ext_id = struct.unpack('>b', obj['payload'][:1])[0]
                payload = obj['payload'][1:]

                return {
                    'size': msg_len,
                    'id': msg_id,
                    'ext_id': ext_id,
                    'payload': payload 
                } 

            return {
                'size': msg_len,
                'id': msg_id,
                'payload': payload 
            }
            
        except Exception as e:
            pass
        return None


    def send_interested(self, sock):
        byte_data = struct.pack('>Ib', 1, Messages.MSG_INTERESTED)
        sock.sendall(byte_data)

    def send_unchoke(self, sock):
        byte_data = struct.pack('>Ib', 1, Messages.MSG_UNCHOKE)
        sock.sendall(byte_data)
