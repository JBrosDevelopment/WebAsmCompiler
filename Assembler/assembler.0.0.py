import os
import sys

script_dir = os.path.dirname(os.path.abspath(__file__))
input_file_name = sys.argv[1] if len(sys.argv) > 1 else "assembler.0.0.wal"
input_file_path = os.path.join(script_dir, input_file_name)

input_code = ""

with open(input_file_path, "r") as f:
    input_code = f.read()


def print_i32(value): # import
    print(value, end='')

def print_char(value): # import
    print(value, end='')

output_directory = os.path.join(os.path.dirname(__file__), "bin")
os.makedirs(output_directory, exist_ok=True)
output_file = open(os.path.join(output_directory, input_file_name + ".wasm"), "wb")

def write_char(char): # import
    output_file.write(bytearray([char]))

    length_of_number = len(str(char))
    string_of_number = str(char) + "," + " " * (4 - length_of_number)

    if char >= 32 and char <= 126:
        print("write: " + string_of_number + "'" + chr(char) + "'")
    else:
        print("write: " + string_of_number + "0x" + format(char, "02X"))

def exit_program(errCode): # import
    exit(errCode)

memory = list([0] * (len(input_code) + 17))

for i in range(len(input_code)):
    memory[i] = input_code[i].encode()[0]

sectionMemory = list([0] * max(1024 * 1024, len(input_code))) # global
functionMemory = list([0] * max(1024 * 1024, len(input_code))) # global

SECTION_BYTES_OUT = 0 # global
SECTION_LAST_BYTES_OUT = 0 # global
FUNCTION_BYTES_OUT = 0 # global
FUNCTION_LAST_BYTES_OUT = 0 # global
WRITING_TO_FUNCTION = 0 # global
LAST_SYMBOL_ID = 0 # global
CURRENT_SECTION: int = 0 # global

# All named things use the same two flat stacks.  Names are stored as
# ID, KIND, STR_LENGTH, STRING_BYTES.  Values are stored as ID, VALUE.
# KIND 0 is a normal variable; KIND 1 is a control-flow label.
SYMBOL_VARIABLE = 0
SYMBOL_LABEL = 1
symbol_names = list([0] * 1024 * 4) # global
symbol_names_stack_index: int = 0 # global
symbol_values = list([0] * 1024 * 4) # global
symbol_values_stack_index: int = 0 # global

LABEL_SCOPE = 0 # global
LABEL_FIRST_SYMBOL_ID = 0 # global; labels from earlier functions are invalid

def writeSectionChar(char: int) -> None:
    global SECTION_BYTES_OUT
    global FUNCTION_BYTES_OUT
    global WRITING_TO_FUNCTION
    if WRITING_TO_FUNCTION == 1:
        functionMemory[FUNCTION_BYTES_OUT] = char
        FUNCTION_BYTES_OUT = FUNCTION_BYTES_OUT + 1
    else:
        sectionMemory[SECTION_BYTES_OUT] = char
        SECTION_BYTES_OUT = SECTION_BYTES_OUT + 1 

