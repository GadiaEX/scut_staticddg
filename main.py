import src.CFGBuilder
import src.DDGBuilder
import json
import src.Utils
import flask
import time

debug_counter: int = 0
def debug_specific(file_name: str, counter: int) -> None:
    with open(file_name, 'r') as src_file:
        json_codes: list = src_file.readlines()
    json_codes = json.loads(json_codes[counter])
    start = time.time()
    src_code: str = json_codes['code']
    print('\n' + src_code)
    build_once(src_code)
    end = time.time()
    print(f'counter: {counter}, time:{(end - start) * 1000}ms')
    src_file.close()

def build_once(src_code: str) -> str:
    # print('\n' + src_code)
    cfg = src.CFGBuilder.CFGVisitor(src_code)
    cfg.build_cfg()
    # code = cfg.export_cfg_to_mermaid()
    data = src.Utils.DataContainer(cfg, None, True)
    # main
    ddg = src.DDGBuilder.DDGVisitor(cfg.cfg_nodes)
    ddg.build_ddg()

    # function
    ddgs: list = [ddg]
    for key,value in cfg.function_def_node.items():
        ddgs.append(src.DDGBuilder.DDGVisitor(value.cfg_nodes, key))
        ddgs[-1].build_ddg()
    data = src.Utils.DataContainer(cfg, ddgs, True)
    return str(data)
def sample_test(file_name: str = 'target.py'):
    with open(file_name, 'r') as src_file:
        src_code = src_file.read()
    src_file.close()
    return build_once(src_code)

def test_main(file_name:str):
    global debug_counter
    with open(file_name, 'r') as src_file:
        json_codes: list = src_file.readlines()
    succ_counter: int = 0
    for each_json_raw_code in json_codes:
        start = time.time()
        json_code = json.loads(each_json_raw_code)
        try:
            build_once(json_code['code'])
            succ_counter = succ_counter + 1
        except Exception:
            pass
        debug_counter = debug_counter + 1
        end = time.time()
        spend_time: float = (end - start)*1000
        print(f'counter: {json_codes.index(each_json_raw_code)}, time:{spend_time}ms')
        if spend_time > 1000.0:
            print(json_code['code'])
    print(succ_counter)
    src_file.close()

def interface_main(src_code: str) -> str:
    return build_once(src_code)

app = flask.Flask(__name__)

@app.route('/python', methods=['POST'])
def index():
    code = flask.request.get_json()['code']
    return build_once(code)

if __name__ == '__main__':
    # app.run()
    sample_test('temp.py')
