from json import JSONDecoder
import threading
from trecho import Trecho
from gerenciador_de_trajetos import Gerenciador_de_trajetos
from requests import get,post

decoder = JSONDecoder()
def load_conf_from_file(file_path:str) -> dict:
    conf = {}
    with open(file_path,'r',encoding="utf-8") as a:
        json_string = '{' + (','.join(a.readlines())).replace('\n', '') + '}'
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


def __propagate__(to_which_companies,what_companies):
    to_which_companies = to_which_companies.copy()
    for href in to_which_companies.values():
        try:
            print(what_companies)
            post(f'{href}/companias_conectadas',data=what_companies, timeout=5)
        except Exception:
            pass

def propagate(to_which_companies,what_companies):
    t = threading.Thread(target=__propagate__,args=(to_which_companies,what_companies))
    t.setDaemon(True)
    t.start()

def load(argv):
    dados = None
    for n,arg in enumerate(argv): # procuramos se foi passado arquivo de configuração
        if( arg == '-c'): # caso tenha sido passado caregamos ele
            dados = load_conf_from_file(argv[n+1])
            dados['trechos'] = make_trechos(dados['voos'])
            dados['trajetos'] = Gerenciador_de_trajetos(dados['trechos'])
            __escrever_binario_de_conf__(dados)
        if( arg == '-cb'): # caso tenha sido passado caregamos ele
            import pickle
            with open(argv[n+1], 'rb') as f:
                dados = pickle.load(f)
                dados['trechos'] = make_trechos(dados['voos'])
                dados['trajetos'] = Gerenciador_de_trajetos(dados['trechos'])
    if(not dados): # caso nao tenha sido caregado os dado atravez de um arquivo de configuração
        dados = manual_conf()
    return dados

def inicializar(companias,nome,self_href): # para testa usar arquivos de companias que a conheça b, b conheca c e c conheça a, ao iniciar uma por uma ver se conforme novas sao iniciadas elas passam a se conhecer
    ## Passando para os que conhecemos as companias que temos
    __propagate__(companias,companias) # para todas as companias que conhecemos passamos todas as companias que conhecemos
    # assim todas as que conhecemos sao conhecidos por todos

    ## Para todas as companias que conhecemos nos adicionamos a lista de companias que elas conhecem
    for href in companias.values():
        try:
            post(f'{href}/add_compania',data={"compania":nome,"href":self_href,"propagate":'True'})
        except Exception:
            pass
    # assim todas as companias que conhecemos nos conhecem tambem

    ## Busca de companias conectadas de nas companias ja conectadas
    continuar = True
    companias_to_do = companias.copy()
    while continuar:
        companias_copy = companias.copy()
        for compania,href in companias_to_do.items():
            print(f'pergunta para: {href}')
            try:
                resp = get(f'{href}/companias_conectadas',timeout=5)
                resp = resp.json()
            except Exception: # se der timeout ou se nao tiver nada no json ( nao conseguir pega um json na resposta ) ou se o server estiver offline
                print(f' erro request para {compania}')
                continue # segue pra proxima
            print(f'resposta foi: {resp}')
            companias_copy.update(resp) # se conseguio adicionamos na nossa copia ( pra nao dar problema no loop )
        if(nome in companias_copy): # apagamos a referencia desta compania do conjunto de companias conhecidas
            del(companias_copy[nome])
        if(companias_copy.items() == companias.items()): # se o resultado da busca é igual ao que ja temos
            continuar = False # acabamos a busca
        else: # se nao
            companias_adicionadas={}
            for compania,href in companias_copy.items():
                if not(compania in companias and companias[compania] == href):
                    companias_adicionadas[compania]=href
            companias.update(companias_copy)
            companias_to_do = companias_adicionadas
    # assim as que ja estavam no sistema e nos nao conheciamos sao conhecidos por todos

if(__name__== "__main__"):
    load_conf_from_file('.//src//arquivos_conf_testes//emp_c.txt')