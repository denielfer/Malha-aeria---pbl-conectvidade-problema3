from json import JSONDecoder
from trecho import Trecho
from gerenciador_de_trajetos import Gerenciador_de_trajetos
decoder = JSONDecoder()
def load_conf_from_file(file_path:str) -> dict:
    conf = {}
    with open(file_path,'r',encoding="utf-8") as a:
        json_string = '{'+(','.join(a.readlines())).replace('\n','')+'}'
        return decoder.decode(json_string)

def __escrever_binario_de_conf__(conf):
    with open(f'arquivos_bin//{conf["nome"]}.bin','wb') as f:
        import pickle
        d = conf.copy()
        del(d['trechos'])
        del(d['trajetos'])
        pickle.dump(d,f)
class ConfiguraçãoMalSucedida(Exception):
    pass

def make_trechos(trechos:list[dict]):
    return [ Trecho(**a) for a in trechos ]

def manual_conf() -> dict:
    dados={}
    dados['nome'] = input("Digite o nome da compania: ")
    dados['ip'] = input("Digite o ip desse servidor: ")
    dados['port'] = input("Digite a porta na qual esse servidor sera executado: ")
    dados['trechos'] = []
    dados['voos']=[]
    dados['companias']={}
    dados['trajetos'] = Gerenciador_de_trajetos([])
    return dados


if(__name__== "__main__"):
    load_conf_from_file('.//src//arquivos_conf_testes//emp_c.txt')