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
        for line in self.source:
            line = line.strip()
            if not line or line.startswith('//'):
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
            elif line.startswith('$'):
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
            params = [p.split(':')[0].strip() for p in match.group(2).split(',')]
            return Token('FUNCDEF', (match.group(1), params))
        raise SyntaxError(f"Invalid funcdef: {line}")
    
    def _match_call(self, line):
        match = re.match(r'call\s+%(\w+)\((.*)\);', line)
        if match:
            func = match.group(1)
            args = [a.split(':')[0].strip() for a in match.group(2).split(',')]
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
        # Update regex to capture variables in struct init
        struct_init = r'(\w+)\s*{([^}]*)}'
        pattern = (
            r'\$(\w+):\s*(\w+)\s*=\s*'
            r'(?:call\s+%(\w+)\((.*)\)|'
            f'{struct_init}|'
            r'"([^"]*)"|'
            r'(\d+)|'
            r'([a-z]+)\s+(\$?\w+),\s*(\$?\w+)'
            r')'
        )
        match = re.match(pattern, line)
        
        if not match:
            raise SyntaxError(f"Invalid declaration: {line}")
        
        var_name, var_type = match.group(1), match.group(2)
        
        if match.group(5):  # Struct initialization
            fields = re.findall(r'\$(\w+):\s*(\$?\w+)', match.group(6))
            return Token('VAR_DECL', (var_name, var_type, fields))
        elif match.group(3):  # Function call
            args = [a.split(':')[0].strip() for a in match.group(4).split(',')]
            return Token('FUNC_CALL_ASSIGN', (var_name, match.group(3), args))
        elif match.group(7):  # String
            return Token('STR_DECL', (var_name, match.group(7)))
        elif match.group(8):  # Integer
            return Token('VAR_DECL', (var_name, var_type, int(match.group(8))))
        elif match.group(9):  # BinOp
            return Token('BIN_OP', (match.group(9), var_name, match.group(10), match.group(11)))
        
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
        self.value = value  # Could be int, str, or list of field values

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

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self):
        ast = []
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            # Add label handling
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
            elif token.type == 'VAR_DECL':
                if len(token.value) == 3:  # Struct case
                    name, var_type, value = token.value
                    ast.append(VarDeclNode(name, var_type, value))
                else:  # Regular variable
                    name, value = token.value
                    var_type = 'int' if isinstance(value, int) else 'bytes'
                    ast.append(VarDeclNode(name, var_type, value))
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
            self.pos += 1
        return ast
