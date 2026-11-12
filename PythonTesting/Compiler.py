import sys
from pathlib import Path

# -----------------------------------------------------------------------------
# imports
# -----------------------------------------------------------------------------

# Capacities, 4 MiB
INPUT_LIMIT = 4 * 1024 * 1024 # global
OUTPUT_LIMIT = 4 * 1024 * 1024 # global

memory = [] # global memory
output_buffer = [] # global output buffer

stack_pointer = 0 # global
stack_length = 0 # global

lexer_buffer = [] # global token buffer
lexer_stack_pointer = 0 # global
lexer_stack_length = 0 # global

parser_buffer = [] # global AST buffer
parser_stack_pointer = 0 # global
parser_stack_length = 0 # global

codegen_type_buffer = [] # global type buffer 
codegen_import_buffer = [] # global import buffer 
codegen_function_buffer = [] # global function buffer 
codegen_memory_buffer = [] # global memory buffer 
codegen_export_buffer = [] # global export buffer 
codegen_code_buffer = [] # global code buffer 
codegen_locals_buffer = [] # global locals buffer 
codegen_data_buffer = [] # global data buffer 
codegen_custom_buffer = [] # global custom buffer 

output_path = "" # global
input_name = "" # global

# strings
s_output_limit = "Generated binary exceeds the output buffer capacity\0"
s_cli_arguments = "Expected two arguments: input.cweb output.wal\0"
s_input_file = "Input file does not exist or is not a regular file\0"
s_same_input_output = "Input and output must be different files\0"
s_input_limit = "Source exceeds the input region capacity\0"
s_non_ascii_source = "Source must contain only ASCII bytes\0"
s_nul_source = "Source must not contain embedded NUL bytes\0"
s_output_directory = "Output directory does not exist\0"
s_output_file = "Output path is not a regular file\0"
s_memory_out_of_bounds = "Memory out of bounds\0"
s_lexer_stack_limit = "Lexer stack limit exceeded\0"

other_builtin_type: int = 1 # global
other_identifier: int = 2 # global
res_export: int = 10 # global
res_import: int = 11 # global
res_if: int = 12 # global
res_else: int = 13 # global
res_while: int = 14 # global
res_return: int = 15 # global
res_break: int = 16 # global
res_continue: int = 17 # global
res_struct: int = 18 # global
res_typedef: int = 19 # global
op_add: int = 30 # `+` global
op_sub: int = 31 # `-` global
op_mul: int = 32 # `*` global
op_div: int = 33 # `/` global
op_mod: int = 34 # `%` global
op_bitwise_and: int = 35 # `&` global
op_bitwise_or: int = 36 # `|` global
op_bitwise_xor: int = 37 # `^`  global
op_shl: int = 38 # `<<` global
op_shr: int = 39 # `>>` global
op_eq: int = 40 # `==` global
op_neq: int = 41 # `!=` global
op_lt: int = 42 # `<` global
op_gt: int = 43 # `>` global
op_lte: int = 44 # `<=` global
op_gte: int = 45 # `>=` global
op_assign: int = 46 # `=` global
op_add_assign: int = 47 # `+=` global
op_sub_assign: int = 48 # `-=` global
op_mul_assign: int = 49 # `*=` global
op_div_assign: int = 50 # `/=` global
op_mod_assign: int = 51 # `%=` global
op_bitwise_and_assign: int = 52 # `&=` global
op_bitwise_or_assign: int = 53 # `|=` global
op_bitwise_xor_assign: int = 54 # `^=`  global
op_logical_and: int = 55 # `&&` global
op_logical_or: int = 56 # `||` global
op_logical_not: int = 57 # `!` global
op_bitwise_not: int = 58 # `~` global
op_bitwise_not_assign: int = 59 # `~=` global
op_increment: int = 60 # `++` global
op_decrement: int = 61 # `--` global

def fd_read(fd, iovs_ptr, iovs_len, nread_ptr): # imported WASI function
    iovs_ptr.extend(fd.read(iovs_len))
    return 0

