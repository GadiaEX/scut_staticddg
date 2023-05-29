import copy
import logging

from flask_cors import cross_origin
import src.CFGBuilder
import src.DDGBuilder
import json
import src.Utils
import flask
import time
import flask_cors

logging.getLogger(('flask_cors')).level = logging.DEBUG

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
        # if spend_time > 1000.0:
            # print(json_code['code'])
        print(f'index: {json_codes.index(each_json_raw_code)}, time:{spend_time}ms')
    print(succ_counter)
    src_file.close()

def interface_main(src_code: str) -> str:
    return build_once(src_code)

app = flask.Flask(__name__)
cors = flask_cors.CORS(app, resources={r"/*": {"origins": "*"}})

last_result:str = ''

@app.route('/python', methods=['POST'])
@cross_origin()
def index():
    global last_result
    try:
        code = flask.request.get_json()['code']
        ret = build_once(code)
        last_result = copy.deepcopy(ret)
        return ret
    except Exception as e:
        ret = src.Utils.DataContainer.generate_error(last_result, 'syntax error', str(e))
        return ret

@app.route('/batch', methods=['POST'])
@cross_origin()
def batch():
    codes: list = flask.request.get_json()['codes']
    ret: list = []
    counter: int = 0
    for each in codes:
        try:
            ret.append(build_once(each['code']))
        except Exception as e:
            ret.append(str(e))
        counter = counter + 1

        if counter > 10:
            break

    return json.dumps(ret)


if __name__ == '__main__':
    app.run()
    # test_main('python_test_0.jsonl')
    # print(sample_test())
    # sample_test()


