from flask import Flask, jsonify, request, render_template
import requests
import sys
from gerenciador_de_trajetos import Gerenciador_de_trajetos
from reservar_trajeto import Reservador_trajeto
from trecho import Trecho
import util
# dados = None
pedidos_trajetos_pra_processar = []

dados = util.load(sys.argv)
# print(dados)
if(dados is None):
    raise("Caregamento de informações não foi realizada com sucesso")
util.inicializar(dados['companias'],dados['nome'],f"http://{dados['ip']}:{dados['port']}")

# print(f"Este servidor corresponde ao da Compania: {dados['nome']} e esta sendo executado no link: http://{dados['ip']}:{dados['port']}")

app = Flask(__name__)

def __get_all_href__():
    data = dados['companias'].copy()
    data[dados['nome']] = f"http://{dados['ip']}:{dados['port']}"
    return data

def __get_whitch_companies_is_up__(): ################################################ pensar em um jeito de colocar como assincrono ###################################################################################
    returned = []
    for c in dados['companias']:
        try:
            request = requests.get(f'{dados["companias"][c]}/ping', timeout = 0.5)
            returned.append((c, request.status_code == 200))
        except Exception:
            returned.append((c, False))
    return returned

def __get_base_context__():
    return {'title':dados['nome'],'compania_is_up':__get_whitch_companies_is_up__()}

@app.route('/', methods=['GET'])
def home():
    v = dados['voos']
    for n, a in enumerate(v): # inplace operation
        a['vagas'] = dados['trajetos'].trechos[n].get_vagas_livres()
    return render_template('home.html', base_context = __get_base_context__(), trechos = v)

@app.route('/ping', methods=['GET'])
def ping():
    return '', 200

def __get_self_voos__():
    return [trecho.get_info() for trecho in dados['trechos']]

def __get_all_voos__(): ################### tranforma em um metodo assincrono ###############################################################################################
    hrefs = dados['companias'].copy()
    voos = __get_self_voos__()
    for c in hrefs:
        try:
            # print(hrefs[c])
            voos += requests.get(f"{hrefs[c]}/voos", timeout = 1).json()
        except Exception: #caso algum não responda, apenas vamos para o próximo
            pass
    return voos

def __get_gerenciador_todos_trajetos__():
    return Gerenciador_de_trajetos(util.make_trechos(__get_all_voos__()))

def __render_home_with_text__(text=''):
        return render_template('text.html', base_context=__get_base_context__(), text = text)
@app.route('/reservar', methods=['POST'])
def reservar_trajetos():
    r = Reservador_trajeto(request.form['trajeto'], href_companias=__get_all_href__())
    return __render_home_with_text__(text=r.reservar())

@app.route('/ver_trajetos/', methods=['POST'])
def ver_trajetos():
    saida,destino = request.form['saida'], request.form['destino']
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
        caminho = dados['trajetos'].find_from_to(saida, destino)
        if(caminho == None):
            return "Trajeto indicado nao foi encontrado", 404
        caminho = caminho[0]
        if (caminho):
            if(dados['trechos'][caminho['index']].ocupar_vaga()):
                return 'Assento alocado', 200
            else:
                return f'limite de passageiros ja alcançado no voo de "{saida}" -> "{destino}" na companhia "{compania}"', 404
        return  f'Trecho "{saida}" -> "{destino}" não encontrado na companhia "{compania}"', 404
    elif(compania in dados['companias']):
        dados_compania = dados['companias'][compania]
        href = f"http://{dados_compania['ip']}:{dados_compania['port']}/ocupar/{saida}/{destino}/{compania}"
        try:
            request = requests.get(href, timeout=60)
        except Exception as e: #essa exception seria relacionada ao request
            return f'Problema na reserva do trecho "{saida}" -> "{destino}" na companhia "{compania}"', 404
        return request.raw,request.status_code # ainda nao testado se isso sobrepoe o if else abaixo
        if(request.status_code != 200): #se tiver uma forma mais fácil, pode tirar o if else aqui (ex: retornando o request recebido)
            return 'Problema na reserva do trecho {saida} -> {destino} na companhia {compania}', 404
        else:
            return 'Assento alocado', 200
    else:
        return  'A companhia informada não foi encontrada', 404

