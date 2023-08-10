import math

def calculate_bounds_for_piece(piece_length, length, ind):
    beg = ind * piece_length
    end = beg + piece_length
    if end > length:
        end = length

    return (beg, end)


def calculate_piece_size(piece_length, length, ind):
    beg, end = calculate_bounds_for_piece(piece_length, length, ind)
    return end - beg


# def get_piece_len(info, piece_ind):
#     total_len = info['length']
#     piece_len = info['piece_length']

#     last_piece_len = total_len % piece_len
#     last_piece_ind = math.floor(total_len / piece_len)

#     return last_piece_ind if last_piece_ind == piece_ind else piece_len

# def blocks_per_piece(info, piece_ind):
#     piece_len = get_piece_len(info, piece_ind)
#     return math.ceil(piece_len / 16384)

# def block_len(info, piece_ind, block_ind):
#     piece_len = get_piece_len(info, piece_ind)

#     last_piece_len = piece_len % 16384
#     last_piece_ind = math.floor(piece_len / 16384)

#     return last_piece_ind if block_ind == last_piece_ind else 16384