def writeSection(writing_function: int, type: int, length: int, start: int) -> None:
    if writing_function == 0:
        write_char(type)

    section_length = length

    # write length as ULEB128
    byte = 0

    while length > 0:
        byte = length & 0x7F

        if length >= 128:
            byte |= 0x80

        if writing_function == 1:
            writeSectionChar(byte)
        else:
            write_char(byte)
        length = length >> 7

    # write section data
    index = start

    while index < start + section_length:
        if writing_function == 1:
            writeSectionChar(functionMemory[index])
        else:
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
        if number >= 128:
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
            val = char - '0'.encode()[0]
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
    global LAST_SYMBOL_ID
    global symbol_names_stack_index
    global symbol_values_stack_index

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
    symbol_names[symbol_names_stack_index] = LAST_SYMBOL_ID
    symbol_names_stack_index += 1

    symbol_names[symbol_names_stack_index] = SYMBOL_VARIABLE
    symbol_names_stack_index += 1

    symbol_names[symbol_names_stack_index] = variable_name_length
    symbol_names_stack_index += 1

    while loop_index < variable_name_length:
        symbol_names[symbol_names_stack_index] = memory[variable_name_start + loop_index]

        symbol_names_stack_index += 1
        loop_index += 1

    # Store variable value:
    symbol_values[symbol_values_stack_index] = LAST_SYMBOL_ID
    symbol_values_stack_index += 1

    symbol_values[symbol_values_stack_index] = result
    symbol_values_stack_index += 1

    LAST_SYMBOL_ID += 1

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

    # Search symbol names for a normal variable.
    while vname_pointer < symbol_names_stack_index:
        variable_id = symbol_names[vname_pointer]
        vname_pointer += 1

        symbol_kind = symbol_names[vname_pointer]
        vname_pointer += 1

        stored_name_length = symbol_names[vname_pointer]
        vname_pointer += 1

        matches = 1

        # Lengths must match first
        if stored_name_length != variable_name_length:
            matches = 0
        if symbol_kind != SYMBOL_VARIABLE:
            matches = 0

        # Compare characters
        loop_index = 0
        while loop_index < stored_name_length:

            if matches == 1:
                if memory[variable_name_start + loop_index] != symbol_names[vname_pointer + loop_index]:
                    matches = 0

            loop_index += 1

        if matches == 1:
            value_pointer = 0
            while value_pointer < symbol_values_stack_index:
                if symbol_values[value_pointer] == variable_id:
                    value = symbol_values[value_pointer + 1]

                    writeByte(value)
                    return index

                value_pointer += 2

        vname_pointer += stored_name_length

    error(0x03)

def setLabel(index: int) -> int:
    global LAST_SYMBOL_ID
    global symbol_names_stack_index
    global symbol_values_stack_index

    label_start = index
    label_length = 0
    loop_index = 0

    while not isWhiteSpace(index):
        label_length += 1
        index += 1

    if label_length == 0 or LABEL_SCOPE == 0:
        error(0x05)

    # Store label name: ID, kind, length, then each character byte.
    symbol_names[symbol_names_stack_index] = LAST_SYMBOL_ID
    symbol_names_stack_index += 1
    symbol_names[symbol_names_stack_index] = SYMBOL_LABEL
    symbol_names_stack_index += 1
    symbol_names[symbol_names_stack_index] = label_length
    symbol_names_stack_index += 1
    while loop_index < label_length:
        symbol_names[symbol_names_stack_index] = memory[label_start + loop_index]
        symbol_names_stack_index += 1
        loop_index += 1

    # Store label value: ID and the control-flow scope it refers to.
    symbol_values[symbol_values_stack_index] = LAST_SYMBOL_ID
    symbol_values_stack_index += 1
    symbol_values[symbol_values_stack_index] = LABEL_SCOPE
    symbol_values_stack_index += 1

    LAST_SYMBOL_ID += 1
    return index

def getLabel(index: int) -> int:
    label_start = index
    label_length = 0
    name_pointer = 0
    label_id = 0
    stored_length = 0
    matches = 0

    while True:
        label_length += 1
        index += 1
        if isWhiteSpace(index):
            break

    while name_pointer < symbol_names_stack_index:
        label_id = symbol_names[name_pointer]
        name_pointer += 1
        symbol_kind = symbol_names[name_pointer]
        name_pointer += 1
        stored_length = symbol_names[name_pointer]
        name_pointer += 1
        matches = 1

        if stored_length != label_length:
            matches = 0
        if symbol_kind != SYMBOL_LABEL:
            matches = 0
        if label_id < LABEL_FIRST_SYMBOL_ID:
            matches = 0

        loop_index = 0
        while loop_index < stored_length:
            if matches == 1:
                if memory[label_start + loop_index] != symbol_names[name_pointer + loop_index]:
                    matches = 0
            loop_index += 1

        if matches == 1:
            value_pointer = 0
            while value_pointer < symbol_values_stack_index:
                if symbol_values[value_pointer] == label_id:
                    label_scope = symbol_values[value_pointer + 1]
                    branch_depth = LABEL_SCOPE - label_scope
                    if branch_depth < 0:
                        error(0x06)
                    writeByte(branch_depth)
                    return index
                value_pointer += 2

        name_pointer += stored_length

    error(0x06)

