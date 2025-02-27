from parser_lexer import DataDefNode, ExternNode, FuncDefNode, CallNode, RetNode, VarDeclNode, BinOpNode, FuncCallAssignNode, StrDeclNode, LabelNode, CmpNode, JumpNode, StructDefNode, EnumDefNode, BssDefNode, ArrayAccessNode, AddressOfNode, PointerDerefNode, ArrayAssignNode, PushNode, PopNode, UseRuntimeNode
import re

class CodeGenerator:
    def __init__(self, target_os='linux'):
        self.data_section = []
        self.text_section = []
        self.externs = set()
        self.stack_offset = 0
        self.vars = {}  # Now stores (offset, type) tuples
        self.structs = {}
        self.enums = {}
        self.func_prologue_index = None
        self.func_prologue_index_updated = False
        self.target_os = target_os  # 'linux' or 'win64'
        self.param_regs = ['rcx', 'rdx', 'r8', 'r9'] if target_os == 'win64' else ['rdi', 'rsi', 'rdx', 'rcx', 'r8', 'r9']
        self.use_runtime = False
        self.runtime_funcs = ['open', 'write', 'close', 'allocate', 'deallocate', 'starts_with', 'ends_with']
    
    def generate(self, ast):
        for node in ast:
            if isinstance(node, StructDefNode):
                self.structs[node.name] = node.fields
            elif isinstance(node, BssDefNode):
                self._gen_bss_def(node)
            elif isinstance(node, LabelNode):
                self.text_section.append(f'.{node.name}:')
            elif isinstance(node, DataDefNode):
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
            elif isinstance(node, AddressOfNode):
                self._gen_var_decl(node)
            elif isinstance(node, BinOpNode):
                self._gen_bin_op(node)
            elif isinstance(node, FuncCallAssignNode):
                self._gen_func_call_assign(node)
            elif isinstance(node, StrDeclNode):
                self._gen_str_decl(node)
            elif isinstance(node, CmpNode):
                self._gen_cmp(node)
            elif isinstance(node, JumpNode):
                self._gen_jump(node)
            elif isinstance(node, EnumDefNode):
                self.enums[node.name] = {variant: i for i, variant in enumerate(node.variants)}
            elif 'ArrayAssignNode' in str(type(node)):
                self._gen_array_assign(node)
            elif isinstance(node, ArrayAssignNode):
                self._gen_array_assign(node)
            elif hasattr(node, 'var_name') and hasattr(node, 'target') and type(node).__name__ == 'GetNode':
                self._gen_get(node)
            elif isinstance(node, PushNode):
                self._gen_push(node)
            elif isinstance(node, PopNode):
                self._gen_pop(node)
            elif isinstance(node, UseRuntimeNode):
                self.use_runtime = True
                # Add externs for runtime functions
                runtime_funcs = ['open', 'write', 'close', 'allocate', 'deallocate']
                for func in runtime_funcs:
                    self.externs.add(func)
                    self.text_section.append(f'.extern {func}')
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
        shadow_space = 32 if self.target_os == 'win64' else 0
        
        self.text_section.extend([
            f'.text',
            f'.globl {node.name}',
            f'.type {node.name}, @function' if self.target_os == 'linux' else '',
            f'{node.name}:',
            '    push rbp',
            '    mov rbp, rsp',
            f'    sub rsp, STACK_SIZE_PLACEHOLDER + {shadow_space}'
        ])
        
        # Filter out empty strings from the assembly
        self.text_section = [line for line in self.text_section if line.strip() != '']
        
        # Record the index of our placeholder prologue line for later update.
        self.func_prologue_index = len(self.text_section) - 1
        # Reset stack offset for local variables
        self.stack_offset = shadow_space  # Start after shadow space on Windows
        self.vars = {}
        
        # Store parameters
        for i, param in enumerate(node.params):
            offset = self.stack_offset + 16
            self.vars[param] = (offset, param)
            if i < len(self.param_regs):
                self.text_section.append(f'    mov [rbp - {offset}], {self.param_regs[i]}')
            self.stack_offset += 8
        
        # Windows main function handling
        if node.name == 'main' and self.target_os == 'win64':
            self.text_section.extend([
                f'    mov [rbp - {self.stack_offset + 8}], rcx',   # Store argc
                f'    mov [rbp - {self.stack_offset + 16}], rdx'   # Store argv
            ])
            self.vars['argc'] = (self.stack_offset + 8, 'int')
            self.vars['argv'] = (self.stack_offset + 16, 'bytes**')
            self.stack_offset += 16
    
    def _gen_var_decl(self, node):
        if isinstance(node, AddressOfNode):
            # Handle pointer declaration with address-of
            offset = self.stack_offset + 16
            self.vars[node.var_name] = (offset, node.var_type)
            self.stack_offset += 8
            
            # Get target variable's address
            target_offset, _ = self.vars[node.target]  # Use target name directly
            self.text_section.extend([
                f'    lea rax, [rbp - {target_offset}]',
                f'    mov QWORD PTR [rbp - {offset}], rax'
            ])
            return
        # Handle enum values
        if node.type in self.enums:
            enum_values = self.enums[node.type]
            if isinstance(node.value, str) and '::' in node.value:
                _, variant = node.value.split('::')
                int_value = enum_values[variant]
                offset = self.stack_offset + 16
                self.vars[node.name] = (offset, node.type)
                self.text_section.append(f'    mov QWORD PTR [rbp - {offset}], {int_value}')
                self.stack_offset += 8
                return
        elif node.type == 'bytes':
            # Allocate stack space for pointer
            offset = self.stack_offset + 16
            self.vars[node.name] = (offset, 'bytes')
            self.stack_offset += 8
            
            # Generate string literal in rodata
            label = f'..LC{len(self.data_section)//4}'
            self.data_section.extend([
                f'.section .rodata',
                f'.align 8',
                f'{label}:',
                f'    .asciz "{node.value}"'
            ])
            
            # Store pointer to string
            self.text_section.extend([
                f'    lea rax, [{label} + rip]',
                f'    mov QWORD PTR [rbp - {offset}], rax'
            ])
        elif node.type in self.structs:
            struct_fields = self.structs[node.type]
            struct_size = len(struct_fields) * 8
            base_offset = self.stack_offset + 16
            self.vars[node.name] = (base_offset, node.type)
            self.stack_offset += struct_size
            
            for i, (field, field_type) in enumerate(struct_fields):
                field_value = node.value[i][1]
                offset = base_offset + i * 8
                
                if field_type == 'bytes' and field_value.startswith('"'):
                    # Handle string literals in structs
                    label = f'..LC{len(self.data_section)//4}'
                    self.data_section.extend([
                        f'.section .rodata',
                        f'.align 8',
                        f'{label}:',
                        f'    .asciz {field_value}'
                    ])
                    self.text_section.extend([
                        f'    lea rax, [{label} + rip]',
                        f'    mov QWORD PTR [rbp - {offset}], rax'
                    ])
                else:
                    # Existing handling for other types
                    if field_value.startswith('$'):
                        src_offset, _ = self.vars[field_value[1:]]
                        self.text_section.extend([
                            f'    mov rax, QWORD PTR [rbp - {src_offset}]',
                            f'    mov QWORD PTR [rbp - {offset}], rax'
                        ])
                    else:
                        self.text_section.append(f'    mov QWORD PTR [rbp - {offset}], {field_value}')
        elif re.match(r'\w+\[\d+\]', node.type):
            m = re.match(r'(\w+)\[(\d+)\]', node.type)
            base_type = m.group(1)
            count = int(m.group(2))
            # Parse comma-separated integers from the array literal (node.value)
            values = [int(x.strip()) for x in node.value.split(',')]
            if len(values) != count:
                raise ValueError(f"Array literal for {node.name} expects {count} values, got {len(values)}")
            base_offset = self.stack_offset + 16
            self.vars[node.name] = (base_offset, node.type)
            element_size = 8  # assuming 8 bytes per int element
            self.stack_offset += count * element_size
            for i, value in enumerate(values):
                offset = base_offset + i * element_size
                self.text_section.append(f'    mov QWORD PTR [rbp - {offset}], {value}')
            return
        elif isinstance(node.value, int):
            offset = self.stack_offset + 16
            self.vars[node.name] = (offset, node.type)
            self.text_section.extend([
                f'    mov QWORD PTR [rbp - {offset}], {node.value}'
            ])
            self.stack_offset += 8
    
    def _gen_bin_op(self, node):
        # Allocate stack space for the result variable first
        result_var = node.result_var
        if result_var not in self.vars:
            offset = self.stack_offset + 16
            self.vars[result_var] = (offset, result_var)
            self.stack_offset += 8  # Allocate 8 bytes for 64-bit int

        target_offset, _ = self.vars[result_var]
        
        def get_operand(operand):
            if operand.startswith('$'):
                var_name = operand[1:]
                var_offset, var_type = self.vars[var_name]
                return f'QWORD PTR [rbp - {var_offset}]'
            return operand

        left = get_operand(node.left_var)
        right = get_operand(node.right_var)

        if node.op == 'add':
            asm = [
                f'    mov rax, {left}',
                f'    add rax, {right}'
            ]
        elif node.op == 'sub':
            asm = [
                f'    mov rax, {left}',
                f'    sub rax, {right}'
            ]
        elif node.op == 'mul':
            asm = [
                f'    mov rax, {left}',
                f'    imul rax, {right}'
            ]
        elif node.op == 'div':
            asm = [
                f'    mov rax, {left}',
                f'    cqo',
                f'    idiv {right}'
            ]
        elif node.op == 'shr':
            asm = [
                f'    mov rax, {left}',
                f'    mov rcx, {right}',
                f'    shr rax, cl'
            ]
        elif node.op == 'shl':
            asm = [
                f'    mov rax, {left}',
                f'    mov rcx, {right}',
                f'    shl rax, cl'
            ]
        
        asm.append(f'    mov QWORD PTR [rbp - {target_offset}], rax')
        self.text_section.extend(asm)
    
    def _gen_call(self, node):
        processed_args = []
        for arg in node.args:
            if isinstance(arg, PointerDerefNode):
                clean_var_name = arg.var_name.lstrip('$')
                offset, _ = self.vars[clean_var_name]
                # Load pointer value from stack
                self.text_section.append(f'    mov rax, QWORD PTR [rbp - {offset}]')
                pointer_offset = arg.index * 8
                if pointer_offset != 0:
                    self.text_section.append(f'    add rax, {pointer_offset}')
                # Always dereference pointers when using <> syntax
                self.text_section.append(f'    mov rax, QWORD PTR [rax]')
                processed_args.append('rax')
                continue
            # Existing case for simple variable usage
            if isinstance(arg, str) and arg.startswith('$'):
                var_name = arg[1:]  # Remove $
                if var_name in self.vars:
                    offset, var_type = self.vars[var_name]
                    if '*' in var_type:  # Pointer variable used directly
                        self.text_section.append(f'    mov rdi, QWORD PTR [rbp - {offset}]')
                        processed_args.append('rdi')
                        continue
            
            # Handle array accesses (now using square brackets '[]')
            if isinstance(arg, ArrayAccessNode):
                clean_var_name = arg.var_name.lstrip('$')
                var_offset, _ = self.vars[clean_var_name]
                element_offset = var_offset + arg.index * 8
                self.text_section.append(f'    mov rax, QWORD PTR [rbp - {element_offset}]')
                processed_args.append('rax')
                continue
            
            if arg == 'mybuff':  # Handle buffer name directly
                processed_args.append(arg)
                continue
            
            if '->' in arg:
                parts = [p.strip()[1:] for p in arg.split('->')]
                current_var, *fields = parts
                current_offset, current_type = self.vars[current_var]
                total_offset = current_offset
                for field in fields:
                    if current_type not in self.structs:
                        break  # Stop if not a struct type
                    struct_fields = self.structs[current_type]
                    field_index = next(i for i, (name, _) in enumerate(struct_fields) if name == field)
                    total_offset += field_index * 8
                    current_type = struct_fields[field_index][1]
                processed_args.append(f'[rbp - {total_offset}]')
            else:
                processed_args.append(arg)
        
        # Windows requires 32 bytes of shadow space
        if self.target_os == 'win64':
            self.text_section.append('    sub rsp, 32')  # Allocate shadow space

        regs = self.param_regs
        for i, arg in enumerate(processed_args):
            if i >= len(regs):
                # On Windows, push remaining args to stack in reverse order
                self.text_section.insert(-1, f'    push {arg}')
                continue
            if arg in ['rax', 'rbx', 'rcx', 'rdx', 'rdi', 'rsi', 'r8', 'r9']:
                self.text_section.append(f'    mov {regs[i]}, {arg}')
            elif arg.startswith('['):
                self.text_section.append(f'    mov {regs[i]}, {arg}')
            elif arg.startswith('$'):
                offset, _ = self.vars[arg[1:]]
                if ': bytes' in arg:  # String pointer
                    self.text_section.append(f'    mov {regs[i]}, QWORD PTR [rbp - {offset}]')
                else:
                    self.text_section.append(f'    mov {regs[i]}, QWORD PTR [rbp - {offset}]')
            else:  # Global data reference
                self.text_section.append(f'    lea {regs[i]}, [{arg} + rip]')
        self.text_section.append('    xor rax, rax')
        self.text_section.append(f'    call {node.func}')
        
        if self.target_os == 'win64':
            self.text_section.append('    add rsp, 32')  # Cleanup shadow space
    
    def _gen_ret(self, node):
        # If this is the first RET in the current function, patch the placeholder
        if self.func_prologue_index is not None:
            final_offset = ((self.stack_offset + 63) // 64) * 64
            self.text_section[self.func_prologue_index] = f'    sub rsp, {final_offset}'
            # Clear the index so that subsequent RET nodes do not re-patch
            self.func_prologue_index = None

        if node.ret_type != 'void':
            if node.value.startswith('$'):
                offset, _ = self.vars[node.value[1:]]
                # Use QWORD PTR and RAX for 64-bit values
                self.text_section.append(f'    mov rax, QWORD PTR [rbp - {offset}]')
            else:
                self.text_section.append(f'    mov rax, {node.value}')

        self.text_section.extend([
            '    mov rsp, rbp',
            '    pop rbp',
            '    ret'
        ])
    
    def _gen_func_call_assign(self, node):
        # Allocate space for the result variable if not exists
        if node.var_name not in self.vars:
            offset = self.stack_offset + 16
            self.vars[node.var_name] = (offset, 'int')
            self.stack_offset += 8
        
        # Use the correct platform-specific registers for arguments
        regs = self.param_regs  # Use the platform-specific registers defined in __init__
        
        # Windows requires 32 bytes of shadow space
        if self.target_os == 'win64':
            self.text_section.append('    sub rsp, 32')  # Allocate shadow space
        
        for i, arg in enumerate(node.args):
            if i >= len(regs):
                # Handle stack arguments if needed
                continue
            
            if arg.startswith('$'):
                offset, _ = self.vars[arg[1:]]
                self.text_section.append(f'    mov {regs[i]}, QWORD PTR [rbp - {offset}]')
            else:
                self.text_section.append(f'    lea {regs[i]}, [{arg} + rip]')
        
        self.text_section.append('    xor rax, rax')  # Zero out RAX for variadic functions
        self.text_section.append(f'    call {node.func_name}')
        
        # Clean up shadow space if on Windows
        if self.target_os == 'win64':
            self.text_section.append('    add rsp, 32')
        
        # Store result
        offset, _ = self.vars[node.var_name]
        self.text_section.append(f'    mov QWORD PTR [rbp - {offset}], rax')
    
    def _gen_str_decl(self, node):
        # Allocate stack space first
        offset = self.stack_offset + 16
        self.vars[node.name] = (offset, 'bytes')
        self.stack_offset += 8  # Allocate space for pointer
        
        # Create unique label
        label = f'..LC{len(self.data_section)//4}'
        self.data_section.extend([
            f'.section .rodata',
            f'.align 8',
            f'{label}:',
            f'    .asciz "{node.value}"'
        ])
        
        # Store address in allocated space
        self.text_section.extend([
            f'    lea rax, [{label} + rip]',
            f'    mov QWORD PTR [rbp - {offset}], rax'
        ])
    
    def _gen_cmp(self, node):
        def get_operand(operand):
            if operand.startswith('$'):
                var_name = operand[1:]
                var_offset, var_type = self.vars[var_name]
                return f'QWORD PTR [rbp - {var_offset}]'
            return operand
        
        left = get_operand(node.left)
        right = get_operand(node.right)
        
        # Load right operand into register first
        self.text_section.extend([
            f'    mov rax, {right}',
            f'    cmp {left}, rax'
        ])
    
    def _gen_jump(self, node):
        self.text_section.append(f'    {node.condition} .{node.label}')
    
    def _gen_bss_def(self, node):
        self.data_section.extend([
            f'.section .bss',
            f'.globl {node.name}',
            f'.align 32',  # Align to 32-byte boundary
            f'{node.name}:',
            f'    .space {node.size}'
        ])
    
    def _gen_array_assign(self, node):
        """
        Generates code for an array element assignment.
        Example: "$arr[0] = 10;" will store 10 into the first element of the array.
        """
        if node.var_name not in self.vars:
            raise ValueError(f"Array variable {node.var_name} not declared")
        base_offset, var_type = self.vars[node.var_name]
        element_offset = base_offset + node.index * 8  # assuming 8 bytes per element
        if isinstance(node.value, int):
            self.text_section.append(f'    mov QWORD PTR [rbp - {element_offset}], {node.value}')
        elif isinstance(node.value, str):
            # Handle cases where the right-hand side is a variable reference (e.g., $x)
            if node.value.startswith('$'):
                ref_var = node.value[1:]
                if ref_var not in self.vars:
                    raise ValueError(f"Variable {ref_var} not declared")
                off, _ = self.vars[ref_var]
                self.text_section.append(f'    mov rax, QWORD PTR [rbp - {off}]')
                self.text_section.append(f'    mov QWORD PTR [rbp - {element_offset}], rax')
            else:
                self.text_section.append(f'    mov QWORD PTR [rbp - {element_offset}], {node.value}')
    
    def _gen_get(self, node):
        # Allocate stack space for the new variable
        offset = self.stack_offset + 16
        self.vars[node.var_name] = (offset, node.var_type)
        self.stack_offset += 8

        # Determine the source variable name (strip leading '$' if present)
        target_name = node.target.lstrip('$')
        if target_name not in self.vars:
            raise ValueError(f"Variable '{target_name}' not declared for get operation")
        source_offset, _ = self.vars[target_name]

        # Load the value from the target variable into rax and store it to the new variable's slot
        self.text_section.append(f'    mov rax, QWORD PTR [rbp - {source_offset}]')
        self.text_section.append(f'    mov QWORD PTR [rbp - {offset}], rax')
    
    def _gen_push(self, node):
        if node.value.startswith('"'):
            # Handle string literals
            label = f'..LC{len(self.data_section)//4}'
            self.data_section.extend([
                f'.section .rodata',
                f'.align 8',
                f'{label}:',
                f'    .asciz {node.value}'
            ])
            self.text_section.extend([
                f'    lea rax, [{label} + rip]',
                '    push rax'
            ])
        else:
            # Handle integers
            self.text_section.append(f'    push {node.value}')
    
    def _gen_pop(self, node):
        offset = self.stack_offset + 16
        self.vars[node.var_name] = (offset, node.var_type)
        self.stack_offset += 8
        
        if node.var_type == 'bytes':
            self.text_section.append(f'    pop QWORD PTR [rbp - {offset}]')
        else:
            self.text_section.append(f'    pop QWORD PTR [rbp - {offset}]')
    
    def _finalize_asm(self):
        assembly = [
            '.intel_syntax noprefix',
        ]
        
        # Add platform-specific sections
        if self.target_os == 'linux':
            assembly.extend([
                '.section .note.GNU-stack,"",@progbits',
                '.section .note.gnu.property,"a"',
                '    .align 8',
                '    .long 1f - 0f',
                '    .long 4f - 1f',
                '    .long 5',
                '0: .asciz "GNU"',
                '1: .align 8',
                '    .long 0xc0000002',
                '    .long 3f - 2f',
                '2: .long 0x3',
                '3: .align 8',
                '4:'
            ])
        
        assembly.extend(self.data_section)
        assembly.append('')
        assembly.append('.text')
        assembly.extend(self.text_section)
        assembly.append('')
        return '\n'.join(assembly)
