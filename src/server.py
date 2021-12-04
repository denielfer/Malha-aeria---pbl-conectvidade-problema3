import threading
from flask import Flask, jsonify, request, render_template
import requests
import sys
from gerenciador_de_trajetos import Gerenciador_de_trajetos
from reservar_trajeto import Reservador_trajeto
from trecho import Trecho
import util
from time import sleep
from threading import Semaphore
from gerenciador_de_manager import Gerenciador_de_manager

pedidos_trajetos_pra_processar = []

dados = util.load(sys.argv)
if(dados is None):
    raise("Caregamento de informações não foi realizada com sucesso")
global todas_as_companhias #existe uma variável global chamada todas_as_companhias
todas_as_companhias = dados['companhias'].copy()
todas_as_companhias[dados['nome']] = f'http://{dados["ip"]}:{dados["port"]}'
t = util.inicializar_ring(dados['companhias'], todas_as_companhias)

if(t != None):
    todas_as_companhias = t

trajetos_para_reservar:list[Reservador_trajeto] = []
pode_reservar = Semaphore()
bool_fazendo_reserva = False
gerenciador_manager = Gerenciador_de_manager(companhias = todas_as_companhias, 
                                             trajetos_para_reservar = trajetos_para_reservar,
                                             who_am_i = dados['nome'],
                                             semaphore_de_liberação_resolver_pedidos = pode_reservar, 
                                             pode_fazer_reserva = bool_fazendo_reserva)

app = Flask(__name__)

def __get_whitch_companies_is_up__():
    '''
        Função que pinga os servidores conhecidos para sabermos qual esta up

        @return vetor contendo tuplas no sequinte formato (__nome_da_compania__,__is_up__) no qual 
        __nome_da_compania__ é o nome da compania guardada no sistema e __is_up__ é uam booleana 
        que indica True se o server responder
    '''
    returned = []
    companhias:dict = todas_as_companhias.copy() #caso uma companhia seja adicionada emquanto loopamos pelas companhias isso faz com que não quebre
    for companie, href in companhias.items():
        if(companie != dados['nome']):
            try:
                request = requests.get(f'{href}/ping', timeout = 0.5)
                returned.append((companie, request.status_code == 200))
            except Exception:
                returned.append((companie, False))
    return returned

def __get_base_context__():
    '''
        Retorna um dicionario contendo valores basicos que sao usados para renderizar todas as paginas que sao renderizadas

        @return: dict contendo 'title': nome da empresa, e 'companhia_is_up': vetor contendo retorno de __get_whitch_companies_is_up__
    '''
    return {'title':dados['nome'], 'companhia_is_up':__get_whitch_companies_is_up__()}

@app.route('/', methods=['GET'])
def home(): 
    '''
        Pagina home da pagina na qual é renderizada todos os voos da empresa
    
        Rota deve ser publica
    '''
    v = dados['voos']
    for n, a in enumerate(v): #inplace operation
        a['vagas'] = dados['trajetos'].trechos[n].get_vagas_livres()
    return render_template('home.html', base_context = __get_base_context__(), trechos = enumerate(v))

@app.route('/fazendo_operação', methods=['GET'])
def fazendo_operação():
    '''
        Rota privada para outras companhias verificarem se esta empresa esta fazendo operações, ( ao receber mensagem nesta travamos para que novas operações noa sejam mais feitas)
    '''
    global bool_fazendo_reserva # informamos ao python que esta variavel deve ser pega do escopo global
    temp = bool_fazendo_reserva
    bool_fazendo_reserva = False
    return f'{temp}', 201 if (temp) else 200 #retornamos 201 se estamos fazendo operação e 200 se não

@app.route('/set_ordem_manager', methods=['POST'])
def set_ordem_manager():
    '''
        Rota privada para setar a ordem do Ring
    '''
    temp = {companhia:href for companhia,href in request.form.items()}
    global todas_as_companhias
    todas_as_companhias = temp
    gerenciador_manager.companhias = temp
    return '', 200

@app.route('/get_ordem_manager', methods=['GET'])
def get_ordem_manager():
    '''
        Rota privada para pegar a ordem do Ring
    '''
    return jsonify(gerenciador_manager.companhias), 200

@app.route('/ciclo_iniciar', methods=['GET'])
def ciclo_iniciar():
    '''
        Rota privada que é usada quando um ciclo do ring vai ser iniciado
    '''
    gerenciador_manager.init_circulo()
    return f'{gerenciador_manager.ciclo}', 200 if (gerenciador_manager.ciclo) else 0 #retornamos 201 se estamos fazendo operação e 200 se não

