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
        for line in self.source:
            line = line.strip()
            if not line or line.startswith('//'):
                continue
                
            # Match tokens
            if line.startswith('datadef'):
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
        match = re.match(
            r'\$(\w+):\s*(\w+)\s*=\s*(?:"(.*)"|(\d+)|add\s+\$(\w+),\s*\$(\w+)|call\s+%(\w+)\((.*)\));', 
            line
        )
        if match:
            var_type = match.group(2)
            if var_type == 'int':
                if match.group(3):  # string (inválido para int)
                    raise SyntaxError(f"Tipo inválido para string: {line}")
                elif match.group(4):  # int literal
                    return Token('VAR_DECL', (match.group(1), int(match.group(4))))
                elif match.group(5) and match.group(6):  # add
                    return Token('BIN_OP', (match.group(1), match.group(5), match.group(6)))
                elif match.group(7) and match.group(8):  # call
                    args = [a.split(':')[0].strip() for a in match.group(8).split(',')]
                    return Token('FUNC_CALL_ASSIGN', (match.group(1), match.group(7), args))
                else:
                    raise SyntaxError(f"Declaração inválida: {line}")
            elif var_type == 'bytes':
                return Token('STR_DECL', (match.group(1), match.group(3)))
        raise SyntaxError(f"Declaração inválida: {line}")

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
    def __init__(self, name, value):
        self.name = name
        self.value = value

class BinOpNode(ASTNode):
    def __init__(self, result_var, left_var, right_var):
        self.result_var = result_var
        self.left_var = left_var
        self.right_var = right_var

class FuncCallAssignNode(ASTNode):
    def __init__(self, var_name, func_name, args):
        self.var_name = var_name
        self.func_name = func_name
        self.args = args

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
    
    def parse(self):
        ast = []
        while self.pos < len(self.tokens):
            token = self.tokens[self.pos]
            if token.type == 'DATA_DEF':
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
                ast.append(VarDeclNode(*token.value))
            elif token.type == 'BIN_OP':
                ast.append(BinOpNode(*token.value))
            elif token.type == 'FUNC_CALL_ASSIGN':
                ast.append(FuncCallAssignNode(*token.value))
            elif token.type == 'STR_DECL':
                ast.append(StrDeclNode(*token.value))
            self.pos += 1
        return ast
