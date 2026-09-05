memory = """
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

""" + str(0xFE)

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
    exit(errCode)
    
def isWhiteSpace(index: int) -> int:
    return memory[index] == ' '.encode()[0] or memory[index] == '\t'.encode()[0]

def skipWhiteSpace(index: int) -> int:
    while True:
        if isWhiteSpace(index):
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
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and isWhiteSpace(index)

def equals4(index: int, c1: int, c2: int, c3: int, c4: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == ' '.encode()[0]

def error(value):
    print_char('E')
    print_char('R')
    print_char('R')
    print_char('[')
    print_i32(value)    
    print_char(']')
    exit_program(value)

def writeFromHex(index: int) -> int:
    result = 0
    val = 0
    char = 0
    
    while True:
        char = memory[index]

        if char >= '0'.encode()[0] and char <= '9'.encode()[0]:
            val = '0'.encode()[0]     
        elif c >= 'A'.encode()[0] and c <= 'F'.encode()[0]:
            val = c - 'A'.encode()[0] + 10
        elif c >= 'a'.encode()[0] and c <= 'f'.encode()[0]:
            val = c - 'a'.encode()[0] + 10
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
        write_char(memory[index])

        index = index + 1
        if isWhiteSpace(index):
            break
    return index

def writeByte(number: int):
    byte = 0

    while number > 0:
        byte = number & 0x7F
        if number > 128:
            byte |= 0x80
        write_char(byte)
        number = number >> 7

def writeFromEncoding(index: int) -> int:
    if equals3(index, 'h'.encode()[0], 'e'.encode()[0], 'x'.encode()[0]):
        index = skipWhiteSpace(index)
        return writeFromHex(index)
    elif equals3(index, 'b'.encode()[0], 'i'.encode()[0], 'n'.encode()[0]):
        index = skipWhiteSpace(index)
        return writeFromBin(index)
    elif equals3(index, 's'.encode()[0], 't'.encode()[0], 'r'.encode()[0]):
        index = skipWhiteSpace(index)
        return writeFromString(index)
    elif equals4(index, 'u'.encode()[0], 'l'.encode()[0], 'e'.encode()[0], 'b'.encode()[0]):
        index = skipWhiteSpace(index)
        return writeFromString(index)
    else:
        error(0x03)

def main():
    pass

main()


print_i32(3)
print_char(3)
write_char(3)
isWhiteSpace(3)
skipWhiteSpace(3)
isComment(3)
skipComment(3)
equals3(3, 3, 3, 3)
equals4(3, 3, 3, 3, 3)
writeFromHex(3)
writeFromBin(3)
writeFromString(3)
writeByte(3)
writeFromEncoding(3)
main()
error(3)
exit_program(3)