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
global todas_as_companias # existe uma variavel global chamada todas_as_companias
todas_as_companias = dados['companias'].copy()
todas_as_companias[dados['nome']] = f'http://{dados["ip"]}:{dados["port"]}'
t = util.inicializar_ring(dados['companias'],todas_as_companias)

if(t != None):
    todas_as_companias = t

trajetos_para_reservar:list[Reservador_trajeto] = []
pode_reservar = Semaphore()
bool_fazendo_reserva = False
gerenciador_manager = Gerenciador_de_manager(companias = todas_as_companias, 
                                             trajetos_para_reservar = trajetos_para_reservar,
                                             who_am_i = dados['nome'],
                                             semapharo_de_liberação_resolver_pedidos = pode_reservar, 
                                             pode_fazer_reserva = bool_fazendo_reserva)

app = Flask(__name__)

def __get_whitch_companies_is_up__():
    returned = []
    companias:dict = todas_as_companias.copy() # caso uma companhia seja adicionada emquanto loopamos pelas companias isso faz com q nao quebre
    for companie,href in companias.items():
        if(companie != dados['nome']):
            try:
                request = requests.get(f'{href}/ping', timeout = 0.5)
                returned.append((companie, request.status_code == 200))
            except Exception:
                returned.append((companie, False))
    return returned

def __get_base_context__():
    return {'title':dados['nome'],'compania_is_up':__get_whitch_companies_is_up__()}

@app.route('/', methods=['GET'])
def home():
    v = dados['voos']
    for n, a in enumerate(v): # inplace operation
        a['vagas'] = dados['trajetos'].trechos[n].get_vagas_livres()
    return render_template('home.html', base_context = __get_base_context__(), trechos = enumerate(v))

@app.route('/fazendo_operação', methods=['GET'])
def fazendo_operação():
    bool_fazendo_reserva = False
    return f'{bool_fazendo_reserva}', 201 if (bool_fazendo_reserva) else 200 # retornamos 201 se estamos fazendo operação e 200 se nao

@app.route('/set_ordem_manager', methods=['POST'])
def set_ordem_manager():
    temp = {compania:href for compania,href in request.form.items()}
    global todas_as_companias
    todas_as_companias = temp
    gerenciador_manager.companias = temp
    return'',200

@app.route('/get_ordem_manager', methods=['GET'])
def get_ordem_manager():
    return jsonify(gerenciador_manager.companias), 200

@app.route('/ciclo_iniciar', methods=['GET'])
def ciclo_iniciar():
    gerenciador_manager.init_circulo()
    return f'{gerenciador_manager.ciclo}', 200 if (gerenciador_manager.ciclo) else 0 # retornamos 201 se estamos fazendo operação e 200 se nao

@app.route('/tem_manager', methods=['GET'])
def tem_manager():
    return f'{gerenciador_manager.manager}', 200 if (gerenciador_manager.manager is not None) else 0 

@app.route('/ping', methods=['GET'])
def ping():
    return '', 200

def __get_self_voos__():
    return [trecho.get_info() for trecho in dados['trechos']]

def __get_all_voos__():
    hrefs:dict = todas_as_companias.copy()
    voos = []
    for c in hrefs.values():
        try:
            voos += requests.get(f"{c}/voos", timeout = 1).json()
        except Exception: #caso algum não responda, apenas vamos para o próximo
            pass
    return voos

def __get_gerenciador_todos_trajetos__():
    return Gerenciador_de_trajetos(util.make_trechos(__get_all_voos__()))

def __render_home_with_text__(text=''):
        return render_template('text.html', base_context=__get_base_context__(), text = text)

@app.route('/reservar', methods=['POST'])
def reservar_trajetos():
    r = Reservador_trajeto(request.form['trajeto'], href_companias = todas_as_companias)
    trajetos_para_reservar.append(r)
    while not(r.status == "Erro" or r.status == "Reservado"):
        sleep(1)
    success = r.status == "Reservado"
    return jsonify({'success':success,'text':r.text}), 200

