import { readFileSync } from "fs";

// to run, 
// node Assembler/bin/run_wasm.js

const wasmBytes = readFileSync("Assembler/bin/assembler.0.0.wal.wasm");

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