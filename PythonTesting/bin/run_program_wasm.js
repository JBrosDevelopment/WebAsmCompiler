import { readFileSync } from "fs";

// to run, 
// node PythonTesting/bin/run_program_wasm.js

const wasmBytes = readFileSync("./PythonTesting/bin/test_defines.wasm");

const imports = {
    env: {
        print_i32: (value) => {
            console.log(value);
        },
        print_i64: (value) => {
            console.log(value);
        },
        print_f32: (value) => {
            console.log(value);
        },
        print_f64: (value) => {
            console.log(value);
        },
    },
};

const wasmModule = await WebAssembly.instantiate(wasmBytes, imports);
const instance = wasmModule.instance;

instance.exports.main();