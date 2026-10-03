// to run the assembler.0.1 wasm and input the same program (assembler.0.1.wal) and output assembler.0.1.wasm2, which should be equal to the original
// node ./Assembler/bin/runner.js ./Assembler/assembler.0.1.wal ./Assembler/bin/assembler.0.1.wal.wasm2
// to assemble assembler.0.2.wal into assembler.0.2.wal.wasm from the assembler.0.1.wal.wasm assembler
// node ./Assembler/bin/runner.js ./Assembler/assembler.0.2.wal ./Assembler/bin/assembler.0.2.wal.wasm

import { readFileSync, writeFileSync } from 'fs';

const inputFile = 'Assembler/bin/assembler.0.2.wal.wasm';

const sourcePath = process.argv[2];
const outputPath = process.argv[3];

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