import typing
import ast
import astor

class CFG_Node:
    """
    single node in control flow graph
    """
    def __init__(self):
        self.line = 0
        self.code = ''
        self.doc_str = ''
        self.doc_str_token = []
        # use or not in code segment
        self.sha = False
        self.variable_define: list = []
        self.variable_depend: list = []
        self.function_call: list = []
        self.child: list = []
        self.parent: list = []

class CFG_Blank_Node(CFG_Node):
    """
     for special usage
    """
    def __init__(self):
        super().__init__()

class CFG_END_If_Node(CFG_Node):
    """
     for special usage
    """
    def __init__(self):
        super().__init__()

class CFG_END_For_Node(CFG_Node):
    """
     for special usage
    """
    def __init__(self):
        super().__init__()

class CFG_END_While_Node(CFG_Node):
    """
     for special usage
    """
    def __init__(self):
        super().__init__()

# global node indicating blank info in a block, with sigliten
blank_node = CFG_Blank_Node()

class Block:
    """
    A block in AST
    """

    def __init__(self, _id, ast_node):
        # id of the block.
        self.id = _id
        # original ast tree root of a single block
        self.ast_node = ast_node
        # Statements in the block.
        self.statements = []
        # Calls to functions inside the block (represents context switches to
        # some functions' DDGs).
        self.func_calls = []
        self.exits = []
        # variable name --> node
        self.symbol_table = {}
        # block that inside this block
        self.blocks = []
        self.inner_block_id: int = 0
        # collector
        self.cfg_node = []
        # header for further searching
        self.cfg_header = blank_node
        self.cfg_tail = blank_node
        self.parse(ast_node)

    def parse(self, ast_node):

        if hasattr(ast_node, 'body'):
            for each in ast_node.body:
                self.parse_body(each)
        else:
            # single statement
            statement_type = type(ast_node)
            if statement_type == ast.Assign:
                self.cfg_node.append(self.__assign(ast_node))
            elif statement_type == ast.If:
                self.cfg_node.append(self.__if(ast_node))
            elif statement_type == ast.For:
                self.cfg_node.append(self.__for(ast_node))
            elif statement_type == ast.expr:
                pass

    def parse_body(self, node) -> None:
        statement_type = type(node)
        if statement_type == ast.FunctionDef or statement_type == ast.ClassDef:
            new_block = Block(self.inner_block_id, node)
            self.inner_block_id = self.inner_block_id + 1
            self.blocks.append(new_block)
        elif statement_type == ast.Assign:
            self.__assign(node)
        elif statement_type == ast.If:
            self.__if(node)
        elif statement_type == ast.For:
            self.__for(node)
        elif statement_type == ast.expr:
            self.__add_single_node__(node.lineno, astor.to_source(node))
        elif statement_type == ast.Import or statement_type == ast.ImportFrom:
            self.__import__(node)

    def __add_single_node__(self, line: int = 0, code: str = '', doc_str: str = '', doc_str_token = None,
                            sha: bool = False, variable_define = None, variable_depend = None,
                            function_call = None, child = None):
        if self.cfg_tail is blank_node:
            # empty create new one
            self.cfg_tail = CFG_Node()
            self.cfg_header = CFG_Node()
            self.cfg_header.child.append(self.cfg_tail)
            self.cfg_tail.parent.append(self.cfg_header)
            node = self.cfg_header
        else:
            temp = CFG_Node()
            node = self.cfg_tail
            node.child.append(temp)
            temp.parent.append(self.cfg_tail)
            self.cfg_tail = temp

        # copy value
        node.line = line
        node.code = code
        node.doc_str = doc_str
        node.sha = sha
        if doc_str_token is not None:
            node.doc_str_token = doc_str_token
        else:
            node.doc_str_token = []

        if variable_depend is not None:
            node.variable_define = variable_define
        else:
            node.variable_define = []

        if variable_define is not None:
            node.variable_depend = variable_depend
        else:
            node.variable_depend = []

        if function_call is not None:
            node.function_call = function_call
        else:
            node.function_call = []

        if node.child is None:
            node.child = []

        if child is not None:
            node.child += child




    def __import__(self, node) -> None:

        variable_define = []
        for each in node.names:
            if each.asname is not None:
                variable_define.append(str(each.asname))
            else:
                variable_define.append(str(each.name))

        self.__add_single_node__(node.lineno, astor.to_source(node), variable_define = variable_define)

    @staticmethod
    def __binary_operation__(node) -> typing.Tuple[typing.List[str], any]:
        """
        For searching BinOp tree
        :param node:
        :return:
            the first is the variable name the tree dependences
            the second is the function call if exits, will return the __function_call__
            else it will be None
        """
        return Block.__binary_tree_search_inorder__(node)

    @staticmethod
    def __process_one_leave__(node) -> typing.Tuple[typing.List[str], any]:
        variables = []
        function_cal = []

        if type(node) == ast.Call:
            extra_args, extra_function = Block.__function_call__(node)
            variables += extra_args
            function_cal += extra_function

        if type(node) == ast.Name:
            variables.append(str(node.id))

        return variables, function_cal

    @staticmethod
    def __concat_function_cal(one, another):
        # if any is None, abort this action
        if one is None or len(one) == 0:
            return another
        elif another is None or len(another) == 0:
            return one
        a = 1

    @staticmethod
    def __binary_tree_search_inorder__(node) -> typing.Tuple[typing.List[str], any]:
        # first left
        variable_depends = []
        function_calls = None

        if hasattr(node, 'left'):
            variables, functions = Block.__binary_tree_search_inorder__(node.left)

            # concat them
            variable_depends += variables
            function_calls = Block.__concat_function_cal(functions, function_calls)

        # then mid, but it's an operation, we don't care, ignore

        # right final
        if hasattr(node, 'right'):
            variables, functions = Block.__binary_tree_search_inorder__(node.right)
        else:
            variables, functions = Block.__process_one_leave__(node)
        # concat them
        variable_depends += variables
        function_calls = Block.__concat_function_cal(functions, function_calls)

        return variable_depends, function_calls

    @staticmethod
    def __function_call__(node) -> typing.Tuple[typing.List[str], typing.List[str]]:
        """
        Returns:
            A Tuple, the first is the args that are not constant (in other words,
            the arg depends on other variable will be added into the list).
            the second is the function name
        """

        # we should remind the function to deal with the mutil-function calling
        args = []
        if hasattr(node.func, 'id'):
            function_name = [str(node.func.id)]
        else:
            function_name = [str(node.func.attr)]

        for each_arg in node.args:
            if type(each_arg) == ast.Call:
                extra_args, extra_function = Block.__function_call__(each_arg)
                args += extra_args
                function_name += extra_function
            elif type(each_arg) == ast.Name:
                args.append(each_arg.id)
            elif type(each_arg) == ast.BinOp:
                extra_args, function = Block.__binary_operation__(each_arg)
                args += extra_args
                if function is not None:
                    args += function[0]
                    function_name += function[1]

        return args, function_name

    def __assign(self, node) -> None:
        # ret.doc_str = ast.get_docstring(node)
        # get what variable the code define so as to build DDG
        variable_define = []
        variable_depend = []
        for each_name in node.targets:
            if type(each_name) == ast.Attribute:
                # assignment dynamic
                name = each_name.attr
            else:
                name = each_name.id
            variable_define.append(name)

        function_calls = []
        # search every defined @TODO(gadiahan)
        if type(node.value) == ast.Num:
            # operation detection
            pass
        elif type(node.value) == ast.Dict:
            # search values but keys
            pass
        elif type(node.value) == ast.Call:
            args, name = Block.__function_call__(node.value)
            function_calls.append(name)
            variable_depend += args
        elif type(node.value) == ast.BinOp:
            extra_var, function_call = Block.__binary_operation__(node.value)
            variable_depend += extra_var
            if function_call is not None:
                function_calls += function_call

        self.__add_single_node__(node.lineno, astor.to_source(node), variable_define = variable_define,
                                 variable_depend = variable_depend)

    def __if(self, node) -> None:
        # if node, parse the condiction
        condition_point = self.cfg_tail

        end_point = CFG_Node()
        condition_point.child.append(end_point)

        for each in node.orelse:
            new_node = CFG_Node()
            condition_point.child.append(new_node)
            self.cfg_tail = new_node
            # build one path
            for each in each.body:
                self.parse_body(each)
            # end one path
            end_if = CFG_END_If_Node()
            end_if.child.append(end_point)
            end_point.parent.append(end_if)

        # end if node @TODO(check)
        self.cfg_tail = end_point

    def __for(self, node) -> None:
        pass

    def __while(self, node) -> None:
        pass

    def __str__(self):
        if self.statements:
            return "block:{}@{}".format(self.id, self.at())
        return "empty block:{}".format(self.id)

    def __repr__(self):
        txt = "{} with {} exits".format(str(self), len(self.exits))
        if self.statements:
            txt += ", body=["
            txt += ", ".join([ast.dump(node) for node in self.statements])
            txt += "]"
        return txt

    def at(self):
        """
        Get the line number of the first statement of the block in the program.
        """
        if self.statements and self.statements[0].lineno >= 0:
            return self.statements[0].lineno
        return None

    def is_empty(self):
        """
        Check if the block is empty.

        Returns:
            A boolean indicating if the block is empty (True) or not (False).
        """
        return len(self.statements) == 0

    def get_source(self):
        """
        Get a string containing the Python source code corresponding to the
        statements in the block.

        Returns:
            A string containing the source code of the statements.
        """
        src = ""
        for statement in self.statements:
            if type(statement) in [ast.If, ast.For, ast.While]:
                src += (astor.to_source(statement)).split('\n')[0] + "\n"
            elif type(statement) == ast.FunctionDef or\
                 type(statement) == ast.AsyncFunctionDef:
                src += (astor.to_source(statement)).split('\n')[0] + "...\n"
            else:
                src += astor.to_source(statement)
        return src

    def get_calls(self):
        """
        Get a string containing the calls to other functions inside the block.

        Returns:
            A string containing the names of the functions called inside the
            block.
        """
        txt = ""
        for func_name in self.func_calls:
            txt += func_name + '\n'
        return txt
