# Web Assembly Compiler

This Project is to folliow the evolution of the Computers from opcode to programming languages. First is to learn the opcodes and how to run programs in web assembly binary. After I do this, I will create my own Assembly language for the web assembly binary. Once I have that, I can create my own C type programming language that will compile into my Assembly language and then into the web assembly binary.

I will update the README as I progress through the project. Treat this almost as a blog of my progress.

**[WEB ASSEMBLY OPCODES](Opcodes.md)**

# Contents

- **[Setting up WebAsm](#setting-up-webasm)**
  - **[First Program](#first-program)**
  - **[Insert Data into Program](#insert-data-into-program)**
- **[Assembler](#assembler)**
  - **[First Step, Replacing Characters](#first-step-replacing-characters)**

## Setting Up WebAsm

### First Program

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

```
import from "env" print_i32(i32) -> void

function main() -> void {
    print_i32(add(6, 7))
}
```

### Insert Data into Program

Okay we're going to try to effect the output with some input from the javascript file. I will create a file named, input.cwa (custom web assembly), then I will read this file in javascript and convert it into binary and feed it into the webasm program. I will do this by exporting a memory page inside the program.wasm file. 

## Assembler

### First Step, Replacing Characters

So for the assembler, we're going to start with replacing characters from the input and then converting that into the opcode. Say `add` is `a` and such, if the character is not in the list it will just ignore it. This way we can start making the assembler and then later have this a little bit more usable assembler and integrate on top of it.