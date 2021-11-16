from json import JSONDecoder
from trecho import Trecho
decoder = JSONDecoder()
def load_conf_from_file(file_path:str) -> dict:
    conf = {}
    with open(file_path,'r',encoding="utf-8") as a:
        json_string = '{'+(','.join(a.readlines())).replace('\n','')+'}'
        return decoder.decode(json_string)

class ConfiguraçãoMalSucedida(Exception):
    pass

def make_trechos(trechos:list[dict]):
    return [ Trecho(**a) for a in trechos ]
