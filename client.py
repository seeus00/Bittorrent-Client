from message import Messages
import datetime
import time
import bitfield
import hashlib
import threading
import bencoding 
import math
import traceback

lock = threading.Lock()

class Client:
    MAX_BACKLOG = 10

    def __init__(self, ip, port, info, metadata_info, vpn_interface = None, disconnect_callback = None, write_callback = None):
        self.ip = ip
        self.port = port
        self.info = info

        self.disconnect_callback = disconnect_callback
        self.write_callback = write_callback

        self.handshake_recieved = True

        self.is_running = False
        self.is_choking = True
        self.download_started = False

        self.have_all = False

        self.downloading_pieces = False

        self.vpn_interface = vpn_interface
        self.metadata_info = metadata_info
        self.bitfield = bytearray(math.ceil(len(self.info['piece_hashes'])))
        
        self.last_active = datetime.datetime.now(datetime.timezone.utc)
        self.sock_conn = None

    def check_integrity(self, work, buffer_bytes):
        buf_hash = hashlib.sha1(buffer_bytes).digest()
        return work['hash'] == buf_hash

    def has_piece(self, piece_ind):
        return bitfield.has_piece(self.bitfield, piece_ind)

    def handle_message(self, msg, state):
        msg_id = msg['id']
        payload = msg['payload']

        if msg['id'] == Messages.EXTENDED:
            self.metadata_info = bencoding.decode(msg['payload'])
        elif msg['id'] == Messages.MSG_BITFIELD:
            self.have_all = True
            self.bitfield = bytearray(msg['payload'])
            bitfield.set_all_true(self.bitfield)
        elif msg['id'] == Messages.MSG_HAVE or msg['id'] == Messages.MSG_ALLOWED_FAST_PIECE:
            ind = int.from_bytes(msg['payload'], byteorder='big')
            if not bitfield.has_piece(self.bitfield, ind):
                bitfield.set_piece(self.bitfield, ind)

            self.have_all = bitfield.check_all_true(self.bitfield)
        elif msg['id'] == Messages.MSG_HAVE_ALL:
            bitfield.set_all_true(self.bitfield)
            self.have_all = True
        elif msg['id'] == Messages.MSG_CHOKE:
            self.is_choking = True  
        elif msg['id'] == Messages.MSG_UNCHOKE:
            self.is_choking = False
        elif msg_id == self.message.MSG_PIECE:
            n = self.message.read_piece(state['index'], state['buf'], payload)

            state['downloaded'] += n
            state['backlog'] -= 1


    def read_message(self, sock, state):
        self.last_active = datetime.datetime.now(datetime.timezone.utc)
        msg = self.message.recieve_data(sock)
        
        if msg is None:
            return -1
        #Keep alive message
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

    def disconnect(self):
        if self.sock_conn:
            self.sock_conn.close()
        
        if self.disconnect_callback:
            self.disconnect_callback(self)

        self.is_running = False

    def start(self, work_queue, results):
        self.last_active = datetime.datetime.now(datetime.timezone.utc)

        self.is_running = True
        self.message = Messages()

        self.sock_conn = self.message.create_conn(self.ip, self.port, vpn_ip=self.vpn_interface)
        if not self.sock_conn:
            return

        reserved = bytearray(8)
        if self.metadata_info:
            reserved[5] |= 0x10 #Set reserved byte for metadata
        #reserved[7] |= 0x04 #Set reserved by for fast extension 

        resp = self.message.send_handshake(self.sock_conn, self.info, reserved)
        if not resp:
            self.disconnect()
            return

        handshake_data = self.message.read_handshake(resp)
        client_info_hash = handshake_data[3].hex()
        if client_info_hash != self.info['info_hash']:
            print("CLIENT INFO_HASH DOESN'T MATCH ORIGNAL")
            self.disconnect()
            return
        
        self.handshake_recieved = True

        # if self.metadata_info:
        #     metadata_handshake = self.message.create_metadata_handshake(self.metadata_info)
        #     self.sock_conn.sendall(metadata_handshake)
        #     self.message.send_have_none(self.sock_conn)


        # self.message.send_unchoke(self.sock_conn)
        # self.message.send_interested(self.sock_conn)   
        self.is_choking = False

        #Get bitfield
        # res = self.read_message(self.sock_conn, None)
        # if not self.bitfield:
        #     print("NO BITFIELD")

        #The bitfield has the same number as piece hashes, but bitfield.py sets the bits 
        
        
        msg = self.read_message(self.sock_conn, None)
        if msg == -1:
            self.disconnect()
            return
        try:
            while self.is_running:
                work = work_queue.get()

                #self.have_all = bitfield.check_all_true(self.bitfield)
                #if not self.have_all:
                
                if not bitfield.has_piece(self.bitfield, work['index']):
                    work_queue.put(work)
                    time.sleep(1)
                    continue
                
                buf = self.attempt_download_piece(work, self.sock_conn)
                if not buf:
                    work_queue.put(work)
                    self.disconnect()
                    
                    # time.sleep(2)
                    # return self.start(work_queue, results)
                    break
                    
                if not self.check_integrity(work, bytes(buf)):
                    print("FAILED INTEGRITY CHECK")
                    work_queue.put(work)
                    self.disconnect()
                    
                    break

                self.message.send_have(self.sock_conn, work['index'])
                results.put({'index': work['index'], 'buffer': buf})

                bitfield.set_piece(self.bitfield, work['index'])
                #self.write_callback({'index': work['index'], 'buffer': buf})

        except Exception as e:
            print(traceback.format_exc())
            self.disconnect()
            if work:
                work_queue.put(work)

        # data = self.message.recieve_data(self.sock_conn)
        # if msg['id'] == Messages.EXTENDED:
        #     metadata = bencoding.decode(data['payload'])

        # bitfield_data = self.message.recieve_data(self.sock_conn)

        # # reserved = handshake_data[2]
        # # if reserved[7] & 0x04 == 4:
        # #     msg = self.message.recieve_data(self.sock_conn)
        # #     if msg['id'] == Messages.MSG_HAVE_ALL:
        # #         print("HAVE ALL PIECES")

        
        # self.message.send_unchoke(self.sock_conn)
        # self.message.send_interested(self.sock_conn)       

        # #self.is_choking = False
        # if not bitfield_data:
        #     print("Failed to recieve bitfield data")
        #     self.sock_conn.close()
        #     return

        # if bitfield_msg['id'] == -1:
        #     print("INVALID DATA")
        #     self.sock_conn.close()
        #     return

        # if not bitfield_data['payload']:
        #     print("EMPTY BITFIELD")
        #     self.sock_conn.close()
        #     return

        # if bitfield_msg['id'] == self.message.MSG_CHOKE:
        #     # print("CHOKED")
        #     self.is_choking = True
        #     self.sock_conn.close()
        #     return

        # if bitfield_msg['id'] == self.message.MSG_HAVE:
        #     ind = int.from_bytes(bitfield_data['payload'], byteorder='big')
        #     bitfield.set_piece(self.bitfield, ind)

        # if bitfield_msg['id'] == self.message.MSG_BITFIELD:
        #     self.bitfield = bytearray(bitfield_data['payload'])

        # while not work_queue.empty() and self.is_running:
        #     work = work_queue.get()

        #     self.read_message(self.sock_conn, None)
        #     if not bitfield.has_piece(self.bitfield, work['index']):
        #         work_queue.put(work)
        #         continue

        #     buf = self.attempt_download_piece(work, self.sock_conn)
        #     if not buf:
        #         work_queue.put(work)
        #         self.sock_conn.close()
        #         return
            
        #     if not self.check_integrity(work, bytes(buf)):
        #         print("FAILED INTEGRITY CHECK")
        #         work_queue.put(work)
        #         continue

        #     self.message.send_have(self.sock_conn, work['index'])
        #     results.put({'index': work['index'], 'buffer': buf})
        
        #self.disconnect()

    def send_keep_alive(self):
        if not self.sock_conn:
            return
        self.message.send_keep_alive(self.sock_conn)