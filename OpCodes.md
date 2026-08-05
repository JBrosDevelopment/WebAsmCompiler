
# Web Assembly Opcodes

## Control Flow

| Opcode | Hex | Description |
|---|---:|---|
| `unreachable` | `0x00` | Trap execution immediately |
| `nop` | `0x01` | Does nothing |
| `block` | `0x02` | Creates a branch target for exiting a block |
| `loop` | `0x03` | Creates a branch target for looping back |
| `if` | `0x04` | Executes a block conditionally |
| `else` | `0x05` | Begins the else branch |
| `end` | `0x0B` | Ends a block, loop, or if |
| `br` | `0x0C` | Unconditionally branches to a control-flow depth |
| `br_if` | `0x0D` | Branches if the stack condition is non-zero |
| `return` | `0x0F` | Returns from the current function |

## Functions

| Opcode | Hex | Description |
|---|---:|---|
| `call` | `0x10` | Calls a function by function index |
| `call_indirect` | `0x11` | Calls a function through a function table |

## Locals

| Opcode | Hex | Description |
|---|---:|---|
| `local.get` | `0x20` | Pushes a local variable's value onto the stack |
| `local.set` | `0x21` | Pops a value from the stack and stores it in a local |
| `local.tee` | `0x22` | Stores a value in a local while keeping it on the stack |

## Constants

| Opcode | Hex | Description |
|---|---:|---|
| `i32.const` | `0x41` | Pushes a 32-bit integer |
| `i64.const` | `0x42` | Pushes a 64-bit integer |
| `f32.const` | `0x43` | Pushes a 32-bit floating-point value |
| `f64.const` | `0x44` | Pushes a 64-bit floating-point value |

## i32 Arithmetic

| Opcode | Hex | Description |
|---|---:|---|
| `i32.add` | `0x6A` | Adds two i32 values |
| `i32.sub` | `0x6B` | Subtracts two i32 values |
| `i32.mul` | `0x6C` | Multiplies two i32 values |
| `i32.div_s` | `0x6D` | Signed integer division |
| `i32.div_u` | `0x6E` | Unsigned integer division |
| `i32.rem_s` | `0x6F` | Signed remainder |
| `i32.rem_u` | `0x70` | Unsigned remainder |

## i32 Comparisons

| Opcode | Hex | Description |
|---|---:|---|
| `i32.eqz` | `0x45` | Tests whether value is zero |
| `i32.eq` | `0x46` | Tests equality |
| `i32.ne` | `0x47` | Tests inequality |
| `i32.lt_s` | `0x48` | Signed less-than |
| `i32.lt_u` | `0x49` | Unsigned less-than |
| `i32.gt_s` | `0x4A` | Signed greater-than |
| `i32.gt_u` | `0x4B` | Unsigned greater-than |
| `i32.le_s` | `0x4C` | Signed less-than-or-equal |
| `i32.le_u` | `0x4D` | Unsigned less-than-or-equal |
| `i32.ge_s` | `0x4E` | Signed greater-than-or-equal |
| `i32.ge_u` | `0x4F` | Unsigned greater-than-or-equal |

## i32 Bitwise Operations

| Opcode | Hex | Description |
|---|---:|---|
| `i32.and` | `0x71` | Bitwise AND |
| `i32.or` | `0x72` | Bitwise OR |
| `i32.xor` | `0x73` | Bitwise XOR |
| `i32.shl` | `0x74` | Shift left |
| `i32.shr_s` | `0x75` | Signed shift right |
| `i32.shr_u` | `0x76` | Unsigned shift right |
| `i32.rotl` | `0x77` | Rotate bits left |
| `i32.rotr` | `0x78` | Rotate bits right |

## Memory Loads

| Opcode | Hex | Description |
|---|---:|---|
| `i32.load` | `0x28` | Loads a 32-bit integer from memory |
| `i64.load` | `0x29` | Loads a 64-bit integer from memory |
| `f32.load` | `0x2A` | Loads a 32-bit float from memory |
| `f64.load` | `0x2B` | Loads a 64-bit float from memory |
| `i32.load8_s` | `0x2C` | Loads an 8-bit signed integer |
| `i32.load8_u` | `0x2D` | Loads an 8-bit unsigned integer |
| `i32.load16_s` | `0x2E` | Loads a 16-bit signed integer |
| `i32.load16_u` | `0x2F` | Loads a 16-bit unsigned integer |

## Memory Stores

| Opcode | Hex | Description |
|---|---:|---|
| `i32.store` | `0x36` | Stores a 32-bit integer |
| `i64.store` | `0x37` | Stores a 64-bit integer |
| `f32.store` | `0x38` | Stores a 32-bit float |
| `f64.store` | `0x39` | Stores a 64-bit float |
| `i32.store8` | `0x3A` | Stores the lowest 8 bits |
| `i32.store16` | `0x3B` | Stores the lowest 16 bits |

## Boolean Operations

| Opcode | Hex | Description |
|---|---:|---|
| `i32.eqz` | `0x45` | Logical NOT when using 0/1 booleans |
| `i32.and` | `0x71` | Boolean/bitwise AND |
| `i32.or` | `0x72` | Boolean/bitwise OR |
| `i32.xor` | `0x73` | Boolean/bitwise XOR |

## f32 Arithmetic

| Opcode | Hex | Description |
|---|---:|---|
| `f32.abs` | `0x8B` | Absolute value |
| `f32.neg` | `0x8C` | Negate |
| `f32.add` | `0x92` | Add |
| `f32.sub` | `0x93` | Subtract |
| `f32.mul` | `0x94` | Multiply |
| `f32.div` | `0x95` | Divide |

## f32 Comparisons

| Opcode | Hex | Description |
|---|---:|---|
| `f32.eq` | `0x5B` | Equal |
| `f32.ne` | `0x5C` | Not equal |
| `f32.lt` | `0x5D` | Less than |
| `f32.gt` | `0x5E` | Greater than |
| `f32.le` | `0x5F` | Less than or equal |
| `f32.ge` | `0x60` | Greater than or equal |

## Type Conversions

| Opcode | Hex | Description |
|---|---:|---|
| `i32.wrap_i64` | `0xA7` | Converts i64 to i32 |
| `i64.extend_i32_s` | `0xAC` | Sign-extends i32 to i64 |
| `f32.convert_i32_s` | `0xB2` | Converts signed i32 to f32 |
| `f64.convert_i32_s` | `0xB7` | Converts signed i32 to f64 |
| `i32.trunc_f32_s` | `0xA8` | Converts f32 to signed i32 |
| `i32.trunc_f64_s` | `0xAA` | Converts f64 to signed i32 |

## Function Tables

| Opcode | Hex | Description |
|---|---:|---|
| `call_indirect` | `0x11` | Calls a function selected from a function table |

## WASM GC Structs

| Instruction | Description |
|---|---|
| `struct.new` | Creates a WASM GC struct from values on the stack |
| `struct.get` | Reads a field from a WASM GC struct |
| `struct.set` | Writes a field in a WASM GC struct |

> Note: `struct.new`, `struct.get`, and `struct.set` are part of WebAssembly GC/reference-types functionality. They are different from the linear-memory struct approach using `i32.load` and `i32.store`.