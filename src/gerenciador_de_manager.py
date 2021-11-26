import threading
from requests import get,post
from time import sleep

TEMPO_POR_COMPANIA_EM_S=5 # quantidade de tempo que sera destinado a cada compania

class Gerenciador_de_manager:
    def __init__(self,companias:dict,trajetos_para_reservar:list,who_am_i:str, semapharo_de_liberação_resolver_pedidos:threading.Semaphore,
                 pass_manager:function=None,verificação:function=None,força_passagem:function=None):
        if(pass_manager is not None):
            raise('Nescessario passar função que determina o comportamento de passar a vez como manager')
        if(verificação is not None):
            raise('Nescessario passar função que determina o comportamento para verificação se o manager esta vivo')
        if(força_passagem is not None):
            raise('Nescessario passar função que determina o comportamento que forçe uma passagem de manager')
        self.companias=companias
        self.compania= who_am_i
        self.trajetos_para_reservar = trajetos_para_reservar
        self.semapharo_de_liberação_resolver_pedidos = semapharo_de_liberação_resolver_pedidos
        self.pass_manager = pass_manager
        self.verificação = verificação
        self.força_passagem = força_passagem
        self.manager =  None
        self.temp_companias = companias.copy()
        ## Verificamos se existe um manager no sistema
        exist_manager = self.__verificar_se_existe_manager__()
        #
        ## se nao existir manager agente começa um ciclo ( isso acontece quando nenhuma das companias que conhecemos esta up )
        if( not exist_manager):
            self.init_circulo()
        #
        ## Se ja esxiste uma manager esperamos o proximo ciclo para entrarmos na rotação
        #


    def __main_loop__(self):
        while True:
            self.temp_companias = list(self.companias) # fazemos uma copia para o caso de ter alteração nao quebrar o loop ( assim companias adicionadas depois ficariam para proxima rotação )
            while(len(self.temp_companias) > 0): # enquanto todas as companias nao forem managers
                self.manager = self.temp_companias.pop() # pegamos o primeiro da lista para ser o manager
                # como essa lista propagada pela rede toda vez que uma compania nova entra em contanto com alguma que esta na rede
                # todas as companias que esta conhecem tem a mesma lista
                if(self.manager == self.compania): # se for nossa compania
                    self.start_resolver_pedidos() # liberamos para os nossos pedidos serem resolvidos
                else:
                    sleep(TEMPO_POR_COMPANIA_EM_S) # dormimos pelo periodo que a compania sera deixada como manager
                    # verificamos se o manager esta fazendo operação 
                    #    ( uma vez que o tempo acabo ele ira passa a vez para o proximo porem 
                    #      isso pode demora um pouco pois ele ainda esta fazendo uma operação 
                    #      e deve termina ela )
                    while( self.verificar_manager() ): # se ele estiver fazendo
                        sleep(.2) # esperando 200 ms para pergunta dinovo
                # entao o loop continua passando para o proximo manger
            self.manager = None
            self.esperar_nova_rodada()

    def start_resolver_pedidos(self):
        # if(len(self.trajetos_para_reservar) > 0): # se tivermos trajetos para resolver
            print('sou o cordenador')
            self.semapharo_de_liberação_resolver_pedidos.release() # libramos o semapharo
            sleep(TEMPO_POR_COMPANIA_EM_S) # esperamos o tempo
            self.semapharo_de_liberação_resolver_pedidos.acquire() # pegamos o semapharo de volta ( isso pode ter atraso caso um pedido ainda esteja sendo resolvido )
            print('deixei de ser o coordenador')
        # else: # se nao 
        #     sleep(TEMPO_POR_COMPANIA_EM_S/5) # esperamos um tempo ant

    def verificar_manager(self):
        try: # tentanmos
            resp = get(f'{self.companias[self.manager]}/fazendo_operação',timeout=1) #### AINDA NAO IMPLEMENTADO   # fazer um request para o manager se ele esta fazendo operação
        except Exception: # se der erro ele caiu entao nao esta
            return False # logo retornamos false
        return resp.status_code == 200 # teve resposta e ele nao passou a vez ainda ele ainda esta fazendo operação entao retornamos true

    def esperar_nova_rodada(self):
        temp_comp = self.companias
        cont = 0
        for compania,href in temp_comp:
            try: # tentamos
                resp = get(f'{self.companias[self.manager]}/ciclo_terminou',timeout=1) #### AINDA NAO IMPLEMENTADO  # fazer um request para as companias que conhecemos perguntando se o ciclo deles acabou tambem
            except Exception: 
                pass
            if(resp.status_code != 200): # se alguma das respostas nao for 
               self.sincronize() ##### AINDA NAO IMPLEMENTADO
        
        
    def __verificar_se_existe_manager__(self) -> bool:
        existe_manager = False
        comp_to_check = self.companias.copy() # para o caso de uma compania ser adicionada enquanto estamos iterando nao gerar um erro fazemos uma copia
        for compania,href in comp_to_check.items(): # para cada compania que conhecemos
            try:
                resp = get(f'{href}/tem_manager',timeout=1) # pedimos se esta compania tem um manager
            except Exception: # caso ela esteja desligada
                pass
            # se algumas delas responder quer dizer que estao ligadas entao existe um manager
            existe_manager=True
        return existe_manager


if __name__ == "__main__":
    a = {1:12}
    gerenciador = Gerenciador_de_manager(a)
    print(f'{a=}  |  {gerenciador.companias=}')
    a[2]=21
    print(f'{a=}  |  {gerenciador.companias=}')