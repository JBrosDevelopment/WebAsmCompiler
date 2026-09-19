input_code = list("""
SECTION_HEADER

SECTION SECTION_TYPE ; 1
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
    i32.const uleb 6
    i32.const uleb 7
    i32.add
    call $print_i32
    end
FUNCTION_END
""")

#SECTION_END

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
    print('section memory dump: ', sectionMemory)
    exit(errCode)

memory = list([0] * 1024)

for i in range(len(input_code)):
    memory[i] = input_code[i].encode()[0]

sectionMemory = list([0] * 1024) # global

BYTES_OUT = 0 # global
LAST_BYTES_OUT = 0 # global
LAST_VARIABLE_ID = 0 # global
CURRENT_SECTION: int = 0 # global

variable_names = list([0] * 1024) # global
variable_names_stack_index: int = 0 # global
# variable names formatted like this:
# ID STR_LENGTH STRING
# example:
# 3, 5, 'H', 'e', 'l', 'l', 'o'

variable_values = list([0] * 1024) # global
variable_values_stack_index: int = 0 # global
# variable values formatted like this:
# ID VALUE
# example:
# 3, 72

def writeSectionChar(char: int) -> None:
    global BYTES_OUT
    sectionMemory[BYTES_OUT] = char
    BYTES_OUT = BYTES_OUT + 1 

def writeSection(type: int, length: int, start: int) -> None:
    write_char(type)

    section_length = length

    # write length as ULEB128
    byte = 0

    if length == 0:
        write_char(0)

    while length > 0:
        byte = length & 0x7F

        if length >= 128:
            byte |= 0x80

        write_char(byte)
        length = length >> 7

    # write section data
    index = start

    while index < start + section_length:
        write_char(sectionMemory[index])
        index += 1

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

