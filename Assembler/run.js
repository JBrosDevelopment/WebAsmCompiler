import { readFileSync } from "fs";

// to run, 
// node Assembler/run.js [filename.wasm]

const default_file = "Assembler/bin/assembler.0.0.wal.wasm";

const file = process.argv.length > 2 ? process.argv[2] : default_file;

const wasmBytes = readFileSync(file);

const imports = {
    env: {
        print_i32: (value) => {
            console.log(value);
        },
    },
};

const wasmModule = await WebAssembly.instantiate(wasmBytes, imports);
const instance = wasmModule.instance;

instance.exports.main();