@app.route('/desocupar/<saida>/<destino>/<compania>', methods=['GET'])
def desreservar_passagem(saida:str, destino:str, compania:str):
    '''
    Rota não pública para uso interno
    '''
    if(compania == dados["nome"]):
        caminho = dados['trajetos'].find_from_to(saida,destino)
        if(caminho == None):
            return "Trajeto indicado não foi encontrado", 404
        caminho = caminho[0]
        if (caminho):
            if(dados['trechos'][caminho['index']].liberar_vaga()):
                return 'Assento desalocado',200
            else:
                return  f'O voo já tem sua capacidade máxima livre. Voo de "{saida}" -> "{destino}" na companhia "{compania}"', 200
        return  f'Trecho "{saida}" -> "{destino}" não encontrado na companhia "{compania}"', 404
    elif(compania in dados['companias']):
        dados_compania = dados['companias'][compania]
        href = f"http://{dados_compania['ip']}:{dados_compania['port']}/desocupar/{saida}/{destino}/{compania}"
        try:
            request = requests.get(href, timeout=60)
        except Exception as e: #essa exception seria relacionada ao request
            return  f'Problema na reserva do trecho "{saida}" -> "{destino}" na companhia "{compania}"', 404
        return request.raw,request.status_code #ainda não testado se isso sobrepõe o if else abaixo
        # if(request.status_code != 200): #se tiver uma forma mais fácil, pode tirar o if else aqui (ex: retornando o request recebido)
        #     return 'Problema na reserva do trecho {saida} -> {destino} na companhia {compania}', 404
        # else:
        #     return 'Assento alocado', 200
    else:
        return 'A companhia informada não foi encontrada', 404

@app.route('/voos', methods=['GET'])
def voos():
    return jsonify(__get_self_voos__()), 200

@app.route('/all_voos', methods=['GET'])
def all_voos():
    returned = __get_self_voos__()
    for compania in dados['companias']:
        dados_compania = dados['companias'][compania]
        try:
            returned.append(requests.get(f"http://{dados_compania['ip']}:{dados_compania['port']}/voos", timeout=1).json())
        except Exception: #caso algum não responda, apenas vamos para o próximo
            pass
    return jsonify(returned), 200

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
        dados['trechos'].append(trecho)
        dados['trajetos'].add_voo(trecho)
        return __render_home_with_text__(text=f'O voo de {trecho.saida} para {trecho.destino} foi adicionado, com custo de {trecho.custo} e tempo de {trecho.tempo}'), 200

@app.route('/add_compania', methods=['GET', 'POST'])
def add_compania():
    if(request.method == "GET"):
        return render_template('add_compania.html', base_context=__get_base_context__())
    else:
        try:
            if( request.form["propagate"] == 'True'):
                util.propagate(dados['companias'],{request.form['compania']:request.form["href"]})
            dados["companias"][request.form['compania']] = request.form["href"]
            util.__escrever_binario_de_conf__(dados)
            return  __render_home_with_text__(text=f'a compania: {request.form["compania"]} for adicionada a lista de companias afiliadas. A api desta compania se encontra na porta: {request.form["href"]}'),200
        except Exception: # caso o formulario nao tenha os campos que buscamos
            return  __render_home_with_text__(text='NA MORAL? METEU ESSA MERMO?'),404

@app.route('/companias_conectadas', methods=['GET', 'POST'])
def companias_conectadas():
    if(request.method == "GET"):
        return jsonify(dados['companias']),200
    else:
        try:
            print(request.form)
            companias_to_check = request.form # companias passadas no request
        except Exception:
            return '',404
        companias_already_in={}
        companias_out={}
        for compania,href in companias_to_check.items(): # para as companias recebidas no post
            if(compania in dados['companias'] and dados['companias'][compania] == href): # se ela ja estiver nos dados e o href for o passado
                companias_already_in[compania] = href # adicionanos nas companias que ja tinhamos
            elif(compania == dados['nome']):
                pass
            else: # se nao 
                companias_out[compania] = href # adicionamos nas companias que nao tinhamos
                dados['companias'][compania] = href # adicionamos ela nas companias que guardados
        util.propagate(companias_already_in,companias_out) # propagamos para as comapanias que ja tinhamos as companias que nao tinhamos 
        print(dados['companias'])
        return '',200

if(__name__== "__main__"):
    print( dados['ip'], dados['port'])
    app.run(host = dados['ip'], port = dados['port'], debug = False)