import torrent_util
import threading

lock = threading.Lock()

def save_piece_to_file(file_name, piece_ind, buf_data, piece_length, length):
    with lock:
        beg, end = torrent_util.calculate_bounds_for_piece(piece_length, length, piece_ind)
        with open(file_name, 'wb') as f:
            f.seek(beg)
            f.write(buf_data)