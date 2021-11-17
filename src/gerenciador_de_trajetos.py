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

    def find_from(self,saida:str)-> dict | None:
        if (saida in self.trajetos):
            return self.trajetos[saida]
        return None
    
    def find_from_to(self,saida:str,destino:str) -> list[dict] | None:
        '''
        '''
        if ( saida in self.trajetos ):
            if( destino in self.trajetos[saida] ):
                return self.trajetos[saida][destino]
        return None
    
    def make_all_trajetos(self,saida:str,destino:str):
        resultado = []
        success=False
        search = {saida:{
                "atual":saida,
                "visited":[saida]
            }
        }
        on_going_search = True
        while on_going_search:
            fineshed = True
            next_iteraration={}
            for a in search:
                if( a not in self.trajetos):
                    continue
                d = search[a]
                for c in self.trajetos[d['atual']]:
                    if( c not in d['visited']):
                        fineshed = False
                        if c == destino:
                            d['visited'].append(c)
                            resultado.append(d['visited'])
                            success = True  
                        else:
                            to_be_searched ={'atual':c,'visited':d['visited']+[c]}
                            next_iteraration[c]=to_be_searched
            search = next_iteraration
            on_going_search = not fineshed
            if(next_iteraration == {}):
                on_going_search = False
        return success,resultado
    
    def get_vagas(self,index:int):
        trecho = self.trechos[index]
        return trecho.quantidade_maxima_de_vagas-trecho.quantidade_de_vagas_ocupadas

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
