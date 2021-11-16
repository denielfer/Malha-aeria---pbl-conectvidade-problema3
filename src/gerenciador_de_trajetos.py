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
                'custo':a.custo,
                'tempo':a.tempo})

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

if(__name__=='__main__'):
    saidas = 'asdfasaeqf'
    destinos='sdqefasdsq'
    trechos = []
    for a in range(len(saidas)):
        trechos.append(Trecho(saida=saidas[a],destino = destinos[a],custo = 1, tempo=1,empresa='A',quantidade_maxima_de_vagas=10))
    print(f"Esperado :(True, [['a', 's', 'd'], ['a', 'f', 'e', 'd'], ['a', 'f', 'q', 's', 'd']])")
    print(f"Resultado:{Gerenciador_de_trajetos(trechos).make_all_trajetos('a','d')}")
