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


#Sets all indicies in bitfield to true (peer has all pieces)
def set_all_true(buffer_bytes):
    for ind in range(len(buffer_bytes)):
        set_piece(buffer_bytes, ind)

#Checks if bitfield has all pieces
def check_all_true(buffer_bytes):
    for ind in range(len(buffer_bytes)):
        if not has_piece(buffer_bytes, ind):
            return False
        
    return True