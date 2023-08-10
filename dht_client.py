from message import Messages
from queue import Queue
import bencoding
import traceback
import math
import struct
import binascii
import torrent_util
import time

class DhtClient:
    def __init__(self, ip, port, info, vpn_interface=None):
        self.ip = ip
        self.port = port

        self.info = info

        self.is_running = False
        self.is_choking = True

        self.vpn_interface = vpn_interface

    def handle_message(self, data, state):
        msg_id = data['id']
        payload = data['payload']

        if msg_id == Messages.MSG_UNCHOKE:
            self.is_choking = False
        elif msg_id == Messages.MSG_CHOKE:
            self.is_choking = True
        elif msg_id == Messages.EXTENDED:
            #Recieved piece data
            n = self.message.read_metadata_piece(state['index'], self.meta_data_buf, payload, self.metadata_size)

            state['downloaded'] += n
            state['backlog'] -= 1


    def read_message(self, sock, state):
        msg = self.message.recieve_data(sock)

        #Keep alive message
        if msg is None:
            return -1
        if msg == b'':
            return 1

        self.handle_message(msg, state)

        return 1

    def attempt_download_piece(self, work, sock):
        state = {
            'index': work['index'],
            'downloaded': 0,
            'requested': 0,
            'backlog': 0
        }
        # print("Attemping to download piece")
        while state["downloaded"] < work['length']:
            if not self.is_choking:
                while state['backlog'] < 5 and state['requested'] < work['length']:
                    block_size = 16384
                    if work['length'] - state['requested'] < block_size:
                        block_size = work['length'] - state['requested']

                    req = {
                        'msg_type': 0,
                        'piece': work['index']
                    }

                    self.message.send_metadata_request(sock, req, self.meta_data_info[b'm'][b'ut_metadata'])

                    state['backlog'] += 1
                    state['requested'] += block_size

            res = self.read_message(sock, state)
            if res == -1:
                return None

        return True

    def start_retrieval(self, sock_conn, meta_data):
        self.meta_data_info = bencoding.decode(meta_data['payload'])
        self.metadata_size = self.meta_data_info[b'metadata_size']

        self.buf = bytearray(self.metadata_size)
        num_pieces = math.ceil(self.metadata_size / 16384)

        #Send metadata handshake
        metadata_handshake = self.message.create_metadata_handshake()
        sock_conn.send(metadata_handshake)
        
        work_queue = Queue(maxsize=num_pieces)
        for ind in range(num_pieces):
            length = torrent_util.calculate_piece_size(16384, self.metadata_size, ind)
            work_queue.put({'index': ind, 'length': length})

        self.meta_data_buf = bytearray(self.metadata_size)

        while not work_queue.empty():
            work = work_queue.get()
            buf = self.attempt_download_piece(work, sock_conn)
            if not buf:
                work_queue.put(work)
                sock_conn.close()
                return

        sock_conn.close()
        return self.meta_data_buf

    def start(self):
        self.message = Messages()
        sock_conn = self.message.create_conn(self.ip, self.port, 1, vpn_ip=self.vpn_interface)
        
        try:    
            if not sock_conn:
                return None

            #creates first bittorrent handshake 
            bt_handshake = self.message.create_handshake(self.info['info_hash'], self.info['peer_id'])
            sock_conn.sendall(bt_handshake)

            metadata_handshake = self.message.create_metadata_handshake()
            sock_conn.sendall(metadata_handshake)

            resp = sock_conn.recv(len(bt_handshake))
            if not resp:
                print("No data!")
                sock_conn.close()
                return None


            handshake_resp = self.message.read_handshake(resp)

            client_info_hash = binascii.hexlify(bytes(handshake_resp[3]))
            if client_info_hash != self.info['info_hash'].encode():
                print("CLIENT INFO_HASH DOESN'T MATCH ORIGNAL")
                sock_conn.close()
                return None
            

            reserved = handshake_resp[2]
            if reserved[5] & 0x10 != 16:
                print("Client doesn't support extended metadata!")
                return None


            resp = self.message.recieve_data(sock_conn)
            if not resp:
                return None


            if resp['id'] == Messages.MSG_BITFIELD:
                meta_data = self.message.recieve_data(sock_conn)
                self.meta_data = meta_data

                return self.start_retrieval(sock_conn, meta_data)
            elif resp['id'] == Messages.EXTENDED:
                self.meta_data = resp
                bitfield = self.message.recieve_data(sock_conn)
                
                return self.start_retrieval(sock_conn, resp)

        except Exception as e:
            print(e)
            #traceback.print_exc()

        return None