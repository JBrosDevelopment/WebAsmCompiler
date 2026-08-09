// Using this file to calculate the bytes needed to encode a number
// node .\encodeULEB128.js [whatever_value]


let value = parseInt(process.argv[2], 10);

const bytes = [];

do {
    let byte = value & 0x7F;
    value >>>= 7;

    if (value !== 0)
        byte |= 0x80;

    bytes.push(byte);
} while (value !== 0);

console.log(bytes);