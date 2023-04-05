import src.CFGBuilder
import src.DDGBuilder

def main(file_name:str):
    with open(file_name, 'r') as src_file:
        src_code = src_file.read()
    cfg = src.CFGBuilder.CFGVisitor(src_code)
    cfg.build_cfg()
    code = cfg.export_cfg_to_mermaid()

    ddg = src.DDGBuilder.DDGVisitor(cfg.cfg_nodes)
    ddg.build_ddg()
    code = ddg.export_mermaid_code()
    print(code)

if __name__ == '__main__':
    main('target.py')