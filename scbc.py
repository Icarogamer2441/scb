#!/usr/bin/env python3
import sys
import argparse
import subprocess
from parser_lexer import Lexer, Parser
from codegen import CodeGenerator
import os

# Add this constant near the top of the file
RUNTIME_C_CONTENT = """#include <stdio.h>
#include <stdlib.h>
#include <string.h>

void* open(const char* filename, const char* mode) {
    return fopen(filename, mode);
}

int write(void* file, const char* content) {
    return fputs(content, (FILE*)file);
}

int close(void* file) {
    return fclose((FILE*)file);
}

void* allocate(size_t size) {
    return malloc(size);
}

void deallocate(void* ptr) {
    free(ptr);
}

// String utilities
int starts_with(const char* str, const char* prefix) {
    size_t len_str = strlen(str);
    size_t len_prefix = strlen(prefix);
    if (len_prefix > len_str) return 0;
    return strncmp(str, prefix, len_prefix) == 0;
}

int ends_with(const char* str, const char* suffix) {
    size_t len_str = strlen(str);
    size_t len_suffix = strlen(suffix);
    if (len_suffix > len_str) return 0;
    return strncmp(str + len_str - len_suffix, suffix, len_suffix) == 0;
}
"""

class SCBCompiler:
    def __init__(self, target_os='linux'):
        self.target_os = target_os
        self.code_generator = None  # Add this line
        
    def compile(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        self.code_generator = CodeGenerator(target_os=self.target_os)  # Store as instance variable
        return self.code_generator.generate(ast)

def main():
    parser = argparse.ArgumentParser(description='SCB Compiler')
    parser.add_argument('-c', action='store_true', help='Compile to executable')
    parser.add_argument('--target', choices=['linux', 'win64'], default='linux',
                       help='Target platform (default: linux)')
    parser.add_argument('source', help='Source file to compile')
    args = parser.parse_args()
    
    with open(args.source, 'r') as f:
        source = f.read()
    
    compiler = SCBCompiler(target_os=args.target)
    assembly = compiler.compile(source)
    
    output_file = args.source.replace('.scb', '.s')
    with open(output_file, 'w') as f:
        f.write(assembly)
    
    if args.c:
        exe_file = args.source.replace('.scb', '.exe' if args.target == 'win64' else '')
        link_flags = ['-Wl,-subsystem,console'] if args.target == 'win64' else ['-no-pie']
        sources = [output_file]
        runtime_created = False
        
        # Add runtime if used
        if compiler.code_generator.use_runtime:
            # Write runtime.c temporarily
            with open('runtime.c', 'w') as f:
                f.write(RUNTIME_C_CONTENT)
            sources.append('runtime.c')
            runtime_created = True
            
        subprocess.run(['gcc'] + link_flags + ['-o', exe_file] + sources)
        
        # Cleanup files
        try:
            if args.target == 'win64':
                subprocess.run(f'del {output_file}', shell=True)
                if runtime_created:
                    subprocess.run('del runtime.c', shell=True)
            else:
                os.remove(output_file)
                if runtime_created:
                    os.remove('runtime.c')
        except Exception as e:
            print(f"Warning: Error cleaning up files - {e}")

if __name__ == '__main__':
    main() 