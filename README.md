# Web Assembly Compiler

This Project is to folliow the evolution of the Computers from opcode to programming languages. First is to learn the opcodes and how to run programs in web assembly binary. After I do this, I will create my own Assembly language for the web assembly binary. Once I have that, I can create my own C type programming language that will compile into my Assembly language and then into the web assembly binary.

I will update the README as I progress through the project. Treat this almost as a blog of my progress.

**[WEB ASSEMBLY OPCODES](Opcodes.md)**

# Contents

- [Web Assembly Compiler](#web-assembly-compiler)
- [Contents](#contents)
- [Setting Up WebAsm](#setting-up-webasm)
  - [First Program](#first-program)
  - [Insert Data into Program](#insert-data-into-program)
- [Assembler](#assembler)
  - [First Step, Replacing Characters](#first-step-replacing-characters)
  - [Second Step, Input is Text and Output is bytes](#second-step-input-is-text-and-output-is-bytes)
  - [Third Step, Define the Assembly Language](#third-step-define-the-assembly-language)
    - [Encoding Bytes](#encoding-bytes)
    - [Comments](#comments)
    - [Assembler Variables](#assembler-variables)
    - [Defining Sections](#defining-sections)
    - [TYPE Section](#type-section)
    - [IMPORT Section](#import-section)
    - [FUNCTION Section](#function-section)
    - [MEMORY Section](#memory-section)
    - [GLOBAL Section](#global-section)
    - [EXPORT Section](#export-section)
    - [CODE Section](#code-section)

# Setting Up WebAsm

## First Program

First thing I did was set up a javascript file that would load a `wasm` file and run it. I use [program.wasm](program.wasm) as the target. I also had to create a function to create the file and fill it with the binary data. With the help of ChatGPT to guide me, I was able to make a simple program that would run and I used node js for fast console output. 

I created a program that would add two numbers and print the result. I used the `print_i32` function from the `env` module to print the result. The program is very simple, but it was a good starting point for me to learn how to create a web assembly binary file.

Here is the Binary that I used to create the `program.wasm` file.

```js
// HEADER
0x00, 0x61, 0x73, 0x6D, // magic number
0x01, 0x00, 0x00, 0x00, // version

// TYPE
0x01, 0x08,  // 01 = Type Section, 08= length of section in `8` bytes
0x02, // There are 2 function types

0x60, 0x01, 0x7F, 0x00, // 60=function type, 01=1 parameter, 7F=i32, 00=0 return values
0x60, 0x00, 0x00, // 60=function type, 00=0 parameters, 00=0 return values

// IMPORT
0x02, 0x11, // 02 = Import Section, 11= length of section in `17` bytes
0x01, // 01 = 1 import
0x03, 0x65, 0x6E, 0x76, // 03 = length of module name, "env"; rest = "env"
0x09, 0x70, 0x72, 0x69, 0x6E, 0x74, 0x5F, 0x69, 0x33, 0x32, // 09= length of function name, 
0x00, 0x00, // 00 = import kind (function), 00 = type index (0)

// FUNCTION
0x03, 0x02, // 03 = Function Section, 02= length of section in `2` bytes
0x01, // 01 = 1 function
0x01, // 01 = type index (1)

// EXPORT
0x07, 0x08, // 07 = Export Section, 08= length of section in `8` bytes
0x01, // 01 = 1 export
0x04, 0x6D, 0x61, 0x69, 0x6E, // 04 = length of export name, "main"; rest = "main"
0x00, 0x01, // 00 = export kind (function), 01 = function index (1)

// CODE SECTION
0x0A, 0x0B, // 0A = Code Section, 08= length of section in `11` bytes
0x01, // 01 = function body of function `1` (main)
0x09, // 09 = size of function body in `9` bytes
0x00, // 00 = local variable count (0)
0x41, 0x06, // 41 = i32.const, 06 = value 6
0x41, 0x07, // 41 = i32.const, 07 = value 7
0x6A, // 6A = i32.add
0x10, 0x00, // 10 = call, 00 = function index (print_i32)
0x0B // 0B = end
```

And it sure enough outputed:

```
13
```

The psuedocode for the program is as follows:

```js
import from "env" function print_i32(i32) -> void

function main() -> void {
    print_i32(add(6, 7))
}
```

## Insert Data into Program

Okay we're going to try to effect the output with some input from the javascript file. I will create a file named, input.cwa (custom web assembly), then I will read this file in javascript and convert it into binary and feed it into the webasm program. I will do this by exporting a memory page inside the program.wasm file. 

To do this, I added a memory output to the wasm program.wasm file.

```js
// MEMORY
0x05, 0x03, // 05 = Memory Section, 03= length of section in `3` bytes
0x01, // 01 = 1 page of memory (65,536 bytes)
0x00, 0x01, // 00 = limit flags (0 = no max), 01 = minumum size (1)

// ... later in the program.wasm file:

// export "memory"
0x06, 0x6D, 0x65, 0x6D, 0x6F, 0x72, 0x79, // 06 = length of export name, "memory"; rest = "memory"
0x02, 0x00, // 02 = export kind (memory), 00 = memory index (0)
```

I also wanted to pass `byteLength` as a parameter into the main function. I needed to update the Type section in the program.wasm file.

```js
// main(i32) -> void
0x60, 0x01, 0x7F, 0x00, // 60=function type, 00=1 parameters, 7F=i32, 00=0 return values
```

And then after I added it as an export to the javascript part so that I could access it.

```js
const memory = instance.exports.memory;
const bytes = new Uint8Array(memory.buffer);
const byteLength = 3;
// test bytes
bytes[0] = 10;
bytes[1] = 20;
bytes[2] = 30;

// Start the program and pass the byteLength parameter into the function
instance.exports.main(byteLength);
```

To access the memory, I used `i32.load8_u` (`0x2D`) to load a single byte from memory. Then I made a loop using `loop` (`0x03`). After a bit of time figuring out how that all works and counting the amount of bytes in the program again and again, I ended with the opcode version using 39 bytes for the new main function with a working loop:

```js
// This is the pseudo code version of the opcode for the updated main function taking a total of 39 bytes
function main(byteLength: i32) -> void {
    var index: i32 = 0
    var sum: i32 = 0
    block loop:
        sum = (memory[index] as i32) + sum
        print_i32(memory[index])
        index = index + 1
        if index < byteLength {
            goto loop
        }
    end
    print_i32(sum)
}
```

The above code is coded really weird with the `block` and the `goto` statement, but that is closest way of writing this code in a more readable format. The way Web Assembly works, there is no exact loop that then loops back to the beginning. it does use an opcode named loop, but it is more of a block than a loop. It also has a branch `br` (`0x0C`) and a conditional branch `br_if` (`0x0D`), and these will return to a depth defined, or can also break if you return to a  surrounding block. But also if the code reaches the `end` of the loop it breaks instead of looping back. It's interesting the way it works but once you understand it it makes sense.

# Assembler

## First Step, Replacing Characters

So for the assembler, we're going to start with replacing characters from the input and then converting that into the opcode. Say `add` is `a` and such, if the character is not in the list it will just ignore it. This way we can start making the assembler and then later have this a little bit more usable assembler and integrate on top of it.

Here is the psuedo code version of the opcode binary in the program.wasm

```js
import from "env" function print_i32(i32) -> void
import from "env" function write_char(i32) -> void

function main() -> void {
    var bytes: i32 = 0
    var char: i32 = 0
    var lastWasEOF: i32 = 0

    block loop:
        char = memory[bytes]
        bytes = bytes + 1

        // commonly used opcodes
        if char == 97 { // unicode for `a`
            char = 0x6A // opcode for `add`
        }
        if char == 105 { // unicode for `i`
            char = 0x41 // opcode for `i32.const`
        }
        if char == 99 { // unicode for `c`
            char = 0x10 // opcode for `call`
        }
        if char == 103 { // unicode for `g`
            char = 0x20 // opcode for `i32.get`
        }
        if char == 115 { // unicode for `s`
            char = 0x21 // opcode for `i32.set`
        }
        if char == 108 { // unicode for `l`
            char = 0x2D // opcode for `i32.load8_u`
        }

        if lastWasEOF == 1 && char == ENDOFFILEBYTE {
            break // technically branches out of depth
        }
        
        lastWasEOF = if char == ENDOFFILEBYTE {
            1
        } else {
            0
        }

        write_char(char)

        goto loop
    end
    
    print_i32(bytes)
}
```

## Second Step, Input is Text and Output is bytes

Okay so the next step is to make the Input a text file and the output bytes. Right now, it has no idea when a byte is an instruction and when a byte is a number or such. Unfortunately we can not use the program from the first step to work on this, because any number input will just be the byte value and not the ASCI code for the number.

```js
import from "env" function print_i32(i32) -> void
import from "env" function write_char(i32) -> void

function main() -> void {
    var bytes: i32 = 0
    var char: i32 = 0
    var cmd: i32 = 0
    var number: i32 = 0
    var startWord: i32 = 0
    var wordLength: i32 = 0
    var stateCMD: i32 = 1 // 0=not command byte, 1=next byte is command, 2=byte is command

    block loop:
        char = memory[bytes]
        bytes = bytes + 1

        if char == ENDOFFILEBYTE {
            break
        }

        if char == '\n' as i32 {
            stateCMD = 1 // next byte is command
            startWord = bytes + 1
        }

        else if char == ' ' as i32 || char == '\t' as i32 || char == ';' as i32 {
            if stateCMD == 2 { // End Of Command
                stateCMD = 0
                cmd = WordToCMD(startWord, wordLength)

                if cmd == 0xFB { // check for error
                    print_i32(0xFB)
                    return
                }
                
                write_char(cmd)
            }
            else if stateCMD == 0 { // End Of Argument
                number = WordToI32(startWord, wordLength)

                if number == 0xFC { // check for error
                    print_i32(0xFC)
                    return
                }

                writeULEB128(number)
            }
            startWord = bytes + 1 // next byte is start of word
            wordLength = 0
            goto loop
        }

        // if valid char
        else if (char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') || (char >= '0' && char <= '9') || char == '_' {
            if stateCMD == 1 {
                stateCMD = 2
            }
            wordLength = wordLength + 1
        } else {
            print_i32(0xFD) // error code invalid char
            return
        }

        goto loop
    end

    // END OF FILE SEQUENCE
    write_char(0xFE)
    
    print_i32(bytes)
}

function WordToCMD(startWord: i32, wordLength: i32) -> i32 {
    if wordLength == 3 && memory[startWord] == 'a' && memory[startWord + 1] == 'd' && memory[startWord + 2] == 'd' {
        return 0x6A // opcode for `i32.add`
    }
    if wordLength == 3 && memory[startWord] == 'm' && memory[startWord + 1] == 'u' && memory[startWord + 2] == 'l' {
        return 0x6C // opcode for `i32.mul`
    }
    if wordLength == 3 && memory[startWord] == 's' && memory[startWord + 1] == 'u' && memory[startWord + 2] == 'b' {
        return 0x6B // opcode for `i32.sub`
    }
    if wordLength == 3 && memory[startWord] == 'a' && memory[startWord + 1] == 'n' && memory[startWord + 2] == 'd' {
        return 0x71 // opcode for `i32.and`
    }
    if wordLength == 2 && memory[startWord] == 'o' && memory[startWord + 1] == 'r'  {
        return 0x72 // opcode for `i32.or`
    }
    if wordLength == 3 && memory[startWord] == 's' && memory[startWord + 1] == 'h' && memory[startWord + 2] == 'r'  {
        return 0x76 // opcode for `i32.shr_u`
    }
    if wordLength == 5 && memory[startWord] == 'c' && memory[startWord + 1] == 'o' && memory[startWord + 2] == 'n' && memory[startWord + 3] == 's' && memory[startWord + 4] == 't' { 
        return 0x41 // opcode for `i32.const`
    }
    if wordLength == 4 && memory[startWord] == 'c' && memory[startWord + 1] == 'a' && memory[startWord + 2] == 'l' && memory[startWord + 3] == 'l' {
        return 0x10 // opcode for `call`
    }
    if wordLength == 3 && memory[startWord] == 'g' && memory[startWord + 1] == 'e' && memory[startWord + 2] == 't' { 
        return 0x20 // opcode for `local.get`
    }
    if wordLength == 3 && memory[startWord] == 's' && memory[startWord + 1] == 'e' && memory[startWord + 2] == 't' { 
        return 0x21 // opcode for `local.set`
    }
    if wordLength == 4 && memory[startWord] == 'l' && memory[startWord + 1] == 'o' && memory[startWord + 2] == 'a' && memory[startWord + 3] == 'd' { 
        return 0x2D // opcode for `i32.load8_u`
    }
    if wordLength == 2 && memory[startWord] == 'i' && memory[startWord + 1] == 'f' { 
        return 0x04 // opcode for `if`
    }
    if wordLength == 4 && memory[startWord] == 'e' && memory[startWord + 1] == 'l' && memory[startWord + 2] == 's' && memory[startWord + 3] == 'e' { 
        return 0x05 // opcode for `else`
    }
    if wordLength == 5 && memory[startWord] == 'b' && memory[startWord + 1] == 'l' && memory[startWord + 2] == 'o' && memory[startWord + 3] == 'c' && memory[startWord + 4] == 'k' { 
        return 0x02 // opcode for `block`
    }
    if wordLength == 4 && memory[startWord] == 'l' && memory[startWord + 1] == 'o' && memory[startWord + 2] == 'o' && memory[startWord + 3] == 'p' { 
        return 0x03 // opcode for `loop`
    }
    if wordLength == 3 && memory[startWord] == 'e' && memory[startWord + 1] == 'n' && memory[startWord + 2] == 'd' { 
        return 0x0B // opcode for `end`
    }
    if wordLength == 2 && memory[startWord] == 'b' && memory[startWord + 1] == 'r' { 
        return 0x0C // opcode for `br`
    }
    if wordLength == 5 && memory[startWord] == 'b' && memory[startWord + 1] == 'r' && memory[startWord + 2] == '_' && memory[startWord + 3] == 'i' && memory[startWord + 4] == 'f' { 
        return 0x0D // opcode for `br_if`
    }
    if wordLength == 3 && memory[startWord] == 'r' && memory[startWord + 1] == 'e' && memory[startWord + 2] == 't' { 
        return 0x0F // opcode for `return`
    }
    if wordLength == 2 && memory[startWord] == 'e' && memory[startWord + 1] == 'q' { 
        return 0x46 // opcode for `i32.eq`
    }
    if wordLength == 2 && memory[startWord] == 'n' && memory[startWord + 1] == 'q' { 
        return 0x47 // opcode for `i32.nq`
    }
    if wordLength == 2 && memory[startWord] == 'l' && memory[startWord + 1] == 't' { 
        return 0x49 // opcode for `i32.lt_u`
    }
    if wordLength == 2 && memory[startWord] == 'l' && memory[startWord + 1] == 'e' { 
        return 0x4D // opcode for `i32.le_u`
    }
    if wordLength == 2 && memory[startWord] == 'g' && memory[startWord + 1] == 't' { 
        return 0x4B // opcode for `i32.gt_u`
    }
    if wordLength == 2 && memory[startWord] == 'g' && memory[startWord + 1] == 'e' { 
        return 0x4F // opcode for `i32.ge_u`
    }
    return 0xFB
}

function WordToI32(startWord: i32, wordLength) -> i32 {
    var char: i32 = 0
    var digit: i32 = 0
    var product: i32 = 0
    var index: i32 = 0
    loop: // no block because no need to break out, instead code reaches 'end' and breaks
        char = memory[startWord + index]

        if char < '0' as i32 || char > '9' {
            return 0xFC
        }

        digit = char - 48
        product = product * 10 + digit

        index = index + 1
        if index < wordLength {
            goto loop
        } // else, reaches 'end' and breaks
    end

    return product
}

function IntoULEB128(number: i32) -> i32 {
    var byte: i32 = number & 0x7F

    if number >= 128 {
        byte = byte | 0x80
    }

    return byte
}

function WriteULEB128(number: i32) -> void {
    var byte: i32 = 0

    loop: // no block because no need to break out, instead code reaches 'end' and breaks
        byte = IntoULEB128(number)
        write_char(byte)

        number = number >> 7

        if number > 0 {
            goto loop
        } // else, reaches 'end' and breaks
    end
}

/*
example input code
const 1
load 0 0
const 3
add
call 0 
*/
```

Surprisingly, after a lot of work, it worked! This is not the end goal though. This assembler is extremely limited, and only really works with the CODE section of the WebAsm binary. Even though I worked so hard to get this one to work, I'm going to scrap it for now and start going over what I want the assembly language to look like.

## Third Step, Define the Assembly Language

The assembly language needs to have the following goals:
- [x] Be extremely simple to map to binary
- [x] Assemble all WebAsm sections, not just the CODE section
  - This includes importing and exporting functions, defining memory, and defining functions
- [ ] Be able to look at the assembly language and understand what the program is doing. This is especially true with the other Sections, when defining functions or memory
  - This didn't really happen to work that well with the way the assembler was set up, so I might make this better in the future, but for now it will be a little more complex to read than I would like.
- [x] Be relatively easy to program the assembler in the WebAsm binary
- [x] Does not need to have complete mapping of WebAsm opcodes, just enough to be able to write a simple program

Some of these goals are simple enough, others are more complex.

### Encoding Bytes

Right now, we want to be able to encode number and bytes in a bunch of different ways for simplicity. We'll use prefixes to define how the number or byte is encoded. The following are the prefixes that will be used:

- `hex` - Hexadecimal, 2 bytes per digit, e.g. `hex FF` = 255
- `bin` - Binary, 8 bytes per digit, e.g. `bin 11111111` = 255
- `uleb` - Unsigned LEB128, e.g. `uleb 255` = 255
- `str` - String, e.g. `str Hello` = 72 101 108 108 111
  - Remember usually the length of strings is required before the string, so use `uleb 3 str abc` to encode the string "abc" with the length of 3 before it.

### Comments

I think comments would be a nice touch and not hard to add so the `;` will start a comment and will continue until the end of the line. The assembler will ignore everything after the `;` on that line.

### Assembler Variables

The `$` will be used to access a variable that can be used later in the program. The `#` will be used to define it. The variable will be replaced with the value of the variable when the assembler sees it. The following is an example of how to define and use a variable:

```
; define
#<variable_name> <value>
; access
$<variable_name>
```

This can be anywhere in a line, for example `FUNCTION uleb 1 i32 #main_type 0` is valid and will replace `$main_type` with `0` when the assembler sees it in the future. In this line, `const $main_type` is the same as `const 0`.

### Defining Sections

To define a section, we will use the following syntax:

```
SECTION <section_name> 
; contents
END_SECTION
```

This will allow the assembler to start counting bytes when it sees the `SECTION` keyword, and stop counting when it sees the `END_SECTION` keyword. The section name will be a predefined that will convert to the binary section name. The following are the section names that will be used:

- `SECTION_HEADER` - Header Section -> Converts to `0x00, 0x61, 0x73, 0x6D, 0x01, 0x00, 0x00, 0x00`
- `SECTION_TYPE` - Type Section -> Converts to `0x01`
- `SECTION_IMPORT` - Import Section -> Converts to `0x02`
- `SECTION_FUNCTION` - Function Section -> Converts to `0x03`
- `SECTION_MEMORY` - Memory Section -> Converts to `0x05`
- `SECTION_GLOBAL` - Global Section -> Converts to `0x06`
- `SECTION_EXPORT` - Export Section -> Converts to `0x07`
- `SECTION_CODE` - Code Section -> Converts to `0x0A`

More might come later but these are the main sections we'll use for now.

### TYPE Section

The Type Section will translate directly into bytes, but it will be easier to read and write than just straight bytes because terms like `FUNCTION` -> `0x60` and `i32` -> `0x7F` will be used. The following is an example of how to define a function type in the TYPE section:

```
SECTION SECTION_TYPE
FUNCTION uleb 3 i32 i32 i32 uleb 1 i32 #three_in_1_out 0
FUNCTION uleb 1 i32 uleb 0 #print_i32_type 1
SECTION_END
```

The `uleb 3 i32 i32 i32` are the parameters of the function, and the `i32` is the return type of the function.

The `$three_in_1_out` and `$print_i32_type` are the labels that can be used to reference this type later. If `$three_in_1_out` is used later in the program, it will be replaced with the index -> `0` because it's the first type defined.

### IMPORT Section

The Import sections will also directly translate into bytes. These use strings so the `str` encoding will be used for the module and function names. The following is an example of how to define an import in the IMPORT section:

```
SECTION SECTION_IMPORT
uleb 3 str env uleb 9 str print_i32 FUNCTION_KIND $print_i32_type
SECTION_END
```

`FUNCTION_KIND` is a predefined that will convert to `0x00` for the import kind. The `$print_i32_type` is the label that was defined in the TYPE section, and it will be replaced with the index of the type when the assembler sees it.

### FUNCTION Section

The Function section is pretty simple, it just defines the functions that will be used in the CODE section.

```
SECTION SECTION_FUNCTION
#main 0 $main_type
#other_func 1 $three_in_1_out
SECTION_END
```

The `#main` and `#other_func` are labels defined in the TYPE_SECTION and they translate to the index of the type that corrosponds to the function. The `$main_type` and `$three_in_1_out` are the labels that were defined in the TYPE section, and they will be replaced with the index of the type when the assembler sees them.

### MEMORY Section

The memory section won't be used much in the beginning, so for now I will just keep it simple and it translates directly into bytes. The following is an example of how to define a memory in the MEMORY section:

```
SECTION SECTION_MEMORY
; 1 page of memory, no max, min size 1 page. Define variable for memory index 0
uleb 1 uleb 0 uleb 1 #memory 0
SECTION_END
```

### GLOBAL Section

The global section is for defining global variables that can be used in the program. The following is an example of how to define a global variable in the GLOBAL section:

```
SECTION SECTION_GLOBAL
uleb 1
i32 IMMUTABLE const uleb 45 end #global_var 0
SECTION_END
```

### EXPORT Section

The export section is also pretty simple, it just defines the functions that will be exported from the program. The following is an example of how to define an export in the EXPORT section:

```
SECTION SECTION_EXPORT
uleb 2 
uleb 4 str main FUNCTION_KIND $main
uleb 6 str memory MEMORY_KIND $memory
SECTION_END
```

### CODE Section

The CODE section is where the main program code will be defined. This is where the bulk of the assembly language will be used. Every opcode that will be supported will have a defined keyword that will translate to the opcode. `FUNCTION_START` and `FUNCTION_END` will be used to track how many bytes are in the function declaration.. The following is an example of how to define a function in the CODE section:

```
SECTION SECTION_CODE
uleb 2

FUNCTION_START ; main function
    const uleb 6
    const uleb 7
    add
    call $print_i32
    end
FUNCTION_END

FUNCTION_START ; other_func function
    uleb 1 ; declaration group
    uleb 3 i32 #x 0 #y 0 #z 0 ; local variables
    
    block NO_RETURN %block1
        loop NO_RETURN %loop1
            local.get $x
            local.get $y
            i32.mul
            local.get $z
            i32.mul
            local.set $x
            
            local.get $x
            i32.const uleb 500
            i32.lt
            br_if ^block1
        end
    end
    local.get $x
    return
    end
FUNCTION_END

SECTION_END
```

You can view the opcodes for the above code in the [Opcodes.md](Opcodes.md) file.

The `%` and the `^` are used to define and reference labels for the `block`, `loop`, and `br_if` opcodes. The `%block1` and `%loop1` are labels that can be used to reference the block and loop, and the `^block1` is used to reference the block when using the `br_if` opcode. This is to make it easier to use brances in the language instead of counting the depth.