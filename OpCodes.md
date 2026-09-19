# WebAssembly Opcodes

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

## Stack

| Opcode | Hex | Description |
|---|---:|---|
| `drop` | `0x1A` | Removes the top value from the stack |

## Locals

| Opcode | Hex | Description |
|---|---:|---|
| `local.get` | `0x20` | Pushes a local variable onto the stack |
| `local.set` | `0x21` | Pops a value and stores it in a local |
| `local.tee` | `0x22` | Stores a value in a local while keeping it on the stack |

# Constants

| Type | Opcode | Hex |
|---|---|---:|
| i32 | `i32.const` | `0x41` |
| i64 | `i64.const` | `0x42` |
| f32 | `f32.const` | `0x43` |
| f64 | `f64.const` | `0x44` |

# i32

## i32 Comparisons

| Opcode | Hex | Description |
|---|---:|---|
| `i32.eqz` | `0x45` | Equal to zero |
| `i32.eq` | `0x46` | Equal |
| `i32.ne` | `0x47` | Not equal |
| `i32.lt_s` | `0x48` | Signed less than |
| `i32.lt_u` | `0x49` | Unsigned less than |
| `i32.gt_s` | `0x4A` | Signed greater than |
| `i32.gt_u` | `0x4B` | Unsigned greater than |
| `i32.le_s` | `0x4C` | Signed less than or equal |
| `i32.le_u` | `0x4D` | Unsigned less than or equal |
| `i32.ge_s` | `0x4E` | Signed greater than or equal |
| `i32.ge_u` | `0x4F` | Unsigned greater than or equal |

## i32 Arithmetic / Bitwise

| Opcode | Hex | Description |
|---|---:|---|
| `i32.add` | `0x6A` | Addition |
| `i32.sub` | `0x6B` | Subtraction |
| `i32.mul` | `0x6C` | Multiplication |
| `i32.div_s` | `0x6D` | Signed division |
| `i32.div_u` | `0x6E` | Unsigned division |
| `i32.rem_s` | `0x6F` | Signed remainder |
| `i32.rem_u` | `0x70` | Unsigned remainder |
| `i32.and` | `0x71` | Bitwise AND |
| `i32.or` | `0x72` | Bitwise OR |
| `i32.xor` | `0x73` | Bitwise XOR |
| `i32.shl` | `0x74` | Shift left |
| `i32.shr_s` | `0x75` | Signed shift right |
| `i32.shr_u` | `0x76` | Unsigned shift right |
| `i32.rotl` | `0x77` | Rotate left |
| `i32.rotr` | `0x78` | Rotate right |

# i64

## i64 Comparisons

| Opcode | Hex | Description |
|---|---:|---|
| `i64.eqz` | `0x50` | Equal to zero |
| `i64.eq` | `0x51` | Equal |
| `i64.ne` | `0x52` | Not equal |
| `i64.lt_s` | `0x53` | Signed less than |
| `i64.lt_u` | `0x54` | Unsigned less than |
| `i64.gt_s` | `0x55` | Signed greater than |
| `i64.gt_u` | `0x56` | Unsigned greater than |
| `i64.le_s` | `0x57` | Signed less than or equal |
| `i64.le_u` | `0x58` | Unsigned less than or equal |
| `i64.ge_s` | `0x59` | Signed greater than or equal |
| `i64.ge_u` | `0x5A` | Unsigned greater than or equal |

## i64 Arithmetic / Bitwise

| Opcode | Hex | Description |
|---|---:|---|
| `i64.add` | `0x7C` | Addition |
| `i64.sub` | `0x7D` | Subtraction |
| `i64.mul` | `0x7E` | Multiplication |
| `i64.div_s` | `0x7F` | Signed division |
| `i64.div_u` | `0x80` | Unsigned division |
| `i64.rem_s` | `0x81` | Signed remainder |
| `i64.rem_u` | `0x82` | Unsigned remainder |
| `i64.and` | `0x83` | Bitwise AND |
| `i64.or` | `0x84` | Bitwise OR |
| `i64.xor` | `0x85` | Bitwise XOR |
| `i64.shl` | `0x86` | Shift left |
| `i64.shr_s` | `0x87` | Signed shift right |
| `i64.shr_u` | `0x88` | Unsigned shift right |
| `i64.rotl` | `0x89` | Rotate left |
| `i64.rotr` | `0x8A` | Rotate right |

# f32

## f32 Comparisons

| Opcode | Hex | Description |
|---|---:|---|
| `f32.eq` | `0x5B` | Equal |
| `f32.ne` | `0x5C` | Not equal |
| `f32.lt` | `0x5D` | Less than |
| `f32.gt` | `0x5E` | Greater than |
| `f32.le` | `0x5F` | Less than or equal |
| `f32.ge` | `0x60` | Greater than or equal |

## f32 Arithmetic

| Opcode | Hex | Description |
|---|---:|---|
| `f32.abs` | `0x8B` | Absolute value |
| `f32.neg` | `0x8C` | Negate |
| `f32.ceil` | `0x8D` | Round toward positive infinity |
| `f32.floor` | `0x8E` | Round toward negative infinity |
| `f32.trunc` | `0x8F` | Round toward zero |
| `f32.nearest` | `0x90` | Round to nearest integer |
| `f32.sqrt` | `0x91` | Square root |
| `f32.add` | `0x92` | Addition |
| `f32.sub` | `0x93` | Subtraction |
| `f32.mul` | `0x94` | Multiplication |
| `f32.div` | `0x95` | Division |
| `f32.min` | `0x96` | Minimum |
| `f32.max` | `0x97` | Maximum |
| `f32.copysign` | `0x98` | Copy sign |