@app.route('/tem_manager', methods=['GET'])
def tem_manager():
    '''
        Rota privada para pergunta se o Ring ja esta em operação
    '''
    return f'{gerenciador_manager.manager}', 200 if (gerenciador_manager.manager is not None) else 0 

@app.route('/ping', methods=['GET'])
def ping():
    '''
        rota para saber se o server esta up
    '''
    return '', 200

def __get_self_voos__():
    '''
        Função para conseguir as informações sobre todos os voos desta empresa

        @return: list contendo um dict no qual estao os dados dos voos desta empresa
    '''
    return [trecho.get_info() for trecho in dados['trechos']]

def __get_all_voos__():
    '''
        Função para conseguir as informações sobre todos os voos das empresas conhecidas
        isso é feito atravez de uma consulta a todas as empresas conhecidas

        @return: list contendo um dict no qual estão os dados dos voos das empresas conhecidas
    '''
    hrefs:dict = todas_as_companhias.copy()
    voos = []
    for c in hrefs.values():
        try:
            voos += requests.get(f"{c}/voos", timeout = 1).json()
        except Exception: #caso algum não responda, apenas vamos para o próximo
            pass
    return voos

def __get_gerenciador_todos_trajetos__():
    '''
        Cria um objeto de gerenciador de trajetos com todos os voos das companhias conhecidas

        @return: Gerenciador_de_trajetos no qual estao configurados todos os voos das empresas conhecidas
    '''
    return Gerenciador_de_trajetos(util.make_trechos(__get_all_voos__()))

def __render_home_with_text__(text:str=''):
    '''
        Função que renderiza uma pagina com o base context e um texto centralizado 

        @param text: string que sera colocada na pagina
        @return: pagina html contendo o template default com um texto centralizado no conteudo
    '''
    return render_template('text.html', base_context=__get_base_context__(), text = text)

@app.route('/reservar', methods=['POST'])
def reservar_trajetos():
    '''
        Rota para reservar trajeto, usada pelas interfacies para requirir uma reservar
        
        Aqui o pedido sera colocado numa fila de resolução e quando o pedido for reservado é gerado o retorno 
    '''
    r = Reservador_trajeto(request.form['trajeto'], href_companhias = todas_as_companhias)
    trajetos_para_reservar.append(r)
    while not(r.status == "Erro" or r.status == "Reservado"):
        sleep(1)
    success = r.status == "Reservado"
    return jsonify({'success':success,'text':r.text}), 200

@app.route('/ver_trajetos/', methods=['POST'])
def ver_trajetos():
    '''
        Rota apra pagina que mostra todos os trajetos possiveis entre cidade de saida e destino
    '''
    saida, destino = request.form['saida'], request.form['destino']
    gerenciador = __get_gerenciador_todos_trajetos__()
    success, resultado = gerenciador.make_all_trajetos(saida = saida, destino = destino)
    lista_trajetos =[ 
        (
            i+1,
            [(
                n+1, trajeto[n], trajeto[n+1],
                [
                    {
                        'companhia': trecho['companhia'],
                        'opção': trecho['opção'],
                        'custo': trecho["custo"],
                        'tempo': trecho['tempo'],
                        'vagas': gerenciador.get_vagas(trecho['index']),
                        'display': j == 0
                    } for j, trecho in enumerate(gerenciador.find_from_to(trajeto[n], trajeto[n+1])) 
                    # Não precisa verificar se vai retornar None, pois aqui os parâmetros passados 
                    #    vem da busca feita no mesmo objeto, então o retorno da busca são de cidades 
                    #    que existem no objeto
                ],
                n != len(trajeto) - 2
            )for n in range(len(trajeto) - 1)]
        ) for i, trajeto in enumerate(resultado)
    ]
    return render_template('trajeto_view.html', success = success, resultado = lista_trajetos, saida = saida, destino = destino, base_context = __get_base_context__())


