import { readFileSync } from "fs";

// to run, 
// node pseudo-testing/bin/run_program_wasm.js

const wasmBytes = readFileSync("./pseudo-testing/bin/program.wasm");

const imports = {
    env: {
        print_i32: (value) => {
            console.log(value);
        },
        print_f32: (value) => {
            console.log(value);
        },
    },
};

const wasmModule = await WebAssembly.instantiate(wasmBytes, imports);
const instance = wasmModule.instance;

instance.exports.main();