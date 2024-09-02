import bencodeinfo
import bencoding
import requests
import socket
import struct
import torrent_manager
import urllib
import dht.dht as dht
import tcp

if __name__ == "__main__":    
    manager = torrent_manager.TorrentManager(vpn_interface=None)
    manager.download_torrent_from_file("test.torrent")

    