# f64

## f64 Comparisons

| Opcode | Hex | Description |
|---|---:|---|
| `f64.eq` | `0x61` | Equal |
| `f64.ne` | `0x62` | Not equal |
| `f64.lt` | `0x63` | Less than |
| `f64.gt` | `0x64` | Greater than |
| `f64.le` | `0x65` | Less than or equal |
| `f64.ge` | `0x66` | Greater than or equal |

## f64 Arithmetic

| Opcode | Hex | Description |
|---|---:|---|
| `f64.abs` | `0x99` | Absolute value |
| `f64.neg` | `0x9A` | Negate |
| `f64.ceil` | `0x9B` | Round toward positive infinity |
| `f64.floor` | `0x9C` | Round toward negative infinity |
| `f64.trunc` | `0x9D` | Round toward zero |
| `f64.nearest` | `0x9E` | Round to nearest integer |
| `f64.sqrt` | `0x9F` | Square root |
| `f64.add` | `0xA0` | Addition |
| `f64.sub` | `0xA1` | Subtraction |
| `f64.mul` | `0xA2` | Multiplication |
| `f64.div` | `0xA3` | Division |
| `f64.min` | `0xA4` | Minimum |
| `f64.max` | `0xA5` | Maximum |
| `f64.copysign` | `0xA6` | Copy sign |

# Memory Loads

| Opcode | Hex | Description |
|---|---:|---|
| `i32.load` | `0x28` | Load i32 |
| `i64.load` | `0x29` | Load i64 |
| `f32.load` | `0x2A` | Load f32 |
| `f64.load` | `0x2B` | Load f64 |
| `i32.load8_s` | `0x2C` | Load signed 8-bit value into i32 |
| `i32.load8_u` | `0x2D` | Load unsigned 8-bit value into i32 |
| `i32.load16_s` | `0x2E` | Load signed 16-bit value into i32 |
| `i32.load16_u` | `0x2F` | Load unsigned 16-bit value into i32 |
| `i64.load8_s` | `0x30` | Load signed 8-bit value into i64 |
| `i64.load8_u` | `0x31` | Load unsigned 8-bit value into i64 |
| `i64.load16_s` | `0x32` | Load signed 16-bit value into i64 |
| `i64.load16_u` | `0x33` | Load unsigned 16-bit value into i64 |
| `i64.load32_s` | `0x34` | Load signed 32-bit value into i64 |
| `i64.load32_u` | `0x35` | Load unsigned 32-bit value into i64 |

# Memory Stores

| Opcode | Hex | Description |
|---|---:|---|
| `i32.store` | `0x36` | Store i32 |
| `i64.store` | `0x37` | Store i64 |
| `f32.store` | `0x38` | Store f32 |
| `f64.store` | `0x39` | Store f64 |
| `i32.store8` | `0x3A` | Store lowest 8 bits of i32 |
| `i32.store16` | `0x3B` | Store lowest 16 bits of i32 |
| `i64.store8` | `0x3C` | Store lowest 8 bits of i64 |
| `i64.store16` | `0x3D` | Store lowest 16 bits of i64 |
| `i64.store32` | `0x3E` | Store lowest 32 bits of i64 |

# Type Conversions

| Opcode | Hex | Description |
|---|---:|---|
| `i32.wrap_i64` | `0xA7` | i64 → i32 |
| `i32.trunc_f32_s` | `0xA8` | f32 → signed i32 |
| `i32.trunc_f32_u` | `0xA9` | f32 → unsigned i32 |
| `i32.trunc_f64_s` | `0xAA` | f64 → signed i32 |
| `i32.trunc_f64_u` | `0xAB` | f64 → unsigned i32 |
| `i64.extend_i32_s` | `0xAC` | signed i32 → i64 |
| `i64.extend_i32_u` | `0xAD` | unsigned i32 → i64 |
| `i64.trunc_f32_s` | `0xAE` | f32 → signed i64 |
| `i64.trunc_f32_u` | `0xAF` | f32 → unsigned i64 |
| `i64.trunc_f64_s` | `0xB0` | f64 → signed i64 |
| `i64.trunc_f64_u` | `0xB1` | f64 → unsigned i64 |
| `f32.convert_i32_s` | `0xB2` | signed i32 → f32 |
| `f32.convert_i32_u` | `0xB3` | unsigned i32 → f32 |
| `f32.convert_i64_s` | `0xB4` | signed i64 → f32 |
| `f32.convert_i64_u` | `0xB5` | unsigned i64 → f32 |
| `f32.demote_f64` | `0xB6` | f64 → f32 |
| `f64.convert_i32_s` | `0xB7` | signed i32 → f64 |
| `f64.convert_i32_u` | `0xB8` | unsigned i32 → f64 |
| `f64.convert_i64_s` | `0xB9` | signed i64 → f64 |
| `f64.convert_i64_u` | `0xBA` | unsigned i64 → f64 |
| `f64.promote_f32` | `0xBB` | f32 → f64 |