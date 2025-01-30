# SCB Compiler

SCB (Simple Compiler Backend) is a minimalistic compiler that translates a IR language into x86-64 assembly. The compiler is implemented in Python and generates assembly code that can be assembled and linked using GCC.

## Features

- Basic data definitions with `datadef`
- Function declarations with `funcdef`
- External function declarations with `extern`
- Variable declarations and arithmetic operations
- Function calls and return statements
- String and integer support
- x86-64 assembly code generation

## Language Syntax

### Data Definitions

```scb
datadef fmt: bytes = "%d\n";
```

### Function Declarations

```scb
funcdef %main() -> int {
    ret int 0;
}
```

### External Function Declarations

```scb
extern %printf;
```

### Variable Declarations

```scb
$x: int = int 1;
```

### Arithmetic Operations

```scb
$y: int = add $x, 2;
```

### Function Calls

```scb
$result: int = call %sum($a: int, $b: int);
```

### Return Statements

```scb
ret int 0;
```

### Labels and Control Flow

```scb
.loop:
    # ... code ...
    jmp .loop  # Unconditional jump
    cmp je $a, $b, .target  # Conditional jump (jump if equal)
```

