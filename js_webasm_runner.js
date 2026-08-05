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

    // calls the exported main function to begin the program
    instance.exports.main();
}

function createWasmFile() {
    const wasmBytes = new Uint8Array([

        // HEADER
        0x00, 0x61, 0x73, 0x6D, // magic number
        0x01, 0x00, 0x00, 0x00, // version

        // TYPE
        0x01, 0x08,  // 01 = Type Section, 08= length of section in `8` bytes
        0x02, // There are 2 function types

        // print_i32(i32) -> void
        0x60, 0x01, 0x7F, 0x00, // 60=function type, 01=1 parameter, 7F=i32, 00=0 return values
        
        // main() -> void
        0x60, 0x00, 0x00, // 60=function type, 00=0 parameters, 00=0 return values

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

        // main() -> void
        0x01, // 01 = 1 function
        0x01, // 01 = type index (1)

        // EXPORT
        0x07, 0x08, // 07 = Export Section, 08= length of section in `8` bytes
        0x01, // 01 = 1 export

        // expoort "main"
        0x04, 0x6D, 0x61, 0x69, 0x6E, // 04 = length of export name, "main"; rest = "main"
        0x00, 0x01, // 00 = export kind (function), 01 = function index (1)

        // CODE SECTION

        0x0A, 0x0B, // 0A = Code Section, 08= length of section in `11` bytes
        
        // main()
        0x01, // 01 = function body of function `1` (main)
        0x09, // 09 = size of function body in `9` bytes
        0x00, // 00 = local variable count (0)

        // i32.const 6 -- push 6 onto the stack
        0x41, 0x06, // 41 = i32.const, 06 = value 6

        // i32.const 7 -- push 7 onto the stack
        0x41, 0x07, // 41 = i32.const, 07 = value 7

        // add i32 -- add the two values on the stack
        0x6A, // 6A = i32.add

        // call print_i32 -- call the imported function to print the result
        0x10, 0x00, // 10 = call, 00 = function index (print_i32)

        // end -- end the function
        0x0B // 0B = end
    ]);

    fs.writeFileSync('./program.wasm', wasmBytes);
}

// create the wasm file
createWasmFile();

// run the main function and catch any errors
main().catch(err => {
    console.error(err);
});