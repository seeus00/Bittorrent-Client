from itertools import chain
import torrent_util

class Pieces:
    def __init__(self, info):
        self.info = info
        self.requested = self.build_pieces_array()
        self.received = self.build_pieces_array()

    def build_pieces_array(self):
        n_pieces = len(self.info['piece_hashes'])
        arr = [None] * n_pieces
        for i in range(n_pieces):
            arr[i] = [False] * torrent_util.blocks_per_piece(self.info, i)

        return arr

    def add_requested(self, piece_block):
        block_ind = piece_block['begin'] // 16384
        self.requested[piece_block['index']][block_ind] = True

    def add_recevied(self, piece_block):
        block_ind = piece_block['begin'] // 16384
        self.recevied[piece_block['index']][block_ind] = True

    def needed(self, piece_block):
        req_lst = chain.from_iterable(zip(*self.requested))
        if all(val for val in req_lst):
            self.requested = [self.received[i][:] for i in range(len(self.received))]
        
        block_ind = piece_block['begin'] // 16384
        return not self.requested[piece_block['index']][block_ind]

    def is_done(self):
        rec_lst = chain.from_iterable(zip(*self.received))  
        return all(val for val in rec_lst)

    def print_percent_done():
        rec_lst = chain.from_iterable(zip(*self.received))  

        downloaded = len(list(filter(lambda x: x, rec_lst)))
        total = sum(len(blocks) for blocks in self.received)

        percent = downloaded / total * 100
        print(percent)