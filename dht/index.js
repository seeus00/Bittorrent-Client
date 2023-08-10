import DHT from 'bittorrent-dht'
import dgram from 'dgram'
import bencode from 'bencode'





// function makeid(length) {
//   let result = '';
//   const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
//   const charactersLength = characters.length;
//   let counter = 0;
//   while (counter < length) {
//     result += characters.charAt(Math.floor(Math.random() * charactersLength));
//     counter += 1;
//   }
//   return result;
// }



// var socket = dgram.createSocket('udp4');


// var info_hash = "436e5f8b85a51d5545156e15cc144ba1144991ff"

// var get_peers = {"t":'aa', "y":"q", "q":"get_peers",
// "a": {"id":makeid(20),
//       "info_hash": new TextEncoder().encode(info_hash) }}


// function parseIp (buf, offset) {
//   return buf[offset++] + '.' + buf[offset++] + '.' + buf[offset++] + '.' + buf[offset++]
// }

// function parseNodes (buf, idLength) {
//   var contacts = []

//   try {
//     for (var i = 0; i < buf.length; i += (idLength + 6)) {
//       var port = buf.readUInt16BE(i + (idLength + 4))
//       if (!port) continue
//       contacts.push({
//         id: buf.slice(i, i + idLength),
//         host: parseIp(buf, i + idLength),
//         port: port,
//         distance: 0,
//         token: null
//       })
//     }
//   } catch (err) {
//     console.log(err)
//   }

//   return contacts
// }
      

      
// socket.addListener('message', (buf, obj) => {
//   var ben = bencode.decode(buf)
//   // console.log(ben)
//   if (ben.e || !ben.r) {
//     // console.log(ben)
//     return
//   }
//   if (ben.r.token) {
//     console.log("TOKEN")
//     console.log(ben.r.token)
//   }

//   if (ben.r.values) {
//     console.log("VALUES")
//     console.log(ben.r.values)
//     return
//   }

//   var nodes = parseNodes(Buffer.from(ben.r.nodes), 20)

//   //console.log(nodes.length)
//   // var get_peers_data = {"t":'aa', "y":"q", "q":"get_peers",
//   //   "a": {"id": makeid(20),
//   //   "info_hash": info_hash }
//   // }

//   for (let i = 0; i < nodes.length; i++) {
//     var get_peers_data = {"t":'aa', "y":"q", "q":"get_peers",
//         "a": {"id": makeid(20),
//         "info_hash": info_hash }
//     }

//     var send_data = bencode.encode(get_peers_data)
    
//     socket.send(send_data, 0, send_data.length, nodes[i].port, nodes[i].host, (err, data) => {

//     })
//   }
// })

// var buf = bencode.encode(get_peers)

// socket.send(buf, 0, buf.length, 6881, '67.215.246.10', (err, data) => {
  
// })


const dht = new DHT()

// dht.listen(20000, function () {
//   console.log('now listening')
// })

dht.on('peer', function (peer, infoHash, from) {
  console.log(peer.host + ':' + peer.port)
})

// find peers for the given torrent info hash
dht.lookup(process.argv[2])