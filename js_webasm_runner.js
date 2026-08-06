const fs = require('fs');

async function main() {
    const wasmBytes = fs.readFileSync('./program.wasm');

    // This is for import functions to be exposed in WebAsm
    const imports = {
        env: {
            print_i32: (value) => {
                console.log(value);
            }
        }
    }

    const wasmModule = await WebAssembly.instantiate(wasmBytes, imports);

    const instance = wasmModule.instance;

    // handle inserting data to memory
    const memory = instance.exports.memory;
    const bytes = new Uint8Array(memory.buffer);
    const byteLength = 3;

    // test bytes
    bytes[0] = 10;
    bytes[1] = 20;
    bytes[2] = 30;

    // calls the exported main function to begin the program
    instance.exports.main(byteLength);
}

function createWasmFile() {
    const wasmBytes = new Uint8Array([

        // HEADER
        0x00, 0x61, 0x73, 0x6D, // magic number
        0x01, 0x00, 0x00, 0x00, // version

        // TYPE
        0x01, 0x09,  // 01 = Type Section, 09= length of section in `9` bytes
        0x02, // There are 2 function types

        // print_i32(i32) -> void
        0x60, 0x01, 0x7F, 0x00, // 60=function type, 01=1 parameter, 7F=i32, 00=0 return values
        
        // main(i32) -> void
        0x60, 0x01, 0x7F, 0x00, // 60=function type, 00=1 parameters, 7F=i32, 00=0 return values

        // IMPORT
        0x02, 0x11, // 02 = Import Section, 11= length of section in `17` bytes
        0x01, // 01 = 1 import
        
        // import "env"
        0x03, 0x65, 0x6E, 0x76, // 03 = length of module name, "env"; rest = "env"

        // import "print_i32" -> void
        0x09, 0x70, 0x72, 0x69, 0x6E, 0x74, 0x5F, 0x69, 0x33, 0x32, // 09= length of function name, "print_i32"; rest = "print_i32"
        0x00, 0x00, // 00 = import kind (function), 00 = type index (0)

        // FUNCTION
        0x03, 0x02, // 03 = Function Section, 02= length of section in `2` bytes

        // main(i32) -> void
        0x01, // 01 = 1 function
        0x01, // 01 = type index (1)

        // MEMORY
        0x05, 0x03, // 05 = Memory Section, 03= length of section in `3` bytes
        0x01, // 01 = 1 page of memory (65,536 bytes)
        0x00, 0x01, // 00 = limit flags (0 = no max), 01 = minumum size (1)

        // EXPORT
        0x07, 0x11, // 07 = Export Section, 17= length of section in `17` bytes
        0x02, // 02 = 2 exports

        // expoort "main"
        0x04, 0x6D, 0x61, 0x69, 0x6E, // 04 = length of export name, "main"; rest = "main"
        0x00, 0x01, // 00 = export kind (function), 01 = function index (1)

        // export "memory"
        0x06, 0x6D, 0x65, 0x6D, 0x6F, 0x72, 0x79, // 06 = length of export name, "memory"; rest = "memory"
        0x02, 0x00, // 02 = export kind (memory), 00 = memory index (0)

        // CODE SECTION
        0x0A, 0x39, // 0A = Code Section, =length of section 
        
        // main()
        0x01, // = function body of function (main)
        0x37, // = size of function body in bytes 
        0x02, // = local variable count

        0x01, 0x7F, // = 1 local variable of type i32 (index)
        0x01, 0x7F, // = 1 local variable of type i32 (sum)

        0x41, 0x00, // i32.const 0
        0x21, 0x01, // set_local 1 (index)

        0x41, 0x00, // i32.const 0
        0x21, 0x02, // set_local 2 (sum)

        // loop through the memory and sum the values
        0x02, 0x40, // block, [empty block type]
        0x03, 0x40, // loop, [empty block type]
        
        0x20, 0x01, // get_local 1 (index)
        0x2C, 0x00, 0x00, // i32.load8_s, align=2, offset=0
        0x20, 0x02, // get_local 2 (sum)
        0x6A, // i32.add
        0x21, 0x02, // set_local 2 (sum)

        0x20, 0x01, // get_local 1 (index)
        0x2C, 0x00, 0x00, // i32.load8_s, align=2, offset=0
        0x10, 0x00, // call 0 (print_i32)
        
        0x20, 0x01, // get_local 1 (index)
        0x41, 0x01, // i32.const 1
        0x6A, // i32.add
        0x21, 0x01, // set_local 1 (index)

        0x20, 0x01, // get_local 1 (index)
        0x20, 0x00, // get_local 0 (length)
        0x48, // i32.lt_s 

        0x0D, 0x00, // br_if 0

        0x0B, // end
        0x0B, // end

        0x20, 0x02, // get_local 2 (sum)        

        // call print_i32 -- call the imported function to print the result
        0x10, 0x00, // call 0

        // end -- end the function
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