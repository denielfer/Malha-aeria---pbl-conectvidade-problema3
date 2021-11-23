from json import JSONDecoder
from trecho import Trecho
from gerenciador_de_trajetos import Gerenciador_de_trajetos
decoder = JSONDecoder()
def load_conf_from_file(file_path:str) -> dict:
    conf = {}
    with open(file_path,'r',encoding="utf-8") as a:
        json_string = '{' + (','.join(a.readlines())).replace('\n', '') + '}'
        return decoder.decode(json_string)

class ConfiguraçãoMalSucedida(Exception):
    pass

def make_trechos(trechos:list[dict]):
    return [Trecho(**trecho) for trecho in trechos]

def manual_conf() -> dict:
    dados = {}
    dados['nome'] = input("Digite o nome da companhia: ")
    dados['ip'] = input("Digite o ip desse servidor: ")
    dados['port'] = input("Digite a porta na qual esse servidor será executado: ")
    dados['trechos'] = []
    dados['voos'] = []
    dados['companias'] = {}
    dados['trajetos'] = Gerenciador_de_trajetos([])
    return dados


if(__name__== "__main__"):
    load_conf_from_file('.//src//arquivos_conf_testes//emp_c.txt')