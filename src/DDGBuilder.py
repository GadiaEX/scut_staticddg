import copy
import src.Model


class DDGVisitor:

    def __init__(self, cfg_nodes: list):
        self.cfg_nodes = copy.deepcopy(cfg_nodes)
        # all node instances collector
        self.ddg_nodes: list = []
        self.ddg_node_counter: int = 1
        # from instance id (id function) to search node
        self.cfg_node_id_mapping = {}
        self.ddg_node_id_mapping = {}
        # reverse cfg_node_id_mapping for tick end node out
        self.cfg_obj_lookup_table = {}
        # from my id to search node
        self.ddg_node_instances: dict = {}

        for each in self.cfg_nodes:

            if id(each) not in self.cfg_node_id_mapping:
                self.create_ddg_node(each)

            for child in each.children:
                if id(child) not in self.cfg_node_id_mapping:
                    self.create_ddg_node(child)

    def create_ddg_node(self, node: src.Model.CFGNode):
        self.cfg_node_id_mapping[id(node)] = self.ddg_node_counter
        # create new ddg node
        node = src.Model.DDGNode(node)
        self.ddg_node_instances[self.ddg_node_counter] = node
        self.ddg_node_id_mapping[id(node)] = self.ddg_node_counter
        self.cfg_obj_lookup_table[self.ddg_node_counter] = node
        self.ddg_node_counter = self.ddg_node_counter + 1
        self.ddg_nodes.append(node)

    def build_ddg(self):
        # from var_name to node_id
        var_dict: dict = {}
        visited_table: set = set()
        for each in self.cfg_nodes:
            if id(each) not in visited_table:
                self.dfs_search(var_dict, visited_table, each)

    def dfs_search(self, var_dict: dict, visited_table: set, node: src.Model.CFGNode):
        visited_table.add(id(node))
        var_backup: list = []
        ddg_node_id: int = self.cfg_node_id_mapping[id(node)]
        ddg_node: src.Model.DDGNode = self.ddg_node_instances[ddg_node_id]
        # deal the variable
        for each in node.used_vars:
            try:
                target_obj_id = var_dict[each]
                target_id = self.ddg_node_id_mapping[target_obj_id]
                ddg_node.add_parent(self.ddg_node_instances[target_id])
            except KeyError:
                pass

        for each in node.defined_vars:
            try:
                var_backup.append({each: var_dict[each]})
            except KeyError:
                pass
            var_dict[each] = id(ddg_node)

        for each in node.children:
            self.dfs_search(var_dict, visited_table, each)

        for each in node.defined_vars:
            # reverse variable, delete them
            del var_dict[each]

        for each in var_backup:
            for key, value in each.items():
                var_dict[key] = value

    def export_mermaid_code(self) -> str:
        ret = "graph TD;\n"

        node_instance = {}
        id_counter: int = 1
        # build nodes
        for each in self.ddg_nodes:
            if self.is_end_node(each):
                continue
            if id(each) not in node_instance:
                node_instance[id(each)] = id_counter
                id_counter = id_counter + 1
                content = each.content.replace('\n', '\\n')
                ret += f'{node_instance[id(each)]}["{content}\n(line: {each.line})"]\n'
            for each_parent in each.parent:
                if self.is_end_node(each_parent):
                    continue
                if id(each_parent) not in node_instance:
                    node_instance[id(each_parent)] = id_counter
                    id_counter = id_counter + 1
                    content = each_parent.content.replace('\n', '\\n')
                    ret += f'{node_instance[id(each_parent)]}["{content}\n(line: {each_parent.line})"]\n'

        # Add edges
        for each in self.ddg_nodes:
            if self.is_end_node(each):
                continue
            node_id = id(each)
            for each_parent in each.parent:
                if self.is_end_node(each_parent):
                    continue
                parent_id = id(each_parent)
                ret += f'{node_instance[parent_id]}-->{node_instance[node_id]}\n'

        return ret

    def is_end_node(self, ddg_node: src.Model.DDGNode) -> bool:
        node_obj_id = id(ddg_node)
        node_id = self.ddg_node_id_mapping[node_obj_id]
        cfg_node = self.cfg_obj_lookup_table[node_id]

        if issubclass(type(cfg_node), src.Model.EndNode):
            return True
        else:
            return False