def equals2(index: int, c1: int, c2: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and isWhiteSpace(index + 2)

def equals3(index: int, c1: int, c2: int, c3: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and isWhiteSpace(index + 3)

def equals4(index: int, c1: int, c2: int, c3: int, c4: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and isWhiteSpace(index + 4)

def equals5(index: int, c1: int, c2: int, c3: int, c4: int, c5: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and isWhiteSpace(index + 5)

def equals6(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and isWhiteSpace(index + 6)

def equals7(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and isWhiteSpace(index + 7)

def equals8(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and isWhiteSpace(index + 8)

def equals9(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and isWhiteSpace(index + 9)

def equals10(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and isWhiteSpace(index + 10)

def equals11(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and isWhiteSpace(index + 11)

def equals12(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int, c12: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and memory[index + 11] == c12 and isWhiteSpace(index + 12)

def equals13(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int, c12: int, c13: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and memory[index + 11] == c12 and memory[index + 12] == c13 and isWhiteSpace(index + 13)

def equals14(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int, c12: int, c13: int, c14: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and memory[index + 11] == c12 and memory[index + 12] == c13 and memory[index + 13] == c14 and isWhiteSpace(index + 14)

def equals16(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int, c12: int, c13: int, c14: int, c15: int, c16: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and memory[index + 11] == c12 and memory[index + 12] == c13 and memory[index + 13] == c14 and memory[index + 14] == c15 and memory[index + 15] == c16 and isWhiteSpace(index + 16)

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
    index = skipWhiteSpace(index)
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
    index = skipWhiteSpace(index)
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
    index = skipWhiteSpace(index)
    while True:
        writeSectionChar(memory[index])

        index = index + 1
        if isWhiteSpace(index):
            break
    return index

def writeFromUleb(index: int) -> int:
    index = skipWhiteSpace(index)
    result = 0
    digit = 0

    while True:
        digit = memory[index] - '0'.encode()[0]
        result = result * 10 + digit

        index += 1
        if isWhiteSpace(index):
            break

    writeByte(result)
    return index

def setVariable(index: int) -> int:
    global LAST_VARIABLE_ID
    global variable_names_stack_index
    global variable_values_stack_index

    variable_name_start = index
    variable_name_length = 0
    loop_index = 0
    result = 0

    # Get variable name
    while True:
        variable_name_length += 1
        index += 1

        if isWhiteSpace(index):
            break

    index = skipWhiteSpace(index)

    # Get value
    while True:
        digit = memory[index] - ord('0')
        result = result * 10 + digit
        index += 1

        if isWhiteSpace(index):
            break

    # Store variable name:
    variable_names[variable_names_stack_index] = LAST_VARIABLE_ID
    variable_names_stack_index += 1

    variable_names[variable_names_stack_index] = variable_name_length
    variable_names_stack_index += 1

    while loop_index < variable_name_length:
        variable_names[variable_names_stack_index] = memory[variable_name_start + loop_index]

        variable_names_stack_index += 1
        loop_index += 1

    # Store variable value:
    variable_values[variable_values_stack_index] = LAST_VARIABLE_ID
    variable_values_stack_index += 1

    variable_values[variable_values_stack_index] = result
    variable_values_stack_index += 1

    LAST_VARIABLE_ID += 1

    return index

def getVariable(index: int) -> int:
    variable_name_start = index
    variable_name_length = 0
    vname_pointer = 0
    variable_id = 0
    matches = 0
    stored_name_length = 0

    # Get variable name
    while True:
        variable_name_length += 1
        index += 1

        if isWhiteSpace(index):
            break

    # Search variable_names

    while vname_pointer < variable_names_stack_index:
        variable_id = variable_names[vname_pointer]
        vname_pointer += 1

        stored_name_length = variable_names[vname_pointer]
        vname_pointer += 1

        matches = 1

        # Lengths must match first
        if stored_name_length != variable_name_length:
            matches = 0

        # Compare characters
        loop_index = 0
        while loop_index < stored_name_length:

            if matches == 1:
                if memory[variable_name_start + loop_index] != variable_names[vname_pointer + loop_index]:
                    matches = 0

            loop_index += 1

        if matches == 1:
            # Search [ID, value] pairs
            value_pointer = 0
            while value_pointer < variable_values_stack_index:
                if variable_values[value_pointer] == variable_id:
                    value = variable_values[value_pointer + 1]

                    # Assuming LAST_BYTES_OUT represents the
                    # value that your assembler should output.
                    writeByte(value)
                    return index

                value_pointer += 2

        vname_pointer += stored_name_length

    error(0x03)

def parseCmd(index: int) -> int:
    i32_arithmatic = 0x6A
    i32_comparison = 0x45
    i64_arithmatic = 0x7C
    i64_comparison = 0x50
    f32_arithmatic = 0x8B
    f32_comparison = 0x5B
    f64_arithmatic = 0x99
    f64_comparison = 0x61
    type_arithmatic = 0
    type_comparison = 0
    type = 10
    if equals4(index, 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '.'.encode()[0]):
        type = 0x00
        type_arithmatic = i32_arithmatic
        type_comparison = i32_comparison
    if equals4(index, 'i'.encode()[0], '6'.encode()[0], '4'.encode()[0], '.'.encode()[0]):
        type = 0x01
        type_arithmatic = i64_arithmatic
        type_comparison = i64_comparison
    if equals4(index, 'f'.encode()[0], '3'.encode()[0], '2'.encode()[0], '.'.encode()[0]):
        type = 0x02
        type_arithmatic = f32_arithmatic
        type_comparison = f32_comparison
    if equals4(index, 'f'.encode()[0], '6'.encode()[0], '4'.encode()[0], '.'.encode()[0]):
        type = 0x03
        type_arithmatic = f64_arithmatic
        type_comparison = f64_comparison

    # control flow
    if equals5(index, 'b'.encode()[0], 'l'.encode()[0], 'o'.encode()[0], 'c'.encode()[0], 'k'.encode()[0]):
        writeByte(0x02)
        return index + 5
    if equals4(index, 'l'.encode()[0], 'o'.encode()[0], 'o'.encode()[0], 'p'.encode()[0]):
        writeByte(0x03)
        return index + 4
    if equals2(index, 'i'.encode()[0], 'f'.encode()[0]):
        writeByte(0x04)
        return index + 2
    if equals4(index, 'e'.encode()[0], 'l'.encode()[0], 's'.encode()[0], 'e'.encode()[0]):
        writeByte(0x05)
        return index + 4
    if equals3(index, 'e'.encode()[0], 'n'.encode()[0], 'd'.encode()[0]):
        writeByte(0x0B)
        return index + 3
    if equals2(index, 'b'.encode()[0], 'r'.encode()[0]):
        writeByte(0x0C)
        return index + 2
    if equals5(index, 'b'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 'i'.encode()[0], 'f'.encode()[0]):
        writeByte(0x0D)
        return index + 5
    if equals6(index, 'r'.encode()[0], 'e'.encode()[0], 't'.encode()[0], 'u'.encode()[0], 'r'.encode()[0], 'n'.encode()[0]):
        writeByte(0x0F)
        return index + 6
    # functions
    if equals4(index, 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], 'l'.encode()[0]):
        writeByte(0x10)
        return index + 4
    if equals13(index, 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], 'l'.encode()[0], '_'.encode()[0], 'i'.encode()[0], 'n'.encode()[0], 'd'.encode()[0], 'i'.encode()[0], 'r'.encode()[0], 'e'.encode()[0], 'c'.encode()[0], 't'.encode()[0]):
        writeByte(0x11)
        return index + 13
    # stack
    if equals4(index, 'd'.encode()[0], 'r'.encode()[0], 'o'.encode()[0], 'p'.encode()[0]):
        writeByte(0x1A)
        return index + 4
    # locals
    if equals9(index, 'l'.encode()[0], 'o'.encode()[0], 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], '.'.encode()[0], 'g'.encode()[0], 'e'.encode()[0], 't'.encode()[0]):
        writeByte(0x20)
        return index + 9
    if equals9(index, 'l'.encode()[0], 'o'.encode()[0], 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], '.'.encode()[0], 's'.encode()[0], 'e'.encode()[0], 't'.encode()[0]):
        writeByte(0x21)
        return index + 9
    if equals9(index, 'l'.encode()[0], 'o'.encode()[0], 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], '.'.encode()[0], 'e'.encode()[0], 'e'.encode()[0], 'e'.encode()[0]):
        writeByte(0x22)
        return index + 9
    # type specific instructions
    if type != 10: 
        index += 4
        # constants
        if equals5(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 's'.encode()[0], 't'.encode()[0]):
            writeByte(0x41 + type)
            return index + 5
        #arithmetic
        if equals3(index, 'a'.encode()[0], 'd'.encode()[0], 'd'.encode()[0]):
            writeByte(type_arithmatic + 0)
            return index + 3
        if equals3(index, 's'.encode()[0], 'u'.encode()[0], 'b'.encode()[0]):
            writeByte(type_arithmatic + 1)
            return index + 3
        if equals3(index, 'm'.encode()[0], 'u'.encode()[0], 'l'.encode()[0]):
            writeByte(type_arithmatic + 2)
            return index + 3
        if equals5('d'.encode()[0], 'i'.encode()[0], 'v'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeByte(type_arithmatic + 3)
            return index + 5
        if equals5('d'.encode()[0], 'i'.encode()[0], 'v'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeByte(type_arithmatic + 4)
            return index + 5
        if equals5('r'.encode()[0], 'e'.encode()[0], 'm'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeByte(type_arithmatic + 5)
            return index + 5
        if equals5('r'.encode()[0], 'e'.encode()[0], 'm'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeByte(type_arithmatic + 6)
            return index + 5
        if equals3(index, 'a'.encode()[0], 'n'.encode()[0], 'd'.encode()[0]):
            writeByte(type_arithmatic + 7)
            return index + 3
        if equals2(index, 'o'.encode()[0], 'r'.encode()[0]):
            writeByte(type_arithmatic + 8)
            return index + 2
        if equals3(index, 'x'.encode()[0], 'o'.encode()[0], 'r'.encode()[0]):
            writeByte(type_arithmatic + 9)
            return index + 3
        if equals3(index, 's'.encode()[0], 'h'.encode()[0], 'l'.encode()[0]):
            writeByte(type_arithmatic + 10)
            return index + 3
        if equals5(index, 's'.encode()[0], 'h'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeByte(type_arithmatic + 11)
            return index + 5
        if equals5(index, 's'.encode()[0], 'h'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeByte(type_arithmatic + 12)
            return index + 5
        if equals4(index, 'r'.encode()[0], 'o'.encode()[0], 't'.encode()[0], 'l'.encode()[0]):
            writeByte(type_arithmatic + 13)
            return index + 4
        if equals4(index, 'r'.encode()[0], 'o'.encode()[0], 't'.encode()[0], 'r'.encode()[0]):
            writeByte(type_arithmatic + 14)
            return index + 4
        # comparisons
        if equals3(index, 'e'.encode()[0], 'q'.encode()[0], 'z'.encode()[0]):
            writeByte(type_comparison + 0)
            return index + 3
        if equals2(index, 'e'.encode()[0], 'q'.encode()[0]):
            writeByte(type_comparison + 1)
            return index + 2
        if equals2(index, 'n'.encode()[0], 'e'.encode()[0]):
            writeByte(type_comparison + 2)
            return index + 2
        if equals4(index, 'l'.encode()[0], 't'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeByte(type_comparison + 3)
            return index + 4
        if equals4(index, 'l'.encode()[0], 't'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeByte(type_comparison + 4)
            return index + 4
        if equals4(index, 'g'.encode()[0], 't'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeByte(type_comparison + 5)
            return index + 4
        if equals4(index, 'g'.encode()[0], 't'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeByte(type_comparison + 6)
            return index + 4
        if equals4(index, 'l'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeByte(type_comparison + 7)
            return index + 4
        if equals4(index, 'l'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeByte(type_comparison + 8)
            return index + 4
        if equals4(index, 'g'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeByte(type_comparison + 9)
            return index + 4
        if equals4(index, 'g'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeByte(type_comparison + 10)
            return index + 4
        # memory loads
        if equals4(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0]):
            writeByte(0x28 + type)
            return index + 4
        if type == 0 or type == 1:
            if equals7(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '8'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeByte(0x2C + type*4)
                return index + 7
            if equals7(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '8'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeByte(0x2D + type*4)
                return index + 7
            if equals8(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '1'.encode()[0], '6'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeByte(0x2E + type*4)
                return index + 8
            if equals8(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '1'.encode()[0], '6'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeByte(0x2F + type*4)
                return index + 8
        if type == 1:
            if equals8(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeByte(0x34)
                return index + 8
            if equals8(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeByte(0x35)
                return index + 8
        # memory stores
        if equals5(index, 's'.encode()[0], 't'.encode()[0], 'o'.encode()[0], 'r'.encode()[0], 'e'.encode()[0]):
            writeByte(0x36 + type)
            return index + 5
        if type == 0 or type == 1:
            if equals6(index, 's'.encode()[0], 't'.encode()[0], 'o'.encode()[0], 'r'.encode()[0], 'e'.encode()[0], '8'.encode()[0]):
                writeByte(0x3A + type*2)
                return index + 6
            if equals7(index, 's'.encode()[0], 't'.encode()[0], 'o'.encode()[0], 'r'.encode()[0], 'e'.encode()[0], '1'.encode()[0], '6'.encode()[0]):
                writeByte(0x3B + type*2)
                return index + 7
        if type == 1:
            if equals7(index, 's'.encode()[0], 't'.encode()[0], 'o'.encode()[0], 'r'.encode()[0], 'e'.encode()[0], '3'.encode()[0], '2'.encode()[0]):
                writeByte(0x3E)
                return index + 7
        # conversions
        if type == 0:
            if equals8(index, 'w'.encode()[0], 'r'.encode()[0], 'a'.encode()[0], 'p'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '6'.encode()[0], '4'.encode()[0]):
                writeByte(0xA7)
                return index + 8
        if type == 1:
            if equals12(index, 'e'.encode()[0], 'x'.encode()[0], 't'.encode()[0], 'e'.encode()[0], 'n'.encode()[0], 'd'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeByte(0xAC)
                return index + 12
            if equals12(index, 'e'.encode()[0], 'x'.encode()[0], 't'.encode()[0], 'e'.encode()[0], 'n'.encode()[0], 'd'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeByte(0xAD)
                return index + 12
        if type == 2:
            if equals10(index, 'd'.encode()[0], 'e'.encode()[0], 'm'.encode()[0], 'o'.encode()[0], 't'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '6'.encode()[0], '4'.encode()[0]):
                writeByte(0xB6)
                return index + 10
        if type == 3:
            if equals11(index, 'p'.encode()[0], 'r'.encode()[0], 'o'.encode()[0], 'm'.encode()[0], 'o'.encode()[0], 't'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '3'.encode()[0], '2'.encode()[0]):
                writeByte(0xBB)
                return index + 11
        if type == 0 or type == 1:
            if equals11(index, 't'.encode()[0], 'r'.encode()[0], 'u'.encode()[0], 'n'.encode()[0], 'c'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeByte(0xA8 + type * 6)
                return index + 9
            if equals11(index, 't'.encode()[0], 'r'.encode()[0], 'u'.encode()[0], 'n'.encode()[0], 'c'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeByte(0xA9 + type * 6)
                return index + 9
            if equals11(index, 't'.encode()[0], 'r'.encode()[0], 'u'.encode()[0], 'n'.encode()[0], 'c'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '6'.encode()[0], '4'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeByte(0xAA + type * 6)
                return index + 9
            if equals11(index, 't'.encode()[0], 'r'.encode()[0], 'u'.encode()[0], 'n'.encode()[0], 'c'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '6'.encode()[0], '4'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeByte(0xAB + type * 6)
                return index + 9
        if type == 2 or type == 3:
            if equals12(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 'v'.encode()[0], 'e'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeByte(0xB2 + (type - 2) * 5)
                return index + 12
            if equals12(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 'v'.encode()[0], 'e'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeByte(0xB3 + (type - 2) * 5)
                return index + 12
            if equals12(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 'v'.encode()[0], 'e'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '6'.encode()[0], '4'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeByte(0xB4 + (type - 2) * 5)
                return index + 12
            if equals12(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 'v'.encode()[0], 'e'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '6'.encode()[0], '4'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeByte(0xB5 + (type - 2) * 5)
                return index + 12
            
    return index 

def parseWord(index: int) -> int:
    global LAST_BYTES_OUT
    global BYTES_OUT
    global CURRENT_SECTION
    if equals3(index, 'h'.encode()[0], 'e'.encode()[0], 'x'.encode()[0]):
        return writeFromHex(index + 3)
    if equals3(index, 'b'.encode()[0], 'i'.encode()[0], 'n'.encode()[0]):
        return writeFromBin(index + 3)
    if equals3(index, 's'.encode()[0], 't'.encode()[0], 'r'.encode()[0]):
        return writeFromString(index + 3)
    if equals3(index, 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0]):
        writeByte(0x7F)
        return index + 3
    if equals4(index, 'u'.encode()[0], 'l'.encode()[0], 'e'.encode()[0], 'b'.encode()[0]):
        return writeFromUleb(index + 4)
    if equals7(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0]):
        LAST_BYTES_OUT = BYTES_OUT
        return index + 7
    if equals11(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'E'.encode()[0], 'N'.encode()[0], 'D'.encode()[0]):
        writeSection(CURRENT_SECTION, BYTES_OUT - LAST_BYTES_OUT, LAST_BYTES_OUT)
        return index + 11
    if equals14(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'H'.encode()[0], 'E'.encode()[0], 'A'.encode()[0], 'D'.encode()[0], 'E'.encode()[0], 'R'.encode()[0]):
        write_char(0x00)
        write_char(0x61)
        write_char(0x73)
        write_char(0x6D)
        write_char(0x01)
        write_char(0x00)
        write_char(0x00)
        write_char(0x00)
        return index + 14
    if equals12(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'T'.encode()[0], 'Y'.encode()[0], 'P'.encode()[0], 'E'.encode()[0]):
        CURRENT_SECTION = 0x01
        return index + 12
    if equals14(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'I'.encode()[0], 'M'.encode()[0], 'P'.encode()[0], 'O'.encode()[0], 'R'.encode()[0], 'T'.encode()[0]):
        CURRENT_SECTION = 0x02
        return index + 14
    if equals16(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'F'.encode()[0], 'U'.encode()[0], 'N'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0]):
        CURRENT_SECTION = 0x03
        return index + 16
    if equals14(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'M'.encode()[0], 'E'.encode()[0], 'M'.encode()[0], 'O'.encode()[0], 'R'.encode()[0], 'Y'.encode()[0]):
        CURRENT_SECTION = 0x05
        return index + 14
    if equals14(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'G'.encode()[0], 'L'.encode()[0], 'O'.encode()[0], 'B'.encode()[0], 'A'.encode()[0], 'L'.encode()[0]):
        CURRENT_SECTION = 0x06
        return index + 14
    if equals14(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'E'.encode()[0], 'X'.encode()[0], 'P'.encode()[0], 'O'.encode()[0], 'R'.encode()[0], 'T'.encode()[0]):
        CURRENT_SECTION = 0x07
        return index + 14
    if equals12(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'C'.encode()[0], 'O'.encode()[0], 'D'.encode()[0], 'E'.encode()[0]):
        CURRENT_SECTION = 0x0A
        return index + 12
    if equals8(index, 'F'.encode()[0], 'U'.encode()[0], 'N'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0]):
        writeByte(0x60)
        return index + 8
    if equals13(index, 'F'.encode()[0], 'U'.encode()[0], 'N'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'K'.encode()[0], 'I'.encode()[0], 'N'.encode()[0], 'D'.encode()[0]):
        writeByte(0x00)
        return index + 13
    if isComment(index):
        return skipComment(index)
    if memory[index] == '#'.encode()[0]:
        return setVariable(index + 1)
    if memory[index] == '$'.encode()[0]:
        return getVariable(index + 1)
    if parseCmd(index):
        return index
    if memory[index] == 0:
        return -67

    error(0x04)

def main():
    index = 0
    while True:
        index = skipWhiteSpace(index)
        index = parseWord(index)

        if index >= len(memory) or index == -67:
            break

main()
