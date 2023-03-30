import copy


class DDGVisitor:

    def __init__(self, cfg_nodes: list):
        self.cfg_nodes = copy.deepcopy(cfg_nodes)
        self.ddg_nodes: list = []

    def build_ddg(self):
        pass

    def export_mermaid_code(self) -> str:
        ret = ''

        return ret