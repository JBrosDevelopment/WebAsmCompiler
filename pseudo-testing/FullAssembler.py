memory = list("""
SECTION_HEADER

SECTION SECTION_TYPE
FUNCTION uleb 1 i32 uleb 0 #print_i32_type 0 ; func(i32) -> void
FUNCTION uleb 0 uleb 0 #main_type 1 ; func() -> void
SECTION_END

SECTION SECTION_IMPORT
uleb 3 str env uleb 9 str print_i32 FUNCTION_KIND $print_i32_type
SECTION_END

SECTION SECTION_FUNCTION
#main 0 $main_type
SECTION_END

SECTION SECTION_EXPORT
uleb 1
uleb 4 str main FUNCTION_KIND $main
SECTION_END

SECTION SECTION_CODE
uleb 1

FUNCTION_START ; main function
    const uleb 6
    const uleb 7
    add
    call $print_i32
    end
FUNCTION_END

SECTION_END

""" + str(0xFE))

for i in range(len(memory)):
    memory[i] = memory[i].encode()[0]

# pseudo code more indepth:
#
# define type print_i32_type(i32) -> void
# define type main_type() -> void
# import print_i32_type: "env.print_i32"
# define function main_type: main()
# export main: "main"
# main:
#    print_i32(6+7)
#

# pseudo code lite:
#
# import print_i32
# func main() -> void {
#     print_i32(6 + 7)
# }
#

def print_i32(value): # import
    print(value)

def print_char(value): # import
    print(value)

def write_char(char): # import
    print('write: `', char, '`')

def exit_program(errCode): # import
    global BYTES_OUT
    print('memory dump: ', sectionMemory)
    exit(errCode)

sectionMemory = list([0] * 1024) # global

BYTES_OUT = 0 # global
LAST_BYTES_OUT = 0 # global


def writeSectionChar(char: int) -> None:
    global BYTES_OUT
    sectionMemory[BYTES_OUT] = char
    BYTES_OUT = BYTES_OUT + 1 

def writeSection(type: int, length: int, start: int) -> None:
    # write type
    write_char(type)

    # write length
    byte = 0
    while length > 0:
        byte = length & 0x7F
        if length > 128:
            byte |= 0x80
        write_char(byte)
        length = length >> 7

    # write section data
    index = start
    while start + length > index:
        write_char(sectionMemory[index])
        index = index + 1

def isWhiteSpace(index: int) -> int:
    return memory[index] == ' '.encode()[0] or memory[index] == '\t'.encode()[0] or memory[index] == '\n'.encode()[0]

def skipWhiteSpace(index: int) -> int:
    while True:
        if not isWhiteSpace(index):
            break
        index = index + 1
    return index

def isComment(index: int) -> int:
    return memory[index] == ';'.encode()[0]

def skipComment(index: int) -> int:
    while True:
        if memory[index] == '\n'.encode()[0]:
            break
        index = index + 1
    return index

def equals3(index: int, c1: int, c2: int, c3: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and isWhiteSpace(index + 3)

def equals4(index: int, c1: int, c2: int, c3: int, c4: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and isWhiteSpace(index + 4)

def equals7(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and isWhiteSpace(index + 7)

def equals11(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and isWhiteSpace(index + 11)

def equals14(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int, c12: int, c13: int, c14: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and memory[index + 11] == c12 and memory[index + 12] == c13 and memory[index + 13] == c14 and isWhiteSpace(index + 14)

def error(value):
    print_char('E')
    print_char('R')
    print_char('R')
    print_char('[')
    print_i32(value)    
    print_char(']')
    exit_program(value)

def writeByte(number: int):
    byte = 0

    if number == 0:
        writeSectionChar(0x00)
        return

    while number > 0:
        byte = number & 0x7F
        if number > 128:
            byte |= 0x80
        writeSectionChar(byte)
        number = number >> 7

def writeFromHex(index: int) -> int:
    result = 0
    val = 0
    char = 0
    
    while True:
        char = memory[index]

        if char >= '0'.encode()[0] and char <= '9'.encode()[0]:
            val = '0'.encode()[0]     
        elif char >= 'A'.encode()[0] and char <= 'F'.encode()[0]:
            val = char - 'A'.encode()[0] + 10
        elif char >= 'a'.encode()[0] and char <= 'f'.encode()[0]:
            val = char - 'a'.encode()[0] + 10
        else:
            error(0x01)
        
        result = result * 16 + val

        index = index + 1
        if isWhiteSpace(index):
            break
    
    writeByte(result)

    return index

def writeFromBin(index: int) -> int:
    result = 0
    val = 0
    char = 0
    
    while True:
        char = memory[index]

        if char == '0'.encode()[0] or char == '1'.encode()[0]:
            val = char - '0'.encode()[0]
        else:
            error(0x02)
        
        result = (result << 1) | val

        index = index + 1
        if isWhiteSpace(index):
            break
    
    writeByte(result)

    return index

def writeFromString(index: int) -> int:
    while True:
        writeSectionChar(memory[index])

        index = index + 1
        if isWhiteSpace(index):
            break
    return index

def parseWord(index: int) -> int:
    global LAST_BYTES_OUT
    global BYTES_OUT
    if equals3(index, 'h'.encode()[0], 'e'.encode()[0], 'x'.encode()[0]):
        return writeFromHex(index)
    if equals3(index, 'b'.encode()[0], 'i'.encode()[0], 'n'.encode()[0]):
        return writeFromBin(index)
    if equals3(index, 's'.encode()[0], 't'.encode()[0], 'r'.encode()[0]):
        writeByte(memory[index])
        return index + 1
    if equals4(index, 'u'.encode()[0], 'l'.encode()[0], 'e'.encode()[0], 'b'.encode()[0]):
        return writeByte(index)
    if equals7(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0]):
        LAST_BYTES_OUT = BYTES_OUT
        return index + 7
    if equals11(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'E'.encode()[0], 'N'.encode()[0], 'D'.encode()[0]):
        writeSection(0x00, BYTES_OUT - LAST_BYTES_OUT, LAST_BYTES_OUT)
        return index + 11
    if equals14(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'H'.encode()[0], 'E'.encode()[0], 'A'.encode()[0], 'D'.encode()[0], 'E'.encode()[0], 'R'.encode()[0]):
        writeByte(0x00)
        writeByte(0x61)
        writeByte(0x73)
        writeByte(0x6D)
        writeByte(0x01)
        writeByte(0x00)
        writeByte(0x00)
        writeByte(0x00)
        return index + 14
        

    error(0x04)

def main():
    pass

main()

index = 0
while True:
    index = skipWhiteSpace(index)
    index = parseWord(index)

    if index >= len(memory):
        break

if LAST_BYTES_OUT != BYTES_OUT:
    writeSection(0x00, BYTES_OUT - LAST_BYTES_OUT, LAST_BYTES_OUT)