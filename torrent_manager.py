from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

#from multiprocessing import Queue
from pathlib import Path
import datetime
import client
import torrent_util
import bencodeinfo
import bencoding
import concurrent
import threading
import time
import udp
import tcp
import dht.dht as dht
import requests
import os
import traceback
import math

class TorrentManager:
    def __init__(self, info=None, vpn_interface=None, port=6881):
        self.info = info
        self.peers = []
        self.clients = []
        self.reconnect_peers = []

        self.lock = threading.Lock()

        self.worker_threads = []

        self.finished = False
        self.fs = None

        self.metadata_info = None

        self.vpn_interface = vpn_interface
        self.port = port
        
        self.files = []
        self.open_files = []

        self.pieces = []
        self.requested_pieces = []

        self.done_pieces = 0

    # def write_data(self, res):
    #     if self.finished:
    #         return
        
    #     with self.lock:
    #         beg, end = torrent_util.calculate_bounds_for_piece(self.info['piece_length'], 
    #         self.info['length'], res['index'])
            
    #         end = beg + len(res['buffer'])

    #         curr_len = 0
    #         curr_buff = res['buffer']
    #         for ind, file in enumerate(self.files):
    #             #If the piece exceeds the length of the file, then it is not for that file
    #             if (beg < curr_len and end < curr_len) or (beg > file['length'] + curr_len and end > file['length'] + curr_len):
    #                 curr_len += file['length']
    #                 continue
    #             else:
    #                 fstart = max(0, beg - curr_len)
    #                 fend = min(end - curr_len, file['length'])
    #                 flength = int(fend - fstart)
    #                 bstart = max(0, int(curr_len - beg))

    #                 # with open(file['path'], 'wb') as f:
    #                 self.open_files[ind].seek(fstart)
    #                 self.open_files[ind].write(curr_buff[bstart:bstart + flength])


    #             curr_len += file['length']

    #         self.done_pieces += 1
    #         percent = (float(self.done_pieces) / len(self.info['piece_hashes']) * 100)

    #         #self.worker_threads = list(filter(lambda worker: worker.is_alive(), self.worker_threads))
    #         #self.clients = list(filter(lambda client: client.is_running, self.clients))
    #         print(f"Downloading piece #{res['index']} from {len(self.clients)} peers - {round(percent, 1)}%")


    def save(self):
        # for file in self.files:
        #     if os.path.dirname(file['path']):
        #         os.makedirs(os.path.dirname(file['path']), exist_ok=True)
        #     f = open(file['path'], 'wb')
        #     f.truncate(file['length'])
        #     self.open_files.append(f)

        done_pieces = 0
        while not self.finished:
            while done_pieces < len(self.info['piece_hashes']):
                try:
                    res = self.results.get()
                    
                    beg, end = torrent_util.calculate_bounds_for_piece(self.info['piece_length'], 
                        self.info['length'], res['index'])
                    
                    end = beg + len(res['buffer'])

                    curr_len = 0
                    curr_buff = res['buffer']
                    for ind, file in enumerate(self.files):
                        #If the piece exceeds the length of the file, then it is not for that file
                        if (beg < curr_len and end < curr_len) or (beg > file['length'] + curr_len and end > file['length'] + curr_len):
                            curr_len += file['length']
                            continue
                        else:
                            fstart = max(0, beg - curr_len)
                            fend = min(end - curr_len, file['length'])
                            flength = int(fend - fstart)
                            bstart = max(0, int(curr_len - beg))

                            # with open(file['path'], 'wb') as f:
                            self.open_files[ind].seek(fstart)
                            self.open_files[ind].write(curr_buff[bstart:bstart + flength])


                        curr_len += file['length']

                    done_pieces += 1
                    percent = (float(done_pieces) / len(self.info['piece_hashes']) * 100)

                    #self.worker_threads = list(filter(lambda worker: worker.is_alive(), self.worker_threads))
                    #self.clients = list(filter(lambda client: client.is_running, self.clients))
                    print(f"Downloading piece #{res['index']} from {len(self.clients)} peers - {round(percent, 1)}%")

                    #self.results.task_done()

                #If it takes too long to retrieve data, get new peers
                except Exception as e:
                    print("RESULTS QUEUE PASSED ERROR")
                    #self.clients = []
                    #self.worker_threads = []
                    #timeout += 5
                    #self.start_workers()
    
            print("FINISHED")
            self.finished = True

        # self.process_trackers_timer.cancel()
        # self.process_peers_timer.cancel()

        #Disconnect all clients as the file is done (if seeding is implemented, don't disconnect every peer, only the ones that are done downloading)
        for client in self.clients:
            client.disconnect()

        # self.get_peers_thread = None
        # self.process_trackers_timer = None
        # self.process_peers_timer = None

    def get_peers(self):
        payload = {
            'info_hash': bytes.fromhex(self.info['info_hash']),
            'peer_id': bytes.fromhex(bencodeinfo.generate_rand_peerid()),
            'port': 6881,
            'uploaded': 0,
            'downloaded': 0,
            'compact': 1
        }

        # dht.get_info_from_dht(self.info['info_hash'])

        ips = []
        if 'announce_list' in self.info:
            for url in self.info['announce_list']:
                peers = []
                if url.startswith("udp"):
                    peers = udp.get_peers(payload, url)
                elif url.startswith('http'):
                    peers = tcp.get_peers(payload, url)
                # if url.startswith("udp"):
                #     peers = udp.get_peers(payload, url)
                #     print(peers)
                
                if peers:
                    # ips.extend(peers)

                    for peer in peers:
                        self.start_worker(peer)


        #Start dht 
        threading.Thread(target=dht.get_info_from_dht, args=(self.info['info_hash'],self.start_worker,)).start()

        #ips.extend([ip for ip in dht.get_info_from_dht(self.info['info_hash'])])
        #return ips
    
    def check_for_metadata(self, fut):
        if self.info:
            return
        
        res = fut.result()
        if not res:
            return

        buf = res[0]

        info = bencodeinfo.get_from_buf(buf)
        if info['info_hash'] == self.info_hash:
            self.info = info
            self.metadata_info = res[1]

            self.stop_event.set()


    def download_magnet(self, magnet_url):
        import re
        from urllib.parse import unquote
        from dht_client import DhtClient

        split_data = magnet_url.split('&')
        self.info_hash = split_data[0].split(':')[-1]

        url_args = [args.split('=') for args in split_data][1:]
        for args in url_args:
            if args[0] == 'tr':
                tracker_url = unquote(args[1])
                payload = {
                    'info_hash': bytes.fromhex(self.info_hash),
                    'peer_id': bytes.fromhex(bencodeinfo.generate_rand_peerid()),
                    'port': 6881,
                    'uploaded': 0,
                    'downloaded': 0,
                    'compact': 1
                }
                peers = []
                if tracker_url.startswith('udp'):
                    peers = udp.get_peers(payload, tracker_url, self.vpn_interface)
                elif tracker_url.startswith('http'):
                    peers = tcp.get_peers(payload, tracker_url)
                
                if peers:
                    self.peers.extend(peers)

        info = {
            'info_hash': self.info_hash,
            'peer_id': bencodeinfo.generate_rand_peerid()
        }

        futures = []
        self.stop_event = threading.Event()
        while not self.info and not self.stop_event.is_set():
            # for peer in self.peers:
            #     res = DhtClient(peer[0], peer[1], info, self.vpn_interface).start(self.stop_event)
            #     if res:
            #         break
            with ThreadPoolExecutor(40) as e:
                for peer in self.peers:
                    future = e.submit(DhtClient(peer[0], peer[1], info, self.vpn_interface).start, self.stop_event)
                    future.add_done_callback(self.check_for_metadata)

                    futures.append(future)

                concurrent.futures.wait(futures)

            #     self.peers = []
                for peer in dht.get_info_from_dht(self.info_hash):
                    if peer not in self.peers:
                        self.peers.append(peer)
                    future = e.submit(DhtClient(peer[0], peer[1], info, self.vpn_interface).start, self.stop_event)
                    future.add_done_callback(self.check_for_metadata)

                    futures.append(future)

                concurrent.futures.wait(futures)

            if self.info:
                break
            time.sleep(2)

            #use dht to get node
            # if not self.info:
            #     for peer in dht.get_info_from_dht(self.info_hash):
            #         self.peers.append(peer)
            #         future = e.submit(DhtClient(peer[0], peer[1], info, self.vpn_interface).start, self.info)
            #         future.add_done_callback(self.check_for_metadata)

            #         futures.append(future)

        
        
        self.download()
    
    def reconnect_workers(self):
        for client in self.clients[:]:
            self.start_worker((client.ip, client.port))
        
    def start_worker(self, peer, delay=-1):
        if self.finished:
            return
        
        if delay != -1:
            time.sleep(delay)

        client_peers = [(client.ip, client.port) for client in self.clients]

        #If peer is already connected, don't reconnect to it
        if peer in client_peers:
            return
        
        #print(f"Connecting to {peer[0]}:{peer[1]}")

        worker = client.Client(peer[0], peer[1], self.info, self.metadata_info, self.vpn_interface, disconnect_callback=self.disconnect_peer)
        worker_thread = threading.Thread(target=worker.start, daemon=True, args=[self.work_queue, self.results])

        worker_thread.start()
        self.clients.append(worker) 

        
    def download_torrent(self, torrent_url: str):
        content = requests.get(torrent_url).content
        if not content:
            print("Invalid torrent url")
            return
        
        self.info = bencodeinfo.get_from_buf(content)
        #self.peers = self.get_peers()
        self.download()

    def download_torrent_from_file(self, torrent_path: str):
        with open(torrent_path, 'rb') as f:
            content = f.read()
            if not content:
                print("Invalid torrent file")
                return
            
            self.info = bencodeinfo.get_from_buf(content)
            self.download()

    
    def process_trackers(self):
        print("GETTING NEW PEERS!")
        new_peers = self.get_peers()
        for new_peer in new_peers:
            if self.finished:
                break

            if not new_peer in self.peers:
                self.peers.append(new_peer)
            else:
                self.peers.remove(new_peer)

        self.start_workers()


    def disconnect_peer(self, client):
        if client in self.clients:
            self.clients.remove(client)
        if (client.ip, client.port) in self.peers:
            self.peers.remove((client.ip, client.port))

        #print(f"{client.ip}:{client.port} disconnected!, Total clients: {len(self.clients)}")

        #Try to reconnect to this peer 
        if self.finished:
            return
        self.start_worker((client.ip, client.port), delay=10)
    

    def process_peers(self):
        while not self.finished:
            for client in self.clients[:]:
                try:
                    if self.finished:
                        break
                    if not client.is_running:
                        continue
                    if not client.sock_conn:
                        continue

                        
                    #If client hasn't recieved any new messages in over 30 seconds, then disconnect
                    if (datetime.datetime.now(datetime.timezone.utc) - client.last_active).total_seconds() > 30:
                        client.disconnect() 
                        continue

                    if client.is_choking:
                        client.message.send_unchoke(client.sock_conn)
                        # client.message.send_interested(client.sock_conn)   
                    
                    client.send_keep_alive()
                except Exception as e:
                    pass
            time.sleep(2)

            
            
                

    def get_dht_peers(self):
        while not self.finished:
            worker_threads = []
            for peer in dht.get_info_from_dht(self.info_hash):
                worker = client.Client(peer[0], peer[1], self.info, self.metadata_info, self.vpn_interface)
                thread = threading.Thread(target = worker.start, args=[self.work_queue, self.results])

                worker_threads.append(thread)
                thread.start()
            # with ThreadPoolExecutor(40) as e:
            #     futures = []
            #     for peer in dht.get_info_from_dht(self.info_hash):
            #         worker = client.Client(peer[0], peer[1], self.info, self.metadata_info, self.vpn_interface)
            #         futures.append(e.submit(worker.start, self.work_queue, self.results))
                
            #     concurrent.futures.wait(futures)
            time.sleep(30)

    def get_new_dht_peers(self):
        while not self.finished:
            time.sleep(5)
            dht.get_info_from_dht(self.info['info_hash'],self.start_worker)


    def download(self):
        if not self.info:
            print("No info... not enough seeders")
            return


        self.files = self.info['files']

        print("DOWNLOADING!")
        #print(f"DOWNLOADING {self.info['name']}")
        # if not self.peers:
        #     self.peers = self.get_peers()

        self.work_queue = Queue()
        self.results = Queue()

        for file in self.files:
            if os.path.dirname(file['path']):
                os.makedirs(os.path.dirname(file['path']), exist_ok=True)

            
            f = open(file['path'], 'wb')
            f.truncate(file['length'])
            self.open_files.append(f)

        self.get_peers_thread = threading.Thread(target = self.get_peers)
        self.get_peers_thread.start()

        save_thread = threading.Thread(target = self.save)
        save_thread.start()

        for ind, piece_hash in enumerate(self.info['piece_hashes']):
            length = torrent_util.calculate_piece_size(self.info['piece_length'], self.info['length'], ind)
            self.work_queue.put({'index': ind, 'hash': piece_hash, 'length': length})

        # self.start_workers()
        
        # #Tries to get new peers from dht every 10 seconds
        self.process_trackers_thread = threading.Thread(target=self.get_new_dht_peers)
        self.process_trackers_thread.start()

        self.process_peers_thread = threading.Thread(target=self.process_peers)
        self.process_peers_thread.start()
    

      
