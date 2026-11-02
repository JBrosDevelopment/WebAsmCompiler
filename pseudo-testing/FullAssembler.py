import sys
from pathlib import Path

# soon to add opcode: sqrt
# soon to add syntax:
# new import syntax
#   define_import FUNCTION_KIND $t_f64__void env print_result   -   defines as well: #f_print_result 5
# new type syntax
#   define_type FUNCTION f64 f64 -> f64                         -   defines as well: #t_f64_f64__f64 5 
# new function syntax
#   define_function $t_f64_f64__f64 pythagorean                 -   defines as well: #f_pythagorean 6
# new export syntax
#   define_export FUNCTION_KIND $f_main main
# new memory syntax
#   define_memory 0 97
#   define_import MEMORY_KIND 0 env memory
# new data syntax
#   define_data active $destination STRING "Hello World!"
#   define_data active $destination DATA str Hello hex 20 str World!
# code syntax
#   define_code f64 a f64 b ; pythagorean(a, b)
#   LOCALS f64 c
#   define_code_end

# Capacities, 4 MiB
INPUT_LIMIT = 4 * 1024 * 1024 # global
OUTPUT_LIMIT = 4 * 1024 * 1024 # global
EOF_PADDING = 17 # global

memory = [] # global memory
output_buffer = [] # global output buffer

sectionMemory = list([0] * 1024 * 1024) # global
functionMemory = list([0] * 1024 * 1024) # global

output_path = "" # global
input_name = "" # global

# imported WASI function, did not use nread_ptr, but WAL version would write the number of bytes read to memory at that address.
# WASI will implement this function in the WAL version.
def fd_read(fd, iovs_ptr, iovs_len, nread_ptr):
    iovs_ptr.extend(fd.read(iovs_len))
    return 0

# imported WASI function, did not use nwritten_ptr, but WAL version would write the number of bytes written to memory at that address.
# WASI will implement this function in the WAL version. 
def fd_write(fd, iovs_ptr, iovs_len, nwritten_ptr): 
    if fd == 2:
        fd = sys.stderr.buffer
    written = fd.write(bytes(iovs_ptr[:iovs_len]))
    if written != iovs_len:
        exit_program(1)
    return 0

# imported WASI function
def proc_exit(status):
    sys.exit(status)

SECTION_BYTES_OUT = 0 # global
SECTION_LAST_BYTES_OUT = 0 # global
FUNCTION_BYTES_OUT = 0 # global
FUNCTION_LAST_BYTES_OUT = 0 # global
WRITING_TO_FUNCTION = 0 # global
LAST_SYMBOL_ID = 0 # global
CURRENT_SECTION: int = 0 # global
COUNT: int = 0 # global

# All named things use the same two flat stacks. 
# Names are stored as ID, KIND, STR_LENGTH, STRING_BYTES.
# Values are stored as ID, VALUE.
# KIND 0 is a normal variable, KIND 1 is a control-flow label.
SYMBOL_VARIABLE = 0
SYMBOL_LABEL = 1
symbol_names = list([0] * 1024 * 4) # global
symbol_names_stack_index: int = 0 # global
symbol_values = list([0] * 1024 * 4) # global
symbol_values_stack_index: int = 0 # global

LABEL_SCOPE = 0 # global
LABEL_FIRST_SYMBOL_ID = 0 # global; labels from earlier functions are invalid

# Tracing
CURRENT_LINE = 1 # global

# Strings
s_ei_start = "Error `\0"
s_ei_end = "`: \0"
s_vdne_start = "Variable `\0"
s_vdne_end = "` does not exist.\n\0"
s_ihc_start = "Invalid hex character `\0"
s_ihc_end = "`, valid characters (0-9 and A-F).\n\0"
s_ibc_start = "Invalid binary character `\0"
s_ibc_end = "`, valid characters (0 and 1).\n\0"
s_iuc_start = "Invalid uleb character `\0"
s_iuc_end = "`, valid characters (0-9).\n\0"
s_iac_start = "Invalid ascii character `\0"
s_iac_end = "`, Expected a single character with ascii value within 1-127.\n\0"
s_ise_start = "Invalid SLEB 128 encoding `\0"
s_ise_end = "`, valid characters are (0-9 and '-') and expected atleast 1 digit after '-'.\n\0"
s_ifpn_start = "Invalid Floating-Point number `\0"
s_ifpn_end = "`, valid characters are (0-9, '-', and '.'), expects atleast 1 digit after sign if present, and number must not exceed exponent limit (i.e. 1.7976931348623157e+308).\n\0"
s_sizilc_start = "Scope is zero invalid label call `\0"
s_sizilc_end = "`.\n\0"
s_ik_start = "Invalid keyword `\0"
s_ik_end = "`.\n\0"
s_ldne_start = "Label `\0"
s_ldne_end = "` does not exist.\n\0"
s_ecind_start = "Error Code `\0"
s_ecind_end = "` is not defined.\n\0"
s_eool_start = "Error occurred on line `\0"
s_eool_end = "`.\n\0"
s_ois_start = "Occurred in Section `\0"
s_ois_end = "`.\n\0"
s_ois_TYPE = "TYPE\0"
s_ois_IMPORT = "IMPORT\0"
s_ois_FUNCTION = "FUNCTION\0"
s_ois_MEMORY = "MEMORY\0"
s_ois_EXPORT = "EXPORT\0"
s_ois_CODE = "CODE\0"
s_ois_DATA = "DATA\0"
s_pf = "Program Fault.\0"

