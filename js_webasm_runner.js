const fs = require('fs');

async function main() {
    const wasmBytes = fs.readFileSync('./program.wasm');
    const outputFile = fs.createWriteStream('./output.cwa');

    // This is for import functions to be exposed in WebAsm
    const imports = {
        env: {
            print_i32: (value) => {
                console.log(value);
            },
            write_char: (value) => {
                outputFile.write(Buffer.from([value]));
            }
        }
    }

    const wasmModule = await WebAssembly.instantiate(wasmBytes, imports);

    const instance = wasmModule.instance;

    // handle inserting data to memory
    const memory = instance.exports.memory;
    const bytes = new Uint8Array(memory.buffer);
    
    const replaceBytes = [
        'i'.charCodeAt(0), 77,
        'c'.charCodeAt(0), 5,
        0xFE, 0xFE
    ];

    for (let i = 0; i < replaceBytes.length; i++) {
        bytes[i] = replaceBytes[i];
    }

    // calls the exported main function to begin the program
    instance.exports.main();

    outputFile.end();
}

function createWasmFile() {
    const wasmBytes = new Int8Array([

        // HEADER
        0x00, 0x61, 0x73, 0x6D, // magic number
        0x01, 0x00, 0x00, 0x00, // version

        // TYPE
        0x01, 12, // 01 = Type Section, = length of section in bytes
        0x03, // There are 3 function types

        // print_i32(i32) -> void
        0x60, 0x01, 0x7F, 0x00, // 60=function type, 01=1 parameter, 7F=i32, 00=0 return values

        // write_char(i32) -> void
        0x60, 0x01, 0x7F, 0x00, // 60=function type, 01=1 parameter, 7F=i32, 00=0 return values
        
        // main() -> void
        0x60, 0x00, 0x00, // 60=function type, 00=0 parameters, 00=0 return values

        // IMPORT
        0x02, 34, // 02 = Import Section, = length of section in bytes
        0x02, // = imports
        
        // inside "env" module
        0x03, 0x65, 0x6E, 0x76, // 03 = length of module name, "env"; rest = "env"
        // import "print_i32" -> void
        0x09, 0x70, 0x72, 0x69, 0x6E, 0x74, 0x5F, 0x69, 0x33, 0x32, // 09= length of function name, "print_i32"; rest = "print_i32"
        0x00, 0x00, // 00 = import kind (function), 00 = type index (0)

        // inside "env" module
        0x03, 0x65, 0x6E, 0x76,
        // import "write_char" -> void
        0x0A, 0x77, 0x72, 0x69, 0x74, 0x65, 0x5F, 0x63, 0x68, 0x61, 0x72, // 0A= length of function name, "write_char"; rest = "write_char"
        0x00, 0x01, // 00 = import kind (function), 01 = type index (1)

        // FUNCTION
        0x03, 2, // 03 = Function Section, = length of section in bytes

        // main() -> void
        0x01, // = 1 function
        0x02, // = type index

        // MEMORY
        0x05, 3, // 05 = Memory Section, = length of section in bytes
        0x01, // 01 = 1 page of memory (65,536 bytes)
        0x00, 0x01, // 00 = limit flags (0 = no max), 01 = minumum size (1)

        // EXPORT
        0x07, 17, // 07 = Export Section, = length of section in bytes
        0x02, // 02 = 2 exports

        // expoort "main"
        0x04, 0x6D, 0x61, 0x69, 0x6E, // 04 = length of export name, "main"; rest = "main"
        0x00, 0x02, // 00 = export kind (function), function index 
        
        // export "memory"
        0x06, 0x6D, 0x65, 0x6D, 0x6F, 0x72, 0x79, // 06 = length of export name, "memory"; rest = "memory"
        0x02, 0x00, // 02 = export kind (memory), 00 = memory index (0)

        // CODE SECTION
        0x0A, 149, 0x01, // 0A = Code Section, = length of section ULEB128 encoded
        0x01, // = function body of function (main)
        
        // main()
        146, 0x01, // = size of function body in bytes ULEB128 encoded
        
        0x01, // = local variable declaration count
        0x03, 0x7F, // (bytes), (char), (lastWasEOF)

        0x02, 0x40, // block -> null
        0x03, 0x40, // loop -> null
        
        // char = memory[bytes]
        0x20, 0x00, // local.get 0 (bytes)
        0x2D, 0x00, 0x00, // i32.load8_u align=0 offset=0
        0x21, 0x01, // local.set 1 (char)

        // bytes = bytes + 1
        0x20, 0x00, // local.get 0 (bytes)
        0x41, 1, // i32.const 1
        0x6A, // i32.add
        0x21, 0x00, // local.set 0 (bytes)

        // ----------------------------- add
        // char == 97
        0x20, 0x01, // local.get 1 (char)
        0x41, 0xE1, 0x00, // i32.const 97
        0x46, // i32.eq 
        0x04, 0x40, // if -> null
        // char = 0x6A
        0x41, 0xEA, 0x00, // i32.const 0x6A
        0x21, 0x01, // local.set 1 (char)
        0x0B, // end [if]

        // ----------------------------- i32.const
        // char == 105
        0x20, 0x01, // local.get 1 (char)
        0x41, 0xE9, 0x00, // i32.const 105
        0x46, // i32.eq 
        0x04, 0x40, // if -> null
        // char = 0x41
        0x41, 0xC1, 0x00, // i32.const 0x41
        0x21, 0x01, // local.set 1 (char)
        0x0B, // end [if]

        // ----------------------------- call
        // char == 99
        0x20, 0x01, // local.get 1 (char)
        0x41, 0xE3, 0x00, // i32.const 99
        0x46, // i32.eq 
        0x04, 0x40, // if -> null
        // char = 0x10
        0x41, 0x10, // i32.const 0x10
        0x21, 0x01, // local.set 1 (char)
        0x0B, // end [if]

        // ----------------------------- i32.get
        // char == 103
        0x20, 0x01, // local.get 1 (char)
        0x41, 0xE7, 0x00, // i32.const 103
        0x46, // i32.eq 
        0x04, 0x40, // if -> null
        // char = 0x20
        0x41, 0x20, // i32.const 0x20
        0x21, 0x01, // local.set 1 (char)
        0x0B, // end [if]

        // ----------------------------- i32.set
        // char == 115
        0x20, 0x01, // local.get 1 (char)
        0x41, 0xF3, 0x00, // i32.const 115
        0x46, // i32.eq 
        0x04, 0x40, // if -> null
        // char = 0x21
        0x41, 0x21, // i32.const 0x21
        0x21, 0x01, // local.set 1 (char)
        0x0B, // end [if]

        // ----------------------------- i32.load8_u
        // char == 108
        0x20, 0x01, // local.get 1 (char)
        0x41, 0xEC, 0x00, // i32.const 108
        0x46, // i32.eq 
        0x04, 0x40, // if -> null
        // char = 0x2D
        0x41, 0x2D, // i32.const 0x2D
        0x21, 0x01, // local.set 1 (char)
        0x0B, // end [if]

        // lastWasEOF == 1
        0x20, 0x02, // local.get 2 (lastWasEOF)
        0x41, 1, // i32.const 1
        0x46, // i32.eq
        0x04, 0x40, // if -> null
        // char == 0xFE (EOF)
        0x20, 0x01, // local.get 1 (char)
        0x41, 0xFE, 0x01, // i32.const 0xFE
        0x46, // i32.eq
        0x0D, 0x02, // br_if (if=0, loop=1, block=2)
        0x0B, // end [if]
        
        // char == 0xFE (EOF)
        0x20, 0x01, // local.get 1 (char)
        0x41, 0xFE, 0x01, // i32.const 0xFE
        0x46, // i32.eq
        0x04, 0x7F, // if -> i32
        0x41, 1, // i32.const 1
        0x05, // else 
        0x41, 0, // i32.const 0
        0x0B, // end [if]
        0x21, 0x02, // local.set 2 (lastWasEOF)

        // write_char(char)
        0x20, 0x01, // local.get 1 (char)
        0x10, 1, // call 1

        0x0C, 0x00, // br (loop=0, block=1)

        0x0B, // end [loop]
        0x0B, // end [block]

        // print_i32(bytes)
        0x20, 0, // local.get 0 (bytes)
        0x10, 0, // call 0

        0x0B // end
    ]);

    fs.writeFileSync('./program.wasm', wasmBytes);
}

// create the wasm file
createWasmFile();

// run the main function and catch any errors
main().catch(err => {
    console.error(err);
});