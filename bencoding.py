def decode(data):
    stack = []
    root = {} if chr(data[0]) == 'd' else []
    stack.append(root)

    ind = 1 #skip first byte
    prev_str = b""
    while ind < len(data):
        if chr(data[ind]) == 'd':
            if type(stack[-1]) is list:
                stack[-1].append({})
                stack.append(stack[-1][-1])
            else:
                stack[-1][prev_str] = {}
                stack.append(stack[-1][prev_str])
                prev_str = None
        elif chr(data[ind]) == 'l':
            if type(stack[-1]) is list:
                stack[-1].append([])
                stack.append(stack[-1][-1])
            else:
                stack[-1][prev_str] = []
                stack.append(stack[-1][prev_str])
                prev_str = None
        elif chr(data[ind]) == 'i':
            empty_str = bytearray(b"")
            ind += 1
            while chr(data[ind]) != 'e':
                empty_str.append(data[ind])
                ind += 1
            
            if stack[-1] is list:
                stack[-1].append(int(bytes(empty_str)))
            else:
                stack[-1][prev_str] = int(bytes(empty_str))
                prev_str = None

        elif chr(data[ind]) == 'e':
            stack.pop()
        else:
            str_len = ""
            while chr(data[ind]) != ':':
                str_len += chr(data[ind])
                ind += 1
            ind += 1
            empty_str = bytearray(b"")
            for i in range(int(str_len)):
                empty_str.append(data[ind])
                ind += 1
            ind -= 1
            
            if type(stack[-1]) is list:
                stack[-1].append(bytes(empty_str))
            elif type(stack[-1]) is dict and prev_str:
                stack[-1][prev_str] = bytes(empty_str)
                prev_str = None
            else:
                prev_str = bytes(empty_str)

        ind += 1
    return root

def encode(data, ben_str=bytes(b"")):
    if not data:
        return ben_str

    if type(data) is dict:
        ben_str += b'd'
        for key, value in data.items():
            if type(value) is str:
                value = value.encode()
            if type(key) is str:
                key = key.encode()

            if type(value) is bytes:
                ben_str += b"%d:%b%d:%b" % (len(key), key, len(value), value)                    
            elif type(value) is int:
                ben_str += b"%d:%bi%de" % (len(key), key, value)  
            else:
                ben_str += b"%d:%b" %(len(key), key)
                ben_str = encode(value, ben_str)

        ben_str += b'e'
    elif type(data) is list:
        ben_str += b'l'
        for child in data:
            ben_str = encode(child, ben_str)
        ben_str += b'e'
    else:
        if type(data) is bytes:
            ben_str += b"%d:%b" % (len(data), data)
        elif type(data) is int:
            ben_str += b"i%de" % (data)  

    return ben_str