def fd_write(fd, iovs_ptr, iovs_len, nwritten_ptr): # imported WASI function 
    if fd == 2:
        fd = sys.stderr.buffer
    written = fd.write(bytes(iovs_ptr[:iovs_len]))
    if written != iovs_len:
        exit_program(1)
    return 0

def proc_exit(status): # imported WASI function
    sys.exit(status)

# -----------------------------------------------------------------------------
# helpers
# -----------------------------------------------------------------------------

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
    global output_path, input_name, memory, stack_length

    if len(sys.argv) != 3:
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

    # Allocate destination memory with room for the optional newline and padding.
    memory = [0] * source_length

    # Copy only the normalized source bytes.
    index = 0
    while index < source_length:
        memory[index] = source[index]
        index += 1
    
    stack_length = index # set stack length for len(memory) calculation

    # EOF padding is already zero from allocation.
    output_buffer.clear()

def handle_cli_output():
    if not output_path.parent.is_dir():
        runtime_error(s_output_directory)
    if output_path.exists() and not output_path.is_file():
        runtime_error(s_output_file)
    with output_path.open("wb") as output_file:
        #fd_write(output_file, output_buffer, len(output_buffer), 0)
        fd_write(2, output_buffer, len(output_buffer), 0) # FOR TESTING PRINT OUTPUT TO STD.ERR INSTEAD OF TO FILE

def read_memory(address: int) -> int:
    global memory
    if address >= stack_length:
        runtime_error(s_memory_out_of_bounds)
    return memory[address]

def isWhiteSpace(index: int) -> bool:
    if index < stack_length:
        runtime_error(s_memory_out_of_bounds)
    return memory[index] == ord(' ') or memory[index] == ord('\t') or memory[index] == ord('\n')

def skipWhiteSpace(index: int) -> int:
    while isWhiteSpace(index):
        index += 1
    return index

def isOperator(index: int) -> int:
    if index < stack_length:
        runtime_error(s_memory_out_of_bounds)
    return memory[index] == ord('-') \
        or memory[index] == ord('=') \
        or memory[index] == ord('+') \
        or memory[index] == ord('[') \
        or memory[index] == ord(']') \
        or memory[index] == ord('{') \
        or memory[index] == ord('}') \
        or memory[index] == ord('|') \
        or memory[index] == ord('\\') \
        or memory[index] == ord(';') \
        or memory[index] == ord(':') \
        or memory[index] == ord('\'') \
        or memory[index] == ord('"') \
        or memory[index] == ord(',') \
        or memory[index] == ord('<') \
        or memory[index] == ord('.') \
        or memory[index] == ord('>') \
        or memory[index] == ord('/') \
        or memory[index] == ord('?') \
        or memory[index] == ord('!') \
        or memory[index] == ord('@') \
        or memory[index] == ord('#') \
        or memory[index] == ord('$') \
        or memory[index] == ord('%') \
        or memory[index] == ord('^') \
        or memory[index] == ord('&') \
        or memory[index] == ord('*') \
        or memory[index] == ord('(') \
        or memory[index] == ord(')') \
        or memory[index] == ord('`') \
        or memory[index] == ord('~') \

def getEndOfCapture(index: int, capture: int) -> int:
    while memory[index] != capture:
        if index >= stack_length:
            runtime_error(s_memory_out_of_bounds)
        index += 1
    return index

def getEndOfWord(index: int) -> int:
    while not isWhiteSpace(index) and not isOperator(index):
        index += 1
        if index == stack_length:
            return index
    return index

def skipLine(index: int) -> int:
    while memory[index] != ord('\n'):
        if index >= stack_length:
            runtime_error(s_memory_out_of_bounds)
        index += 1
    return index

def isComment(index: int) -> int:
    if index + 1 >= stack_length:
        runtime_error(s_memory_out_of_bounds)
    return memory[index] == ord('/') and memory[index + 1] == ord('/')

def equals1(index: int, c1: int) -> int:
    return memory[index] == c1

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

