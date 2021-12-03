import threading
from typing import Sequence
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

# dados = None
pedidos_trajetos_pra_processar = []

dados = util.load(sys.argv)
# print(dados)
if(dados is None):
    raise("Caregamento de informações não foi realizada com sucesso")
todas_as_companhias = dados['companhias'].copy()
todas_as_companhias[dados['nome']] = f'http://{dados["ip"]}:{dados["port"]}'
t = util.inicializar_ring(dados['companhias'], todas_as_companhias)
# print(t)
if(t != None):
    todas_as_companhias = t

# print(f"Este servidor corresponde ao da companhia: {dados['nome']} e esta sendo executado no link: http://{dados['ip']}:{dados['port']}")

# precisamos de um dicionario com todas as companhias 
# ( o que inclui a nossa que nao esta nesse dicionario 
# e precisa ser um dicionario que é atualizado conforme novas 
# companhias entram no sistema)

# print(f'{dados=}\n\n\n{todas_as_companhias=}')
# input()

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
    return {'title':dados['nome'], 'companhia_is_up':__get_whitch_companies_is_up__()}

@app.route('/', methods=['GET'])
def home():
    v = dados['voos']
    for n, a in enumerate(v): #inplace operation
        a['vagas'] = dados['trajetos'].trechos[n].get_vagas_livres()
    return render_template('home.html', base_context = __get_base_context__(), trechos = enumerate(v))

@app.route('/fazendo_operação', methods=['GET'])
def fazendo_operação():
    bool_fazendo_reserva = False
    return f'{bool_fazendo_reserva}', 201 if (bool_fazendo_reserva) else 200 #retornamos 201 se estamos fazendo operação e 200 se não

@app.route('/set_ordem_manager', methods=['POST'])
def set_ordem_manager():
    temp = {companhia:href for companhia,href in request.form.items()}
    todas_as_companhias = temp
    gerenciador_manager.companhias = temp
    return'',200

@app.route('/get_ordem_manager', methods=['GET'])
def get_ordem_manager():
    return jsonify(gerenciador_manager.companhias), 200

@app.route('/ciclo_iniciar', methods=['GET'])
def ciclo_iniciar():
    # print(request.form)
    # print("___________")
    gerenciador_manager.init_circulo()
    return f'{gerenciador_manager.ciclo}', 200 if (gerenciador_manager.ciclo) else 0 #retornamos 201 se estamos fazendo operação e 200 se não

@app.route('/tem_manager', methods=['GET'])
def tem_manager():
    return f'{gerenciador_manager.manager}', 200 if (gerenciador_manager.manager is not None) else 0 

@app.route('/ping', methods=['GET'])
def ping():
    return '', 200

def __get_self_voos__():
    return [trecho.get_info() for trecho in dados['trechos']]

def __get_all_voos__():
    hrefs:dict = todas_as_companhias.copy()
    voos = []
    for c in hrefs.values():
        try:
            # print(hrefs[c])
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
    r = Reservador_trajeto(request.form['trajeto'], href_companhias = todas_as_companhias)
    # return __render_home_with_text__(text=r.reservar())
    trajetos_para_reservar.append(r)
    while not(r.status == "Erro" or r.status == "Reservado"):
        # print(r.status,(r.status != "Erro" or r.status != "Reservado"))
        sleep(1)
    # return __render_home_with_text__(text=r.text)
    success = r.status == "Reservado"
    return jsonify({'success':success,'text':r.text}), 200

