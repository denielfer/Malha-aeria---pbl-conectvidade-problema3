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
    
    def find_from_to(self,saida:str,destino:str) -> list | None:
        '''
        '''
        if ( saida in self.trajetos ):
            if( destino in self.trajetos[saida] ):
                return self.trajetos[saida][destino]
            return None
        return None
