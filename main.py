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
    import psutil
    
    addrs = psutil.net_if_addrs()
    vpn_interfaces = list(filter(lambda key: 'surfshark' in key.lower(), addrs.keys()))
    if not vpn_interfaces:
        print("NO VPN!")
    else:
        vpn_interface = vpn_interfaces[0]
        vpn_ip = addrs[vpn_interface][0][1]

        manager = torrent_manager.TorrentManager(vpn_interface=vpn_ip)
        # manager.download_torrent("https://sukebei.nyaa.si/download/4008011.torrent")
        # manager.download_torrent_from_file("C:/Users/casey/Downloads/linuxmint-21.2-cinnamon-64bit.iso.torrent")
        # manager.download_torrent_from_file("C:/Users/casey/Downloads/So I'm a Spider, So What [Yen Press] [LuCaZ].torrent")
        manager.download_torrent("https://sukebei.nyaa.si/download/4010005.torrent")
  
    #manager = torrent_manager.TorrentManager()
    #manager.download_torrent_from_file("C:/Users/casey/Downloads/debian.torrent")

    