# runtime error strings
s_output_limit = "Generated binary exceeds the output buffer capacity\0"
s_cli_arguments = "Expected two arguments: python FullAssembler.py input.wal output.wasm\0"
s_input_file = "Input file does not exist or is not a regular file\0"
s_same_input_output = "Input and output must be different files\0"
s_input_limit = "Source exceeds the input region capacity\0"
s_non_ascii_source = "Source must contain only ASCII bytes\0"
s_nul_source = "Source must not contain embedded NUL bytes\0"
s_eof_padding = "Source leaves insufficient room for EOF padding\0"
s_output_directory = "Output directory does not exist\0"
s_output_file = "Output path is not a regular file\0"
s_function_capacity = "Function scratch buffer capacity exceeded\0"
s_section_capacity = "Section scratch buffer capacity exceeded\0"
s_symbol_names_capacity = "Symbol-name buffer capacity exceeded\0"
s_symbol_values_capacity = "Symbol-value buffer capacity exceeded\0"

def print_i32(value):
    value = value & 0xFFFFFFFF
    negative = value >= 0x80000000
    if negative:
        value = 0x100000000 - value
    digits = bytearray()
    while True:
        digits.append(48 + value % 10)
        value //= 10
        if value == 0:
            break
    if negative:
        digits.append(45)
    digits.reverse()
    fd_write(2, digits, len(digits), 0)

def print_char(value):
    fd_write(2, bytes([value & 255]), 1, 0) # bytes([value & 255]) just means an array of one byte with the value of value & 255 

def print_string(value: str):
    # Python strings stand in for WAL pointers to zero-terminated strings.
    data = value.split("\0", 1)[0].encode("utf-8")
    fd_write(2, data, len(data), 0)

def write_char(char: int):
    if len(output_buffer) >= OUTPUT_LIMIT:
        runtime_error(s_output_limit)
    output_buffer.append(char)

def exit_program(status):
    proc_exit(status)

def runtime_error(message: str):
    print_string("Assembler: ")
    print_string(message)
    print_char(10)
    exit_program(1)

def handle_cli_input():
    global output_path, input_name, memory

    if len(sys.argv) != 3:
        # The `python` command will not be in the WAL version, this is for the Python Pseudo-Testing version.
        runtime_error(s_cli_arguments)

    input_name = sys.argv[1]
    source_path = Path(input_name)
    output_path = Path(sys.argv[2])

    # validate the input and output paths
    if not source_path.is_file():
        runtime_error(s_input_file)
    if (source_path.resolve() == output_path.resolve() or (output_path.exists() and source_path.samefile(output_path))):
        runtime_error(s_same_input_output)

    # Read the source bytes into source, up to the input limit plus one extra byte to detect overflow.
    source = bytearray()
    with source_path.open("rb") as source_file:
        fd_read(source_file, source, INPUT_LIMIT + 1, 0)

    source_length = len(source) # in wasi, the nread_ptr would be used to get source byte count, but to simplify fd_read, len(source) is used

    if source_length > INPUT_LIMIT:
        runtime_error(s_input_limit)

    # Validate the source bytes.
    index = 0
    while index < source_length:
        character = source[index]
        if character > 127:
            runtime_error(s_non_ascii_source)
        if character == 0:
            runtime_error(s_nul_source)
        index += 1

    # Normalize line endings in place - The write position never moves ahead of the read position.
    # This is for CRLF normalization for end of line: `\n`, `\r\n`, `\r` -> `\n`
    read_index = 0
    write_index = 0
    while read_index < source_length:
        character = source[read_index]
        read_index += 1
        if character == 13:  # CR
            character = 10  # Replace with LF.
            # Consume the LF following CR, if present.
            if read_index < source_length:
                if source[read_index] == 10:
                    read_index += 1

        source[write_index] = character
        write_index += 1

    source_length = write_index

    # Determine whether a trailing newline is needed.
    needs_newline = 1
    if source_length > 0:
        if source[source_length - 1] == 10:
            needs_newline = 0

    # Reserve space for the newline and EOF padding before writing them.
    if source_length + needs_newline + EOF_PADDING > INPUT_LIMIT:
        runtime_error(s_eof_padding)

    # Allocate destination memory with room for the optional newline and padding.
    memory = [0] * (source_length + needs_newline + EOF_PADDING)

    # Copy only the normalized source bytes.
    index = 0
    while index < source_length:
        memory[index] = source[index]
        index += 1

    if needs_newline == 1:
        memory[source_length] = 10
        source_length += 1

    # EOF padding is already zero from allocation.
    output_buffer.clear()

def handle_cli_output():
    if not output_path.parent.is_dir():
        runtime_error(s_output_directory)
    if output_path.exists() and not output_path.is_file():
        runtime_error(s_output_file)
    with output_path.open("wb") as output_file:
        fd_write(output_file, output_buffer, len(output_buffer), 0)

def writeSectionChar(char: int) -> None:
    global SECTION_BYTES_OUT
    global FUNCTION_BYTES_OUT
    global WRITING_TO_FUNCTION
    if WRITING_TO_FUNCTION == 1:
        if FUNCTION_BYTES_OUT >= len(functionMemory):
            runtime_error(s_function_capacity)
        functionMemory[FUNCTION_BYTES_OUT] = char
        FUNCTION_BYTES_OUT = FUNCTION_BYTES_OUT + 1
    else:
        if SECTION_BYTES_OUT >= len(sectionMemory):
            runtime_error(s_section_capacity)
        sectionMemory[SECTION_BYTES_OUT] = char
        SECTION_BYTES_OUT = SECTION_BYTES_OUT + 1 

