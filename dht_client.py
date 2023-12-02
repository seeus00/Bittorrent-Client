from message import Messages
from queue import Queue
import bencoding
import traceback
import math
import struct
import binascii
import torrent_util
import time
import threading

class DhtClient:
    def __init__(self, ip, port, info, vpn_interface=None):
        self.ip = ip
        self.port = port

        self.info = info

        self.is_running = False
        self.is_choking = True

        self.metadata_size = 0

        self.vpn_interface = vpn_interface

    def handle_message(self, data, state):
        msg_id = data['id']
        payload = data['payload']

        if msg_id == Messages.MSG_UNCHOKE:
            self.is_choking = False
        elif msg_id == Messages.MSG_CHOKE:
            self.is_choking = True
        elif msg_id == Messages.EXTENDED:
            #Handshake
            if self.metadata_size == 0:
                self.meta_data_info = bencoding.decode(payload)
                self.metadata_size = self.meta_data_info[b'metadata_size']
            else:
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
        while not self.stop_event.is_set() and state["downloaded"] < work['length']:
            if not self.is_choking:
                while state['backlog'] < 1 and state['requested'] < work['length']:
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

    def start_retrieval(self, sock_conn):
        while self.metadata_size == 0:
            resp = self.read_message(sock_conn, None)
            if resp == -1:
                sock_conn.close()
                return None

        self.buf = bytearray(self.metadata_size)
        num_pieces = math.ceil(self.metadata_size / 16384)
        
        work_queue = Queue(maxsize=num_pieces)
        for ind in range(num_pieces):
            length = torrent_util.calculate_piece_size(16384, self.metadata_size, ind)
            work_queue.put({'index': ind, 'length': length})

        self.meta_data_buf = bytearray(self.metadata_size)

        
        while not self.stop_event.is_set() and not work_queue.empty():
            work = work_queue.get()

            buf = self.attempt_download_piece(work, sock_conn)
            if not buf:
                work_queue.put(work)
                sock_conn.close()
                return

            work_queue.task_done()

        sock_conn.close()

        self.global_info = self.meta_data_buf
        return self.meta_data_buf, self.meta_data_info

    def threadsafe_function(fn):
        """decorator making sure that the decorated function is thread safe"""
        lock = threading.Lock()
        def new(*args, **kwargs):
            lock.acquire()
            try:
                r = fn(*args, **kwargs)
            except Exception as e:
                raise e
            finally:
                lock.release()
            return r
        return new  

    # @threadsafe_function
    def start(self, stop_event):
        self.stop_event = stop_event

        self.message = Messages()
        sock_conn = self.message.create_conn(self.ip, self.port, 1, vpn_ip=self.vpn_interface)
        

        try:    
            if not sock_conn:
                return None

            #creates first bittorrent handshake 
            bt_handshake = self.message.create_handshake(self.info['info_hash'], self.info['peer_id'])
            sock_conn.sendall(bt_handshake)

            # metadata_handshake = self.message.create_metadata_handshake()
            # sock_conn.sendall(metadata_handshake)

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


            # resp = self.message.recieve_data(sock_conn)
            # if not resp:
            #     return None

            # self.message.send_unchoke(sock_conn)
            # self.message.send_interested(sock_conn)   
            self.is_choking = False

            # if resp['id'] == Messages.EXTENDED:
            #     return self.start_retrieval(sock_conn, resp['payload'])

            self.bitfield = bytearray(8)
            return self.start_retrieval(sock_conn)
        # if resp['id'] == Messages.MSG_BITFIELD:
        #     resp = self.message.recieve_data(sock_conn)

        #     return self.start_retrieval(sock_conn, resp['payload'])
        # elif resp['id'] == Messages.EXTENDED:
        #     self.bitfield = self.message.recieve_data(sock_conn)
            
        #     return self.start_retrieval(sock_conn, resp['payload'])

        except Exception as e:
            print(e)
            #traceback.print_exc()

        sock_conn.close()
        return None