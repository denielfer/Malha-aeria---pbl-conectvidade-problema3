from flask import Flask, jsonify, request
import requests
import sys
from gerenciador_de_trajetos import Gerenciador_de_trajetos
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

@app.route('/reservar_trajeto', methods=['POST'])
def reservar_trajeto():
    request
    raise("NÃO IMPLEMENTADO")


@app.route('/ocupar/<saida>/<destino>/<compania>', methods=['GET'])
def reserva_passagem(saida:str,destino:str,compania:str):
    '''
    
    Rota nao publica para uso interno
    '''
    if(compania == dados["nome"]):
        caminho = dados['trajetos'].find_from_to(saida,destino)[0]
        if ( caminho ):
            if(dados['trechos'][caminho['index']].ocupar_vaga()):
                return 'Assento alocado',200
            else:
                return f'limite de passageiros ja alcançado no voou de {saida} -> {destino} na compania {compania}'
        return f'Trecho {saida} -> {destino} não encontrado na compania {compania}',404
    elif(compania in dados['companias']):
        dados_compania = dados['companias'][compania]
        href = f"http://{dados_compania['ip']}:{dados_compania['port']}/{saida}/{destino}/{compania}"
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
    

def __get_self_voos__():
    return [trecho.get_info() for trecho in dados['trechos']]

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