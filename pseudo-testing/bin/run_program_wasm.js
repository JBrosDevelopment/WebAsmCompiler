import { readFileSync } from "fs";

const wasmBytes = readFileSync("./pseudo-testing/bin/program.wasm");

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