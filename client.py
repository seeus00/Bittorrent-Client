from message import Messages
import time
import bitfield
import torrent_util
import file_util
import struct
import hashlib
import binascii
import sys
import threading

lock = threading.Lock()

class Client:
    MAX_BACKLOG = 10

    def __init__(self, ip, port, info, file, vpn_interface=None):
        self.ip = ip
        self.port = port
        self.info = info
        self.file = file

        self.is_running = False
        self.is_choking = True

        self.vpn_interface = vpn_interface

    def check_integrity(self, work, buffer_bytes):
        buf_hash = hashlib.sha1(buffer_bytes).digest()
        if work['hash'] != buf_hash:
            return False

        return True

    def handle_message(self, data, state):
        msg_id = data['id']
        payload = data['payload']

        if msg_id == self.message.MSG_CHOKE:
            self.is_choking = True
        elif msg_id == self.message.MSG_UNCHOKE:
            self.is_choking = False
        elif msg_id == self.message.MSG_HAVE:
            ind = int.from_bytes(payload, byteorder='big')
            bitfield.set_piece(self.bitfield, ind)
        elif msg_id == self.message.MSG_PIECE:
            n = self.message.read_piece(state['index'], state['buf'], payload)

            # print(data)
            # print(len(payload['block']))

            # if not n:
            #     return
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
            'backlog': 0,
            'buf': bytearray(work['length'])
        }
        while state["downloaded"] < work['length']:
            if not self.is_choking:
                while state['backlog'] < Client.MAX_BACKLOG and state['requested'] < work['length']:
                    block_size = 16384
                    if work['length'] - state['requested'] < block_size:
                        block_size = work['length'] - state['requested']

                    self.message.send_request(sock, work['index'], state['requested'], block_size)
                    state['backlog'] += 1
                    state['requested'] += block_size

            res = self.read_message(sock, state)
            if res == -1:
                return None

        return state['buf']

    def start(self, work_queue, results):
        self.is_running = True
        self.message = Messages()

        sock_conn = self.message.create_conn(self.ip, self.port, vpn_ip=self.vpn_interface)
        if not sock_conn:
            return

        resp = self.message.send_handshake(sock_conn, self.info)
        if not resp:
            sock_conn.close()
            return


        # 8x = skip 8 bytes
        client_info_hash = self.message.read_handshake(resp)[3].hex()
        if client_info_hash != self.info['info_hash']:
            print("CLIENT INFO_HASH DOESN'T MATCH ORIGNAL")
            sock_conn.close()
            return

        bitfield_data = self.message.recieve_data(sock_conn)
        #print(bitfield_data)

        self.message.send_unchoke(sock_conn)
        self.message.send_interested(sock_conn)       

        self.is_choking = False

        if not bitfield_data:
            #print("Failed to recieve bitfield data")
            sock_conn.close()
            return

        if bitfield_data['id'] == -1:
            sock_conn.close()
            return

        if not bitfield_data['payload']:
            print("EMPTY BITFIELD")
            sock_conn.close()
            return

        if bitfield_data['id'] == self.message.MSG_CHOKE:
            # print("CHOKED")
            self.is_choking = True
            sock_conn.close()
            return

        if bitfield_data['id'] == self.message.MSG_HAVE:
            ind = int.from_bytes(bitfield_data['payload'], byteorder='big')
            bitfield.set_piece(self.bitfield, ind)

        if bitfield_data['id'] == self.message.MSG_BITFIELD:
            self.bitfield = bytearray(bitfield_data['payload'])

        while not work_queue.empty() and self.is_running:
            work = work_queue.get()

            if not bitfield.has_piece(self.bitfield, work['index']):
                work_queue.put(work)
                continue

            buf = self.attempt_download_piece(work, sock_conn)
            if not buf:
                work_queue.put(work)
                sock_conn.close()
                return
            
            if not self.check_integrity(work, bytes(buf)):
                print("FAILED INTEGRITY CHECK")
                work_queue.put(work)
                continue

            self.message.send_have(sock_conn, work['index'])
            # file_util.save_piece_to_file(self.info['file_name'], work['index'], bytes(buf), 
            #         self.info['piece_length'], self.info['length'])
            #self.update_progress()
            results.put({'index': work['index'], 'buffer': buf})
        
            #work_queue.pop(ind)

        sock_conn.close()

            