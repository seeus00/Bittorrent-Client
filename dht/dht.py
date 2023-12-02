import socket
import bencoding
import random
import peer_helper
import time
import struct
import traceback
import subprocess
from threading import Timer

# def split_nodes(nodes):
#     length = len(nodes)
#     if (length % 26) != 0:
#         return

#     info = []
#     for i in range(0, length, 26):
#         nid = nodes[i:i+20]
#         ip = socket.inet_ntoa(nodes[i+20:i+24])
#         port = struct.unpack("!H", nodes[i+24:i+26])[0]
#         info.append((nid, ip, port))

#     return info

# def get_data_from_dht_node(peer):
#     print(peer)
#     ip, port = peer

#     try:
#         sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         sock.settimeout(3)

#         sock.connect((ip, port))

#         # handshake = {
#         #     b'm': {
#         #         b'LT_metadata': 1,
#         #         b'ut_pex': 2
#         #     },
#         #     b'p': port,
#         #     b'v': b'Torrent 1.2'
#         # }

#         # handshake_encoded = bencoding.encode(handshake)

#         # sock.sendall(handshake_encoded)

#         res=sock.recv(1024)
#         print(res)

#         data = {
#             b'msg_type': 0, 
#             b'piece': 0
#         }
#         # data_encoded = bencoding.encode(data)
#         # sock.sendall(data_encoded)
#         # res = sock.recv(1024)
#         # print(res)
#     except Exception as e:
#         print(str(e))


def newID():
  import uuid
  return uuid.uuid4().hex[0:20].encode()








    # time.sleep(1 * 60)


#Callback is used to notify user of new peer
def get_info_from_dht(info_hash, callback):
    from subprocess import Popen, PIPE, STDOUT
    from watchdog_timer import WatchdogTimer
    
    proc = subprocess.Popen(['node', 'dht/index.js', info_hash], stdout=subprocess.PIPE)
    
    ips = []
        
    timeout = 3
    with Popen(['node', 'dht/index.js', info_hash], stdout=PIPE, stderr=STDOUT, universal_newlines=True) as process:  # text mode
    # kill process in timeout seconds unless the timer is restarted
        watchdog = WatchdogTimer(timeout, callback=process.kill, daemon=True)
        watchdog.start()
        for line in process.stdout:
            # don't invoke the watcthdog callback if do_something() takes too long
            with watchdog.blocked:
                if not line:  # some criterium is not satisfied
                    process.kill()
                    break
                
                ip, port = [peer for peer in line.rstrip().split(':')]
                #ips.append((ip, int(port)))
                callback((ip, int(port)))

                watchdog.restart()  # restart timer just before reading the next line
        watchdog.cancel()

    # while True:
    #     line = proc.stdout.readline().decode()
    #     if not line:
    #         break
        
    #     ip, port = [peer for peer in line.rstrip().split(':')]

    #     ips.append((ip, int(port)))

    proc.kill()
    
    #return ips

# def get_info_from_dht(info_hash):
#     try:
#         sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
#         # sock.bind(('0.0.0.0', 6881))

#         # network_info = ('87.98.162.88', 6881)
#         network_info = (socket.gethostbyname('router.bittorrent.com'), 6881)
#         sock.connect(network_info)

#         # sock.connect(network_info)
#         sock.settimeout(3)
#         # sock.connect(('87.98.162.88', 6881))
#         #sock.connect((socket.gethostbyname('router.bittorrent.com'), 6881))

#         #announce_peers = {"t":"aa", "y":"q", "q":"announce_peer", "a": {"id":0, "implied_port": 1, "info_hash":info_hash, "port": 6881, "token": ""}}

#         rand = lambda: ''.join([chr(random.randint(0, 255)) for _ in range(20)])
#         my_id = rand()
#         get_peers = {b"t":b'aa', b"y":b"q", b"q":b"get_peers",
#             b"a": {b"id":my_id,
#                   b"info_hash": info_hash}
#         }


#         encoded_data = bencoding.encode(get_peers)
#         sock.send(encoded_data)
#         res = sock.recv(1024)
#         decoded_resp = bencoding.decode(res)
#         # vals = struct.unpack("!20s4sH", decoded_resp[b'r'][b'nodes'])
#         #print(len(decoded_resp[b'r'][b'nodes']))
#         nodes = decoded_resp[b'r'][b'nodes']
#         print(nodes)
#         # ret = []
#         # for i in range(0, len(nodes), 26):
#         #     s = nodes[i:i+26]
#         #     ip = socket.inet_ntop(socket.AF_INET, s[-6:][:4])
#         #     port = struct.unpack(">H", s[-2:])[0]
#         #     ret += [(ip, port)]
#         # print(ret)
#         # split = split_nodes(nodes)
#         # connect_peer = split[0]

#         # get_peers = {b"t":b'aa', b"y":b"q", b"q":b"get_peers",
#         #     b"a": {b"id":my_id,
#         #           b"info_hash": info_hash}
#         # }
#         # encoded_data = bencoding.encode(get_peers)
#         # sock.sendto(encoded_data, (connect_peer[1], connect_peer[2]))
#         # res = sock.recvfrom(1024)
#         # print(res)


#         # query_id = decoded_resp[b'r'][b'id']
#         # target_id, ip, port = split[0]

#         #val = search_for_values(sock, info_hash, target_id)
#         #print(val)












#         # find_node = {b"t":b"0f", b"y":b"q", b"q":b"find_node", b"a": {b"id":my_id.encode(), b"target":target_id}}
#         # encoded_data = bencoding.encode(find_node)

#         # sock.sendall(encoded_data)
#         # res = sock.recv(1024)
#         # decoded_resp = bencoding.decode(res)
#         # print(decoded_resp)
#         # nodes = decoded_resp[b'r'][b'nodes']
#         # split = split_nodes(nodes)
        
#         # id = nodes = decoded_resp[b'r'][b'id']
#         # target_node = split[0][0]











#         # print(split)

#         # sock.close()



#         # announce_peers = {"t":"aa", "y":"q", "q":"announce_peer", "a": {"id":target_node, "implied_port": 1, "info_hash":info_hash, "port": 6881, "token": "aoeusnth"}}
#         # encoded_data = bencoding.encode(announce_peers)

#         # sock.sendall(encoded_data)
#         # res = sock.recv(1024)
#         # decoded_resp = bencoding.decode(res)
#         # print(decoded_resp)

#         # val = search_for_values(sock, info_hash, target_node)
#         # print(val)














#         # while True:
#         #     find_node = {b"t":b"0f", b"y":b"q", b"q":b"find_node", b"a": {b"id":target_node, b"target":id}}
#         #     encoded_data = bencoding.encode(find_node)

#         #     sock.sendall(encoded_data)
#         #     res = sock.recv(1024)
#         #     decoded_resp = bencoding.decode(res)

#         #     nodes = decoded_resp[b'r'][b'nodes']
#         #     split = split_nodes(nodes)
            
#         #     id = nodes = decoded_resp[b'r'][b'id']
#         #     target_node = split[0][0]



#         # values = search_for_values(info_hash, split[0][0])
#         # print(values)

#         # peers = peer_helper.parse_ips(nodes)
#         # get_data_from_dht_node(peers[0])
            
#     except Exception as e:
#         pass

#         traceback.print_exc()