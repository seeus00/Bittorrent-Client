import torrent_util

class TorrentQueue:
    def __init__(self, info):
        self.info = info
        self.queue = []
        self.choked = True
    
    def add_piece(self, piece_ind):
        n_blocks = torrent_util.blocks_per_piece(self.info, piece_ind)
        for i in range(n_blocks):
            piece_block = {
                'index': piece_ind,
                'begin': i * 16384,
                'length': torrent_util.block_len(self.info, piece_ind, i)
            }
            self.queue.append(piece_block)

    def push(self, item):
        self.queue.append(item)

    def pop(self):
        return self.queue.pop()

    def size(self):
        return len(self.queue)