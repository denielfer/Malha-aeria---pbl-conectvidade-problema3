from trecho import Trecho

class Gerenciador_de_trajetos():
    def __init__(self, trechos:list[Trecho]):
        self.trechos = trechos
        self.trajetos = {trecho.saida:{} for trecho in trechos}
        for i, trecho in enumerate(trechos):
            if(trecho.destino not in self.trajetos[trecho.saida]):
                self.trajetos[trecho.saida][trecho.destino] = []
            self.trajetos[trecho.saida][trecho.destino].append({
                'companhia': trecho.empresa,
                'index': i,
                'opção': len(self.trajetos[trecho.saida][trecho.destino]) + 1,
                'custo': trecho.custo,
                'tempo': trecho.tempo,
                'vagas_totais': trecho.quantidade_maxima_de_vagas})

    def find_from(self, saida:str) -> dict:
        '''
            Função para achar cidades conectadas as cidade informada ( {saida} )

            @param saida: string inidicando de qual cidade queremos saber
            @return dict contendo informações das cidades conectadas e informações do voo que as conecta 
                ( neste dicionario temos como chave o nome da cidade conectada e o seu dado 
                  correspondente é uma lista de dados de voos que conectam estas cidades    )
        '''
        if (saida in self.trajetos):
            return self.trajetos[saida]
        return None
    
    def find_from_to(self, saida:str, destino:str) -> list[dict]:
        '''
            Função para achar os voos que conectam cidade {saida} a {destino}

            @param saida: string inidicando de qual cidade queremos saber
            @param destino: string indicando para qual cidade queremos
            @return list de dict contendo informações dos voos que conectam estas cidades
        '''
        if (saida in self.trajetos):
            if(destino in self.trajetos[saida]):
                return self.trajetos[saida][destino]
        return None
    
    def make_all_trajetos(self, saida:str, destino:str):
        '''
            Função que faz a busca de todos os trajetos que ligam {saida} a {destino}

            @param saida: string indiciando a cidade de saida
            @parma destino: string indicando a cidade de destino
            @return: tupla contendo (success,resultado_da_busca) no qual
                success é um bool que guarda True se a existe caminhos em 
                    resultado_da_busca
                Resultado_da_busca é uma list de trajetos, um trajeto
                    é uma lista de nome de cidades na ordem que leva de
                    {saida} para {destino}
        '''
        resultado = []
        success = False
        search = {f'_{saida}':[saida]}
        while search != {}: # emquanto a busca nao acaba
            next_iteraration = {}
            for id in search:
                cidade = id.split('_')[1]
                if(cidade in self.trajetos):
                    vizinhos = search[id]
                    for cidade_conectada in self.trajetos[cidade]:
                        if(cidade_conectada not in vizinhos):
                            if cidade_conectada == destino:
                                resultado.append(vizinhos + [cidade_conectada])
                                success = True  
                            else:
                                next_iteraration[f'{cidade}_{cidade_conectada}'] = vizinhos + [cidade_conectada] #é usado {cidade}_{cidade_conectada} pois como usamos um dicionario pra guardar as buscas em processo ainda caso hajam em um mesmo nivel 2 cidades que tenham conecção com uma terceira cidade uma das 2 cidades teria sua busca apagada
            search = next_iteraration
        return success, resultado

    def get_vagas(self, index:int):
        '''
            informa a quantidade de vagas disponiveis do trecho especificado

            @param index: int indicando o index do voo solicitado na lista de voos
            @return int indicando a quantidade de vagas resmanecentes do voo solicitado
        '''
        trecho = self.trechos[index]
        return trecho.quantidade_maxima_de_vagas - trecho.quantidade_de_vagas_ocupadas

    def add_voo(self, voo:Trecho):
        '''
            Função para adiciona um voo no gerenciador

            @param voo: Trecho que sera adicionado
        '''
        self.trechos.append(voo)
        if(voo.saida not in self.trajetos):
            self.trajetos[voo.saida] = {}
        if(voo.destino not in self.trajetos[voo.saida]):
            self.trajetos[voo.saida][voo.destino] = []
        self.trajetos[voo.saida][voo.destino].append({
                'companhia': voo.empresa,
                'index': len(self.trechos) - 1,
                'opção': len(self.trajetos[voo.saida][voo.destino]) + 1,
                'custo': voo.custo,
                'tempo': voo.tempo,
                'vagas_totais': voo.quantidade_maxima_de_vagas})


if(__name__=='__main__'):
    saidas = 'asdfasaeqfef'
    destinos ='sdqefasdsqwd'
    trechos = []
    for i in range(len(saidas)):
        trechos.append(Trecho(saida = saidas[i], destino = destinos[i], custo = 1, tempo = 1, empresa = 'A', quantidade_maxima_de_vagas = 10))
    gerenciador = Gerenciador_de_trajetos(trechos)
    # print(f"Esperado :(True, [['a', 's', 'd'], ['a', 'f', 'd'], ['a', 'f', 'e', 'd'], ['a', 'f', 'q', 's', 'd']]) ->")
    print(f"Resultado busca de 'a' para 'd':{gerenciador.make_all_trajetos('a','d')}")
    assert (True, [['a', 's', 'd'], ['a', 'f', 'd'], ['a', 'f', 'e', 'd'], ['a', 'f', 'q', 's', 'd']]) == gerenciador.make_all_trajetos('a','d')
    # print('passed test: 1')
    # print(f"Esperado :(True, [['f', 'q', 's', 'a'], ['f', 'e', 'd', 'q', 's', 'a'], ['f', 'e', 'd', 'q', 's', 'a']]) -> ")
    print(f"Resultado  busca de 's' para 'a':{gerenciador.make_all_trajetos('f','a')}")
    assert (True, [['f', 'q', 's', 'a'], ['f', 'd', 'q', 's', 'a'], ['f', 'e', 'd', 'q', 's', 'a']]) == gerenciador.make_all_trajetos('f','a')
    # print('passed test: 2')
    # del(trechos[8])
    # print(f"Esperado :(True, [['a', 's', 'd'], ['a', 'f', 'd'], ['a', 'f', 'e', 'd'], ['a', 'f', 'q', 's', 'd']]) -> ")
    print(f"Resultado busca de 'a' para 'q':{gerenciador.make_all_trajetos('a','q')}")
    assert (True, [['a', 'f', 'q'], ['a', 's', 'd', 'q'], ['a', 'f', 'd', 'q'], ['a', 'f', 'e', 'd', 'q']]) == gerenciador.make_all_trajetos('a','q')
    # print('passed test: 3')
    # print(f"Esperado :(False, []) -> ")
    print(f"Resultado busca de 'w' para 'a':{gerenciador.make_all_trajetos('w','a')}")
    assert (False, []) == gerenciador.make_all_trajetos('w','a')
    # print('passed test: 4')