def writeSection(writing_function: int, type: int, length: int, start: int) -> None:
    section_length = length
    count = COUNT
    
    if writing_function == 0:
        write_char(type)
        remaining_count = count
        while remaining_count > 0:
            length += 1
            remaining_count >>= 7

    # write length and count as ULEB128
    length_byte = 0

    while length > 0:
        length_byte = length & 0x7F

        if length >= 128:
            length_byte |= 0x80

        if writing_function == 1:
            writeSectionChar(length_byte)
        else:
            write_char(length_byte)
        length = length >> 7

    count_byte = 0

    while count > 0 and writing_function == 0: # if COUNT == 0, don't write, so count > 0 is fine
        count_byte = count & 0x7F

        if count >= 128:
            count_byte |= 0x80

        write_char(count_byte)
        count = count >> 7

    # write section data
    index = start

    while index < start + section_length:
        if writing_function == 1:
            writeSectionChar(functionMemory[index])
        else:
            write_char(sectionMemory[index])
        index += 1

def isWhiteSpace(index: int) -> int:
    return memory[index] == ord(' ') or memory[index] == ord('\t') or memory[index] == ord('\n')

def skipWhiteSpace(index: int) -> int:
    global CURRENT_LINE
    while True:
        if memory[index] == ord('\n'):
            CURRENT_LINE = CURRENT_LINE + 1
        if not isWhiteSpace(index):
            break
        index = index + 1
    return index

def isComment(index: int) -> int:
    return memory[index] == ord(';')

def skipComment(index: int) -> int:
    while True:
        if memory[index] == ord('\n'):
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

def error(index, value):
    print_string(s_ei_start)
    print_i32(value)
    print_string(s_ei_end)
    index_pointer = index
    if value == 0x01:
        print_string(s_ihc_start)
        print_char(memory[index_pointer])
        print_string(s_ihc_end)
    if value == 0x02:
        print_string(s_ibc_start)
        print_char(memory[index_pointer])
        print_string(s_ibc_end)
    if value == 0x03:
        print_string(s_vdne_start)
        while not isWhiteSpace(index_pointer):
            print_char(memory[index_pointer])
            index_pointer += 1
        print_string(s_vdne_end)
    if value == 0x04:
        print_string(s_ik_start)
        while not isWhiteSpace(index_pointer):
            print_char(memory[index_pointer])
            index_pointer += 1
        print_string(s_ik_end)
    if value == 0x05:
        print_string(s_ldne_start)
        while not isWhiteSpace(index_pointer):
            print_char(memory[index_pointer])
            index_pointer += 1
        print_string(s_ldne_end)
    if value == 0x06:
        print_string(s_sizilc_start)
        while not isWhiteSpace(index_pointer):
            print_char(memory[index_pointer])
            index_pointer += 1
        print_string(s_sizilc_end)
    if value == 0x07:
        print_string(s_iac_start)
        while not isWhiteSpace(index_pointer):
            print_char(memory[index_pointer])
            index_pointer += 1
        print_string(s_iac_end)
    if value == 0x08:
        print_string(s_ise_start)
        print_char(memory[index_pointer])
        print_string(s_ise_end)
    if value == 0x09:
        print_string(s_iuc_start)
        print_char(memory[index_pointer])
        print_string(s_iuc_end)
    if value == 0x0A:
        print_string(s_ifpn_start)
        print_char(memory[index_pointer])
        print_string(s_ifpn_end)
    if value > 0x0A or value < 0x01:
        print_i32(value)
        print_string(s_ecind_end)

    print_string(s_ois_start)
    if CURRENT_SECTION == 0x01:
        print_string(s_ois_TYPE)
    if CURRENT_SECTION == 0x02:
        print_string(s_ois_IMPORT)
    if CURRENT_SECTION == 0x03:
        print_string(s_ois_FUNCTION)
    if CURRENT_SECTION == 0x05:
        print_string(s_ois_MEMORY)
    if CURRENT_SECTION == 0x07:
        print_string(s_ois_EXPORT)
    if CURRENT_SECTION == 0x0A:
        print_string(s_ois_CODE)
    if CURRENT_SECTION == 0x0B:
        print_string(s_ois_DATA)
    print_string("` of file `")
    print_string(input_name)
    print_string("`.\n")
        
    print_string(s_eool_start)
    print_i32(CURRENT_LINE)
    print_string(s_eool_end)

    index_pointer = index
    while index_pointer > 0 and memory[index_pointer - 1] != ord('\n'):
        index_pointer -= 1
    start_of_line = index_pointer
    
    print_char(ord('\n'))
    while memory[index_pointer] != ord('\n'):
        print_char(memory[index_pointer])
        index_pointer += 1
    print_char(ord('\n'))
    while start_of_line < index:
        print_char(ord(' '))
        start_of_line += 1
    while not isWhiteSpace(start_of_line):
        print_char(ord('~'))
        start_of_line += 1
    print_char(ord('\n'))
    print_char(ord('\n'))

    print_string(s_pf)
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

