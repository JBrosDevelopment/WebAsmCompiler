// to run, node ./Assembler/assemble.js [version (ex: 0.1) or input file] [Assembler/ + input file] [Assembler/bin/ + output file]
// node ./Assembler/assemble.js 0.1 assembler.0.1.wal assembler.0.1.wal.wasm2
// node ./Assembler/assemble.js 0.1 assembler.0.1.wal assembler.0.2.wal.wasm

import { readFileSync, writeFileSync } from 'fs';

const default_version = "0.1";
const before_version = "Assembler/bin/assembler.";
const after_version = ".wal.wasm";
const bin_path = "Assembler/bin/";
const assembler_path = "Assembler/";

const input = process.argv.length > 2 ? process.argv[2] : default_version;
const version = /^\d+\.\d+$/.test(input) ? input : -1;
const inputFile = version === -1 ? input : before_version + version + after_version;

const sourcePath = assembler_path + process.argv[3];
const outputPath = bin_path + process.argv[4];

if (!sourcePath || !outputPath) 
    throw new Error('Supply input WAL and output WASM paths');

const text = readFileSync(sourcePath, 'utf8').replace(/\r\n?/g, '\n');
if (/[^\x00-\x7f]/.test(text)) 
    throw new Error('This assembler accepts ASCII source');

const source = Buffer.from(text, 'ascii');
if (source.length + 17 >= 4194304) 
    throw new Error('Input exceeds 4 MiB source region');

const output = [];

const module = new WebAssembly.Module(readFileSync(inputFile));

const instance = new WebAssembly.Instance(module, {
    env: {
        print_i32: n => process.stdout.write(String(n)),
        print_char: n => process.stdout.write(String.fromCharCode(n)),
        write_char: n => output.push(n),
        exit_program: n => {
          throw new Error('Assembler error ' + n);
        }
    }
});

const memory = new Uint8Array(instance.exports.memory.buffer);

memory.set(source); 
memory.fill(0, source.length, source.length + 17);

instance.exports.main();

writeFileSync(outputPath, Buffer.from(output));