#!/usr/bin/env python3
import sys
import argparse
import subprocess
from parser_lexer import Lexer, Parser
from codegen import CodeGenerator

class SCBCompiler:
    def __init__(self):
        pass
        
    def compile(self, source):
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        ast = parser.parse()
        codegen = CodeGenerator()
        return codegen.generate(ast)

def main():
    parser = argparse.ArgumentParser(description='SCB Compiler')
    parser.add_argument('-c', action='store_true', help='Compile to executable')
    parser.add_argument('source', help='Source file to compile')
    args = parser.parse_args()
    
    with open(args.source, 'r') as f:
        source = f.read()
    
    compiler = SCBCompiler()
    assembly = compiler.compile(source)
    
    output_file = args.source.replace('.scb', '.s')
    with open(output_file, 'w') as f:
        f.write(assembly)
    
    if args.c:
        exe_file = args.source.replace('.scb', '')
        subprocess.run(['gcc', '-no-pie', '-o', exe_file, output_file])
        subprocess.run(['rm', output_file])

if __name__ == '__main__':
    main() 