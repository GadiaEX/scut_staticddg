import copy
import src.Model

class DDGVisitor:

    def __init__(self, cfg_nodes: list):
        self.cfg_nodes = copy.deepcopy(cfg_nodes)
        # all node instances collector
        self.ddg_nodes: list = []
        self.ddg_node_counter: int = 1
        # from instance id (id function) to search cfg node
        self.cfg_node_id_mapping = {}
        self.ddg_node_id_mapping = {}
        # from my id to search node
        self.ddg_node_instances: dict = {}

        for each in cfg_nodes:
            if id(each) not in self.cfg_node_id_mapping:
                self.cfg_node_id_mapping[id(each)] = self.ddg_node_counter
                # create new ddg node
                node = src.Model.DDGNode(each)
                self.ddg_node_instances[self.ddg_node_counter] = node
                self.ddg_node_id_mapping[id(node)] = self.ddg_node_counter
                self.ddg_node_counter = self.ddg_node_counter + 1
                self.ddg_nodes.append(node)

            for child in each.children:
                if id(child) not in self.cfg_node_id_mapping:
                    self.cfg_node_id_mapping[id(child)] = self.ddg_node_counter
                    # create new ddg node
                    node = src.Model.DDGNode(child)
                    self.ddg_node_instances[self.ddg_node_counter] = node
                    self.ddg_node_id_mapping[id(node)] = self.ddg_node_counter
                    self.ddg_node_counter = self.ddg_node_counter + 1
                    self.ddg_nodes.append(node)

    def build_ddg(self):
        # from var_name to node_id
        var_dict: dict = {}
        visited_table: set = set()
        for each in self.ddg_nodes:
            if id(each) not in visited_table:
                self.dfs_search(var_dict, visited_table, each)

    def dfs_search(self, var_dict: dict, visited_table: set, node: src.Model.CFGNode):
        visited_table.add(id(node))

        # deal the variable
        for each in node.used_vars:
            try:
                target_obj_id = var_dict[each]
                target_id = self.ddg_node_id_mapping[target_obj_id]
                node.add_child(self.ddg_node_instances[target_id])
            except KeyError:
                pass

        for each in node.defined_vars:
            var_dict[each] = id(node)


        for each in node.children:
            self.dfs_search(var_dict, visited_table, each)

    def export_mermaid_code(self) -> str:
        ret = "graph TD;\n"

        node_instance = {}
        id_counter: int = 1

        # build nodes
        for each in self.cfg_nodes:
            if id(each) not in node_instance:
                node_instance[id(each)] = id_counter
                id_counter = id_counter + 1
                content = each.content.replace('\n', '\\n')
                ret += f'{node_instance[id(each)]}["{content}\n(line: {each.line})"]\n'
            for child in each.children:
                if id(child) not in node_instance:
                    node_instance[id(child)] = id_counter
                    id_counter = id_counter + 1
                    content = child.content.replace('\n', '\\n')
                    ret += f'{node_instance[id(child)]}["{content}\n(line: {child.line})"]\n'

        # Add edges
        for each in self.cfg_nodes:
            node_id = id(each)
            for child in each.children:
                child_id = id(child)
                ret += f'{node_instance[node_id]}-->{node_instance[child_id]}\n'

        return ret