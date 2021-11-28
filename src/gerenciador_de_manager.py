import threading
from requests import get,post
from time import sleep

TEMPO_POR_COMPANIA_EM_S=5 # quantidade de tempo que sera destinado a cada compania

class Gerenciador_de_manager:
    def __init__(self,companias:dict,trajetos_para_reservar:list,who_am_i:str, semapharo_de_liberação_resolver_pedidos:threading.Semaphore):
        self.companias=companias
        self.compania= who_am_i
        self.trajetos_para_reservar = trajetos_para_reservar
        self.semapharo_de_liberação_resolver_pedidos = semapharo_de_liberação_resolver_pedidos
        self.manager =  None
        self.temp_companias = list(companias)
        self.ciclo = False
        self.thread = None
        ## Verificamos se existe um manager no sistema
        exist_manager = self.__verificar_se_existe_manager__()
        #
        ## se nao existir manager agente começa um ciclo ( isso acontece quando nenhuma das companias que conhecemos esta up )
        if( not exist_manager):
            self.init_circulo(self.companias)
        #
        ## Se ja esxiste uma manager esperamos o proximo ciclo para entrarmos na rotação
        #

    def init_circulo(self,companias:dict):
        if(self.thread is None):
            self.companias = companias
            # print("[Gerenciador de manager] thread_iniciada")
            self.thread = threading.Thread(target=self.__main_loop__)
            self.thread.setDaemon(True)
            self.thread.start()

    def __main_loop__(self):
        while True:
            # print(f'++++++++++++++++++++++++++{list(self.companias)}+++++++++++++++++++++++++++++++++++++++')
            self.temp_companias = list(self.companias) # fazemos uma copia para o caso de ter alteração nao quebrar o loop ( assim companias adicionadas depois ficariam para proxima rotação )
            self.esperar_nova_rodada()
            print('[Gerenciador de manager] rodada começada')
            self.ciclo = True
            while(len(self.temp_companias) > 0): # enquanto todas as companias nao forem managers
                self.manager = self.temp_companias.pop() # pegamos o primeiro da lista para ser o manager
                print(f'[Gerenciador de manager] manager atual = {self.manager}')
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
            self.ciclo = False
            self.manager = None

    def start_resolver_pedidos(self):
        # if(len(self.trajetos_para_reservar) > 0): # se tivermos trajetos para resolver
            print('sou o cordenador')
            self.semapharo_de_liberação_resolver_pedidos.acquire() # libramos o semapharo
            semapharo_resolvendo_pedido:threading.Semaphore = self.init_thread_resolver_pedidos(self.semapharo_de_liberação_resolver_pedidos,self.trajetos_para_reservar)
            sleep(TEMPO_POR_COMPANIA_EM_S) # esperamos o tempo
            self.semapharo_de_liberação_resolver_pedidos.release() # pegamos o semapharo de volta ( isso pode ter atraso caso um pedido ainda esteja sendo resolvido )
            semapharo_resolvendo_pedido.acquire()
            print('deixei de ser o coordenador')
        # else: # se nao 
        #     sleep(TEMPO_POR_COMPANIA_EM_S/5) # esperamos um tempo ant


    def __resolver_reserva_trajeto__(self,pode_resolver:threading.Semaphore,estou_resolvendo_pedido:threading.Semaphore, lista_de_pedidos:list):
        while not pode_resolver.acquire(False):
            # print(f'{lista_de_pedidos=}')
            if(len(lista_de_pedidos)>0):
                estou_resolvendo_pedido.acquire()
                pedido = lista_de_pedidos.pop()
                pedido.reservar()
                estou_resolvendo_pedido.release()
            else:
                sleep(.1)
        pode_resolver.release()# solta o acquire q aconteceu na verificação de para ver se continuamos tentando resolver

    def init_thread_resolver_pedidos(self,pode_resolver:threading.Semaphore, lista_de_pedidos:list) -> threading.Semaphore:
        estou_resolvendo_pedido=threading.Semaphore()
        t = threading.Thread(target=self.__resolver_reserva_trajeto__,kwargs={'pode_resolver':pode_resolver,'estou_resolvendo_pedido':estou_resolvendo_pedido,'lista_de_pedidos':lista_de_pedidos},daemon=True)
        t.setDaemon(True)
        t.start()
        return estou_resolvendo_pedido

    def verificar_manager(self):
        try: # tentanmos
            resp = get(f'{self.companias[self.manager]}/fazendo_operação',timeout=1) # fazer um request para o manager se ele esta fazendo operação
        except Exception: # se der erro ele caiu entao nao esta
            return False # logo retornamos false
        return resp.status_code == 201 # teve resposta e ele nao passou a vez ainda ele ainda esta fazendo operação entao retornamos true

    def esperar_nova_rodada(self):
        temp_comp = self.companias.copy()
        for compania,href in temp_comp.items():
            keep_going = True
            while keep_going: # neste loop esperamos ate que todos so servidores conectados concordem em iniciar um novo ciclo
                keep_going = False
                resp = None
                try: # tentamos
                    # print('_____________________________________')
                    # print(self.companias)
                    # print('_____________________________________')
                    resp = post(f'{href}/ciclo_iniciar',timeout=1,data=self.companias)# fazer um request para as companias que conhecemos perguntando se o ciclo deles acabou tambemx
                except Exception as e:
                    pass
                if(resp is not None and resp.status_code == 200): # se alguma das respostas nao for 
                    keep_going = True                    
                else:
                    print(f'esperando por {compania=}')
                    sleep(.1)

    def __verificar_se_existe_manager__(self) -> bool:
        existe_manager = False
        comp_to_check = self.companias.copy() # para o caso de uma compania ser adicionada enquanto estamos iterando nao gerar um erro fazemos uma copia
        for compania,href in comp_to_check.items(): # para cada compania que conhecemos
            # print(f'[Gerenciador de manager] {compania=} : {href=}')
            try:
                resp = get(f'{href}/tem_manager',timeout=1) # pedimos se esta compania tem um manager
            except Exception: # caso ela esteja desligada
                print(f'[Gerenciador de manager] {compania=} nao respondeu')
                continue # assim skipamos a parte abaixo
            # se algumas delas responder quer dizer que estao ligadas entao existe um manager
            if(resp.status_code == 200):
                print(f'[Gerenciador de manager] Existe manager, esperando notificação de {compania=}')
                existe_manager=True
            break # assi que acharmos manager em 1 companias podemos para de procuirar
        return existe_manager


if __name__ == "__main__":
    a = {1:12}
    gerenciador = Gerenciador_de_manager(a)
    print(f'{a=}  |  {gerenciador.companias=}')
    a[2]=21
    print(f'{a=}  |  {gerenciador.companias=}')