@app.route('/ver_trajetos/', methods=['POST'])
def ver_trajetos():
    saida,destino = request.form['saida'], request.form['destino']
    gerenciador = __get_gerenciador_todos_trajetos__()
    success,resultado = gerenciador.make_all_trajetos(saida=saida,destino=destino)
    lista_trajetos =[ 
        (
            i+1,
            [(
                n+1,trajeto[n],trajeto[n+1],
                [
                    {
                        'compania': trecho['compania'],
                        'opção': trecho['opção'],
                        'custo': trecho["custo"],
                        'tempo': trecho['tempo'],
                        'vagas': gerenciador.get_vagas(trecho['index']),
                        'display': j==0
                    } for j, trecho in enumerate(gerenciador.find_from_to(trajeto[n], trajeto[n+1])) 
                    # Não precisa verificar se vai retornar None, pois aqui os parâmetros passados 
                    #    vem da busca feita no mesmo objeto, então o retorno da busca são de cidades 
                    #    que existem no objeto
                ],
                n != len(trajeto)-2
            )for n in range(len(trajeto)-1)]
        ) for i, trajeto in enumerate(resultado)
    ]
    return render_template('trajeto_view.html',success=success,resultado=lista_trajetos,saida=saida,destino=destino,base_context=__get_base_context__())


@app.route('/ocupar/<saida>/<destino>/<compania>', methods=['GET'])
def reserva_passagem(saida:str, destino:str, compania:str):
    '''
    Rota não pública para uso interno
    '''
    if(compania == dados["nome"]):
        caminhos = dados['trajetos'].find_from_to(saida, destino) # retorna None se nao tiver caminho se tiver retorna lista com trechos
        if(caminhos is None):
            return "Trajeto indicado nao foi encontrado", 404 # caso a compania nao tenha o trecho solicitado retornamos que o trajeto pedido nao existe
        for caminho in caminhos: # se tivermos mais de um quer dizer q a compania ofere mais de um vol de {saida} para {destino} entao se nao der pra ocupar vaga em um tentaremos no proximo
            if(dados['trechos'][caminho['index']].ocupar_vaga()): # se conseguimos ocupar a vaga com sucesso
                return 'Assento alocado', 200 # retornamos ok
        return f'limite de passageiros ja alcançado no voo de "{saida}" -> "{destino}" na companhia "{compania}"', 404 # se passamos por toda as opções da compania e nao foi possivel reservar retornamos que todos os assentos estao alocados ja 
    elif(compania in todas_as_companias):
        href = f"{todas_as_companias[compania]}/ocupar/{saida}/{destino}/{compania}"
        try:
            request = requests.get(href, timeout=60)
        except Exception as e: #essa exception seria relacionada ao request
            return f'Problema na reserva do trecho "{saida}" -> "{destino}" na companhia "{compania}"', 404
        return request.text,request.status_code
    else:
        return  'A companhia informada não foi encontrada', 404

@app.route('/desocupar/<saida>/<destino>/<compania>', methods=['GET'])
def desreservar_passagem(saida:str, destino:str, compania:str):
    '''
    Rota não pública para uso interno
    '''
    if(compania == dados["nome"]):# se for do nosso servidor o desocupamos a vaga
        caminhos = dados['trajetos'].find_from_to(saida, destino) # retorna None se nao tiver caminho se tiver retorna lista com trechos
        if(caminhos is None):
            return "Trajeto indicado não foi encontrado", 404 # caso a compania nao tenha o trecho solicitado retornamos que o trajeto pedido nao existe
        # se tivermos mais de um quer dizer q a compania ofere mais de um vol de {saida} para {destino} entao se nao der pra desocupar vaga em um tentaremos no proximo 
        # ( assim ainda nao existe suporte para desocupar acento de um voos especifico caso 2 ou mais voos da mesma compania fassam o mesmo trecho, assim ele vai liberando 
        # vagas na ordem na qual os trechos foram colocados no arquivo de conf, ou adicionados posteriormente )
        for caminho in caminhos: 
            if(dados['trechos'][caminho['index']].liberar_vaga()): # se conseguimos liberar a vaga com sucesso
                return 'Assento desalocado',200 # retornamos ok
        return  f'O voo já tem sua capacidade máxima livre. Voo de "{saida}" -> "{destino}" na companhia "{compania}"', 404 # se passamos por toda as opções da compania e nao foi possivel reservar retornamos que todos os assentos estao alocados ja 
    elif(compania in todas_as_companias): # se o pedido for pra um servidor conhecido repassamos o request para ele
        href = f"{todas_as_companias[compania]}/desocupar/{saida}/{destino}/{compania}"
        try:
            request = requests.get(href, timeout=60)
        except Exception as e: #essa exception seria relacionada ao request
            return  f'Problema na reserva do trecho "{saida}" -> "{destino}" na companhia "{compania}"', 404
        return request.text,request.status_code
    else:
        return 'A companhia informada não foi encontrada', 404