@app.route('/ocupar/<saida>/<destino>/<companhia>', methods=['GET'])
def reserva_passagem(saida:str, destino:str, companhia:str):
    '''
        Rota privada para uso interno, na qual o assento de um voos com saida e 
        destino especificados sao reservados na companhia especidicada

        Esta rota repassa request para outras companhias caso a companhia especificada
        seja uma conhecida
    '''     
    if(companhia == dados["nome"]): # se for para nossa compania
        caminho = dados['trajetos'].find_from_to(saida, destino) #retorna None se não tiver caminho, se tiver, retorna lista com trechos
        if(caminho is None):
            return "Trajeto indicado nao foi encontrado", 404 #caso a companhia não tenha o trecho solicitado, retornamos que o trajeto pedido não existe
        for caminho in caminho: #se tivermos mais de um, quer dizer que a companhia oferece mais de um voo de {saida} para {destino}, então se não der pra ocupar vaga em um, tentaremos no próximo
            if(dados['trechos'][caminho['index']].ocupar_vaga()): #se conseguimos ocupar a vaga com sucesso
                return 'Assento alocado', 200 #retornamos ok
        return f'limite de passageiros ja alcançado no voo de "{saida}" -> "{destino}" na companhia "{companhia}"', 404 #se passamos por toda as opções da companhia e não foi possível reservar, retornamos que todos os assentos estão alocados 
    elif(companhia in todas_as_companhias): # se for para uma conhecida
        href = f"{todas_as_companhias[companhia]}/ocupar/{saida}/{destino}/{companhia}"
        try:
            request = requests.get(href, timeout = 60)
        except Exception as e: #essa exception seria relacionada ao request
            return f'Problema na reserva do trecho "{saida}" -> "{destino}" na companhia "{companhia}"', 404
        return request.text, request.status_code
    else: # caso nao conhecermos a compania informada
        return  'A companhia informada não foi encontrada', 404

@app.route('/desocupar/<saida>/<destino>/<companhia>', methods=['GET'])
def desreservar_passagem(saida:str, destino:str, companhia:str):
    '''
        Rota privada para uso interno, na qual o assento de um voos com saida e 
        destino especificados sao desreservados na companhia especidicada

        Esta rota repassa request para outras companhias caso a companhia especificada
        seja uma conhecida
    '''     
    if(companhia == dados["nome"]):#se for do nosso servidor o desocupamos a vaga
        caminhos = dados['trajetos'].find_from_to(saida, destino) #retorna None se não tiver caminho, se tiver retorna lista com trechos
        if(caminhos is None):
            return "Trajeto indicado não foi encontrado", 404 #caso a companhia não tenha o trecho solicitado, retornamos que o trajeto pedido não existe

        #se tivermos mais de um elemento em caminhos, quer dizer que a companhia oferece mais de um voo de {saida} para {destino}, 
        # então se não der pra desocupar vaga em um, tentaremos no próximo (assim ainda não existe suporte para desocupar acento 
        # de um voos específico caso 2 ou mais voos da mesma companhia façam o mesmo trecho, assim, ele vai liberando vagas na 
        # ordem na qual os trechos foram colocados no arquivo de conf, ou adicionados posteriormente)
        for caminho in caminhos: 
            if(dados['trechos'][caminho['index']].liberar_vaga()): #se conseguimos liberar a vaga com sucesso
                return 'Assento desalocado', 200 #retornamos ok
        return  f'O voo já tem sua capacidade máxima livre. Voo de "{saida}" -> "{destino}" na companhia "{companhia}"', 404 # se passamos por toda as opções da companhia e nao foi possivel reservar retornamos que todos os assentos estao alocados ja 
    elif(companhia in todas_as_companhias): #se o pedido for pra um servidor conhecido, repassamos o request para ele
        href = f"{todas_as_companhias[companhia]}/desocupar/{saida}/{destino}/{companhia}"
        try:
            request = requests.get(href, timeout = 60)
        except Exception as e: #essa exception seria relacionada ao request
            return  f'Problema na reserva do trecho "{saida}" -> "{destino}" na companhia "{companhia}"', 404
        return request.text,request.status_code
    else:
        return 'A companhia informada não foi encontrada', 404

@app.route('/voos', methods=['GET'])
def voos():
    '''
        rota para pegar os voos desta compania
    '''
    return jsonify(__get_self_voos__()), 200

@app.route('/all_voos', methods=['GET'])
def all_voos():
    '''
        rota para pegar todos os voos das companhias conhecidas
    '''
    return jsonify(__get_all_voos__()), 200

