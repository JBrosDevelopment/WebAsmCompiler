const fs = require('fs');

async function main() {
    const wasmBytes = fs.readFileSync('./program.wasm');
    const outputFile = fs.createWriteStream('./bin/mainFunction.output.wasm');

    // This is for import functions to be exposed in WebAsm
    const imports = {
        env: {
            print_i32: (value) => {
                console.log(value);
            },
            write_char: (value) => {
                console.log('write:', value);
                outputFile.write(Buffer.from([value]));
            }
        }
    }

    const wasmModule = await WebAssembly.instantiate(wasmBytes, imports);

    const instance = wasmModule.instance;

    // handle inserting data to memory
    const memory = instance.exports.memory;
    const bytes = new Uint8Array(memory.buffer);
    
    const replaceBytes = fs.readFileSync('./cwa/mainFunction.cwa');

    for (let i = 0; i < replaceBytes.length; i++) {
        bytes[i] = replaceBytes[i];
    }

    // calls the exported main function to begin the program
    instance.exports.main();

    outputFile.end();
}

function cmd(input) {
    if (input == 'i32.add') { return 0x6A }
    else if (input == 'i32.sub') { return 0x6B }
    else if (input == 'i32.mul') { return 0x6C }
    else if (input == 'i32.and') { return 0x71 }
    else if (input == 'i32.or') { return 0x72 }
    else if (input == 'i32.shr_u') { return 0x76 }
    else if (input == 'i32.const') { return 0x41 }
    else if (input == 'call') { return 0x10 }
    else if (input == 'local.get') { return 0x20 }
    else if (input == 'local.set') { return 0x21 }
    else if (input == 'i32.load8_u') { return 0x2D }
    else if (input == 'if') { return 0x04 }
    else if (input == 'else') { return 0x05 }
    else if (input == 'block') { return 0x02 }
    else if (input == 'loop') { return 0x03 }
    else if (input == 'end') { return 0x0B }
    else if (input == 'i32.eq') { return 0x46 }
    else if (input == 'i32.nq') { return 0x47 }
    else if (input == 'i32.lt_u') { return 0x49 }
    else if (input == 'i32.le_u') { return 0x4D }
    else if (input == 'i32.gt_u') { return 0x4B }
    else if (input == 'i32.ge_u') { return 0x4F }
    else if (input == 'br') { return 0x0C }
    else if (input == 'br_if') { return 0x0D }
    else if (input == 'return') { return 0x0F }
    console.error("Command, " + input + ", not found.");
    process.exit(1);
}

function ULEB128(number) {
    const bytes = [];
    while (number > 0) {
        const byte = number & 0x7F;
        number >>>= 7;
        if (number > 0) {
            bytes.push(byte | 0x80);
        } else {
            bytes.push(byte);
        }
    }
    return bytes;
}

function SLEB128(value) {
    const bytes = [];
    value |= 0;

    let more = true;

    while (more) {
        let byte = value & 0x7F;
        value >>= 7;
        if ((value === 0 && (byte & 0x40) === 0) || (value === -1 && (byte & 0x40) !== 0)) {
            more = false;
        } else {
            byte |= 0x80;
        }

        bytes.push(byte);
    }

    return bytes;
}

