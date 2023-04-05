import src.CFGBuilder
import src.DDGBuilder
import json

def build_once(src_code: str) -> None:
    cfg = src.CFGBuilder.CFGVisitor(src_code)
    cfg.build_cfg()
    code = cfg.export_cfg_to_mermaid()

    ddg = src.DDGBuilder.DDGVisitor(cfg.cfg_nodes)
    ddg.build_ddg()
    code = ddg.export_mermaid_code()
    print(code)

def main(file_name:str):
    with open(file_name, 'r') as src_file:
        json_codes: list = src_file.readlines()

    for each_json_raw_code in json_codes:
        json_code = json.loads(each_json_raw_code)
        build_once(json_code['code'])

if __name__ == '__main__':
    main('python_test_0.jsonl')