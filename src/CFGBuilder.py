"""
    Data dependence graph builder, for building Graph use
"""
# Gadia, 2023
import src.Model.CFGNode
import ast
import astor


class CFGVisitor(ast.NodeVisitor):
    def __init__(self, source_code, base_line=0):
        self.source_code = source_code
        self.cfg_nodes = []
        self.cfg_exit_nodes = []
        self.function_def_node: dict = {}
        self.function_doc_string: dict = {}
        self.heads: list = []
        self.tails: list = []
        self.base_line: int = base_line

    def build_cfg(self):
        self.visit(ast.parse(self.source_code))
        self.cfg_nodes += self.cfg_exit_nodes
        return self.cfg_nodes

    def visit_Module(self, node):
        for item in node.body:
            self.visit(item)

    def visit_AugAssign(self, node: ast.AugAssign):
        content = astor.to_source(node).strip()
        temp = src.Model.CFGNode.CFGNode(node.lineno + self.base_line, content)
        self.add_link_to_previous(temp)
        self.cfg_nodes.append(temp)

    def visit_Raise(self, node: ast.Raise):
        content = astor.to_source(node).strip()
        temp = src.Model.CFGNode.CFGNode(node.lineno + self.base_line, content)
        if len(self.cfg_nodes) > 1:
            self.cfg_nodes[-1].add_child(temp)
        self.cfg_nodes.append(temp)

    def visit_FunctionDef(self, node):
        cfg_visitor = CFGVisitor('')

        # get docstring, @TODO
        doc_string = ast.get_docstring(node)

        # get args
        args: list = []
        for each_arg in node.args.args:
            args.append(each_arg.arg)

        # parse body
        for item in node.body:
            if isinstance(item, ast.Expr) and isinstance(item.value, ast.Str):
                continue
            cfg_visitor.visit(item)

        cfg_nodes = cfg_visitor.cfg_nodes
        if not cfg_nodes:
            return
        # concat args and function name
        func_node_name: str = f'def {node.name}'
        args_str: str = ''
        for each_arg in args:
            args_str += f'{each_arg}, '
        if len(args) > 0:
            args_str = args_str[:-2]
        # create cfg node
        entry_node = src.Model.CFGNode.FunctionNode(node.lineno + self.base_line, f'{func_node_name}({args_str})')

        # add variable info
        for each_arg in args:
            entry_node.defined_vars.add(each_arg)

        entry_node.add_child(cfg_nodes[0])
        entry_node.cfg_nodes += cfg_nodes
        self.function_def_node[f'{node.name}'] = entry_node
        self.function_doc_string[f'{node.name}'] = doc_string

    def visit_ClassDef(self, node):
        pass

    def visit_Try(self, node: ast.Try):
        # body
        cfg_visitor = CFGVisitor('')
        for item in node.body:
            cfg_visitor.visit(item)

        # exception
        for eachException in node.handlers:
            cfg_visitor = CFGVisitor('')
            for item in eachException.body:
                if isinstance(item, ast.Expr) and isinstance(item.value, ast.Str):
                    continue
                cfg_visitor.visit(item)
        # final
        cfg_visitor = CFGVisitor('')
        for item in node.finalbody:
            cfg_visitor.visit(item)




    def visit_Return(self, node):
        content = astor.to_source(node).strip()
        temp = src.Model.CFGNode.ReturnNode(node.lineno + self.base_line, content)
        self.add_link_to_previous(temp)
        self.cfg_exit_nodes.append(temp)

    def visit_Assign(self, node):
        content = astor.to_source(node).strip()
        temp = src.Model.CFGNode.CFGNode(node.lineno + self.base_line, content)
        self.add_link_to_previous(temp)
        self.cfg_nodes.append(temp)

    def visit_Expr(self, node):
        content = astor.to_source(node).strip()
        temp = src.Model.CFGNode.CFGNode(node.lineno + self.base_line, content)
        self.add_link_to_previous(temp)
        self.cfg_nodes.append(temp)

    def visit_If(self, node):
        content = astor.to_source(node.test).strip()
        if_stmt = src.Model.CFGNode.IfNode(node.lineno + self.base_line, content.split('\n')[0])
        node_collector: list = []

        tail = self.__get_last_tail()
        end_if = src.Model.CFGNode.EndIfNode(node.lineno + self.base_line)
        node_collector.append(if_stmt)

        if_body = node.body
        else_body = node.orelse if node.orelse else []

        current = None
        for stmt in if_body:
            if isinstance(stmt, ast.Break):
                current = [src.Model.CFGNode.BreakNode(stmt.lineno + self.base_line, 'break')]
                if_stmt.add_child(current)
                break
            elif isinstance(stmt, ast.Continue):
                current = [src.Model.CFGNode.ContinueNode(stmt.lineno + self.base_line, 'continue')]
                if_stmt.add_child(current)
                break

            child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line)
            child = child.build_cfg()
            if current is None:
                if_stmt.add_child(CFGVisitor.__get_head_node((child)))
            else:
                child_tails = CFGVisitor.__get_list_tail_node(current)
                child_heads = CFGVisitor.__get_head_node(child)
                for single_tail in child_tails:
                    for each_head in child_heads:
                        single_tail.add_child(each_head)
            if current is not None:
                current += child
            else:
                current = child
            # self.visit(stmt)

        if current is not None and len(current) > 0:
            tails = CFGVisitor.__get_list_tail_node(current)
            for child_tail in tails:
                child_tail.add_child(end_if)
            # if not isinstance(current[-1], src.Model.CFGNode.ReturnNode):
            #     current[-1].add_child(end_if)
            node_collector += current

        if not if_stmt.children:
            if_stmt.add_child(end_if)

        if len(else_body) > 0:
            else_nodes = []
            for each in else_body:
                # elif
                if isinstance(each, ast.If):
                    self.visit_elif(each, end_if=end_if)
                else:
                    # else statement
                    for stmt in else_body:
                        if isinstance(stmt, ast.Break):
                            else_nodes += [src.Model.CFGNode.BreakNode(stmt.lineno + self.base_line, 'break')]
                            break
                        elif isinstance(stmt, ast.Continue):
                            else_nodes += [src.Model.CFGNode.ContinueNode(stmt.lineno + self.base_line, 'continue')]
                            break

                        child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line).build_cfg()
                        else_nodes += child

                    if len(else_nodes) > 0:
                        else_nodes[-1].add_child(end_if)
                        if_stmt.add_child(CFGVisitor.__get_head_node(else_nodes))
                        node_collector += else_nodes
                    else:
                        if_stmt.add_child(end_if)
        else:
            if_stmt.add_child(end_if)


        for parent in tail:
            parent.add_child(if_stmt)
        self.cfg_nodes += node_collector
        self.cfg_nodes.append(end_if)
        self.tails = [end_if]

    # additional function to help parsing if-elif-else statement
    def visit_elif(self, node: ast.If, end_if: src.Model.CFGNode.EndIfNode):
        content = astor.to_source(node.test).strip()
        if_stmt = src.Model.CFGNode.IfNode(node.lineno + self.base_line, content.split('\n')[0])
        node_collector: list = []
        tail = self.__get_last_tail()
        node_collector.append(if_stmt)

        if_body = node.body
        else_body = node.orelse if node.orelse else []

        current = None
        for stmt in if_body:
            if isinstance(stmt, ast.Break):
                current = [src.Model.CFGNode.BreakNode(stmt.lineno + self.base_line, 'break')]
                if_stmt.add_child(current)
                break
            elif isinstance(stmt, ast.Continue):
                current = [src.Model.CFGNode.ContinueNode(stmt.lineno + self.base_line, 'continue')]
                if_stmt.add_child(current)
                break
            child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line).build_cfg()
            if_stmt.add_child(child)
            if current is not None:
                current += child
            else:
                current = child
            # self.visit(stmt)

        if current is not None and len(current) > 0:
            if not isinstance(current[-1], src.Model.CFGNode.ReturnNode):
                current[-1].add_child(end_if)
            node_collector += current

        if not if_stmt.children:
            if_stmt.add_child(end_if)

        if len(else_body) > 0:
            else_nodes = []
            for each in else_body:
                # elif
                if isinstance(each, ast.If):
                    self.visit_If(each)
                else:
                    # else statement
                    for stmt in else_body:
                        if isinstance(stmt, ast.Break):
                            else_nodes += [src.Model.CFGNode.BreakNode(stmt.lineno + self.base_line, 'break')]
                            break
                        elif isinstance(stmt, ast.Continue):
                            else_nodes += [src.Model.CFGNode.ContinueNode(stmt.lineno + self.base_line, 'continue')]
                            break

                        child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line).build_cfg()
                        else_nodes += child
                        # self.visit(stmt)
                    if len(else_nodes) > 0:
                        else_nodes[-1].add_child(end_if)
                        if_stmt.add_child(else_nodes[0])
                        node_collector += else_nodes
                    else:
                        if_stmt.add_child(end_if)
        else:
            if_stmt.add_child(end_if)

        for parent in tail:
            parent.add_child(if_stmt)
        self.cfg_nodes += node_collector

    # help function to connect break and continue node
    @staticmethod
    def connect_continue(while_node: src.Model.CFGNode.CFGNode, continue_nodes: list):
        for each in continue_nodes:
            each.clear_children()
            each.add_child(while_node)
            each.linked = True
    @staticmethod
    def connect_break(end_node: src.Model.CFGNode.CFGNode, break_nodes: list):
        for each in break_nodes:
            each.clear_children()
            each.add_child(end_node)
            each.linked = True

    def visit_While(self, node):

        content = astor.to_source(node.test).strip()
        end_while = src.Model.CFGNode.EndWhileNode(node.lineno + self.base_line)
        cfg_node = src.Model.CFGNode.WhileNode(node.lineno + self.base_line, content.split('\n')[0])
        cfg_node.add_child(end_while)
        self.add_link_to_previous(cfg_node)

        if hasattr(node, 'body'):
            current = []
            current_tail = []
            for stmt in node.body:
                child_visitor = CFGVisitor(astor.to_source(stmt).strip(), node.lineno + self.base_line)
                child = child_visitor.build_cfg()
                if len(current) > 0 and len(child) > 0:
                    if len(child_visitor.heads) != 0:
                        current[-1].add_child(child_visitor.heads)
                    else:
                        current[-1].add_child(CFGVisitor.__get_head_node(child))
                current += child
                current_tail = child_visitor.tails

            if len(current) > 0:
                if len(current_tail) > 0 :
                    for each_tail in current_tail:
                        each_tail.add_child(cfg_node)
                else:
                    current[-1].add_child(cfg_node)
                cfg_node.add_child(CFGVisitor.__get_head_node(current))
            else:
                cfg_node.add_child(end_while)
            # search break and continue node
            while_node = None
            continue_node = []
            break_node = []
            for each in current:
                if isinstance(each, src.Model.CFGNode.WhileNode):
                    while_node = each
                    self.connect_continue(while_node, break_node)
                    self.connect_break(end_while, break_node)
                    continue_node.clear()
                    break_node.clear()

                if isinstance(each, src.Model.CFGNode.BreakNode):
                    each.clear_children()
                    break_node.append(each)
                if isinstance(each, src.Model.CFGNode.ContinueNode):
                    each.clear_children()
                    continue_node.append(each)

            if while_node is None:
                # connect them
                self.connect_break(end_while, break_node)
                self.connect_continue(cfg_node, continue_node)
            self.cfg_nodes += current

        elif hasattr(node, 'orelse'):
            current = []
            for stmt in node.orelse:
                child = CFGVisitor(astor.to_source(stmt).strip(), stmt.lineno + self.base_line).build_cfg()
                current += child

            if len(current) > 0:
                current[-1].add_child(end_while)
                cfg_node.add_child(CFGVisitor.__get_head_node(current))
            else:
                cfg_node.add_child(end_while)

            self.cfg_nodes += current
        if len(self.heads) == 0:
            self.heads.append(cfg_node)

        self.cfg_nodes.append(cfg_node)
        self.cfg_nodes.append(end_while)
        self.tails = [end_while]

    def visit_For(self, node):
        content = astor.to_source(node).strip()
        cfg_node = src.Model.CFGNode.ForNode(node.lineno + self.base_line, content)

        end_for = src.Model.CFGNode.EndForNode(node.lineno + self.base_line)
        cfg_node.add_child(end_for)
        for_tails = self.__get_last_tail()

        if hasattr(node, 'body'):
            current = []
            for stmt in node.body:
                child_visitor = CFGVisitor(astor.to_source(stmt).strip(), node.lineno + self.base_line)
                child = child_visitor.build_cfg()
                if len(current) > 0 and len(child) > 0:
                    if len(child_visitor.heads) != 0:
                        current[-1].add_child(child_visitor.heads)
                    else:
                        current[-1].add_child(CFGVisitor.__get_head_node(child))
                current += child

            if len(current) > 0:
                # current[-1].add_child(end_for)
                tails = CFGVisitor.__get_list_tail_node(current)
                for each_tail in tails:
                    each_tail.add_child(cfg_node)
                cfg_node.add_child(CFGVisitor.__get_head_node(current))
            else:
                cfg_node.add_child(end_for)



            # search break and continue node
            for_node = None
            continue_node = []
            break_node = []
            for each in current:
                if isinstance(each, src.Model.CFGNode.ForNode):
                    for_node = each

                # collect first
                if isinstance(each, src.Model.CFGNode.BreakNode):
                    each.clear_children()
                    break_node.append(each)
                if isinstance(each, src.Model.CFGNode.ContinueNode):
                    each.clear_children()
                    continue_node.append(each)

                if isinstance(each, src.Model.CFGNode.EndForNode) and for_node is not None:
                    self.connect_continue(for_node, break_node)
                    self.connect_break(each, break_node)
                    continue_node.clear()
                    break_node.clear()

            if for_node is None:
                # connect them
                self.connect_break(end_for, break_node)
                self.connect_continue(cfg_node, continue_node)

            self.cfg_nodes += current

        for each in for_tails:
            each.add_child(cfg_node)
        if len(self.heads) == 0:
            self.heads.append(cfg_node)
        self.cfg_nodes.append(cfg_node)
        self.cfg_nodes.append(end_for)
        self.tails = [end_for]

    def export_cfg_to_mermaid(self):
        ret = "graph TD;\n"

        node_instance = {}
        id_counter: int = 1

        # build nodes
        for each in self.cfg_nodes:
            if id(each) not in node_instance:
                node_instance[id(each)] = id_counter
                id_counter = id_counter + 1
                ret += f'{node_instance[id(each)]}{str(each)}'
            for child in each.children:
                if id(child) not in node_instance:
                    node_instance[id(child)] = id_counter
                    id_counter = id_counter + 1
                    ret += f'{node_instance[id(child)]}{str(child)}'

        # Add edges
        for each in self.cfg_nodes:
            node_id = id(each)
            for child in each.children:
                child_id = id(child)
                ret += f'{node_instance[node_id]}-->{node_instance[child_id]}\n'

        return ret

    @staticmethod
    def __get_head_node(cfg_nodes: list) -> list:
        """
        help function to search the head nodes from a list
        """
        ret = []
        visited_table: dict = {}

        for each in cfg_nodes:
            if id(each) not in visited_table:
                visited_table[(id(each))] = each

        for each in cfg_nodes:
            for each_child in each.children:
                # if it is a child, it must not a head node
                try:
                    del  visited_table[id(each_child)]
                except KeyError:
                    pass

        for key, value in visited_table.items():
            ret.append(value)

        return ret
    @staticmethod
    def __get_list_tail_node(cfg_nodes: list) -> list:
        ret = []
        for each in cfg_nodes:

            if isinstance(type(each), src.Model.CFGNode.ReturnNode):
                continue

            if len(each.children) == 0:
                ret.append(each)
        return ret

    @staticmethod
    def __build_mermaid_once(cfg_nodes: list, after_fix: int) -> str:
        ret = f'subgraph \"{after_fix}\";\n'

        node_instance = {}
        id_counter: int = 1

        # build nodes
        for each in cfg_nodes:
            if id(each) not in node_instance:
                node_instance[id(each)] = id_counter
                id_counter = id_counter + 1
                ret += f'{node_instance[id(each)]}{str(each)}'
            for child in each.children:
                if id(child) not in node_instance:
                    node_instance[id(child)] = id_counter
                    id_counter = id_counter + 1
                    ret += f'{node_instance[id(child)]}{str(child)}'

        # Add edges
        for each in cfg_nodes:
            node_id = id(each)
            for child in each.children:
                child_id = id(child)
                ret += f'{node_instance[node_id]}-->{node_instance[child_id]}\n'

        return ret

    def add_link_to_previous(self, node: src.Model.CFGNode.CFGNode):
        parents = self.__get_last_tail()
        for each_parent in parents:
            each_parent.add_child(node)

    def __get_last_tail(self) -> list:
        ret = []
        for each in self.cfg_nodes:

            if isinstance(type(each), src.Model.CFGNode.ReturnNode):
                continue

            if len(each.children) == 0:
                ret.append(each)
        return ret