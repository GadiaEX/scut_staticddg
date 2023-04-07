import src.CFGBuilder
import src.DDGBuilder
import json

debug_counter: int = 0
def debug_specific(file_name: str, counter: int) -> None:
    with open(file_name, 'r') as src_file:
        json_codes: list = src_file.readlines()
    build_once(json.loads(json_codes[counter])['code'])
    src_file.close()

def build_once(src_code: str) -> None:
    # print('\n' + src_code)
    cfg = src.CFGBuilder.CFGVisitor(src_code)
    cfg.build_cfg()
    code = cfg.export_cfg_to_mermaid()

    ddg = src.DDGBuilder.DDGVisitor(cfg.cfg_nodes)
    ddg.build_ddg()
    code = ddg.export_mermaid_code()
    print(code)
def sample_test():
    with open('target.py', 'r') as src_file:
        src_code = src_file.read()
    build_once(src_code)
    src_file.close()

def main(file_name:str):
    global debug_counter
    with open(file_name, 'r') as src_file:
        json_codes: list = src_file.readlines()
    succ_counter: int = 0
    for each_json_raw_code in json_codes:
        json_code = json.loads(each_json_raw_code)
        try:
            build_once(json_code['code'])
            succ_counter = succ_counter + 1
        except Exception:
            pass
        debug_counter = debug_counter + 1
        print(debug_counter)
    print(succ_counter)
    src_file.close()


if __name__ == '__main__':
    # debug_specific('python_test_0.jsonl', 1940)
    try:
        main('python_test_0.jsonl')
    except Exception:
        print(debug_counter)
