#!/usr/bin/env python3
import sys
import argparse
import subprocess
from parser_lexer import Lexer, Parser
from codegen import CodeGenerator

class SCBCompiler:
    def __init__(self, target_os='linux'):
        self.target_os = target_os
        
    def compile(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        codegen = CodeGenerator(target_os=self.target_os)
        return codegen.generate(ast)

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
        subprocess.run(['gcc'] + link_flags + ['-o', exe_file, output_file])
        
        # Windows-compatible file deletion
        if args.target == 'win64':
            subprocess.run(f'del {output_file}', shell=True)
        else:
            subprocess.run(['rm', output_file])

if __name__ == '__main__':
    main() 