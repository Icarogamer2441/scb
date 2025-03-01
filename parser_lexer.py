import re

class Token:
    def __init__(self, type_, value):
        self.type = type_
        self.value = value

    def __repr__(self):
        return f"Token({self.type}, {self.value})"

class Lexer:
    def __init__(self, source):
        self.source = source.split('\n')
        self.pos = 0
        self.current_line = 0
    
    def tokenize(self):
        tokens = []
        in_struct = False
        struct_lines = []
        in_enum = False
        enum_lines = []
        for line in self.source:
            line = line.strip()
            if not line or line.startswith('//'):
                continue

            # Check for use runtime first
            use_runtime = self._match_use_runtime(line)
            if use_runtime:
                tokens.append(use_runtime)
                continue
                
            if line.startswith('structdef'):
                in_struct = True
                struct_lines = [line]
                continue
                
            if in_struct:
                struct_lines.append(line)
                if '}' in line:
                    full_struct = ' '.join(struct_lines)
                    tokens.append(self._match_structdef(full_struct))
                    in_struct = False
                continue
                
            if line.startswith('enumdef'):
                in_enum = True
                enum_lines = [line]
                continue
                
            if in_enum:
                enum_lines.append(line)
                if '}' in line:
                    full_enum = ' '.join(enum_lines)
                    tokens.append(self._match_enumdef(full_enum))
                    in_enum = False
                continue
                
            # Add bssdef handling
            if line.startswith('bssdef'):
                tokens.append(self._match_bssdef(line))
                
            # Add label matching
            if line.startswith('.'):
                tokens.append(self._match_label(line))
            # Match tokens
            elif line.startswith('datadef'):
                tokens.append(self._match_datadef(line))
            elif line.startswith('extern'):
                tokens.append(self._match_extern(line))
            elif line.startswith('funcdef'):
                tokens.append(self._match_funcdef(line))
            elif line.startswith('call'):
                tokens.append(self._match_call(line))
            elif line.startswith('ret'):
                tokens.append(self._match_ret(line))
            elif line.startswith('push'):
                value = line.split(' ', 1)[1].rstrip(';')
                tokens.append(Token('PUSH', value))
            elif '= pop' in line:
                match = re.match(r'\$(\w+):\s*(\w+)\s*=\s*pop;', line)
                if match:
                    tokens.append(Token('POP', (match.group(1), match.group(2))))
            elif line.startswith('$'):
                # If the line starts with $<name>[..., it's an array element assignment.
                if re.match(r'^\$\w+\[', line):
                    tokens.append(self._match_array_assign(line))
                else:
                    tokens.append(self._match_var_decl(line))
            elif 'add' in line:
                tokens.append(self._match_binop(line))
            elif line.startswith('cmp'):
                tokens.append(self._match_cmp(line))
            elif line.startswith('j'):
                tokens.append(self._match_jump(line))
        return tokens
    
    def _match_datadef(self, line):
        match = re.match(r'datadef\s+(\w+):\s+bytes\s*=\s*"(.*)";', line)
        if match:
            return Token('DATA_DEF', (match.group(1), match.group(2)))
        raise SyntaxError(f"Invalid datadef: {line}")
    
    def _match_extern(self, line):
        match = re.match(r'extern\s+%(\w+);', line)
        if match:
            return Token('EXTERN', match.group(1))
        raise SyntaxError(f"Invalid extern: {line}")
    
    def _match_funcdef(self, line):
        match = re.match(r'funcdef\s+%(\w+)\((.*)\)\s*->\s*\w+\s*{', line)
        if match:
            # Strip $ and * from parameter names
            params = [p.split(':')[0].strip().lstrip('$').lstrip('*') for p in match.group(2).split(',')]
            return Token('FUNCDEF', (match.group(1), params))
        raise SyntaxError(f"Invalid funcdef: {line}")
    
    def _match_call(self, line):
        match = re.match(r'call\s+%(\w+)\((.*)\);', line)
        if match:
            func = match.group(1)
            args = []
            for arg in match.group(2).split(','):
                arg = arg.split(':')[0].strip()
                # Check for pointer dereference using "<>"
                pointer_match = re.match(r'(\$?\w+)<(\d+)>', arg)
                if pointer_match:
                    args.append(PointerDerefNode(pointer_match.group(1), int(pointer_match.group(2))))
                    continue
                # Check for array access using "[]"
                array_match = re.match(r'(\$?\w+)\[(\d+)\]', arg)
                if array_match:
                    args.append(ArrayAccessNode(array_match.group(1), int(array_match.group(2))))
                    continue
                args.append(arg)
            return Token('CALL', (func, args))
        raise SyntaxError(f"Invalid call: {line}")
    
    def _match_ret(self, line):
        match = re.match(r'ret\s+(void|\w+)(?:\s+(\$?\w+))?;', line)
        if match:
            ret_type = match.group(1)
            value = match.group(2) if ret_type != 'void' else None
            return Token('RET', (ret_type, value))
        raise SyntaxError(f"Invalid return: {line}")

    def _match_var_decl(self, line):
        # NEW: Handle "get" keyword for variable declarations, e.g.,
        # "$x2: int = get $x;"
        if re.search(r'=\s*get\s+\$?\w+\s*;', line):
            match = re.match(r'\$(\w+)\*?:\s*([\w\[\]]+)\s*=\s*get\s+(\$?\w+)\s*;', line)
            if match:
                var_name = match.group(1)
                var_type = match.group(2)
                target = match.group(3)
                return Token('GET', (var_name, var_type, target))
        # Updated regex pattern to support array initializers and types like int[10]
        struct_init = r'(\w+)\s*{([^}]*)}'
        enum_value = r'(\w+)::(\w+)'
        # NEW: Pointer dereference uses "<...>"
        pointer_access = r'(\$?\w+)<(\d+)>'
        # Update array access to use square brackets: "[...]"
        array_access = r'(\$?\w+)\[(\d+)\]'
        pattern = (
            r'\$(\w+)\*?:\s*([\w\[\]]+)\s*=\s*'  # allow types like int[10]
            r'(?:call\s+%(\w+)\((.*)\)|'
            f'{struct_init}|'
            f'{enum_value}|'
            r'array\s+((?:-?\d+\s*,\s*)*-?\d+)|'
            f'{pointer_access}|'  # NEW alternative for pointer dereference
            f'{array_access}|'    # Updated alternative for array access
            r'&(\$?\w+)|'        # Address-of operator
            r'"([^"]*)"|'        # String literal
            r'(\d+)|'            # Number
            r'([a-z]+)\s+(\$?\w+),\s*(\$?\w+)'  # BinOp
            r')\s*;'
        )
        match = re.match(pattern, line)
        if not match:
            raise SyntaxError(f"Invalid declaration: {line}")
        
        var_name, var_type = match.group(1), match.group(2)
        if match.group(3):  # Function call
            args = [a.split(':')[0].strip() for a in match.group(4).split(',')]
            return Token('FUNC_CALL_ASSIGN', (var_name, match.group(3), args))
        elif match.group(5):  # Struct initializer
            fields_text = match.group(6)
            fields = []
            # Split by comma and process each field individually
            for part in fields_text.split(','):
                part = part.strip()
                m_field = re.match(r'\$(\w+):\s*(?:"([^"]+)"|(\$?\w+))', part)
                if m_field:
                    name = m_field.group(1)
                    # Preserve quotes for string literals so that codegen can recognize them
                    value = f'"{m_field.group(2)}"' if m_field.group(2) is not None else m_field.group(3)
                    fields.append((name, value))
            return Token('VAR_DECL', (var_name, var_type, fields))
        elif match.group(7):  # Enum value
            return Token('ENUM_VALUE', (var_name, var_type, f"{match.group(7)}::{match.group(8)}"))
        elif match.group(9):  # Array initializer (new)
            return Token('VAR_DECL', (var_name, var_type, match.group(9)))
        elif match.group(10):  # Pointer dereference (e.g. $ptr<0>)
            return Token('POINTER_DEREF', (var_name, int(match.group(11))))
        elif match.group(12):  # Array access (e.g. $arr[0])
            return Token('ARRAY_ACCESS', (var_name, int(match.group(13))))
        elif match.group(14):  # Address-of
            return Token('ADDRESS_OF', (var_name, var_type, match.group(14)))
        elif match.group(15):  # String literal
            return Token('VAR_DECL', (var_name, var_type, match.group(15)))
        elif match.group(16):  # Number literal
            return Token('VAR_DECL', (var_name, var_type, int(match.group(16))))
        elif match.group(17):  # BinOp
            return Token('BIN_OP', (match.group(17), var_name, match.group(18), match.group(19)))
        
        raise SyntaxError(f"Invalid declaration: {line}")

    def _match_label(self, line):
        match = re.match(r'^\.(\w+):$', line)
        if match:
            return Token('LABEL', match.group(1))
        raise SyntaxError(f"Invalid label: {line}")

    def _match_cmp(self, line):
        match = re.match(r'cmp\s+(\$?\w+),\s*(\$?\w+);', line)
        if match:
            return Token('CMP', (match.group(1), match.group(2)))
        raise SyntaxError(f"Invalid cmp: {line}")

    def _match_jump(self, line):
        valid_jumps = ['jge', 'je', 'jg', 'jl', 'jne', 'jle', 'jmp']
        match = re.match(r'(' + '|'.join(valid_jumps) + r')\s+\.(\w+);', line)
        if match:
            return Token('JUMP', (match.group(1), match.group(2)))
        raise SyntaxError(f"Invalid jump: {line}")

    def _match_structdef(self, line):
        # Allow newlines and multiple spaces
        match = re.match(
            r'structdef\s+(\w+)\s*{\s*((?:[\s\$]*\w+:\s*\w+;?\s*)*)\s*}', 
            line, 
            re.DOTALL
        )
        if not match:
            raise SyntaxError(f"Invalid structdef: {line}")
        
        struct_name = match.group(1)
        fields = []
        # Split fields while ignoring empty entries
        for field in re.split(r';\s*', match.group(2)):
            field = field.strip()
            if not field:
                continue
            name_type = re.match(r'\$(\w+):\s*(\w+)', field)
            if name_type:
                fields.append((name_type.group(1), name_type.group(2)))
            
        return Token('STRUCT_DEF', (struct_name, fields))

    def _match_enumdef(self, line):
        match = re.match(
            r'enumdef\s+(\w+)\s*{\s*((?:[\s\w,]+\s*)*)\s*}', 
            line, 
            re.DOTALL
        )
        if not match:
            raise SyntaxError(f"Invalid enumdef: {line}")
        
        enum_name = match.group(1)
        variants = [v.strip() for v in match.group(2).split(',') if v.strip()]
        return Token('ENUM_DEF', (enum_name, variants))

    def _match_bssdef(self, line):
        match = re.match(r'bssdef\s+(\w+):\s+bytesbuff\s*=\s*(\d+);', line)
        if match:
            return Token('BSS_DEF', (match.group(1), int(match.group(2))))
        raise SyntaxError(f"Invalid bssdef: {line}")

    def _match_array_assign(self, line):
        # Matches an array element assignment e.g., "$arr[0] = 10;"
        match = re.match(r'\$(\w+)\[(\d+)\]\s*=\s*(.+);', line)
        if match:
            var_name = match.group(1)
            index = int(match.group(2))
            value_str = match.group(3).strip()
            # If value is a number, convert it to int; else leave as string (e.g. variable reference).
            if re.match(r'^-?\d+$', value_str):
                value = int(value_str)
            else:
                value = value_str
            return Token('ARRAY_ASSIGN', (var_name, index, value))
        raise SyntaxError(f"Invalid array assignment: {line}")

    def _match_use_runtime(self, line):
        if line.strip() == 'use runtime;':
            return Token('USE_RUNTIME', None)
        return None

