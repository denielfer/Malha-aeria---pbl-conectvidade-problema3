from json import JSONDecoder
import threading
from trecho import Trecho
from gerenciador_de_trajetos import Gerenciador_de_trajetos
from requests import get,post

decoder = JSONDecoder()
def load_conf_from_file(file_path:str) -> dict:
    '''
        Função que carega as configurações apartir de um arquivo

        @param file_path: string contendo o caminho do arquivo que sera caregado
        @return dict contendo as configurações colocadas no arquivo
    '''
    with open(file_path, 'r', encoding = "utf-8") as a:
        json_string = '{' + (','.join(a.readlines())).replace('\n', '') + '}'
        return decoder.decode(json_string)

def __escrever_binario_de_conf__(conf):
    '''
        Função que escreve as configurações passadas em um arquivo

        @param conf: dict cotnendo as configurações que serao escritas
    '''
    with open(f'arquivos_bin//{conf["nome"]}.bin', 'wb') as f:
        import pickle
        d = conf.copy()
        del(d['trechos'])
        del(d['trajetos'])
        pickle.dump(d, f)
class ConfiguraçãoMalSucedida(Exception):
    '''
        Exception de load mal sucedido
    '''
    pass

def make_trechos(trechos:list[dict]):
    '''
        Função que retorna uma lista de objetos do tipo trecho gerador apartir dos dados
        presentes em {trechos}

        @param trechos: list de dict no qual cada dict deve conter as informações para geração de um Trecho
        @return list de Trecho sendo uma lista dos trechos gerados apartir dos dados presenters em {trechos}
    '''
    return [Trecho(**trecho) for trecho in trechos]

def manual_conf() -> dict:
    '''
        Funcão que gera uma configuração manual do servidor

        @return dict contendo as configurações do servidor
    '''
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
    '''
        Função que faz a propagação de {what_companies} para {to_which_companies}

        Função usada para propagar alguma nova compania para as conhecidas ( havendo suport para enviar mutiplas ao mesmo tempo )

        @param to_which_companies: dict que tem como value o href das companhias para qual {what_companies} sera enviado
        @param what_companies: dict dict contendo como key o nome da compania e value o href desta compania
    '''
    to_which_companies = to_which_companies.copy()
    for href in to_which_companies.values():
        try:
            post(f'{href}/companhias_conectadas', data = what_companies, timeout = 5)
        except Exception:
            pass

def propagate(to_which_companies,what_companies):
    '''
        Função que cria uma thread para fazer a propagação das companhias informadas para as companhias passadas

        @param to_which_companies: dict que tem como value o href das companhias para qual {what_companies} sera enviado
        @param what_companies: dict dict contendo como key o nome da compania e value o href desta compania
    '''
    t = threading.Thread(target = __propagate__, args = (to_which_companies, what_companies))
    t.setDaemon(True)
    t.start()

def load(argv):
    '''
        Função responsavel por olhar entre os parametros passados para inicialização do servidor e 
        determina se o load é por arquivo txt, binario ou manual

        @param argv: list de parametros passados no terminal quando o arquivo server.py foi executado
    '''
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
    '''
        Função legado de inicialização ( nao tem inicialização do ring )

        @param companhias: dict contendo como key nome da compania e value o href da api desta compania
        @param nome: string contendo o nome da nossa colpania
        @param self_href: string contendo o href da nossa API
        @param todas_as_companhias: dict contendo como key nome da compania e value o href da api desta compania ( este dicionario 
            é igual ao {companhias} com adição dos dados da nossa compania ) 
    '''
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
    '''
        Função que faz a propagação das companhias conhecidas e inicialização do Ring, verificando com companhias conhecidas

        @param companhias: dict contendo como key nome da compania e value o href da api desta compania
        @param todas_as_companhias: dict contendo como key nome da compania e value o href da api desta compania ( este dicionario 
            é igual ao {companhias} com adição dos dados da nossa compania ) 
    '''
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