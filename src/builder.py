"""
    Data dependence graph builder, for building Graph use
"""
# Gadia, 2023
import src.model


class Connection:
    """
        Describe the linkage among nodes in GUI, it is a directed arrow in graph
    """

    def __init__(self, node):
        self.node: GraphicNode = node
        self.target: GraphicNode = None


class GraphicNode(src.model.CFG_Node):
    """
        To convert the CFG_Node into graph
    """

    def __init__(self, node: src.model.CFG_Node):
        super().__init__()

        self.line =  node.line
        self.code = node.code
        self.doc_str = node.doc_str
        self.doc_str_token = node.doc_str_token
        # use or not in code segment
        self.sha = node.sha
        self.variable_define = node.variable_define
        self.variable_depend = node.variable_depend

        # arrow in DDG, inner is the aimed to this node
        # outer is from this node but aimed to another node
        self.inner: list = []
        self.outer: list = []


class DDG:
    """
    a single DDG class definition
    """

    def __init__(self):
        self.head = None
        self.node = []


class DDG_Builder:
    """
    builder for a block, which may contain many DDGs
    """

    def __init__(self, block: src.model.Block):
        self.variable_mapping: dict = {}
        self.DDGs = self.__process_one_block__(block)

    def __process_one_block__(self, block: src.model.Block) -> [DDG]:

        ret = []

        # transfer the node to grapic node
        node_collector: list = []
        for each in block.cfg_node:
            node = GraphicNode(each)
            node_collector.append(node)

        # build linkage
        # link the Nodes in one block
        # @TODO(gadiahan) schema leaves some problem
        ret += self.__build_connection(node_collector)

        for each in block.blocks:
            ret += self.__process_one_block__(each)

        return ret

    def __build_connection(self, nodes: list) -> [DDG]:
        # @TODO(gadiahan) build linkage, O(n^2)
        # @TODO(gadiahan) how to recognize different DDGs ?
        # [], {} -> O(n);
        ret = []
        for each in nodes:
            # @TODO(gadiahan) how to deal with if-else statement ?
            for each_var in each.variable_define:
                self.variable_mapping[each_var] = each

            for each_var in each.variable_depend:
                # search
                try:
                    # data from node, directed to each
                    node = self.variable_mapping[each_var]
                    if node is each:
                        continue
                    # build connection
                    connection = Connection(node)
                    connection.target = each
                    node.outer.append(connection)
                    each.inner.append(connection)
                except KeyError:
                    pass

        for each in nodes:
            if len(each.inner) == 0:
                ddg = DDG()
                ddg.head = each
                ret.append(ddg)

        return ret


def export_data(ddg: DDG):
    pass