def writeSignedByte(number: int):
    while True:
        byte = number & 0x7F
        number >>= 7

        finished = (
            (number == 0 and (byte & 0x40) == 0) or
            (number == -1 and (byte & 0x40) != 0)
        )

        if not finished:
            byte |= 0x80

        writeSectionChar(byte)

        if finished:
            return

def writeFromHex(index: int) -> int:
    index = skipWhiteSpace(index)
    result = 0
    val = 0
    char = 0
    
    while True:
        char = memory[index]

        if char >= ord('0') and char <= ord('9'):
            val = char - ord('0')
        elif char >= ord('A') and char <= ord('F'):
            val = char - ord('A') + 10
        elif char >= ord('a') and char <= ord('f'):
            val = char - ord('a') + 10
        else:
            error(index, 0x01)
        
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

        if char == ord('0') or char == ord('1'):
            val = char - ord('0')
        else:
            error(index, 0x02)
        
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
        
        if memory[index] < ord('0') or memory[index] > ord('9'):
            error(index, 0x09)

        digit = memory[index] - ord('0')
        result = result * 10 + digit

        index += 1
        if isWhiteSpace(index):
            break

    writeByte(result)
    return index

def writeFromSleb(index: int) -> int:
    index = skipWhiteSpace(index)
    number_start = index
    negative = 0
    number = 0

    if memory[index] == ord('-'):
        negative = 1
        index += 1

    if memory[index] < ord('0') or memory[index] > ord('9'):
        error(number_start, 0x08)

    while memory[index] != 0 and not isWhiteSpace(index):
        char = memory[index]

        if char < ord('0') or char > ord('9'):
            error(index, 0x08)

        number = number * 10 + char - ord('0')
        index += 1

    if negative:
        number = -number

    if number < -2147483648 or number > 2147483647:
        error(number_start, 0x04)

    writeSignedByte(number)
    return index

def writeFromAscii(index: int) -> int:
    index = skipWhiteSpace(index)
    char = memory[index]

    if char > 127:
        error(index, 0x07)

    if memory[index + 1] != 0 and not isWhiteSpace(index + 1):
        error(index, 0x07)

    if char >= 64:
        writeSectionChar(char | 0x80)
        writeSectionChar(0)
    else:
        writeSectionChar(char)

    return index + 1

def writeFromFloat32(index: int) -> int:
    return writeFromFloat(index, 23, 8, 127)

def writeFromFloat64(index: int) -> int:
    return writeFromFloat(index, 52, 11, 1023)

def writeFromFloat(index: int, fraction_bits: int, exponent_bits: int, bias: int) -> int:
    index = skipWhiteSpace(index)
    number_start = index

    negative = 0
    decimal_seen = 0
    digit_count = 0

    number = 0.0
    scale = 1.0

    if memory[index] == 45:
        negative = 1
        index += 1

    while memory[index] != 0 and not isWhiteSpace(index):
        char = memory[index]

        if char == 46:
            if decimal_seen:
                error(index, 0x0A)

            decimal_seen = 1

        else:
            if char < 48 or char > 57:
                error(index, 0x0A)

            number = number * 10.0 + (char - 48)
            digit_count += 1

            if decimal_seen:
                scale *= 10.0

            if number > 1.7976931348623157e308:
                error(number_start, 0x0A)

            if scale > 1.7976931348623157e308:
                error(number_start, 0x0A)

        index += 1

    if digit_count == 0:
        error(number_start, 0x0A)

    number = number / scale

    writeFloatBits(number, negative, fraction_bits, exponent_bits, bias, number_start)
    return index

def writeFloatBits(number: float, negative: int, fraction_bits: int, exponent_bits: int, bias: int, number_start: int):
    exponent = 0
    encoded_exponent = 0
    fraction = 0
    exponent_limit = (1 << exponent_bits) - 1

    if number != 0.0:
        while number >= 2.0: # Normalize towards 1 <= number < 2.
            number /= 2.0
            exponent += 1

        while number < 1.0 and exponent > 1 - bias: # Stop at the smallest normal exponent.
            number *= 2.0
            exponent -= 1

        if number < 1.0: # Subnormal: no implicit leading 1.
            encoded_exponent = 0
        else:
            encoded_exponent = exponent + bias
            number -= 1.0

        if encoded_exponent >= exponent_limit:
            error(number_start, 0x0A)

        # Extract the fraction one binary digit at a time.
        bit_index = 0

        while bit_index < fraction_bits:
            number *= 2.0
            fraction <<= 1

            if number >= 1.0:
                fraction |= 1
                number -= 1.0

            bit_index += 1

        # Round to nearest, resolving exact ties towards even.
        if number > 0.5 or (
            number == 0.5 and (fraction & 1) != 0
        ):
            fraction += 1

        # Rounding can carry into the exponent.
        if fraction == (1 << fraction_bits):
            fraction = 0
            encoded_exponent += 1

        if encoded_exponent >= exponent_limit:
            error(number_start, 0x0A)

    bits = (negative << (fraction_bits + exponent_bits)) | (encoded_exponent << fraction_bits) | fraction

    byte_count = (1 + exponent_bits + fraction_bits) // 8
    byte_index = 0

    # Least-significant byte first: little endian.
    while byte_index < byte_count:
        writeSectionChar(bits & 0xFF)
        bits >>= 8
        byte_index += 1