@app.route('/ver_trajetos/', methods=['POST'])
def ver_trajetos():
    saida, destino = request.form['saida'], request.form['destino']
    # print('from', saida, 'to', destino)
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
    Rota não pública para uso interno
    '''
    if(companhia == dados["nome"]):
        caminho = dados['trajetos'].find_from_to(saida, destino)
        if(caminho == None):
            return "Trajeto indicado nao foi encontrado", 404
        caminho = caminho[0]
        if (caminho):
            if(dados['trechos'][caminho['index']].ocupar_vaga()):
                return 'Assento alocado', 200
            else:
                return f'limite de passageiros ja alcançado no voo de "{saida}" -> "{destino}" na companhia "{companhia}"', 404
        return  f'Trecho "{saida}" -> "{destino}" não encontrado na companhia "{companhia}"', 404
    elif(companhia in todas_as_companhias):
        dados_companhia = todas_as_companhias[companhia]
        href = f"http://{dados_companhia['ip']}:{dados_companhia['port']}/ocupar/{saida}/{destino}/{companhia}"
        try:
            request = requests.get(href, timeout=60)
        except Exception as e: #essa exception seria relacionada ao request
            return f'Problema na reserva do trecho "{saida}" -> "{destino}" na companhia "{companhia}"', 404
        return request.raw,request.status_code # ainda nao testado se isso sobrepoe o if else abaixo
        if(request.status_code != 200): #se tiver uma forma mais fácil, pode tirar o if else aqui (ex: retornando o request recebido)
            return 'Problema na reserva do trecho {saida} -> {destino} na companhia {companhia}', 404
        else:
            return 'Assento alocado', 200
    else:
        return  'A companhia informada não foi encontrada', 404

@app.route('/desocupar/<saida>/<destino>/<companhia>', methods=['GET'])
def desreservar_passagem(saida:str, destino:str, companhia:str):
    '''
    Rota não pública para uso interno
    '''
    if(companhia == dados["nome"]):
        caminho = dados['trajetos'].find_from_to(saida,destino)
        if(caminho == None):
            return "Trajeto indicado não foi encontrado", 404
        caminho = caminho[0]
        if (caminho):
            if(dados['trechos'][caminho['index']].liberar_vaga()):
                return 'Assento desalocado', 200
            else:
                return  f'O voo já tem sua capacidade máxima livre. Voo de "{saida}" -> "{destino}" na companhia "{companhia}"', 200
        return  f'Trecho "{saida}" -> "{destino}" não encontrado na companhia "{companhia}"', 404
    elif(companhia in todas_as_companhias):
        dados_companhia = todas_as_companhias[companhia]
        href = f"http://{dados_companhia['ip']}:{dados_companhia['port']}/desocupar/{saida}/{destino}/{companhia}"
        try:
            request = requests.get(href, timeout = 60)
        except Exception as e: #essa exception seria relacionada ao request
            return  f'Problema na reserva do trecho "{saida}" -> "{destino}" na companhia "{companhia}"', 404
        return request.raw,request.status_code #ainda não testado se isso sobrepõe o if else abaixo
        # if(request.status_code != 200): #se tiver uma forma mais fácil, pode tirar o if else aqui (ex: retornando o request recebido)
        #     return 'Problema na reserva do trecho {saida} -> {destino} na companhia {companhia}', 404
        # else:
        #     return 'Assento alocado', 200
    else:
        return 'A companhia informada não foi encontrada', 404

@app.route('/voos', methods=['GET'])
def voos():
    return jsonify(__get_self_voos__()), 200

@app.route('/all_voos', methods=['GET'])
def all_voos():
    return jsonify(__get_all_voos__()), 200

@app.route('/add_voo', methods=['GET', "POST"])
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
            return  __render_home_with_text__(text = 'NA MORAL? METEU ESSA MERMO?'), 404
        dados['voos'].append(novo_voo)
        util.__escrever_binario_de_conf__(dados)
        trecho = Trecho(**novo_voo)
        dados['trechos'].append(trecho)
        dados['trajetos'].add_voo(trecho)
        return __render_home_with_text__(text = f'O voo de {trecho.saida} para {trecho.destino} foi adicionado, com custo de {trecho.custo} e tempo de {trecho.tempo}'), 200

semaphore_add_companhia = threading.Semaphore()

@app.route('/add_companhia', methods=['GET', 'POST'])
def add_companhia():
    if(request.method == "GET"):
        return render_template('add_companhia.html', base_context=__get_base_context__())
    else:
        semaphore_add_companhia.acquire()
        try:
            temp = todas_as_companhias.copy()
            if(dados['nome'] in temp):
                del(temp[dados['nome']])
            util.propagate(temp,{request.form['companhia']:request.form["href"]},todas_as_companhias)
            dados["companhias"][request.form['companhia']] = request.form["href"]
            todas_as_companhias[request.form['companhia']] = request.form["href"]
            semaphore_add_companhia.release()
            util.__escrever_binario_de_conf__(dados)
            return  __render_home_with_text__(text=f'a companhia: {request.form["companhia"]} for adicionada a lista de companhias afiliadas. A api desta companhia se encontra na porta: {request.form["href"]}'),200
        except Exception: #caso o formulário não tenha os campos que buscamos
            semaphore_add_companhia.release()
            return  __render_home_with_text__(text = 'NA MORAL? METEU ESSA MERMO?'), 404

@app.route('/companhias_conectadas', methods=['GET', 'POST'])
def companhias_conectadas():
    if(request.method == "GET"):
        temp = todas_as_companhias.copy()
        if(dados['nome'] in temp):
            del(temp[dados['nome']])
        return jsonify(temp), 200
    else:
        semaphore_add_companhia.acquire()
        try:
            # print(request.form)
            companhias_to_check = request.form #companhias passadas no request
        except Exception:
            return '', 404
        # print("-----------",companhias_to_check)
        companhias_already_in = {}
        companhias_out = {}
        for companhia,href in companhias_to_check.items(): #para as companhias recebidas no post
            if(companhia in todas_as_companhias and todas_as_companhias[companhia] == href): # se ela ja estiver nos dados e o href for o passado
                companhias_already_in[companhia] = href # adicionanos nas companhias que já tínhamos
            else: # se nao 
                todas_as_companhias[companhia] = href
                companhias_out[companhia] = href
        if( companhias_out != {}):
            util.propagate(todas_as_companhias,companhias_out) #propagamos para as comapanhias que já tínhamos todas as companhias que temos agora
        semaphore_add_companhia.release()
        # print("///////////", todas_as_companhias)
        return jsonify(todas_as_companhias), 200

if(__name__== "__main__"):
    print( dados['ip'], dados['port'])
    app.run(host = dados['ip'], port = dados['port'], debug = False)