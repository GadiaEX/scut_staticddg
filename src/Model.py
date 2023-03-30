import typing
import ast
import astor

import ast
import astor

class Node:
    def __init__(self, line, content):
        self.line = line
        self.content = content.strip()
        self.children = []
        self.function_calls = []
        self.used_vars = set()
        self.defined_vars = set()
        self._extract_vars()
        self._extract_function_calls()

    def _extract_vars(self):
        try:
            stmt = ast.parse(self.content).body[0]
        except SyntaxError:
            return

        if isinstance(stmt, ast.Assign):
            self.defined_vars = set(t.id for t in stmt.targets if isinstance(t, ast.Name))
            self.used_vars = set(t.id for t in ast.walk(stmt.value) if isinstance(t, ast.Name))

        elif isinstance(stmt, ast.Expr) or isinstance(stmt, ast.If) or isinstance(stmt, ast.While):
            if isinstance(stmt, ast.BinOp):
                self.used_vars = set(t.id for t in ast.walk(stmt.left) if isinstance(t, ast.Name))
                self.used_vars |= set(t.id for t in ast.walk(stmt.right) if isinstance(t, ast.Name))
            else:
                if hasattr(stmt, 'test'):
                    self.used_vars = set(t.id for t in ast.walk(stmt.test) if isinstance(t, ast.Name))
                elif hasattr(stmt, 'value'):
                    for t in ast.walk(stmt.value):
                        if isinstance(t, ast.Name) and not isinstance(t.ctx, ast.Store):
                            self.used_vars.add(t.id)


            if isinstance(stmt, ast.If) or isinstance(stmt, ast.While):
                for n in ast.walk(stmt):
                    if isinstance(n, ast.Assign):
                        self.defined_vars |= set(t.id for t in n.targets if isinstance(t, ast.Name))
                        self.used_vars |= set(t.id for t in ast.walk(n.value) if isinstance(t, ast.Name))
                    elif isinstance(n, ast.Expr):
                        self.used_vars |= set(t.id for t in ast.walk(n.value) if isinstance(t, ast.Name))

    def _extract_function_calls(self):
        try:
            stmt = ast.parse(self.content).body[0]
        except SyntaxError:
            return

        if isinstance(stmt, ast.Expr) and isinstance(stmt.value, ast.Call):
            func_name = astor.to_source(stmt.value.func).strip()
            if func_name in self.used_vars:
                self.used_vars.remove(func_name)
            args = []
            for arg in stmt.value.args:
                if isinstance(arg, ast.Name):
                    args.append(arg.id)
                # else:
                #     args.append(astor.to_source(arg).strip())
            self.function_calls.append({'name': func_name, 'args': args})

    def add_child(self, child):
        if type(child) is list:
            self.children += child
        else:
            self.children.append(child)
    def __repr__(self):
        return f'Node(line={self.line}, content="{self.content}", used_vars={sorted(self.used_vars)}, defined_vars={sorted(self.defined_vars)}, function_calls={self.function_calls})'