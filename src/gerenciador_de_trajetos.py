from trecho import Trecho

class Gerenciador_de_trajetos():
    def __init__(self,trechos:list[Trecho]):
        self.trechos = trechos
        self.trajetos = { a.saida:{} for a in trechos}
        for n,a in enumerate(trechos):
            if(a.destino not in self.trajetos[a.saida]):
                self.trajetos[a.saida][a.destino] = []
            self.trajetos[a.saida][a.destino].append({
                'compania':a.empresa,
                'index':n,
                'opção':len(self.trajetos[a.saida][a.destino])+1,
                'custo':a.custo,
                'tempo':a.tempo,
                'vagas_totais':a.quantidade_maxima_de_vagas})

    def find_from(self,saida:str)-> dict:
        if (saida in self.trajetos):
            return self.trajetos[saida]
        return None
    
    def find_from_to(self,saida:str,destino:str) -> list[dict]:
        '''
        '''
        if ( saida in self.trajetos ):
            if( destino in self.trajetos[saida] ):
                return self.trajetos[saida][destino]
        return None
    
    def make_all_trajetos(self,saida:str,destino:str):
        resultado = []
        success=False
        search = {saida:[saida]}
        on_going_search = True
        while on_going_search:
            # fineshed = True
            # print(search)
            next_iteraration={}
            for cidade in search:
                if( cidade in self.trajetos):
                    vizinhos = search[cidade]
                    for cidade_conectada in self.trajetos[cidade]:
                        # print(f'olhando cidade: {cidade_conectada}')
                        if( cidade_conectada not in vizinhos):
                            # fineshed = False
                            if cidade_conectada == destino:
                                resultado.append(vizinhos+[cidade_conectada])
                                success = True  
                            else:
                                next_iteraration[cidade_conectada]=vizinhos+[cidade_conectada]
            search = next_iteraration
            # on_going_search = not fineshed
            if(next_iteraration == {}):
                on_going_search = False
        return success,resultado

    def get_vagas(self,index:int):
        trecho = self.trechos[index]
        return trecho.quantidade_maxima_de_vagas-trecho.quantidade_de_vagas_ocupadas

    def add_voo(self,voo:Trecho):
        self.trechos.append(voo)
        if(voo.saida not in self.trajetos):
            self.trajetos[voo.saida]={}
        if(voo.destino not in self.trajetos[voo.saida]):
            self.trajetos[voo.saida][voo.destino]=[]
        self.trajetos[voo.saida][voo.destino].append({
                'compania':voo.empresa,
                'index':len(self.trechos)-1,
                'opção':len(self.trajetos[voo.saida][voo.destino])+1,
                'custo':voo.custo,
                'tempo':voo.tempo,
                'vagas_totais':voo.quantidade_maxima_de_vagas})


if(__name__=='__main__'):
    saidas = 'asdfasaeqf'
    destinos='sdqefasdsq'
    trechos = []
    for a in range(len(saidas)):
        trechos.append(Trecho(saida=saidas[a],destino = destinos[a],custo = 1, tempo=1,empresa='A',quantidade_maxima_de_vagas=10))
    # print(f"Esperado :(True, [['a', 's', 'd'], ['a', 'f', 'e', 'd'], ['a', 'f', 'q', 's', 'd']])")
    # print(f"Resultado:{Gerenciador_de_trajetos(trechos).make_all_trajetos('a','d')}")
    assert (True, [['a', 's', 'd'], ['a', 'f', 'e', 'd'], ['a', 'f', 'q', 's', 'd']]) == Gerenciador_de_trajetos(trechos).make_all_trajetos('a','d')
    print('passed test: 1')
    # print(f"Esperado :(True, [['f', 'q', 's', 'a'], ['f', 'e', 'd', 'q', 's', 'a']])")
    # print(f"Resultado:{Gerenciador_de_trajetos(trechos).make_all_trajetos('f','a')}")
    assert (True, [['f', 'q', 's', 'a'], ['f', 'e', 'd', 'q', 's', 'a']]) == Gerenciador_de_trajetos(trechos).make_all_trajetos('f','a')
    print('passed test: 2')
    del(trechos[8])
    # print(f"Esperado :(False, [])")
    # print(f"Resultado:{Gerenciador_de_trajetos(trechos).make_all_trajetos('f','a')}")
    assert (False, []) == Gerenciador_de_trajetos(trechos).make_all_trajetos('f','a')
    print('passed test: 3')