@app.route('/voos', methods=['GET'])
def voos():
    return jsonify(__get_self_voos__()), 200

@app.route('/all_voos', methods=['GET'])
def all_voos():
    return jsonify(__get_all_voos__()), 200

@app.route('/add_voo', methods=['GET',"POST"])
def add_voo():
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
            return  __render_home_with_text__(text='NA MORAL? METEU ESSA MERMO?'), 404
        dados['voos'].append(novo_voo)
        util.__escrever_binario_de_conf__(dados)
        trecho = Trecho(**novo_voo)
        #dados['trechos'].append(trecho)
        dados['trajetos'].add_voo(trecho)
        return __render_home_with_text__(text=f'O voo de {trecho.saida} para {trecho.destino} foi adicionado, com custo de {trecho.custo} e tempo de {trecho.tempo}'), 200

semapharo_add_compania = threading.Semaphore()

@app.route('/add_compania', methods=['GET', 'POST'])
def add_compania():
    if(request.method == "GET"):
        return render_template('add_compania.html', base_context=__get_base_context__())
    else:
        global todas_as_companias # para informamos ao python que nao estamos criando uma variavel local chamada todas_as_companias e sim usando a global
        semapharo_add_compania.acquire()
        try:
            temp = todas_as_companias.copy()
            if(dados['nome'] in temp):
                del(temp[dados['nome']])
            dados["companias"][request.form['compania']] = request.form["href"]
            todas_as_companias[request.form['compania']] = request.form["href"]
            temp = todas_as_companias
            t = util.inicializar_ring(dados['companias'],todas_as_companias)
            if(t != None and t.items()!=todas_as_companias.items()): # se tiver resposta de outras companias
                todas_as_companias = t
                gerenciador_manager.companias = t
                gerenciador_manager.end_afther_ciclo()
                for href in temp:
                    try:
                        requests.get(f'{href}/end_after_cicle')
                    except Exception:
                        pass
            semapharo_add_compania.release()
            util.__escrever_binario_de_conf__(dados)
            return  __render_home_with_text__(text=f'a compania: {request.form["compania"]} for adicionada a lista de companias afiliadas. A api desta compania se encontra na porta: {request.form["href"]}'),200
        except Exception as e: # caso o formulario nao tenha os campos que buscamos
            semapharo_add_compania.release()
            return  __render_home_with_text__(text='NA MORAL? METEU ESSA MERMO?'),404

@app.route('/end_after_cicle', methods=['GET'])
def end_after_cicle():
    gerenciador_manager.end_afther_ciclo()
    return '',200

@app.route('/companias_conectadas', methods=['GET', 'POST'])
def companias_conectadas():
    if(request.method == "GET"):
        temp = todas_as_companias.copy()
        if(dados['nome'] in temp):
            del(temp[dados['nome']])
        return jsonify(temp),200
    else:
        semapharo_add_compania.acquire()
        try:
            companias_to_check = request.form # companias passadas no request
        except Exception:
            return '',404
        companias_already_in={}
        companias_out = {}
        for compania,href in companias_to_check.items(): # para as companias recebidas no post
            if(compania in todas_as_companias and todas_as_companias[compania] == href): # se ela ja estiver nos dados e o href for o passado
                companias_already_in[compania] = href # adicionanos nas companias que ja tinhamos
            else: # se nao 
                todas_as_companias[compania] = href
                companias_out[compania] = href
        if( companias_out != {}):
            util.propagate(todas_as_companias,companias_out) # propagamos para as comapanias que ja tinhamos todas as companias que temos agora
        semapharo_add_compania.release()
        return jsonify(todas_as_companias),200

if(__name__== "__main__"):
    print( dados['ip'], dados['port'])
    app.run(host = dados['ip'], port = dados['port'], debug = False)