function createWasmFile() {
    const functions = {print_i32: 0, write_char: 1, main: 2, WordToCMD: 3, WordToI32: 4, IntoULEB128: 5, WriteULEB128: 6};
    const b1 = [
        // HEADER
        0x00, 0x61, 0x73, 0x6D, // magic number
        0x01, 0x00, 0x00, 0x00, // version

        // TYPE
        0x01, 27, // 01 = Type Section, = length of section in bytes
        0x06, // function type count

        // print_i32(i32) -> void
        0x60, 0x01, 0x7F, 0x00, // 60=function type, 01=1 parameter, 7F=i32, 00=0 return values

        // write_char(i32) -> void
        0x60, 0x01, 0x7F, 0x00, // 60=function type, 01=1 parameter, 7F=i32, 00=0 return values
        
        // main() -> void
        0x60, 0x00, 0x00, // 60=function type, 00=0 parameters, 00=0 return values
        
        // WordToCMD(), WordToI32() -> i32
        0x60, 0x02, 0x7F, 0x7F, 0x01, 0x7F, // 60=function type, 0x02=2 parameters, 7F=param1 i32, 7F=param2 i32, 1=returns value, 7F=returns i32
        
        // IntoULEB128() -> i32
        0x60, 0x01, 0x7F, 0x01, 0x7F, // 60=function type, 01=1 parameter, 7F=i32, 1=returns value, 7F=returns i32
        
        // WriteULEB128() -> void
        0x60, 0x01, 0x7F, 0x00, // 60=function type, 01=1 parameter, 7F=i32, 00=0 return values

        // IMPORT
        0x02, 34, // 02 = Import Section, = length of section in bytes
        0x02, // = imports
        
        // inside "env" module
        0x03, 0x65, 0x6E, 0x76, // 03 = length of module name, "env"; rest = "env"
        // import "print_i32" -> void
        0x09, 0x70, 0x72, 0x69, 0x6E, 0x74, 0x5F, 0x69, 0x33, 0x32, // 09= length of function name, "print_i32"; rest = "print_i32"
        0x00, 0x00, // 00 = import kind (function), 00 = type index (0)

        // inside "env" module
        0x03, 0x65, 0x6E, 0x76,
        // import "write_char" -> void
        0x0A, 0x77, 0x72, 0x69, 0x74, 0x65, 0x5F, 0x63, 0x68, 0x61, 0x72, // 0A= length of function name, "write_char"; rest = "write_char"
        0x00, 0x01, // 00 = import kind (function), 01 = type index (1)

        // FUNCTION
        0x03, 6, // 03 = Function Section, = length of section in bytes
        0x05, // =function count

        0x02, // = type index -- main()
        0x03, // = type index -- WordToCMD()
        0x03, // = type index -- WordToI32()
        0x04, // = type index -- IntoULEB128()
        0x05, // = type index -- WriteULEB128()

        // MEMORY
        0x05, 3, // 05 = Memory Section, = length of section in bytes
        0x01, // 01 = 1 page of memory (65,536 bytes)
        0x00, 0x01, // 00 = limit flags (0 = no max), 01 = minumum size (1)

        // EXPORT
        0x07, 17, // 07 = Export Section, = length of section in bytes
        0x02, // 02 = 2 exports

        // expoort "main"
        0x04, 0x6D, 0x61, 0x69, 0x6E, // 04 = length of export name, "main"; rest = "main"
        0x00, 0x02, // 00 = export kind (function), function index 
        
        // export "memory"
        0x06, 0x6D, 0x65, 0x6D, 0x6F, 0x72, 0x79, // 06 = length of export name, "memory"; rest = "memory"
        0x02, 0x00, // 02 = export kind (memory), 00 = memory index (0)

        // CODE SECTION
        0x0A
    ];
    const b3 = [
        0x05, // = Number of functions
    ];
    const mainVars = { 
        bytes: 0,
        char: 1,
        cmd: 2,
        number: 3,
        startWord: 4,
        wordLength: 5,
        stateCMD: 6,
    }
    const b5_main = [
        1, // = local variable declaration group count
        0x07, 0x7F, // byets, char, cmd, number, startWord, wordLength, stateCMD

    //    block loop:
    //    char = memory[bytes]
    //    bytes = bytes + 1
    //
    //    if char == ENDOFFILEBYTE {
    //        break
    //    }
    //
    //    if char == '\n' as i32 || char == '\r' as i32 {
    //        stateCMD = 1 // next byte is command
    //        startWord = bytes + 1
    //        goto loop
    //    }
    //    if char == ' ' as i32 || char == '\t' as i32 || char == ';' as i32 {
    //        if stateCMD == 2 { // End Of Command
    //            stateCMD = 0
    //            cmd = WordToCMD(startWord, wordLength)
    //            if cmd == 0xFB { // check for error
    //                print_i32(0xFB)
    //                return
    //            }
    //            write_char(cmd)
    //        }
    //        else if stateCMD == 0 { // End Of Argument
    //            number = WordToI32(startWord, wordLength)
    //            if number == 0xFC { // check for error
    //                print_i32(0xFC)
    //                return
    //            }
    //            writeULEB128(number)
    //        }
    //        startWord = bytes
    //        wordLength = 0
    //        goto loop
    //    }
    //    if (char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') || (char >= '0' && char <= '9') || char == '_' {
    //        if stateCMD == 1 {
    //            stateCMD = 2
    //        }
    //        wordLength = wordLength + 1
    //    } else {
    //        print_i32(0xFD) // error code invalid char
    //        return
    //    }
    //    goto loop
    //end
    //// END OF FILE SEQUENCE
    //write_char(0xFE)
    //write_char(0xFE)
    //
    //print_i32(bytes)
    
        cmd('i32.const'), 1,
        cmd('local.set'), mainVars['stateCMD'],

        cmd('block'), 0x40, // block -> null
            cmd('loop'), 0x40, // loop -> null
            
            // char = memory[bytes]
            cmd('local.get'), mainVars['bytes'],
            cmd('i32.load8_u'), 0, 0,
            cmd('local.set'), mainVars['char'],

            // bytes = bytes + 1
            cmd('local.get'), mainVars['bytes'], 
            cmd('i32.const'), 1, 
            cmd('i32.add'), 
            cmd('local.set'), mainVars['bytes'], 

            // char == 0xFE (EOF) || char == `|` as i32 (this is for ascii character for easaier writing cwa file)
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...ULEB128(0xFE),
            cmd('i32.eq'),
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...ULEB128('|'.charCodeAt(0)),
            cmd('i32.eq'),
            cmd('i32.or'),
            cmd('br_if'), 1, // br_if (loop=0, block=1)

            //if char == '\n' || char == '\r' { stateCMD = 1; startWord = bytes + 1; goto loop }
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...ULEB128('\n'.charCodeAt(0)),
            cmd('i32.eq'),
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...ULEB128('\r'.charCodeAt(0)),
            cmd('i32.eq'),
            cmd('i32.or'),
            cmd('if'), 0x40, // if -> null
                cmd('i32.const'), 1,
                cmd('local.set'), mainVars['stateCMD'],

                cmd('local.get'), mainVars['bytes'],
                cmd('local.set'), mainVars['startWord'],
                
                // goto loop
                cmd('br'), 1, // (if=0, loop=1, block=2)
            cmd('end'), // end [if]

            // if char == ' ' || char == '\t' || char == ';'
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...ULEB128(' '.charCodeAt(0)),
            cmd('i32.eq'),
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...ULEB128('\t'.charCodeAt(0)),
            cmd('i32.eq'),
            cmd('i32.or'),
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...ULEB128(';'.charCodeAt(0)),
            cmd('i32.eq'),
            cmd('i32.or'),
            cmd('if'), 0x40, // if -> null
                // if stateCMD == 2
                cmd('local.get'), mainVars['stateCMD'],
                cmd('i32.const'), 2,
                cmd('i32.eq'),
                cmd('if'), 0x40, // if -> null
                    // stateCMD = 0
                    cmd('i32.const'), 0,
                    cmd('local.set'), mainVars['stateCMD'],

                    // cmd = WordToCMD(startWord, wordLength)
                    cmd('local.get'), mainVars['startWord'],
                    cmd('local.get'), mainVars['wordLength'],
                    cmd('call'), functions['WordToCMD'],
                    cmd('local.set'), mainVars['cmd'],
                    
                    // if cmd == 0xFB { print_i32(0xFB); return; }
                    cmd('local.get'), mainVars['cmd'],
                    cmd('i32.const'), ...ULEB128(0xFB),
                    cmd('i32.eq'),
                    cmd('if'), 0x40, // if -> null
                        cmd('local.get'), mainVars['startWord'],
                        cmd('call'), functions['print_i32'],

                        cmd('i32.const'), ...ULEB128(0xFB),
                        cmd('call'), functions['print_i32'],
                        cmd('return'),
                    cmd('end'), // end [if]

                    // write_char(cmd)
                    cmd('local.get'), mainVars['cmd'],
                    cmd('call'), functions['write_char'],
                cmd('else'),
                    // if stateCMD == 0
                    cmd('local.get'), mainVars['stateCMD'],
                    cmd('i32.const'), 0,
                    cmd('i32.eq'),
                    cmd('if'), 0x40, // if -> null
                        // number = WordToI32(startWord, wordLength)
                        cmd('local.get'), mainVars['startWord'],
                        cmd('local.get'), mainVars['wordLength'],
                        cmd('call'), functions['WordToI32'],
                        cmd('local.set'), mainVars['number'],
                        
                        // if number == 0xFC { print_i32(0xFC); return; }
                        cmd('local.get'), mainVars['number'],
                        cmd('i32.const'), ...ULEB128(0xFC),
                        cmd('i32.eq'),
                        cmd('if'), 0x40, // if -> null
                            cmd('local.get'), mainVars['startWord'],
                            cmd('call'), functions['print_i32'],

                            cmd('i32.const'), ...ULEB128(0xFC),
                            cmd('call'), functions['print_i32'],
                            cmd('return'),
                        cmd('end'), // end [if]

                        // writeULEB128(number)
                        cmd('local.get'), mainVars['number'],
                        cmd('call'), functions['WriteULEB128'],
                    cmd('end'), // end [if]
                cmd('end'), // end [if]
                
                // startWord = bytes
                cmd('local.get'), mainVars['bytes'],
                cmd('local.set'), mainVars['startWord'],

                // wordLength = 0
                cmd('i32.const'), 0,
                cmd('local.set'), mainVars['wordLength'],

                // goto loop
                cmd('br'), 1, // (if=0, loop=1, block=2)
            cmd('end'), // end [if]

            // if (char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') || (char >= '0' && char <= '9') || char == '_'
            // (char >= 'a' && char <= 'z')
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...SLEB128('a'.charCodeAt(0)),
            cmd('i32.ge_u'), // pushes 1
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...SLEB128('z'.charCodeAt(0)),
            cmd('i32.le_u'), // pushes 1
            cmd('i32.and'), // pops both and pushes 1
            // stack: (assuming char is letter a-z)
            // | --- |
            // |  1  |
            // | --- |
            // (char >= 'A' && char <= 'Z')
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...SLEB128('A'.charCodeAt(0)),
            cmd('i32.ge_u'), // pushes 1
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...SLEB128('Z'.charCodeAt(0)),
            cmd('i32.le_u'), // pushes 1
            cmd('i32.and'), // pops both and pushes 1
            // stack: (assuming char is letter a-z)
            // | --- | --- |
            // |  1  |  0  |
            // | --- | --- |
            // (char >= '0' && char <= '9')
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...SLEB128('0'.charCodeAt(0)),
            cmd('i32.ge_u'), // pushes 0
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...SLEB128('9'.charCodeAt(0)),
            cmd('i32.le_u'), // pushes 0
            cmd('i32.and'), // pops both and pushes 0
            // stack: (assuming char is letter a-z)
            // | --- | --- | --- |
            // |  1  |  0  |  0  |
            // | --- | --- | --- |
            // char == '_'
            cmd('local.get'), mainVars['char'],
            cmd('i32.const'), ...SLEB128('_'.charCodeAt(0)),
            cmd('i32.eq'), // pushes 0
            // stack: (assuming char is letter a-z)
            // | --- | --- | --- | --- |
            // |  1  |  0  |  0  |  0  |
            // | --- | --- | --- | --- |
            cmd('i32.or'),
            // | --- | --- | --- |
            // |  1  |  0  |  0  |
            // | --- | --- | --- |
            cmd('i32.or'),
            // | --- | --- |
            // |  1  |  0  |
            // | --- | --- |
            cmd('i32.or'),
            // | --- |
            // |  1  |
            // | --- |
            cmd('if'), 0x40, // if -> null
                // if stateCMD == 1 { stateCMD = 2 }
                cmd('local.get'), mainVars['stateCMD'],
                cmd('i32.const'), 1,
                cmd('i32.eq'),
                cmd('if'), 0x40, // if -> null
                    cmd('i32.const'), 2,
                    cmd('local.set'), mainVars['stateCMD'],
                cmd('end'), // end [if]

                // wordLength = wordLength + 1
                cmd('local.get'), mainVars['wordLength'],
                cmd('i32.const'), 1,
                cmd('i32.add'),
                cmd('local.set'), mainVars['wordLength'],
            cmd('else'),
                // print_i32(0xFD)
                cmd('local.get'), mainVars['char'],
                cmd('call'), functions['print_i32'],
                cmd('i32.const'), ...ULEB128(0xFD),
                cmd('call'), functions['print_i32'],
                // return
                cmd('return'),
            cmd('end'), // end [if]

            cmd('br'), 0, // br (loop=0, block=1)

            cmd('end'), // end [loop]
        cmd('end'), // end [block]

        // print_i32(bytes)
        cmd('local.get'), mainVars['bytes'],
        cmd('call'), functions['print_i32'], 

        cmd('end') // end
    ];

    const wordToCMDVars = { startWord: 0, wordLength: 1 };
    const b7_WordToCMD = [
        0, // = local variable declaration group count

        //if wordLength == 3 && memory[startWord] == 'a' && memory[startWord + 1] == 'd' && memory[startWord + 2] == 'd' {
        //    return 0x6A // opcode for `i32.add`
        //}
        //return 0xFB

        // add
        //////////////////////////////////////////////////////////////////////////
        // wordLength == 3
        cmd('i32.const'), 3, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        // memory[startWord] == 'a'
        cmd('i32.const'), ...SLEB128('a'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        // memory[startWord + 1] == 'd'
        cmd('i32.const'), ...SLEB128('d'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        // memory[startWord + 2] == 'd'
        cmd('i32.const'), ...SLEB128('d'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x6A), // opcode for `i32.add`
        cmd('return'), 
        cmd('end'), // end [if]
        //////////////////////////////////////////////////////////////////////////

        /// mul //////////////////////////////////////////////////////////////////
        cmd('i32.const'), 3, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('m'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('u'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x6C), // opcode for `i32.mul`
        cmd('return'), 
        cmd('end'), // end [if]

        /// sub //////////////////////////////////////////////////////////////////
        cmd('i32.const'), 3, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('s'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('u'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('b'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x6B), // opcode for `i32.sub`
        cmd('return'), 
        cmd('end'), // end [if]

        /// and //////////////////////////////////////////////////////////////////
        cmd('i32.const'), 3, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('a'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('n'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('d'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x71), // opcode for `i32.and`
        cmd('return'), 
        cmd('end'), // end [if]

        /// or ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('o'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('r'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x72), // opcode for `i32.or`
        cmd('return'), 
        cmd('end'), // end [if]

        /// shr //////////////////////////////////////////////////////////////////
        cmd('i32.const'), 3, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('s'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('h'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('r'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x76), // opcode for `i32.shr_u`
        cmd('return'), 
        cmd('end'), // end [if]

        /// const ////////////////////////////////////////////////////////////////
        cmd('i32.const'), 5, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('c'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('o'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('n'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('s'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 3, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('t'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 4, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x41), // opcode for `i32.const`
        cmd('return'), 
        cmd('end'), // end [if]

        /// call /////////////////////////////////////////////////////////////////
        cmd('i32.const'), 4, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('c'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('a'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 3, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x10), // opcode for `call`
        cmd('return'), 
        cmd('end'), // end [if]

        /// set //////////////////////////////////////////////////////////////////
        cmd('i32.const'), 3, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('s'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('t'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x21), // opcode for `local.set`
        cmd('return'), 
        cmd('end'), // end [if]

        /// get //////////////////////////////////////////////////////////////////
        cmd('i32.const'), 3, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('g'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('t'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x20), // opcode for `local.get`
        cmd('return'), 
        cmd('end'), // end [if]

        /// load /////////////////////////////////////////////////////////////////
        cmd('i32.const'), 4, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('o'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('a'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('d'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 3, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x2D), // opcode for `load`
        cmd('return'), 
        cmd('end'), // end [if]

        /// if ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('i'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('f'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x04), // opcode for `if`
        cmd('return'), 
        cmd('end'), // end [if]

        /// else /////////////////////////////////////////////////////////////////
        cmd('i32.const'), 4, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('s'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 3, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x05), // opcode for `else`
        cmd('return'), 
        cmd('end'), // end [if]

        /// block ////////////////////////////////////////////////////////////////
        cmd('i32.const'), 5, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('b'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('o'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('c'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 3, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('k'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 4, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x02), // opcode for `block`
        cmd('return'), 
        cmd('end'), // end [if]

        /// loop /////////////////////////////////////////////////////////////////
        cmd('i32.const'), 4, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('o'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('o'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('p'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 3, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x03), // opcode for `loop`
        cmd('return'), 
        cmd('end'), // end [if]

        /// end //////////////////////////////////////////////////////////////////
        cmd('i32.const'), 3, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('n'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('d'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x0B), // opcode for `end`
        cmd('return'), 
        cmd('end'), // end [if]

        /// br ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('b'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('r'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0xC4), // opcode for `br`
        cmd('return'), 
        cmd('end'), // end [if]

        /// br_if ////////////////////////////////////////////////////////////////
        cmd('i32.const'), 5, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('b'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('r'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('_'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('i'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 3, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('f'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 4, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x0D), // opcode for `br_if`
        cmd('return'), 
        cmd('end'), // end [if]

        /// return ////////////////////////////////////////////////////////////////
        cmd('i32.const'), 6, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('r'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('t'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 2, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('u'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 3, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('r'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 4, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('n'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 5, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x0F), // opcode for `return`
        cmd('return'), 
        cmd('end'), // end [if]

        /// eq ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('q'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x46), // opcode for `i32.eq`
        cmd('return'), 
        cmd('end'), // end [if]

        /// nq ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('n'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('q'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x47), // opcode for `i32.nq_u`
        cmd('return'), 
        cmd('end'), // end [if]

        /// lt ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('t'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x49), // opcode for `i32.eq_u`
        cmd('return'), 
        cmd('end'), // end [if]

        /// le ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('l'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x4D), // opcode for `i32.le_u`
        cmd('return'), 
        cmd('end'), // end [if]

        /// gt ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('g'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('t'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x4B), // opcode for `i32.gt_u`
        cmd('return'), 
        cmd('end'), // end [if]

        /// ge ///////////////////////////////////////////////////////////////////
        cmd('i32.const'), 2, // stackLength: 1
        cmd('local.get'), wordToCMDVars['wordLength'], // stackLength: 2 
        cmd('i32.eq'), // stackLength: 1
        cmd('i32.const'), ...SLEB128('g'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stack length 1
        cmd('i32.const'), ...SLEB128('e'.charCodeAt(0)), // stackLength: 2
        cmd('local.get'), wordToCMDVars['startWord'], // stackLength: 3
        cmd('i32.const'), 1, // stackLength: 4
        cmd('i32.add'), // stackLength: 3
        cmd('i32.load8_u'), 0, 0, // stackLength: 3
        cmd('i32.eq'), // stackLength: 2
        cmd('i32.and'), // stackLength: 1
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...SLEB128(0x4F), // opcode for `i32.ge_u`
        cmd('return'), 
        cmd('end'), // end [if]
        
        cmd('i32.const'), ...ULEB128(0xFB), // error code
        cmd('return'),

        cmd('end')
    ];
    const wordToI32Vars = { startWord: 0, wordLength: 1, char: 2, digit: 3, product: 4, index: 5 };
    const b9_WordToI32 = [
        1, // = local variable declaration group count
        0x04, 0x7F, // char, digit, product, index

        cmd('loop'), 0x40, // loop -> void

        //char = memory[startWord + index]
        //
        //if char < '0' as i32 || char > '9' {
        //    return 0xFC
        //}
        //
        //digit = char - 48
        //product = product * 10 + digit
        //
        //index = index + 1
        //if index < wordLength {
        //    goto loop
        //}

        // char = memory[startWord + index]
        cmd('local.get'), wordToI32Vars['startWord'],
        cmd('local.get'), wordToI32Vars['index'],
        cmd('i32.add'),
        cmd('i32.load8_u'), 0, 0,
        cmd('local.set'), wordToI32Vars['char'],

        // if char < '0' as i32 || char > '9' { return 0xFC }
        cmd('local.get'), wordToI32Vars['char'],
        cmd('i32.const'), 48,
        cmd('i32.lt_u'),
        cmd('local.get'), wordToI32Vars['char'],
        cmd('i32.const'), 57,
        cmd('i32.gt_u'),
        cmd('i32.or'),
        cmd('if'), 0x40, // if -> void
        cmd('i32.const'), ...ULEB128(0xFC), // error code
        cmd('return'), 
        cmd('end'), // end [if]

        // digit = char - 48
        cmd('local.get'), wordToI32Vars['char'],
        cmd('i32.const'), 48,
        cmd('i32.sub'),
        cmd('local.set'), wordToI32Vars['digit'],

        // product = product * 10 + digit
        cmd('local.get'), wordToI32Vars['product'],
        cmd('i32.const'), 10,
        cmd('i32.mul'),
        cmd('local.get'), wordToI32Vars['digit'],
        cmd('i32.add'),
        cmd('local.set'), wordToI32Vars['product'],

        // index = index + 1
        cmd('local.get'), wordToI32Vars['index'],
        cmd('i32.const'), 1,
        cmd('i32.add'),
        cmd('local.set'), wordToI32Vars['index'],

        // index < wordLength
        cmd('local.get'), wordToI32Vars['index'],
        cmd('local.get'), wordToI32Vars['wordLength'],
        cmd('i32.lt_u'),
        cmd('br_if'), 0x00, // (loop=0) branches to loop

        cmd('end'),

        cmd('local.get'), wordToI32Vars['product'],
        cmd('return'),

        cmd('end')
    ];
    const intoULEB128Vars = { number: 0, byte: 1 };
    const b11_IntoULEB128 = [
        1, // = local variable declaration group count
        0x01, 0x7F, // byte

        //var byte: i32 = number & 0x7F
        //if number >= 128 {
        //    byte = byte | 0x80
        //}
        //return byte

        // byte = number & 0x7F
        cmd('local.get'), intoULEB128Vars['number'],
        cmd('i32.const'), ...SLEB128(127),
        cmd('i32.and'),
        cmd('local.set'), intoULEB128Vars['byte'],

        // if number >= 128 { byte = byte | 0x80 }
        cmd('local.get'), intoULEB128Vars['number'],
        cmd('i32.const'), ...ULEB128(128),
        cmd('i32.ge_u'),
        cmd('if'), 0x40, // if -> void
        cmd('local.get'), intoULEB128Vars['byte'],
        cmd('i32.const'), ...ULEB128(0x80),
        cmd('i32.or'),
        cmd('local.set'), intoULEB128Vars['byte'],
        cmd('end'), // end [if]

        // return byte
        cmd('local.get'), intoULEB128Vars['byte'],
        cmd('return'),

        cmd('end')
    ];
    const writeULEB128Vars = { number: 0, byte: 1 };
    const b13_WriteULEB128 = [
        1, // = local variable declaration group count
        0x01, 0x7F, // byte

        cmd('loop'), 0x40, // loop -> void

        //byte = IntoULEB128(number)
        //write_char(byte)
        //number = number >> 7
        //if number > 0 {
        //    goto loop
        //} // else, reaches 'end' and breaks

        // byte = IntoULEB128(number)
        cmd('local.get'), writeULEB128Vars['number'],
        cmd('call'), functions['IntoULEB128'],
        cmd('local.set'), writeULEB128Vars['byte'],

        // write_char(byte)
        cmd('local.get'), writeULEB128Vars['byte'],
        cmd('call'), functions['write_char'],

        // number = number >> 7
        cmd('local.get'), writeULEB128Vars['number'],
        cmd('i32.const'), 7,
        cmd('i32.shr_u'),
        cmd('local.set'), writeULEB128Vars['number'],

        // number > 0
        cmd('local.get'), writeULEB128Vars['number'],
        cmd('i32.const'), 0,
        cmd('i32.gt_u'),
        cmd('br_if'), 0x00, // (loop=0) branches to loop
        
        cmd('end'), // end [loop]

        cmd('end')
    ];

    const b4 = ULEB128(b5_main.length);
    const b6 = ULEB128(b7_WordToCMD.length);
    const b8 = ULEB128(b9_WordToI32.length);
    const b10 = ULEB128(b11_IntoULEB128.length);
    const b12 = ULEB128(b13_WriteULEB128.length);

    const b2 = ULEB128(b3.length + b4.length + b5_main.length + b6.length + b7_WordToCMD.length + b8.length + b9_WordToI32.length + b10.length + b11_IntoULEB128.length + b12.length + b13_WriteULEB128.length);
    
    const bytes = [...b1, ...b2, ...b3, ...b4, ...b5_main, ...b6, ...b7_WordToCMD, ...b8, ...b9_WordToI32, ...b10, ...b11_IntoULEB128, ...b12, ...b13_WriteULEB128];

    const wasmBytes = new Uint8Array(bytes);

    fs.writeFileSync('./program.wasm', wasmBytes);
}

// create the wasm file
createWasmFile();

// run the main function and catch any errors
main().catch(err => {
    console.error(err);
});