class ASTNode:
    pass

class StrDeclNode(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class DataDefNode(ASTNode):
    def __init__(self, name, value):
        self.name = name
        self.value = value

class ExternNode(ASTNode):
    def __init__(self, name):
        self.name = name

class FuncDefNode(ASTNode):
    def __init__(self, name, params):
        self.name = name
        self.params = params

class CallNode(ASTNode):
    def __init__(self, func, args):
        self.func = func
        self.args = args

class RetNode(ASTNode):
    def __init__(self, ret_type, value):
        self.ret_type = ret_type
        self.value = value

class VarDeclNode(ASTNode):
    def __init__(self, name, var_type, value):
        self.name = name
        self.type = var_type  # 'int', 'bytes', or struct name
        self.value = value

# NEW: Define a new AST node for the "get" operation
class GetNode(ASTNode):
    def __init__(self, var_name, var_type, target):
        self.var_name = var_name
        self.var_type = var_type
        self.target = target

class BinOpNode(ASTNode):
    def __init__(self, op, result_var, left_var, right_var):
        self.op = op
        self.result_var = result_var
        self.left_var = left_var
        self.right_var = right_var

class FuncCallAssignNode(ASTNode):
    def __init__(self, var_name, func_name, args):
        self.var_name = var_name
        self.func_name = func_name
        self.args = args

class LabelNode(ASTNode):
    def __init__(self, name):
        self.name = name

class CmpNode(ASTNode):
    def __init__(self, left, right):
        self.left = left
        self.right = right

class JumpNode(ASTNode):
    def __init__(self, condition, label):
        self.condition = condition
        self.label = label

class StructDefNode(ASTNode):
    def __init__(self, name, fields):
        self.name = name
        self.fields = fields

class EnumDefNode(ASTNode):
    def __init__(self, name, variants):
        self.name = name
        self.variants = variants

class BssDefNode(ASTNode):
    def __init__(self, name, size):
        self.name = name
        self.size = size

class ArrayAccessNode(ASTNode):
    def __init__(self, var_name, index):
        self.var_name = var_name
        self.index = index

class AddressOfNode(ASTNode):
    def __init__(self, var_name, var_type, target):
        self.var_name = var_name
        self.var_type = var_type
        self.target = target

class PointerDerefNode(ASTNode):
    def __init__(self, var_name, index):
        self.var_name = var_name
        self.index = index

class ArrayAssignNode(ASTNode):
    def __init__(self, var_name, index, value):
        self.var_name = var_name
        self.index = index
        self.value = value

class PushNode(ASTNode):
    def __init__(self, value):
        self.value = value

class PopNode(ASTNode):
    def __init__(self, var_name, var_type):
        self.var_name = var_name
        self.var_type = var_type

class UseRuntimeNode:
    def __init__(self):
        pass

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self):
        ast = []
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token.type == 'LABEL':
                ast.append(LabelNode(token.value))
            elif token.type == 'DATA_DEF':
                ast.append(DataDefNode(*token.value))
            elif token.type == 'EXTERN':
                ast.append(ExternNode(token.value))
            elif token.type == 'FUNCDEF':
                ast.append(FuncDefNode(*token.value))
            elif token.type == 'CALL':
                ast.append(CallNode(*token.value))
            elif token.type == 'RET':
                ast.append(RetNode(token.value[0], token.value[1]))
            elif token.type == 'GET':
                # NEW: Handle "get" declarations
                name, var_type, target = token.value
                ast.append(GetNode(name, var_type, target))
            elif token.type == 'VAR_DECL':
                if len(token.value) == 3:  # Struct initializer or similar
                    name, var_type, value = token.value
                    ast.append(VarDeclNode(name, var_type, value))
                else:  # Regular variable declaration
                    name, value = token.value
                    var_type = 'int' if isinstance(value, int) else 'bytes'
                    ast.append(VarDeclNode(name, var_type, value))
            elif token.type == 'ARRAY_ASSIGN':
                var_name, index, value = token.value
                ast.append(ArrayAssignNode(var_name, int(index), value))
            elif token.type == 'POINTER_DEREF':
                var_name, index = token.value
                ast.append(PointerDerefNode(var_name, index))
            elif token.type == 'BIN_OP':
                op, result_var, left, right = token.value
                ast.append(BinOpNode(op, result_var, left, right))
            elif token.type == 'FUNC_CALL_ASSIGN':
                ast.append(FuncCallAssignNode(*token.value))
            elif token.type == 'STR_DECL':
                ast.append(StrDeclNode(*token.value))
            elif token.type == 'CMP':
                ast.append(CmpNode(*token.value))
            elif token.type == 'JUMP':
                ast.append(JumpNode(*token.value))
            elif token.type == 'STRUCT_DEF':
                name, fields = token.value
                ast.append(StructDefNode(name, fields))
            elif token.type == 'ENUM_DEF':
                name, variants = token.value
                ast.append(EnumDefNode(name, variants))
            elif token.type == 'ENUM_VALUE':
                name, var_type, value = token.value
                ast.append(VarDeclNode(name, var_type, value))
            elif token.type == 'BSS_DEF':
                name, size = token.value
                ast.append(BssDefNode(name, size))
            elif token.type == 'ARRAY_ACCESS':
                var_name, index = token.value
                ast.append(ArrayAccessNode(var_name, int(index)))
            elif token.type == 'ADDRESS_OF':
                var_name, var_type, target = token.value
                ast.append(AddressOfNode(var_name, var_type, target))
            elif token.type == 'PUSH':
                ast.append(PushNode(token.value))
            elif token.type == 'POP':
                ast.append(PopNode(*token.value))
            elif token.type == 'USE_RUNTIME':
                ast.append(UseRuntimeNode())
            self.pos += 1
        return ast
