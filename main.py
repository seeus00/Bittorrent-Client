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


    # info = bencodeinfo.get_info('C:/Users/casey/Downloads/arch.torrent')
    

    
    # manager = torrent_manager.TorrentManager(info)
    # manager.download()
    
    import psutil
    
    addrs = psutil.net_if_addrs()
    vpn_interfaces = list(filter(lambda key: key.lower() == 'mullvad', addrs.keys()))
    if not vpn_interfaces:
        print("NO VPN!")
    else:
        vpn_interface = vpn_interfaces[0]
        vpn_ip = addrs[vpn_interface][0][1]
        
        manager = torrent_manager.TorrentManager(vpn_interface=vpn_ip)

        magnet_uri = 'magnet:?xt=urn:btih:cd73be1fe75be0a29833c457c586fab9d6bc49a9&dn=%2B%2B%2B%20%5BHD%5D%20ADN-350%20%E3%81%82%E3%81%AA%E3%81%9F%E3%80%81%E8%A8%B1%E3%81%97%E3%81%A6%E2%80%A6%E3%80%82%20%E7%94%B7%E3%82%84%E3%82%82%E3%82%81%E3%81%AE%E3%83%96%E3%83%AB%E3%83%BC%E3%82%B96%20%E6%97%A5%E4%B8%8B%E9%83%A8%E5%8A%A0%E5%A5%88&tr=http%3A%2F%2Fsukebei.tracker.wf%3A8888%2Fannounce&tr=udp%3A%2F%2Fopen.stealth.si%3A80%2Fannounce&tr=udp%3A%2F%2Ftracker.opentrackr.org%3A1337%2Fannounce&tr=udp%3A%2F%2Fexodus.desync.com%3A6969%2Fannounce&tr=udp%3A%2F%2Ftracker.torrent.eu.org%3A451%2Fannounce'
        manager.download_magnet(magnet_uri)

        
  


    

