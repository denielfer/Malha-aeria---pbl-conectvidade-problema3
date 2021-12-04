from json import JSONDecoder
import threading
from trecho import Trecho
from gerenciador_de_trajetos import Gerenciador_de_trajetos
from requests import get,post

decoder = JSONDecoder()
def load_conf_from_file(file_path:str) -> dict:
    conf = {}
    with open(file_path, 'r', encoding = "utf-8") as a:
        json_string = '{' + (','.join(a.readlines())).replace('\n', '') + '}'
        return decoder.decode(json_string)

def __escrever_binario_de_conf__(conf):
    with open(f'arquivos_bin//{conf["nome"]}.bin', 'wb') as f:
        import pickle
        d = conf.copy()
        del(d['trechos'])
        del(d['trajetos'])
        pickle.dump(d, f)
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
    dados['companhias'] = {}
    dados['trajetos'] = Gerenciador_de_trajetos([])
    return dados


def __propagate__(to_which_companies, what_companies):
    to_which_companies = to_which_companies.copy()
    for href in to_which_companies.values():
        try:
            post(f'{href}/companhias_conectadas', data = what_companies, timeout = 5)
        except Exception:
            pass

def propagate(to_which_companies,what_companies):
    t = threading.Thread(target = __propagate__, args = (to_which_companies, what_companies))
    t.setDaemon(True)
    t.start()

def load(argv):
    dados = None
    for n, arg in enumerate(argv): # procuramos se foi passado arquivo de configuração
        if( arg == '-c'): # caso tenha sido passado caregamos ele
            dados = load_conf_from_file(argv[n + 1])
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

def inicializar(companhias, nome, self_href, todas_as_companhias):
    ## Busca de companhias conectadas de nas companhias ja conectadas
    continuar = True
    companhias_to_do = companhias.copy()
    companhias_avizadas = {}
    while continuar:
        companhias_copy = companhias.copy()
        __propagate__(companhias_to_do, todas_as_companhias)
        # com a linha a cima propagamos para todas as companhias que conhecemos
        # (no primeira iteração) todas as companhias que conhecemos, e nas 
        # proximas ( 2 iteração endiante ) para as que passamos a conhecer 
        # todas as que conhecemos
        for companhia, href in companhias_to_do.items(): 
            if(companhia not in companhias_avizadas):
                # assim todas as companhias que conhecemos receberam uma mensagem 
                # indicando que existimos ( 1 iteração ) e as novas que passamos 
                # a conhecer receberao posteriormente ( 2 iteração em diante )
                try:
                    post(f'{href}/add_companhia', data = {"companhia":nome, "href":self_href})
                    companhias_avizadas.append(companhia)
                except Exception:
                    pass
            try:
                resp = get(f'{href}/companhias_conectadas', timeout = 5)
                resp = resp.json()
            except Exception: #se der timeout ou se não tiver nada no json (não conseguir, pega um json na resposta) ou se o server estiver offline
                continue #segue pra próxima
            companhias_copy.update(resp) #se conseguiu adicionamos na nossa cópia (pra não dar problema no loop)
        if(nome in companhias_copy): #apagamos a referência desta companhia do conjunto de companhias conhecidas
            del(companhias_copy[nome])
        if(companhias_copy.items() == companhias.items()): #se o resultado da busca é igual ao que já temos
            continuar = False #acabamos a busca
        else: #se não
            companhias_adicionadas = {}
            for companhia, href in companhias_copy.items():
                if not(companhia in companhias and companhias[companhia] == href):
                    companhias_adicionadas[companhia] = href
            companhias.update(companhias_copy)
            companhias_to_do = companhias_adicionadas
    #assim, as que já estavam no sistema e nós não conhecíamos, são conhecidos por todos

def inicializar_ring(companhias, todas_as_companhias):
    print('propagando informaçoes')
    __propagate__(companhias, todas_as_companhias) #enviamos para todas que conhecemos todas as que conhecemos (incluindo a gente)
    ordens = {}
    print("colhendo informações do ring")
    for companhia, href in companhias.items():
        try:
            resp = get(f'{href}/get_ordem_manager').json()
        except:
            continue
        ordens[companhia] = resp
    base_ordem = None
    print('confirmando ')
    for ordem in ordens.values():
        if(base_ordem is None):
            base_ordem = ordem
        elif(ordem != base_ordem):
            base_ordem.update(ordem)
            change = True
    todas_as_companhias = base_ordem if (base_ordem is not None) else companhias
    for href in todas_as_companhias.values():
        try:
            post(f'{href}/set_ordem_manager', data = base_ordem)
        except:
            pass
    print('inicialização terminada')
    return base_ordem



if(__name__== "__main__"):
    load_conf_from_file('.//src//arquivos_conf_testes//emp_c.txt')