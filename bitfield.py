def has_piece(buffer_bytes, ind):
    byte_ind = ind // 8
    offset = ind % 8

    if byte_ind < 0 or byte_ind >= len(buffer_bytes):
        return False

    return buffer_bytes[byte_ind] >> (7 - offset) & 1 != 0

def set_piece(buffer_bytes, ind):
    byte_ind = ind // 8
    offset = ind % 8

    if byte_ind < 0 or byte_ind >= len(buffer_bytes):
        return False

    buffer_bytes[byte_ind] |= 1 << (7 - offset)
