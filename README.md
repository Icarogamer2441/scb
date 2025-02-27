# SCB Compiler

SCB (Simple Compiler Backend) is a minimalistic compiler that translates a IR language into x86-64 assembly. The compiler is implemented in Python and generates assembly code that can be assembled and linked using GCC.

if you're on windows, see [Installation-Windows](#installation-windows) for more information.

## Features

- Basic data definitions with `datadef`
- Function declarations with `funcdef`
- External function declarations with `extern`
- Variable declarations and arithmetic operations
- Function calls and return statements
- String and integer support
- x86-64 assembly code generation

## Installation

```bash
git clone https://github.com/Icarogamer2441/scb.git
cd scb
make build
sudo make install
```

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
$x: int = 1;
```

### Arithmetic Operations

```scb
$y: int = add $x, 2;
```

- add
- sub
- mul
- div

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
    cmp $a, $b
    je .target
```

## Installation-Windows

install mingw x86_64 and add it to your PATH.

and then run the following commands:
```bash
git clone https://github.com/Icarogamer2441/scb.git
cd scb
.\build.bat build
```

## Build Commands

```bash
.\build.bat build
```

```bash
.\build.bat clean
```

```bash
.\build.bat all
```

```bash
.\build.bat runall
```

```bash
.\build.bat scbclean
```

## Usage

```bash
python scbc.py --target win64 -c examples\hello.scb
```

```bash
.\examples\hello.exe
```