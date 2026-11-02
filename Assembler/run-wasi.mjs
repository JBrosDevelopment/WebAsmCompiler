import { readFile } from 'node:fs/promises';
import { WASI } from 'node:wasi';

const wasmPath = process.argv[2];

if (!wasmPath) {
    throw new Error('Supply a WASM file path');
}

const wasi = new WASI({
    version: 'preview1',
    args: [wasmPath, ...process.argv.slice(3)],
});

const wasmBytes = await readFile(wasmPath);

const { instance } = await WebAssembly.instantiate(
    wasmBytes,
    wasi.getImportObject(),
);

process.exitCode = wasi.start(instance);