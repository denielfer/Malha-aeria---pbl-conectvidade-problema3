from flask import Flask, jsonify, request,render_template
import requests
import sys
from gerenciador_de_trajetos import Gerenciador_de_trajetos
from reservar_trajeto import Reservador_trajeto
dados = None

for n,arg in enumerate(sys.argv): # procuramos se foi passado arquivo de configuração
    if( arg == '-c'): # caso tenha sido passado caregamos ele
        from util import load_conf_from_file, make_trechos
        dados = load_conf_from_file(sys.argv[n+1])
        dados['trechos'] = make_trechos(dados['voos'])
        dados['trajetos'] = Gerenciador_de_trajetos(dados['trechos'])
        
if(not dados): # caso nao tenha sido caregado os dado atravez de um arquivo de configuração
    from util import ConfiguraçãoMalSucedida
    print("[SERVIDOR] ERRO DE INICIALIZAÇÂO: Nenhuma configuração foi passada")
    raise ConfiguraçãoMalSucedida('A configuração não foi realizada')

app = Flask(__name__)

def __get_href_companias__():
    d = dados['companias']
    return [(compania,f"http://{dados['companias'][compania]['ip']}:{d[compania]['port']}") for compania in d]

def __get_all_href__():
    a = __get_href_companias__()
    b = { c:h for c,h in a }
    b[dados['nome']] = f"http://{dados['ip']}:{dados['port']}"
    return b

def __get_whitch_companies_is_up__():
    returned = []
    for c,h in __get_href_companias__():
        try:
            r = requests.get(f'{h}/ping',timeout=0.5)
            returned.append((c,r.status_code == 200))
        except:
            returned.append((c,False))
    return returned

def __get_base_context__():
    return {'title':dados['nome'],'compania_is_up':__get_whitch_companies_is_up__()}

@app.route('/', methods=['GET'])
def home():
    v=dados['voos']
    for n,a in enumerate(v):
        a['vagas'] = dados['trajetos'].trechos[n].get_vagas_livres()# [a["saida"]][a["destino"]]
    return render_template('home.html',base_context=__get_base_context__(),trechos=v)

@app.route('/ping', methods=['GET'])
def ping():
    return '',200

def __get_self_voos__():
    return [trecho.get_info() for trecho in dados['trechos']]

def __get_all_voos__():
    hrefs = __get_href_companias__()
    voos = __get_self_voos__()
    for href in hrefs:
        try:
            # print(f'tentando pega voos: {href[0]} -> {href[1]}/voos')
            voos+= requests.get(f"{href[1]}/voos",timeout=1).json()
        except Exception: # caso algum noa responda apenas vamos parao proximo
            pass
    return voos

def __get_gerenciador_todos_trajetos__():
    return Gerenciador_de_trajetos(make_trechos(__get_all_voos__()))

def __render_home_with_text__(text=''):
        return render_template('text.html',base_context=__get_base_context__(),text=text)
@app.route('/reservar', methods=['POST'])
def reservar_trajetos():
    r = Reservador_trajeto(request.form['trajeto'], href_companias=__get_all_href__())
    return __render_home_with_text__(text=r.reservar())

@app.route('/ver_trajetos/', methods=['POST'])
def ver_trajetos():
    saida,destino = request.form['saida'],request.form['destino']
    # print('from',saida,'to',destino)
    gerenciador = __get_gerenciador_todos_trajetos__()
    success,resultado = gerenciador.make_all_trajetos(saida=saida,destino=destino)
    lista_trajetos =[ 
        (
            i+1,
            [(
                n+1,trajeto[n],trajeto[n+1],
                [
                    {
                        'compania':trecho['compania'],
                        'opção':trecho['opção'],
                        'custo':trecho["custo"],
                        'tempo':trecho['tempo'],
                        'vagas':gerenciador.get_vagas(trecho['index']),
                        'display':j==0
                    } for j,trecho in enumerate(gerenciador.find_from_to(trajeto[n],trajeto[n+1])) 
                ],
                n != len(trajeto)-2
            )for n in range(len(trajeto)-1) ]
        ) for i,trajeto in enumerate(resultado)
    ]
    return render_template('trajeto_view.html',success=success,resultado=lista_trajetos,saida=saida,destino=destino,base_context=__get_base_context__())


