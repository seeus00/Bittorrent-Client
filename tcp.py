import urllib
import requests
import bencoding
import struct
import socket
import peer_helper


def get_peers(payload, announce_url):
    query = urllib.parse.urlencode(payload, quote_via=urllib.parse.quote_plus)
   
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/54.0.2840.90 Safari/537.36'}
    
    get_req = f"{announce_url}&{query}" if '?' in announce_url else f"{announce_url}?{query}"
    try:
        r = requests.get(get_req, headers=headers)
        data = bencoding.decode(r.content)
        peers = data[b'peers']

        return peer_helper.parse_ips(peers)
    except Exception as e:
        print(e)

    return None