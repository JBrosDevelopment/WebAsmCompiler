memory = ['a'.encode()[0], 'd'.encode()[0], 'd'.encode()[0],
          ' '.encode()[0], '1'.encode()[0], '5'.encode()[0],
          ' '.encode()[0], '2'.encode()[0], ';'.encode()[0],
          '\n'.encode()[0],
          'a'.encode()[0], 'd'.encode()[0], 'd'.encode()[0],
          ' '.encode()[0], '1'.encode()[0], '5'.encode()[0],
          ' '.encode()[0], '2'.encode()[0], ';'.encode()[0],
          0xFE]

def print_i32(value):
    if value == 0xFD:
        print(value, '`Invalid Char`')
    elif value == 0xFC:
        print(value, '`Invalid Argument Number`')
    elif value == 0xFB:
        print(value, '`Invalid Command`')
    else: 
        print(value)

def write_char(char):
    if char == 0xFE:
        print('write: `EOF`')
    else:
        print('write: `', char, '`')

def IntoULEB128(number):
    byte = number & 0x7F

    if number > 128:
        byte |= 0x80

    return byte

def WriteULEB128(number):
    byte = 0

    while number > 0:
        byte = IntoULEB128(number)
        write_char(byte)
        number = number >> 7

def WordToI32(startWord, wordLength):
    char = 0
    digit = 0
    product = 0
    index = 0

    while index < wordLength:
        char = memory[startWord + index]

        if char < '0'.encode()[0] or char > '9'.encode()[0]:
            return 0xFC

        digit = char - '0'.encode()[0]
        product = product * 10 + digit

        index = index + 1
    
    return product

def WordToCMD(startWord, wordLength):
    if wordLength == 3 and memory[startWord] == 'a'.encode()[0] and memory[startWord + 1] == 'd'.encode()[0] and memory[startWord + 2] == 'd'.encode()[0]:
        return 0x6A
    else:
        return 0xFB

def main():
    bytes = 0
    char = 0
    cmd = 0
    number = 0
    startWord = 0
    wordLength = 0
    stateCMD = 1

    while True:
        char = memory[bytes]
        bytes = bytes + 1

        if char == 0xFE:
            break

        if char == '\n'.encode()[0]:
            stateCMD = 1
            startWord = bytes
        elif char == ' '.encode()[0] or char == '\t'.encode()[0] or char == ';'.encode()[0]:
            if stateCMD == 2:
                stateCMD = 0
                cmd = WordToCMD(startWord, wordLength)

                if cmd == 0xFB:
                    print_i32(0xFB)
                    return

                write_char(cmd)
            elif stateCMD == 0:
                number = WordToI32(startWord, wordLength)

                if number == 0xFC:
                    print_i32(0xFC)
                    return

                WriteULEB128(number)
            
            startWord = bytes ################################################# only change remove + 1
            wordLength = 0
            continue

        elif (char >= 'a'.encode()[0] and char <= 'z'.encode()[0]) or (char >= 'A'.encode()[0] and char <= 'Z'.encode()[0]) or (char >= '0'.encode()[0] and char <= '9'.encode()[0]) or char == '_'.encode()[0]:
            if stateCMD == 1:
                stateCMD = 2
            wordLength = wordLength + 1
        else: 
            print(char)
            print_i32(0xFD)
            return
        
    write_char(0xFE)
    
    print_i32(bytes)


main()