from parser_lexer import DataDefNode, ExternNode, FuncDefNode, CallNode, RetNode, VarDeclNode, BinOpNode, FuncCallAssignNode, StrDeclNode

class CodeGenerator:
    def __init__(self):
        self.data_section = []
        self.text_section = []
        self.externs = set()
        self.stack_offset = 0
        self.vars = {}
    
    def generate(self, ast):
        for node in ast:
            if isinstance(node, DataDefNode):
                self._gen_data_def(node)
            elif isinstance(node, ExternNode):
                self._gen_extern(node)
            elif isinstance(node, FuncDefNode):
                self._gen_func_def(node)
            elif isinstance(node, CallNode):
                self._gen_call(node)
            elif isinstance(node, RetNode):
                self._gen_ret(node)
            elif isinstance(node, VarDeclNode):
                self._gen_var_decl(node)
            elif isinstance(node, BinOpNode):
                self._gen_bin_op(node)
            elif isinstance(node, FuncCallAssignNode):
                self._gen_func_call_assign(node)
            elif isinstance(node, StrDeclNode):
                self._gen_str_decl(node)
        return self._finalize_asm()
    
    def _gen_data_def(self, node):
        self.data_section.extend([
            f'.data',
            f'.globl {node.name}',
            f'{node.name}:',
            f'    .asciz "{node.value}"'
        ])
    
    def _gen_extern(self, node):
        self.externs.add(node.name)
        self.text_section.append(f'.extern {node.name}')
    
    def _gen_func_def(self, node):
        # Prologue
        self.text_section.extend([
            f'.text',
            f'.globl {node.name}',
            f'{node.name}:',
            '    push rbp',
            '    mov rbp, rsp',
            '    sub rsp, 48',  # Stack space allocation
            '    and rsp, -16'   # Align stack to 16-byte boundary
        ])
        
        # Store parameters
        regs = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        self.stack_offset = 0
        self.vars = {}
        
        for i, param in enumerate(node.params):
            offset = self.stack_offset + 16
            self.vars[param] = offset
            self.text_section.append(f'    mov [rbp - {offset}], {regs[i]}')
            self.stack_offset += 8
    
    def _gen_var_decl(self, node):
        if isinstance(node.value, int):
            # Atribuição direta: $x: int = 5;
            offset = self.stack_offset + 16  # Reserva espaço abaixo do RBP
            self.vars[node.name] = offset
            self.text_section.extend([
                f'    mov DWORD PTR [rbp - {offset}], {node.value}'
            ])
            self.stack_offset += 4
    
    def _gen_bin_op(self, node):
        # Operação add: $z = add $x, $y
        offset_z = self.stack_offset + 16
        self.vars[node.result_var] = offset_z
        offset_x = self.vars[node.left_var]
        offset_y = self.vars[node.right_var]
        
        self.text_section.extend([
            f'    mov eax, DWORD PTR [rbp - {offset_x}]',
            f'    add eax, DWORD PTR [rbp - {offset_y}]',
            f'    mov DWORD PTR [rbp - {offset_z}], eax'
        ])
        self.stack_offset += 4
    
    def _gen_call(self, node):
        regs = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        for i, arg in enumerate(node.args):
            if arg.startswith('$'):
                offset = self.vars[arg[1:]]
                # Usa 32 bits para inteiros, 64 bits para ponteiros
                if isinstance(node.args[i], int) or node.args[i].isdigit():
                    self.text_section.append(f'    mov {regs[i][:3]}, DWORD PTR [rbp - {offset}]')
                else:
                    self.text_section.append(f'    mov {regs[i]}, QWORD PTR [rbp - {offset}]')
            else:
                self.text_section.append(f'    lea {regs[i]}, [{arg} + rip]')
        self.text_section.append(f'    call {node.func}')
    
    def _gen_ret(self, node):
        if node.ret_type != 'void':
            if node.value.startswith('$'):
                offset = self.vars[node.value[1:]]
                self.text_section.append(f'    mov eax, DWORD PTR [rbp - {offset}]')
            else:
                self.text_section.append(f'    mov eax, {node.value}')
        
        self.text_section.extend([
            '    mov rsp, rbp',
            '    pop rbp',
            '    ret'
        ])
    
    def _gen_func_call_assign(self, node):
        # Gerar chamada de função
        regs = ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        for i, arg in enumerate(node.args):
            if arg.startswith('$'):
                offset = self.vars[arg[1:]]
                self.text_section.append(f'    mov {regs[i]}, QWORD PTR [rbp - {offset}]')
            else:
                self.text_section.append(f'    lea {regs[i]}, [{arg} + rip]')
        self.text_section.append(f'    call {node.func_name}')
        
        # Armazenar resultado
        offset = self.stack_offset + 16
        self.vars[node.var_name] = offset
        self.text_section.append(f'    mov DWORD PTR [rbp - {offset}], eax')
        self.stack_offset += 4
    
    def _gen_str_decl(self, node):
        # Cria rótulo único para a string
        label = f'..LC{len(self.data_section)//4}'
        self.data_section.extend([
            f'.section .rodata',
            f'{label}:',
            f'    .string "{node.value}"'
        ])
        
        # Armazena endereço da string na stack
        offset = self.stack_offset + 16
        self.vars[node.name] = offset
        self.text_section.extend([
            f'    lea rax, [{label} + rip]',
            f'    mov QWORD PTR [rbp - {offset}], rax'
        ])
        self.stack_offset += 8
    
    def _finalize_asm(self):
        assembly = ['.intel_syntax noprefix']
        assembly.extend(self.data_section)
        assembly.append('')
        assembly.extend(self.text_section)
        assembly.append('')
        return '\n'.join(assembly)
