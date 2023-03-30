import ast
import src.CFGBuilder
def main(file_name:str):
    with open(file_name, 'r') as src_file:
        src_code = src_file.read()
    a = src.CFGBuilder.CFGVisitor(src_code)
    a.build_cfg()
    code = a.export_cfg_to_mermaid()
    x = 1

if __name__ == '__main__':
    main('target.py')