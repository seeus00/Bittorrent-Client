from concurrent.futures import ThreadPoolExecutor
from queue import Queue, Empty

import client
import torrent_util
import bencodeinfo
import concurrent
import threading
import time
import udp
import tcp
import dht.dht as dht

class TorrentManager:
    def __init__(self, info=None, vpn_interface=None, port=6881):
        self.info = info
        self.peers = []
        self.finished = False
        self.fs = None

        self.vpn_interface = vpn_interface
        self.port = port

    def save(self):
        self.fs = open(self.info['name'], 'wb') 
        self.fs.truncate(self.info['length'])
        #buf = bytearray(self.info['length'])
        
        while not self.finished:
            done_pieces = 0
            while done_pieces < len(self.info['piece_hashes']):
                try:
                    res = self.results.get(timeout=60 * 3)
                    beg, end = torrent_util.calculate_bounds_for_piece(self.info['piece_length'], 
                        self.info['length'], res['index'])

                    self.fs.seek(beg)
                    self.fs.write(res['buffer'])

                    # for i in range(len(res['buffer'])):
                        #buf[beg + i] = res['buffer'][i]

                    done_pieces += 1
                    percent = (float(done_pieces) / len(self.info['piece_hashes']) * 100)
                    print(percent)

                #If it takes too long to retrieve data, get new peers
                except Empty as e:
                    self.peers = self.get_peers()
                    self.start_workers()
        
            print("FINISHED")
            self.finished = True

            self.fs.close()

    def get_peers(self):
        payload = {
            'info_hash': bytes.fromhex(self.info['info_hash']),
            'peer_id': bytes.fromhex(self.info['peer_id']),
            'port': 6881,
            'uploaded': 0,
            'downloaded': 0,
            'left': self.info['length'],
            'compact': 1
        }

        ips = []
        if 'announce_list' in self.info:
            for url in self.info['announce_list']:
                if url.startswith("udp"):
                    peers = udp.get_peers(payload, url)
                    if peers:
                        ips.extend(peers)
                else:
                    peers = tcp.get_peers(payload, url)
                    if peers:
                        ips.extend(peers)
        else:
            ips = dht.get_info_from_dht(self.info['info_hash'])

        return ips
    
    def check_for_metadata(self, fut):
        if self.info:
            return
        
        buf = fut.result()
        if not buf:
            return

        print(buf)

        info = bencodeinfo.get_info_from_buf(buf)
        if info['info_hash'] == self.info_hash:
            self.info = info


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

        if not self.peers:
            self.peers = dht.get_info_from_dht(self.info_hash)

        info = {
            'info_hash': self.info_hash,
            'peer_id': bencodeinfo.generate_rand_peerid()
        }

        futures = []
        with ThreadPoolExecutor(40) as e:
            for peer in self.peers:
                future = e.submit(DhtClient(peer[0], peer[1], info, self.vpn_interface).start)
                future.add_done_callback(self.check_for_metadata)

                futures.append(future)
        
        concurrent.futures.wait(futures)
        self.download()
            

    def start_workers(self):
       with ThreadPoolExecutor(40) as e:
            for peer in self.peers:
                worker = client.Client(peer[0], peer[1], self.info, None, self.vpn_interface)
                e.submit(worker.start, self.work_queue, self.results)
        

    def download(self):
        if not self.info:
            print("No info... not enough seeders")
            return

        print(f"DOWNLOADING {self.info['name']}")
        if not self.peers:
            self.peers = self.get_peers()

        self.work_queue = Queue(maxsize=len(self.info['piece_hashes']))
        self.results = Queue()

        for ind, piece_hash in enumerate(self.info['piece_hashes']):
            length = torrent_util.calculate_piece_size(self.info['piece_length'], self.info['length'], ind)
            self.work_queue.put({'index': ind, 'hash': piece_hash, 'length': length})

        save_thread = threading.Thread(target = self.save)
        save_thread.start()

        self.start_workers()
        save_thread.join()

      