def parseCmd(index: int) -> int:
    global LABEL_SCOPE
    i32_arithmatic = 0x6A
    i32_comparison = 0x45 + 1 # dont include eqz because f32 and f64 dont have it
    i64_arithmatic = 0x7C
    i64_comparison = 0x50 + 1 # same ^
    f32_arithmatic = 0x92
    f32_comparison = 0x5B
    f64_arithmatic = 0xA0
    f64_comparison = 0x61
    type_arithmatic = 0
    type_comparison = 0
    type = 10
    if memory[index] == 'i'.encode()[0] and memory[index + 1] == '3'.encode()[0] and memory[index + 2] == '2'.encode()[0] and memory[index + 3] == '.'.encode()[0]:
        type = 0x00
        type_arithmatic = i32_arithmatic
        type_comparison = i32_comparison
    if memory[index] == 'i'.encode()[0] and memory[index + 1] == '6'.encode()[0] and memory[index + 2] == '4'.encode()[0] and memory[index + 3] == '.'.encode()[0]:
        type = 0x01
        type_arithmatic = i64_arithmatic
        type_comparison = i64_comparison
    if memory[index] == 'f'.encode()[0] and memory[index + 1] == '3'.encode()[0] and memory[index + 2] == '2'.encode()[0] and memory[index + 3] == '.'.encode()[0]:
        type = 0x02
        type_arithmatic = f32_arithmatic
        type_comparison = f32_comparison
    if memory[index] == 'f'.encode()[0] and memory[index + 1] == '6'.encode()[0] and memory[index + 2] == '4'.encode()[0] and memory[index + 3] == '.'.encode()[0]:
        type = 0x03
        type_arithmatic = f64_arithmatic
        type_comparison = f64_comparison

    # control flow
    if equals5(index, 'b'.encode()[0], 'l'.encode()[0], 'o'.encode()[0], 'c'.encode()[0], 'k'.encode()[0]):
        writeSectionChar(0x02)
        LABEL_SCOPE += 1
        return index + 5
    if equals4(index, 'l'.encode()[0], 'o'.encode()[0], 'o'.encode()[0], 'p'.encode()[0]):
        writeSectionChar(0x03)
        LABEL_SCOPE += 1
        return index + 4
    if equals2(index, 'i'.encode()[0], 'f'.encode()[0]):
        writeSectionChar(0x04)
        LABEL_SCOPE += 1
        return index + 2
    if equals4(index, 'e'.encode()[0], 'l'.encode()[0], 's'.encode()[0], 'e'.encode()[0]):
        writeSectionChar(0x05)
        return index + 4
    if equals3(index, 'e'.encode()[0], 'n'.encode()[0], 'd'.encode()[0]):
        writeSectionChar(0x0B)
        if LABEL_SCOPE > 0:
            LABEL_SCOPE -= 1
        return index + 3
    if equals2(index, 'b'.encode()[0], 'r'.encode()[0]):
        writeSectionChar(0x0C)
        return index + 2
    if equals5(index, 'b'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 'i'.encode()[0], 'f'.encode()[0]):
        writeSectionChar(0x0D)
        return index + 5
    if equals6(index, 'r'.encode()[0], 'e'.encode()[0], 't'.encode()[0], 'u'.encode()[0], 'r'.encode()[0], 'n'.encode()[0]):
        writeSectionChar(0x0F)
        return index + 6
    # functions
    if equals4(index, 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], 'l'.encode()[0]):
        writeSectionChar(0x10)
        return index + 4
    if equals13(index, 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], 'l'.encode()[0], '_'.encode()[0], 'i'.encode()[0], 'n'.encode()[0], 'd'.encode()[0], 'i'.encode()[0], 'r'.encode()[0], 'e'.encode()[0], 'c'.encode()[0], 't'.encode()[0]):
        writeSectionChar(0x11)
        return index + 13
    # stack
    if equals4(index, 'd'.encode()[0], 'r'.encode()[0], 'o'.encode()[0], 'p'.encode()[0]):
        writeSectionChar(0x1A)
        return index + 4
    # locals
    if equals9(index, 'l'.encode()[0], 'o'.encode()[0], 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], '.'.encode()[0], 'g'.encode()[0], 'e'.encode()[0], 't'.encode()[0]):
        writeSectionChar(0x20)
        return index + 9
    if equals9(index, 'l'.encode()[0], 'o'.encode()[0], 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], '.'.encode()[0], 's'.encode()[0], 'e'.encode()[0], 't'.encode()[0]):
        writeSectionChar(0x21)
        return index + 9
    if equals9(index, 'l'.encode()[0], 'o'.encode()[0], 'c'.encode()[0], 'a'.encode()[0], 'l'.encode()[0], '.'.encode()[0], 't'.encode()[0], 'e'.encode()[0], 'e'.encode()[0]):
        writeSectionChar(0x22)
        return index + 9
    # type specific instructions
    if type != 10: 
        index += 4
        # constants
        if equals5(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 's'.encode()[0], 't'.encode()[0]):
            writeSectionChar(0x41 + type)
            return index + 5
        #arithmetic
        if equals3(index, 'a'.encode()[0], 'd'.encode()[0], 'd'.encode()[0]):
            writeSectionChar(type_arithmatic + 0)
            return index + 3
        if equals3(index, 's'.encode()[0], 'u'.encode()[0], 'b'.encode()[0]):
            writeSectionChar(type_arithmatic + 1)
            return index + 3
        if equals3(index, 'm'.encode()[0], 'u'.encode()[0], 'l'.encode()[0]):
            writeSectionChar(type_arithmatic + 2)
            return index + 3
        if equals5(index, 'd'.encode()[0], 'i'.encode()[0], 'v'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeSectionChar(type_arithmatic + 3)
            return index + 5
        if equals5(index, 'd'.encode()[0], 'i'.encode()[0], 'v'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeSectionChar(type_arithmatic + 4)
            return index + 5
        if equals5(index, 'r'.encode()[0], 'e'.encode()[0], 'm'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeSectionChar(type_arithmatic + 5)
            return index + 5
        if equals5(index, 'r'.encode()[0], 'e'.encode()[0], 'm'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeSectionChar(type_arithmatic + 6)
            return index + 5
        if equals3(index, 'a'.encode()[0], 'n'.encode()[0], 'd'.encode()[0]):
            writeSectionChar(type_arithmatic + 7)
            return index + 3
        if equals2(index, 'o'.encode()[0], 'r'.encode()[0]):
            writeSectionChar(type_arithmatic + 8)
            return index + 2
        if equals3(index, 'x'.encode()[0], 'o'.encode()[0], 'r'.encode()[0]):
            writeSectionChar(type_arithmatic + 9)
            return index + 3
        if equals3(index, 's'.encode()[0], 'h'.encode()[0], 'l'.encode()[0]):
            writeSectionChar(type_arithmatic + 10)
            return index + 3
        if equals5(index, 's'.encode()[0], 'h'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
            writeSectionChar(type_arithmatic + 11)
            return index + 5
        if equals5(index, 's'.encode()[0], 'h'.encode()[0], 'r'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
            writeSectionChar(type_arithmatic + 12)
            return index + 5
        if equals4(index, 'r'.encode()[0], 'o'.encode()[0], 't'.encode()[0], 'l'.encode()[0]):
            writeSectionChar(type_arithmatic + 13)
            return index + 4
        if equals4(index, 'r'.encode()[0], 'o'.encode()[0], 't'.encode()[0], 'r'.encode()[0]):
            writeSectionChar(type_arithmatic + 14)
            return index + 4
        # comparisons
        if (type == 0 or type == 1) and equals3(index, 'e'.encode()[0], 'q'.encode()[0], 'z'.encode()[0]):
            writeSectionChar(type_comparison - 1)
            return index + 3
        if equals2(index, 'e'.encode()[0], 'q'.encode()[0]):
            writeSectionChar(type_comparison + 0)
            return index + 2
        if equals2(index, 'n'.encode()[0], 'e'.encode()[0]):
            writeSectionChar(type_comparison + 1)
            return index + 2
        if type == 0 or type == 1:
            if equals4(index, 'l'.encode()[0], 't'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(type_comparison + 2)
                return index + 4
            if equals4(index, 'l'.encode()[0], 't'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(type_comparison + 3)
                return index + 4
            if equals4(index, 'g'.encode()[0], 't'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(type_comparison + 4)
                return index + 4
            if equals4(index, 'g'.encode()[0], 't'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(type_comparison + 5)
                return index + 4
            if equals4(index, 'l'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(type_comparison + 6)
                return index + 4
            if equals4(index, 'l'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(type_comparison + 7)
                return index + 4
            if equals4(index, 'g'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(type_comparison + 8)
                return index + 4
            if equals4(index, 'g'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(type_comparison + 9)
                return index + 4
        if type == 2 or type == 3:
            if equals2(index, 'l'.encode()[0], 't'.encode()[0]):
                writeSectionChar(type_comparison + 2)
                return index + 2
            if equals2(index, 'g'.encode()[0], 't'.encode()[0]):
                writeSectionChar(type_comparison + 3)
                return index + 2
            if equals2(index, 'l'.encode()[0], 'e'.encode()[0]):
                writeSectionChar(type_comparison + 4)
                return index + 2
            if equals2(index, 'g'.encode()[0], 'e'.encode()[0]):
                writeSectionChar(type_comparison + 5)
                return index + 2
        # memory loads
        if equals4(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0]):
            writeSectionChar(0x28 + type)
            return index + 4
        if type == 0 or type == 1:
            if equals7(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '8'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(0x2C + type*4)
                return index + 7
            if equals7(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '8'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(0x2D + type*4)
                return index + 7
            if equals8(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '1'.encode()[0], '6'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(0x2E + type*4)
                return index + 8
            if equals8(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '1'.encode()[0], '6'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(0x2F + type*4)
                return index + 8
        if type == 1:
            if equals8(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(0x34)
                return index + 8
            if equals8(index, 'l'.encode()[0], 'o'.encode()[0], 'a'.encode()[0], 'd'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(0x35)
                return index + 8
        # memory stores
        if equals5(index, 's'.encode()[0], 't'.encode()[0], 'o'.encode()[0], 'r'.encode()[0], 'e'.encode()[0]):
            writeSectionChar(0x36 + type)
            return index + 5
        if type == 0 or type == 1:
            if equals6(index, 's'.encode()[0], 't'.encode()[0], 'o'.encode()[0], 'r'.encode()[0], 'e'.encode()[0], '8'.encode()[0]):
                writeSectionChar(0x3A + type*2)
                return index + 6
            if equals7(index, 's'.encode()[0], 't'.encode()[0], 'o'.encode()[0], 'r'.encode()[0], 'e'.encode()[0], '1'.encode()[0], '6'.encode()[0]):
                writeSectionChar(0x3B + type*2)
                return index + 7
        if type == 1:
            if equals7(index, 's'.encode()[0], 't'.encode()[0], 'o'.encode()[0], 'r'.encode()[0], 'e'.encode()[0], '3'.encode()[0], '2'.encode()[0]):
                writeSectionChar(0x3E)
                return index + 7
        # conversions
        if type == 0:
            if equals8(index, 'w'.encode()[0], 'r'.encode()[0], 'a'.encode()[0], 'p'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '6'.encode()[0], '4'.encode()[0]):
                writeSectionChar(0xA7)
                return index + 8
        if type == 1:
            if equals12(index, 'e'.encode()[0], 'x'.encode()[0], 't'.encode()[0], 'e'.encode()[0], 'n'.encode()[0], 'd'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(0xAC)
                return index + 12
            if equals12(index, 'e'.encode()[0], 'x'.encode()[0], 't'.encode()[0], 'e'.encode()[0], 'n'.encode()[0], 'd'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(0xAD)
                return index + 12
        if type == 2:
            if equals10(index, 'd'.encode()[0], 'e'.encode()[0], 'm'.encode()[0], 'o'.encode()[0], 't'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '6'.encode()[0], '4'.encode()[0]):
                writeSectionChar(0xB6)
                return index + 10
        if type == 3:
            if equals11(index, 'p'.encode()[0], 'r'.encode()[0], 'o'.encode()[0], 'm'.encode()[0], 'o'.encode()[0], 't'.encode()[0], 'e'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '3'.encode()[0], '2'.encode()[0]):
                writeSectionChar(0xBB)
                return index + 11
        if type == 0 or type == 1:
            if equals11(index, 't'.encode()[0], 'r'.encode()[0], 'u'.encode()[0], 'n'.encode()[0], 'c'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(0xA8 + type * 6)
                return index + 11
            if equals11(index, 't'.encode()[0], 'r'.encode()[0], 'u'.encode()[0], 'n'.encode()[0], 'c'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(0xA9 + type * 6)
                return index + 11
            if equals11(index, 't'.encode()[0], 'r'.encode()[0], 'u'.encode()[0], 'n'.encode()[0], 'c'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '6'.encode()[0], '4'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(0xAA + type * 6)
                return index + 11
            if equals11(index, 't'.encode()[0], 'r'.encode()[0], 'u'.encode()[0], 'n'.encode()[0], 'c'.encode()[0], '_'.encode()[0], 'f'.encode()[0], '6'.encode()[0], '4'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(0xAB + type * 6)
                return index + 11
        if type == 2 or type == 3:
            if equals13(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 'v'.encode()[0], 'e'.encode()[0], 'r'.encode()[0], 't'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(0xB2 + (type - 2) * 5)
                return index + 13
            if equals13(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 'v'.encode()[0], 'e'.encode()[0], 'r'.encode()[0], 't'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(0xB3 + (type - 2) * 5)
                return index + 13
            if equals13(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 'v'.encode()[0], 'e'.encode()[0], 'r'.encode()[0], 't'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '6'.encode()[0], '4'.encode()[0], '_'.encode()[0], 's'.encode()[0]):
                writeSectionChar(0xB4 + (type - 2) * 5)
                return index + 13
            if equals13(index, 'c'.encode()[0], 'o'.encode()[0], 'n'.encode()[0], 'v'.encode()[0], 'e'.encode()[0], 'r'.encode()[0], 't'.encode()[0], '_'.encode()[0], 'i'.encode()[0], '6'.encode()[0], '4'.encode()[0], '_'.encode()[0], 'u'.encode()[0]):
                writeSectionChar(0xB5 + (type - 2) * 5)
                return index + 13
            
    return index 

def parseWord(index: int) -> int:
    global SECTION_LAST_BYTES_OUT
    global SECTION_BYTES_OUT
    global FUNCTION_LAST_BYTES_OUT
    global FUNCTION_BYTES_OUT
    global CURRENT_SECTION
    global WRITING_TO_FUNCTION
    global LABEL_SCOPE
    global LABEL_FIRST_SYMBOL_ID
    if equals3(index, 'h'.encode()[0], 'e'.encode()[0], 'x'.encode()[0]):
        return writeFromHex(index + 3)
    if equals3(index, 'b'.encode()[0], 'i'.encode()[0], 'n'.encode()[0]):
        return writeFromBin(index + 3)
    if equals3(index, 's'.encode()[0], 't'.encode()[0], 'r'.encode()[0]):
        return writeFromString(index + 3)
    if equals3(index, 'i'.encode()[0], '3'.encode()[0], '2'.encode()[0]):
        writeSectionChar(0x7F)
        return index + 3
    if equals4(index, 'u'.encode()[0], 'l'.encode()[0], 'e'.encode()[0], 'b'.encode()[0]):
        return writeFromUleb(index + 4)
    if equals7(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0]):
        SECTION_LAST_BYTES_OUT = SECTION_BYTES_OUT
        return index + 7
    if equals11(index, 'S'.encode()[0], 'E'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'E'.encode()[0], 'N'.encode()[0], 'D'.encode()[0]):
        writeSection(WRITING_TO_FUNCTION, CURRENT_SECTION, SECTION_BYTES_OUT - SECTION_LAST_BYTES_OUT, SECTION_LAST_BYTES_OUT)
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
        writeSectionChar(0x60)
        return index + 8
    if equals13(index, 'F'.encode()[0], 'U'.encode()[0], 'N'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'K'.encode()[0], 'I'.encode()[0], 'N'.encode()[0], 'D'.encode()[0]):
        writeSectionChar(0x00)
        return index + 13
    if equals14(index, 'F'.encode()[0], 'U'.encode()[0], 'N'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'S'.encode()[0], 'T'.encode()[0], 'A'.encode()[0], 'R'.encode()[0], 'T'.encode()[0]):
        FUNCTION_LAST_BYTES_OUT = FUNCTION_BYTES_OUT
        WRITING_TO_FUNCTION = 1
        LABEL_SCOPE = 0
        LABEL_FIRST_SYMBOL_ID = LAST_SYMBOL_ID
        return index + 14
    if equals12(index, 'F'.encode()[0], 'U'.encode()[0], 'N'.encode()[0], 'C'.encode()[0], 'T'.encode()[0], 'I'.encode()[0], 'O'.encode()[0], 'N'.encode()[0], '_'.encode()[0], 'E'.encode()[0], 'N'.encode()[0], 'D'.encode()[0]):
        WRITING_TO_FUNCTION = 0
        writeSection(1, 0, FUNCTION_BYTES_OUT - FUNCTION_LAST_BYTES_OUT, FUNCTION_LAST_BYTES_OUT)
        LABEL_SCOPE = 0
        return index + 12
    if equals9(index, 'N'.encode()[0], 'O'.encode()[0], '_'.encode()[0], 'R'.encode()[0], 'E'.encode()[0], 'T'.encode()[0], 'U'.encode()[0], 'R'.encode()[0], 'N'.encode()[0]):
        writeSectionChar(0x40)
        return index + 9
    if isComment(index):
        return skipComment(index)
    if memory[index] == '#'.encode()[0]:
        return setVariable(index + 1)
    if memory[index] == '$'.encode()[0]:
        return getVariable(index + 1)
    if memory[index] == '@'.encode()[0]:
        return setLabel(index + 1)
    if memory[index] == '^'.encode()[0]:
        return getLabel(index + 1)
    if memory[index] == 0:
        return -67
    
    parse_index = parseCmd(index)
    
    if parse_index != index:
        return parse_index

    error(0x04)

def main():
    index = 0
    while True:
        index = skipWhiteSpace(index)
        index = parseWord(index)

        if index >= len(memory) or index == -67:
            break

main()
output_file.close()
