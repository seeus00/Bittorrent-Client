import struct
import socket

def parse_ips(peers: bytes):
    ips = []
    offset = 0
    peer_size = 6
    num_peers = int(len(peers) / peer_size)
    for _ in range(0, len(peers), 6):
        # offset = i * peer_size
        # ip = socket.inet_ntoa(peers[offset:offset + 4])
        # port = struct.unpack_from("!H", peers[offset + 4:offset + 6])[0]
        # ips.append((ip, port))
        
        ip1 = struct.unpack_from("!i", peers, offset)[0] # ! = network order(big endian); i = int
        
        first_ip = socket.inet_ntoa(struct.pack("!i", ip1))
        offset += 4 # save where the first ip ends and the port begins

        if offset + 2 > len(peers):
            return ips

        port1 = struct.unpack_from("!H", peers, offset)[0] # H = unsigned short
        offset += 2
        ips.append((first_ip, port1))
        
    return ips 