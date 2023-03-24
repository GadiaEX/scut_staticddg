import ast
from src.model import Block
from src.builder import DDG_Builder
from src.builder import export_data
def main(file_name:str):
    with open(file_name, 'r') as src_file:
        src = src_file.read()
    tree = ast.parse(src, mode='exec')

    # build
    id: int = 1
    single_block = Block(id, tree)
    ddg_builder = DDG_Builder(single_block)
    DDGs :list = ddg_builder.DDGs

    # export
    data = []
    for each in DDGs:
        data.append(export_data(each))


if __name__ == '__main__':
    main('target.py')