@app.route('/ocupar/<saida>/<destino>/<compania>', methods=['GET'])
def reserva_passagem(saida:str,destino:str,compania:str):
    '''
    Rota nao publica para uso interno
    '''
    if(compania == dados["nome"]):
        caminho = dados['trajetos'].find_from_to(saida,destino)[0]
        if ( caminho ):
            if(dados['trechos'][caminho['index']].ocupar_vaga()):
                return __render_home_with_text__(text='Assento alocado') ,200
            else:
                return __render_home_with_text__(text=f'limite de passageiros ja alcançado no voou de {saida} -> {destino} na compania {compania}'),404
        return  __render_home_with_text__(text=f'Trecho {saida} -> {destino} não encontrado na compania {compania}'),404
    elif(compania in dados['companias']):
        dados_compania = dados['companias'][compania]
        href = f"http://{dados_compania['ip']}:{dados_compania['port']}/ocupar/{saida}/{destino}/{compania}"
        try:
            request = requests.get(href,timeout=60)
        except Exception as e:# essa exception seria relacionada ao request
            return __render_home_with_text__(text=f'Problema na reserva do trecho {saida} -> {destino} na compania {compania}'),404
        return request.raw,request.status_code # ainda nao testado se isso sobrepoe o if else abaixo
        if(request.status_code != 200): # se tiver uma forma mais facil pode tira o if else aqui ( ex: retornando o request recebido )
            return 'Problema na reserva do trecho {saida} -> {destino} na compania {compania}',404
        else:
            return 'Assento alocado',200
    else:
        return  __render_home_with_text__(text='A compania informada não foi encontrada'),404

@app.route('/desocupar/<saida>/<destino>/<compania>', methods=['GET'])
def desreservar_passagem(saida:str,destino:str,compania:str):
    '''
    Rota nao publica para uso interno
    '''
    if(compania == dados["nome"]):
        caminho = dados['trajetos'].find_from_to(saida,destino)[0]
        if ( caminho ):
            if(dados['trechos'][caminho['index']].liberar_vaga()):
                return 'Assento alocado',200
            else:
                return f'limite de passageiros ja alcançado no voou de {saida} -> {destino} na compania {compania}'
        return f'Trecho {saida} -> {destino} não encontrado na compania {compania}',404
    elif(compania in dados['companias']):
        dados_compania = dados['companias'][compania]
        href = f"http://{dados_compania['ip']}:{dados_compania['port']}/desocupar/{saida}/{destino}/{compania}"
        try:
            request = requests.get(href,timeout=60)
        except Exception as e:# essa exception seria relacionada ao request
            return f'Problema na reserva do trecho {saida} -> {destino} na compania {compania}',404
        return request.raw,request.status_code # ainda nao testado se isso sobrepoe o if else abaixo
        if(request.status_code != 200): # se tiver uma forma mais facil pode tira o if else aqui ( ex: retornando o request recebido )
            return 'Problema na reserva do trecho {saida} -> {destino} na compania {compania}',404
        else:
            return 'Assento alocado',200
    else:
        return 'A compania informada não foi encontrada',404

@app.route('/voos', methods=['GET'])
def voos():
    return jsonify(__get_self_voos__()),200

@app.route('/all_voos', methods=['GET'])
def all_voos():
    returned = __get_self_voos__()
    for compania in dados['companias']:
        dados_compania = dados['companias'][compania]
        try:
            returned.append(requests.get(f"http://{dados_compania['ip']}:{dados_compania['port']}/voos",timeout=1).json())
        except Exception: # caso algum noa responda apenas vamos parao proximo
            pass
    return jsonify(returned),200

app.run(host = dados['ip'], port = dados['port'], debug = True)