def equals15(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int, c12: int, c13: int, c14: int, c15: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and memory[index + 11] == c12 and memory[index + 12] == c13 and memory[index + 13] == c14 and memory[index + 14] == c15 and isWhiteSpace(index + 15)

def equals16(index: int, c1: int, c2: int, c3: int, c4: int, c5: int, c6: int, c7: int, c8: int, c9: int, c10: int, c11: int, c12: int, c13: int, c14: int, c15: int, c16: int) -> int:
    return memory[index] == c1 and memory[index + 1] == c2 and memory[index + 2] == c3 and memory[index + 3] == c4 and memory[index + 4] == c5 and memory[index + 5] == c6 and memory[index + 6] == c7 and memory[index + 7] == c8 and memory[index + 8] == c9 and memory[index + 9] == c10 and memory[index + 10] == c11 and memory[index + 11] == c12 and memory[index + 12] == c13 and memory[index + 13] == c14 and memory[index + 14] == c15 and memory[index + 15] == c16 and isWhiteSpace(index + 16)

# -----------------------------------------------------------------------------
# Lexer
# -----------------------------------------------------------------------------

def update_lexer_stack_pointer(value: int) -> None:
    global lexer_stack_pointer
    lexer_stack_pointer = value

def increment_lexer_stack_pointer(increment: int) -> None:
    global lexer_stack_pointer
    lexer_stack_pointer += increment

def write_to_lexer_stack(value: int) -> None:
    global lexer_buffer
    if lexer_stack_pointer + 1 >= lexer_stack_length:
        runtime_error(s_lexer_stack_limit)
    lexer_buffer[lexer_stack_pointer] = value
    increment_lexer_stack_pointer(1)

def read_lexer_stack_i32(address: int) -> int:
    if address + 3 >= lexer_stack_length:
        runtime_error(s_lexer_stack_limit)
    return lexer_buffer[address] + (lexer_buffer[address + 1] << 8) + (lexer_buffer[address + 2] << 16) + (lexer_buffer[address + 3] << 24)

def write_lexer_stack_i32(address: int, value: int) -> None:
    if address + 3 >= lexer_stack_length:
        runtime_error(s_lexer_stack_limit)
    lexer_buffer[address] = value & 0xFF
    lexer_buffer[address + 1] = (value >> 8) & 0xFF
    lexer_buffer[address + 2] = (value >> 16) & 0xFF
    lexer_buffer[address + 3] = (value >> 24) & 0xFF
    increment_lexer_stack_pointer(4)

def write_token(type_id: int, length: int, start: int) -> None:
    # tokens are stored as: { type_id: byte, length: byte, start: int }, taking up (1 + 1 + 4) = 6 bytes
    write_to_lexer_stack(type_id)
    write_to_lexer_stack(length)
    write_lexer_stack_i32(lexer_stack_pointer, start)

def isKeyword(index: int) -> int:
    # export, import, if, else, while, return, break, continue, struct, typedef
    if equals6(index, ord('e'), ord('x'), ord('p'), ord('o'), ord('r'), ord('t')):
        return 10
    if equals6(index, ord('i'), ord('m'), ord('p'), ord('o'), ord('r'), ord('t')):
        return 11
    if equals2(index, ord('i'), ord('f')):
        return 12
    if equals4(index, ord('e'), ord('l'), ord('s'), ord('e')):
        return 13
    if equals5(index, ord('w'), ord('h'), ord('i'), ord('l'), ord('e')):
        return 14
    if equals6(index, ord('r'), ord('e'), ord('t'), ord('u'), ord('r'), ord('n')):
        return 15
    if equals6(index, ord('b'), ord('r'), ord('e'), ord('a'), ord('k'), ord('e')):
        return 16
    if equals8(index, ord('c'), ord('o'), ord('n'), ord('t'), ord('i'), ord('n'), ord('u'), ord('e')):
        return 17
    if equals6(index, ord('s'), ord('t'), ord('r'), ord('u'), ord('c'), ord('t')):
        return 18
    if equals7(index, ord('t'), ord('y'), ord('p'), ord('e'), ord('d'), ord('e'), ord('f')):
        return 19
    return -1

def isType(index: int) -> int:
    # char, void, float, double, int, long
    if equals4(index, ord('c'), ord('h'), ord('a'), ord('r')):
        return 1
    if equals4(index, ord('v'), ord('o'), ord('i'), ord('d')):
        return 1
    if equals5(index, ord('f'), ord('l'), ord('o'), ord('a'), ord('t')):
        return 1
    if equals6(index, ord('d'), ord('o'), ord('u'), ord('b'), ord('l'), ord('e')):
        return 1
    if equals3(index, ord('i'), ord('n'), ord('t')):
        return 1
    if equals4(index, ord('l'), ord('o'), ord('n'), ord('g')):
        return 1
    return -1

def getDoubleOperator(index: int) -> int:
    if index + 1 < stack_length:
        runtime_error(s_memory_out_of_bounds)
    if memory[index] == ord('=') + memory[index + 1] == ord('='): return op_eq
    if memory[index] == ord('+') + memory[index + 1] == ord('='): return op_add_assign
    if memory[index] == ord('-') + memory[index + 1] == ord('='): return op_sub_assign
    if memory[index] == ord('*') + memory[index + 1] == ord('='): return op_mul_assign
    if memory[index] == ord('/') + memory[index + 1] == ord('='): return op_div_assign
    if memory[index] == ord('%') + memory[index + 1] == ord('='): return op_mod_assign
    if memory[index] == ord('&') + memory[index + 1] == ord('='): return op_bitwise_and_assign
    if memory[index] == ord('|') + memory[index + 1] == ord('='): return op_bitwise_or_assign
    if memory[index] == ord('^') + memory[index + 1] == ord('='): return op_bitwise_xor_assign
    if memory[index] == ord('<') + memory[index + 1] == ord('='): return op_lte
    if memory[index] == ord('>') + memory[index + 1] == ord('='): return op_gte
    if memory[index] == ord('!') + memory[index + 1] == ord('='): return op_neq
    if memory[index] == ord('>') + memory[index + 1] == ord('>'): return op_shr
    if memory[index] == ord('<') + memory[index + 1] == ord('<'): return op_shl
    if memory[index] == ord('&') + memory[index + 1] == ord('&'): return op_logical_and
    if memory[index] == ord('|') + memory[index + 1] == ord('|'): return op_logical_or
    if memory[index] == ord('+') + memory[index + 1] == ord('+'): return op_increment
    if memory[index] == ord('-') + memory[index + 1] == ord('-'): return op_decrement
    return -1

def getOperator(index: int) -> int:
    pass

def isValidIdentifier(index: int) -> int:
    pass

def getTypeId(index: int) -> int:
    keyword = isKeyword(index)
    if keyword != -1:
        return keyword
    op = getOperator(index) != -1
    if op != -1:
        return op
    ty = isType(index)
    if ty != -1:
        return ty
    if isValidIdentifier(index):
        return other_identifier
    return -1

def lex():
    index = 0
    while index < stack_length:
        start = index
        length = getEndOfWord(index) - index

        if memory[index] == ord('"'):
            length = getEndOfCapture(index, ord('"')) - index
        if memory[index] == ord('\''):
            length = getEndOfCapture(index, ord('\'')) - index
            if length != 2:
                pass
                # error invalid character literal

        if length < 0:
            runtime_error(s_lexer_stack_limit)
        if isComment(start):
            index = skipLine(index)
            continue

        if isOperator(start) and getDoubleOperator(start) != -1:
            length += 1
            index += 1

        type_id = getTypeId(start)
        
        if type_id == -1:
            pass # error invalid token
        
        write_token(type_id, length, start)

        index += 1

# -----------------------------------------------------------------------------
# Parser
# -----------------------------------------------------------------------------
def parse():
    pass

# -----------------------------------------------------------------------------
# Codegen helpers
# -----------------------------------------------------------------------------

# -----------------------------------------------------------------------------
# Compiler
# -----------------------------------------------------------------------------
def compile():
    pass

def main():
    lex()
    parse()
    compile()

def _start():
    handle_cli_input()
    main()
    handle_cli_output()

_start()