def check_symbol_capacity(name_length: int):
    if symbol_names_stack_index + 3 + name_length > len(symbol_names):
        runtime_error(s_symbol_names_capacity)
    if symbol_values_stack_index + 2 > len(symbol_values):
        runtime_error(s_symbol_values_capacity)


def setVariable(index: int) -> int:
    global LAST_SYMBOL_ID
    global symbol_names_stack_index
    global symbol_values_stack_index

    variable_name_start = index
    variable_name_length = 0
    loop_index = 0
    result = 0

    while memory[index + variable_name_length] != 0 and not isWhiteSpace(index + variable_name_length):
        variable_name_length += 1
    index += variable_name_length

    index = skipWhiteSpace(index) # move past whitespace to digit

    # Get value
    while True:
        digit = memory[index] - ord('0')
        result = result * 10 + digit
        index += 1

        if isWhiteSpace(index):
            break

    check_symbol_capacity(variable_name_length)

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

    while memory[index + variable_name_length] != 0 and not isWhiteSpace(index + variable_name_length):
        variable_name_length += 1
    index += variable_name_length

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

    error(variable_name_start, 0x03)

def setLabel(index: int) -> int:
    global LAST_SYMBOL_ID
    global symbol_names_stack_index
    global symbol_values_stack_index

    label_start = index
    label_length = 0
    loop_index = 0

    while memory[index + label_length] != 0 and not isWhiteSpace(index + label_length):
        label_length += 1
    index += label_length

    if label_length == 0 or LABEL_SCOPE == 0:
        error(label_start, 0x05)

    check_symbol_capacity(label_length)

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

    while memory[index + label_length] != 0 and not isWhiteSpace(index + label_length):
        label_length += 1
    index += label_length

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
                        error(label_start, 0x06)
                    writeByte(branch_depth)
                    return index
                value_pointer += 2

        name_pointer += stored_length

    error(label_start, 0x05)

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
    if memory[index] == ord('i') and memory[index + 1] == ord('3') and memory[index + 2] == ord('2') and memory[index + 3] == ord('.'):
        type = 0x00
        type_arithmatic = i32_arithmatic
        type_comparison = i32_comparison
    if memory[index] == ord('i') and memory[index + 1] == ord('6') and memory[index + 2] == ord('4') and memory[index + 3] == ord('.'):
        type = 0x01
        type_arithmatic = i64_arithmatic
        type_comparison = i64_comparison
    if memory[index] == ord('f') and memory[index + 1] == ord('3') and memory[index + 2] == ord('2') and memory[index + 3] == ord('.'):
        type = 0x02
        type_arithmatic = f32_arithmatic
        type_comparison = f32_comparison
    if memory[index] == ord('f') and memory[index + 1] == ord('6') and memory[index + 2] == ord('4') and memory[index + 3] == ord('.'):
        type = 0x03
        type_arithmatic = f64_arithmatic
        type_comparison = f64_comparison

    # control flow
    if equals5(index, ord('b'), ord('l'), ord('o'), ord('c'), ord('k')):
        writeSectionChar(0x02)
        LABEL_SCOPE += 1
        return index + 5
    if equals4(index, ord('l'), ord('o'), ord('o'), ord('p')):
        writeSectionChar(0x03)
        LABEL_SCOPE += 1
        return index + 4
    if equals2(index, ord('i'), ord('f')):
        writeSectionChar(0x04)
        LABEL_SCOPE += 1
        return index + 2
    if equals4(index, ord('e'), ord('l'), ord('s'), ord('e')):
        writeSectionChar(0x05)
        return index + 4
    if equals3(index, ord('e'), ord('n'), ord('d')):
        writeSectionChar(0x0B)
        if LABEL_SCOPE > 0:
            LABEL_SCOPE -= 1
        return index + 3
    if equals2(index, ord('b'), ord('r')):
        writeSectionChar(0x0C)
        return index + 2
    if equals5(index, ord('b'), ord('r'), ord('_'), ord('i'), ord('f')):
        writeSectionChar(0x0D)
        return index + 5
    if equals6(index, ord('r'), ord('e'), ord('t'), ord('u'), ord('r'), ord('n')):
        writeSectionChar(0x0F)
        return index + 6
    # functions
    if equals4(index, ord('c'), ord('a'), ord('l'), ord('l')):
        writeSectionChar(0x10)
        return index + 4
    if equals13(index, ord('c'), ord('a'), ord('l'), ord('l'), ord('_'), ord('i'), ord('n'), ord('d'), ord('i'), ord('r'), ord('e'), ord('c'), ord('t')):
        writeSectionChar(0x11)
        return index + 13
    # stack
    if equals4(index, ord('d'), ord('r'), ord('o'), ord('p')):
        writeSectionChar(0x1A)
        return index + 4
    # locals
    if equals9(index, ord('l'), ord('o'), ord('c'), ord('a'), ord('l'), ord('.'), ord('g'), ord('e'), ord('t')):
        writeSectionChar(0x20)
        return index + 9
    if equals9(index, ord('l'), ord('o'), ord('c'), ord('a'), ord('l'), ord('.'), ord('s'), ord('e'), ord('t')):
        writeSectionChar(0x21)
        return index + 9
    if equals9(index, ord('l'), ord('o'), ord('c'), ord('a'), ord('l'), ord('.'), ord('t'), ord('e'), ord('e')):
        writeSectionChar(0x22)
        return index + 9
    # type specific instructions
    if type != 10: 
        index += 4
        # constants
        if equals5(index, ord('c'), ord('o'), ord('n'), ord('s'), ord('t')):
            writeSectionChar(0x41 + type)
            return index + 5
        #arithmetic
        if equals3(index, ord('a'), ord('d'), ord('d')):
            writeSectionChar(type_arithmatic + 0)
            return index + 3
        if equals3(index, ord('s'), ord('u'), ord('b')):
            writeSectionChar(type_arithmatic + 1)
            return index + 3
        if equals3(index, ord('m'), ord('u'), ord('l')):
            writeSectionChar(type_arithmatic + 2)
            return index + 3
        if equals5(index, ord('d'), ord('i'), ord('v'), ord('_'), ord('s')):
            writeSectionChar(type_arithmatic + 3)
            return index + 5
        if equals5(index, ord('d'), ord('i'), ord('v'), ord('_'), ord('u')):
            writeSectionChar(type_arithmatic + 4)
            return index + 5
        if equals5(index, ord('r'), ord('e'), ord('m'), ord('_'), ord('s')):
            writeSectionChar(type_arithmatic + 5)
            return index + 5
        if equals5(index, ord('r'), ord('e'), ord('m'), ord('_'), ord('u')):
            writeSectionChar(type_arithmatic + 6)
            return index + 5
        if equals3(index, ord('a'), ord('n'), ord('d')):
            writeSectionChar(type_arithmatic + 7)
            return index + 3
        if equals2(index, ord('o'), ord('r')):
            writeSectionChar(type_arithmatic + 8)
            return index + 2
        if equals3(index, ord('x'), ord('o'), ord('r')):
            writeSectionChar(type_arithmatic + 9)
            return index + 3
        if equals3(index, ord('s'), ord('h'), ord('l')):
            writeSectionChar(type_arithmatic + 10)
            return index + 3
        if equals5(index, ord('s'), ord('h'), ord('r'), ord('_'), ord('s')):
            writeSectionChar(type_arithmatic + 11)
            return index + 5
        if equals5(index, ord('s'), ord('h'), ord('r'), ord('_'), ord('u')):
            writeSectionChar(type_arithmatic + 12)
            return index + 5
        if equals4(index, ord('r'), ord('o'), ord('t'), ord('l')):
            writeSectionChar(type_arithmatic + 13)
            return index + 4
        if equals4(index, ord('r'), ord('o'), ord('t'), ord('r')):
            writeSectionChar(type_arithmatic + 14)
            return index + 4
        # comparisons
        if (type == 0 or type == 1) and equals3(index, ord('e'), ord('q'), ord('z')):
            writeSectionChar(type_comparison - 1)
            return index + 3
        if equals2(index, ord('e'), ord('q')):
            writeSectionChar(type_comparison + 0)
            return index + 2
        if equals2(index, ord('n'), ord('e')):
            writeSectionChar(type_comparison + 1)
            return index + 2
        if type == 0 or type == 1:
            if equals4(index, ord('l'), ord('t'), ord('_'), ord('s')):
                writeSectionChar(type_comparison + 2)
                return index + 4
            if equals4(index, ord('l'), ord('t'), ord('_'), ord('u')):
                writeSectionChar(type_comparison + 3)
                return index + 4
            if equals4(index, ord('g'), ord('t'), ord('_'), ord('s')):
                writeSectionChar(type_comparison + 4)
                return index + 4
            if equals4(index, ord('g'), ord('t'), ord('_'), ord('u')):
                writeSectionChar(type_comparison + 5)
                return index + 4
            if equals4(index, ord('l'), ord('e'), ord('_'), ord('s')):
                writeSectionChar(type_comparison + 6)
                return index + 4
            if equals4(index, ord('l'), ord('e'), ord('_'), ord('u')):
                writeSectionChar(type_comparison + 7)
                return index + 4
            if equals4(index, ord('g'), ord('e'), ord('_'), ord('s')):
                writeSectionChar(type_comparison + 8)
                return index + 4
            if equals4(index, ord('g'), ord('e'), ord('_'), ord('u')):
                writeSectionChar(type_comparison + 9)
                return index + 4
        if type == 2 or type == 3:
            if equals2(index, ord('l'), ord('t')):
                writeSectionChar(type_comparison + 2)
                return index + 2
            if equals2(index, ord('g'), ord('t')):
                writeSectionChar(type_comparison + 3)
                return index + 2
            if equals2(index, ord('l'), ord('e')):
                writeSectionChar(type_comparison + 4)
                return index + 2
            if equals2(index, ord('g'), ord('e')):
                writeSectionChar(type_comparison + 5)
                return index + 2
        # memory loads
        if equals4(index, ord('l'), ord('o'), ord('a'), ord('d')):
            writeSectionChar(0x28 + type)
            return index + 4
        if type == 0 or type == 1:
            if equals7(index, ord('l'), ord('o'), ord('a'), ord('d'), ord('8'), ord('_'), ord('s')):
                writeSectionChar(0x2C + type*4)
                return index + 7
            if equals7(index, ord('l'), ord('o'), ord('a'), ord('d'), ord('8'), ord('_'), ord('u')):
                writeSectionChar(0x2D + type*4)
                return index + 7
            if equals8(index, ord('l'), ord('o'), ord('a'), ord('d'), ord('1'), ord('6'), ord('_'), ord('s')):
                writeSectionChar(0x2E + type*4)
                return index + 8
            if equals8(index, ord('l'), ord('o'), ord('a'), ord('d'), ord('1'), ord('6'), ord('_'), ord('u')):
                writeSectionChar(0x2F + type*4)
                return index + 8
        if type == 1:
            if equals8(index, ord('l'), ord('o'), ord('a'), ord('d'), ord('3'), ord('2'), ord('_'), ord('s')):
                writeSectionChar(0x34)
                return index + 8
            if equals8(index, ord('l'), ord('o'), ord('a'), ord('d'), ord('3'), ord('2'), ord('_'), ord('u')):
                writeSectionChar(0x35)
                return index + 8
        # memory stores
        if equals5(index, ord('s'), ord('t'), ord('o'), ord('r'), ord('e')):
            writeSectionChar(0x36 + type)
            return index + 5
        if type == 0 or type == 1:
            if equals6(index, ord('s'), ord('t'), ord('o'), ord('r'), ord('e'), ord('8')):
                writeSectionChar(0x3A + type*2)
                return index + 6
            if equals7(index, ord('s'), ord('t'), ord('o'), ord('r'), ord('e'), ord('1'), ord('6')):
                writeSectionChar(0x3B + type*2)
                return index + 7
        if type == 1:
            if equals7(index, ord('s'), ord('t'), ord('o'), ord('r'), ord('e'), ord('3'), ord('2')):
                writeSectionChar(0x3E)
                return index + 7
        # conversions
        if type == 0:
            if equals8(index, ord('w'), ord('r'), ord('a'), ord('p'), ord('_'), ord('i'), ord('6'), ord('4')):
                writeSectionChar(0xA7)
                return index + 8
        if type == 1:
            if equals12(index, ord('e'), ord('x'), ord('t'), ord('e'), ord('n'), ord('d'), ord('_'), ord('i'), ord('3'), ord('2'), ord('_'), ord('s')):
                writeSectionChar(0xAC)
                return index + 12
            if equals12(index, ord('e'), ord('x'), ord('t'), ord('e'), ord('n'), ord('d'), ord('_'), ord('i'), ord('3'), ord('2'), ord('_'), ord('u')):
                writeSectionChar(0xAD)
                return index + 12
        if type == 2:
            if equals10(index, ord('d'), ord('e'), ord('m'), ord('o'), ord('t'), ord('e'), ord('_'), ord('f'), ord('6'), ord('4')):
                writeSectionChar(0xB6)
                return index + 10
        if type == 3:
            if equals11(index, ord('p'), ord('r'), ord('o'), ord('m'), ord('o'), ord('t'), ord('e'), ord('_'), ord('f'), ord('3'), ord('2')):
                writeSectionChar(0xBB)
                return index + 11
        if type == 0 or type == 1:
            if equals11(index, ord('t'), ord('r'), ord('u'), ord('n'), ord('c'), ord('_'), ord('f'), ord('3'), ord('2'), ord('_'), ord('s')):
                writeSectionChar(0xA8 + type * 6)
                return index + 11
            if equals11(index, ord('t'), ord('r'), ord('u'), ord('n'), ord('c'), ord('_'), ord('f'), ord('3'), ord('2'), ord('_'), ord('u')):
                writeSectionChar(0xA9 + type * 6)
                return index + 11
            if equals11(index, ord('t'), ord('r'), ord('u'), ord('n'), ord('c'), ord('_'), ord('f'), ord('6'), ord('4'), ord('_'), ord('s')):
                writeSectionChar(0xAA + type * 6)
                return index + 11
            if equals11(index, ord('t'), ord('r'), ord('u'), ord('n'), ord('c'), ord('_'), ord('f'), ord('6'), ord('4'), ord('_'), ord('u')):
                writeSectionChar(0xAB + type * 6)
                return index + 11
        if type == 2 or type == 3:
            if equals13(index, ord('c'), ord('o'), ord('n'), ord('v'), ord('e'), ord('r'), ord('t'), ord('_'), ord('i'), ord('3'), ord('2'), ord('_'), ord('s')):
                writeSectionChar(0xB2 + (type - 2) * 5)
                return index + 13
            if equals13(index, ord('c'), ord('o'), ord('n'), ord('v'), ord('e'), ord('r'), ord('t'), ord('_'), ord('i'), ord('3'), ord('2'), ord('_'), ord('u')):
                writeSectionChar(0xB3 + (type - 2) * 5)
                return index + 13
            if equals13(index, ord('c'), ord('o'), ord('n'), ord('v'), ord('e'), ord('r'), ord('t'), ord('_'), ord('i'), ord('6'), ord('4'), ord('_'), ord('s')):
                writeSectionChar(0xB4 + (type - 2) * 5)
                return index + 13
            if equals13(index, ord('c'), ord('o'), ord('n'), ord('v'), ord('e'), ord('r'), ord('t'), ord('_'), ord('i'), ord('6'), ord('4'), ord('_'), ord('u')):
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
    global COUNT
    if equals3(index, ord('i'), ord('3'), ord('2')):
        writeSectionChar(0x7F)
        return index + 3
    if equals3(index, ord('i'), ord('6'), ord('4')):
        writeSectionChar(0x7E)
        return index + 3
    if equals3(index, ord('f'), ord('3'), ord('2')):
        writeSectionChar(0x7D)
        return index + 3
    if equals3(index, ord('f'), ord('6'), ord('4')):
        writeSectionChar(0x7C)
        return index + 3
    if equals3(index, ord('h'), ord('e'), ord('x')):
        return writeFromHex(index + 3)
    if equals3(index, ord('b'), ord('i'), ord('n')):
        return writeFromBin(index + 3)
    if equals3(index, ord('s'), ord('t'), ord('r')):
        return writeFromString(index + 3)
    if equals4(index, ord('u'), ord('l'), ord('e'), ord('b')):
        return writeFromUleb(index + 4)
    if equals4(index, ord('s'), ord('l'), ord('e'), ord('b')):
        return writeFromSleb(index + 4)
    if equals5(index, ord('a'), ord('s'), ord('c'), ord('i'), ord('i')):
        return writeFromAscii(index + 5)
    if equals7(index, ord('f'), ord('l'), ord('o'), ord('a'), ord('t'), ord('3'), ord('2')):
        return writeFromFloat32(index + 7)
    if equals7(index, ord('f'), ord('l'), ord('o'), ord('a'), ord('t'), ord('6'), ord('4')):
        return writeFromFloat64(index + 7)
    if equals7(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N')):
        SECTION_LAST_BYTES_OUT = SECTION_BYTES_OUT
        COUNT = 0
        return index + 7
    if equals11(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('E'), ord('N'), ord('D')):
        writeSection(WRITING_TO_FUNCTION, CURRENT_SECTION, SECTION_BYTES_OUT - SECTION_LAST_BYTES_OUT, SECTION_LAST_BYTES_OUT)
        return index + 11
    if equals14(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('H'), ord('E'), ord('A'), ord('D'), ord('E'), ord('R')):
        write_char(0x00)
        write_char(0x61)
        write_char(0x73)
        write_char(0x6D)
        write_char(0x01)
        write_char(0x00)
        write_char(0x00)
        write_char(0x00)
        return index + 14
    if equals12(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('T'), ord('Y'), ord('P'), ord('E')):
        CURRENT_SECTION = 0x01
        return index + 12
    if equals14(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('I'), ord('M'), ord('P'), ord('O'), ord('R'), ord('T')):
        CURRENT_SECTION = 0x02
        return index + 14
    if equals16(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('F'), ord('U'), ord('N'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N')):
        CURRENT_SECTION = 0x03
        return index + 16
    if equals14(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('M'), ord('E'), ord('M'), ord('O'), ord('R'), ord('Y')):
        CURRENT_SECTION = 0x05
        return index + 14
    if equals14(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('E'), ord('X'), ord('P'), ord('O'), ord('R'), ord('T')):
        CURRENT_SECTION = 0x07
        return index + 14
    if equals12(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('C'), ord('O'), ord('D'), ord('E')):
        CURRENT_SECTION = 0x0A
        return index + 12
    if equals12(index, ord('S'), ord('E'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('D'), ord('A'), ord('T'), ord('A')):
        CURRENT_SECTION = 0x0B
        return index + 12
    if equals8(index, ord('F'), ord('U'), ord('N'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N')):
        writeSectionChar(0x60)
        return index + 8
    if equals13(index, ord('F'), ord('U'), ord('N'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('K'), ord('I'), ord('N'), ord('D')):
        writeSectionChar(0x00)
        return index + 13
    if equals11(index, ord('M'), ord('E'), ord('M'), ord('O'), ord('R'), ord('Y'), ord('_'), ord('K'), ord('I'), ord('N'), ord('D')):
        writeSectionChar(0x02)
        return index + 11
    if equals14(index, ord('F'), ord('U'), ord('N'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('S'), ord('T'), ord('A'), ord('R'), ord('T')):
        FUNCTION_LAST_BYTES_OUT = FUNCTION_BYTES_OUT
        WRITING_TO_FUNCTION = 1
        LABEL_SCOPE = 0
        LABEL_FIRST_SYMBOL_ID = LAST_SYMBOL_ID
        return index + 14
    if equals12(index, ord('F'), ord('U'), ord('N'), ord('C'), ord('T'), ord('I'), ord('O'), ord('N'), ord('_'), ord('E'), ord('N'), ord('D')):
        WRITING_TO_FUNCTION = 0
        writeSection(1, 0, FUNCTION_BYTES_OUT - FUNCTION_LAST_BYTES_OUT, FUNCTION_LAST_BYTES_OUT)
        LABEL_SCOPE = 0
        return index + 12
    if equals9(index, ord('N'), ord('O'), ord('_'), ord('R'), ord('E'), ord('T'), ord('U'), ord('R'), ord('N')):
        writeSectionChar(0x40)
        return index + 9
    if equals5(index, ord('C'), ord('O'), ord('U'), ord('N'), ord('T')):
        COUNT += 1
        return index + 5
    if isComment(index):
        return skipComment(index)
    if memory[index] == ord('#'):
        return setVariable(index + 1)
    if memory[index] == ord('$'):
        return getVariable(index + 1)
    if memory[index] == ord('@'):
        return setLabel(index + 1)
    if memory[index] == ord('^'):
        return getLabel(index + 1)
    if memory[index] == 0:
        return -67
    
    parse_index = parseCmd(index)
    
    if parse_index != index:
        return parse_index

    error(index, 0x04)

def main():
    index = 0
    while True:
        index = skipWhiteSpace(index)
        index = parseWord(index)

        if index >= len(memory) or index == -67:
            break

def _start():
    handle_cli_input()
    main()
    handle_cli_output()

_start()