@app.route('/add_voo', methods=['GET', "POST"])
def add_voo():
    '''
        Rota para adicionar um voo nesta compania

        Se request tipo GET gera um formulario de adição
        se POST tenta fazer a adição
    '''
    if(request.method == "GET"):
        return render_template('add_voo.html', base_context=__get_base_context__())
    else:
        try:
            novo_voo = {'saida': request.form['saida'],
                        'destino': request.form['destino'],
                        'custo': float(request.form['custo']),
                        "tempo": float(request.form['tempo']),
                        "empresa": dados["nome"],
                        "quantidade_maxima_de_vagas": int(request.form['max_pass'])}
        except Exception as e: #caso o formulário não tenha os campos que buscamos
            return  __render_home_with_text__(text = 'NA MORAL? METEU ESSA MERMO?'), 404
        dados['voos'].append(novo_voo)
        util.__escrever_binario_de_conf__(dados)
        trecho = Trecho(**novo_voo)
        #dados['trechos'].append(trecho)
        dados['trajetos'].add_voo(trecho)
        return __render_home_with_text__(text = f'O voo de {trecho.saida} para {trecho.destino} foi adicionado, com custo de {trecho.custo} e tempo de {trecho.tempo}'), 200

semaphore_add_companhia = threading.Semaphore()

@app.route('/add_companhia', methods=['GET', 'POST'])
def add_companhia():
    '''
        Rota para adicionar uma compania conehcida nesta compania

        Se request tipo GET gera um formulario de adição
        se POST tenta fazer a adição
    '''
    if(request.method == "GET"):
        return render_template('add_companhia.html', base_context=__get_base_context__())
    else:
        global todas_as_companhias #para informarmos ao python que não estamos criando uma variavel local chamada todas_as_companhias e sim usando a global
        semaphore_add_companhia.acquire()
        try:
            temp = todas_as_companhias.copy()
            if(dados['nome'] in temp):
                del(temp[dados['nome']])
            dados["companhias"][request.form['companhia']] = request.form["href"]
            todas_as_companhias[request.form['companhia']] = request.form["href"]
            temp = todas_as_companhias
            t = util.inicializar_ring(dados['companhias'],todas_as_companhias)
            if(t != None and t.items()!=todas_as_companhias.items()): # se tiver resposta de outras companhias
                todas_as_companhias = t
                gerenciador_manager.companhias = t
                gerenciador_manager.end_afther_ciclo()
                for href in temp:
                    try:
                        requests.get(f'{href}/end_after_cicle')
                    except Exception:
                        pass
            semaphore_add_companhia.release()
            util.__escrever_binario_de_conf__(dados)
            return  __render_home_with_text__(text=f'a companhia: {request.form["companhia"]} for adicionada a lista de companhias afiliadas. A api desta companhia se encontra na porta: {request.form["href"]}'),200
        except Exception as e: # caso o formulario nao tenha os campos que buscamos
            semaphore_add_companhia.release()
            return  __render_home_with_text__(text='NA MORAL? METEU ESSA MERMO?'),404

@app.route('/end_after_cicle', methods=['GET'])
def end_after_cicle():
    '''
        Rota privada para indicar que devem espera um aviso de outra 
        compania para iniciarmos nosso procimo ciclo no ring
        assim nao automaticamento iniciamos um novo ciclo
    '''
    gerenciador_manager.end_afther_ciclo()
    return '',200

@app.route('/companhias_conectadas', methods=['GET', 'POST'])
def companhias_conectadas():
    '''
        Rota que se request GET retorna as copanhias conhecidas
        se POST faz uma adição das companhias nao conhecidas
        passadas neste request, as propagando no sistema e 
        retorna como ficou todas as companhias conhecidas apos a auteração
    '''
    if(request.method == "GET"):
        temp = todas_as_companhias.copy()
        if(dados['nome'] in temp):
            del(temp[dados['nome']])
        return jsonify(temp), 200
    else:# se POST pois so é aceito GET e POST
        semaphore_add_companhia.acquire()
        try:
            companhias_to_check = request.form # companhias passadas no request
        except Exception:
            return '', 404
        companhias_already_in={}
        companhias_out = {}
        for companhia,href in companhias_to_check.items(): # para as companhias recebidas no post
            if(companhia in todas_as_companhias and todas_as_companhias[companhia] == href): # se ela ja estiver nos dados e o href for o passado
                companhias_already_in[companhia] = href # adicionanos nas companhias que ja tinhamos
            else: # se nao 
                todas_as_companhias[companhia] = href
                companhias_out[companhia] = href
        if( companhias_out != {}):
            util.propagate(todas_as_companhias,companhias_out) # propagamos para as comapanias que ja tinhamos todas as companhias que temos agora
        semaphore_add_companhia.release()
        return jsonify(todas_as_companhias),200

if(__name__== "__main__"): # se executar este arquivo iniciamos o servidor 
    print( dados['ip'], dados['port'])
    app.run(host = dados['ip'], port = dados['port'], debug = False)