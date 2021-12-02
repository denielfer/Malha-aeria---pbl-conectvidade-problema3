import threading
from requests import get, post
from time import sleep

TEMPO_POR_COMPANIA_EM_S = 5 # quantidade de tempo que sera destinado a cada compania

class Gerenciador_de_manager:
    def __init__(self, companias:dict, trajetos_para_reservar:list, who_am_i:str, semapharo_de_liberação_resolver_pedidos:threading.Semaphore, pode_fazer_reserva:bool):
        self.companias = companias
        self.compania = who_am_i
        self.trajetos_para_reservar = trajetos_para_reservar
        self.semapharo_de_liberação_resolver_pedidos = semapharo_de_liberação_resolver_pedidos
        self.pode_fazer_reserva = pode_fazer_reserva
        self.manager =  None
        self.temp_companias = list(companias)
        self.ciclo = False
        self.thread = None
        ##Verificamos se existe um manager no sistema
        exist_manager = self.__verificar_se_existe_manager__()
        #
        ##se não existir manager, começa um ciclo (isso acontece quando nenhuma das companhias que conhecemos está ativa)
        if(not exist_manager):
           self.init_circulo()
        #
        ##Se ja existir uma manager, esperamos o próximo ciclo para entrarmos na rotação
        #

    def init_circulo(self):
        if(self.thread is None):
            # print("[Gerenciador de manager] thread_iniciada")
            self.thread = threading.Thread(target = self.__main_loop__)
            self.thread.setDaemon(True)
            self.thread.start()

    def __main_loop__(self):
        while True:
            # print(f'++++++++++++++++++++++++++{self.companias}+++++++++++++++++++++++++++++++++++++++')
            self.temp_companias = list(self.companias) #fazemos uma copia para o caso de ter alteração nao quebrar o loop ( assim companias adicionadas depois ficariam para proxima rotação )
            self.esperar_nova_rodada()
            sleep(.1)
            print('[Gerenciador de manager] rodada começada')
            self.ciclo = True
            while(len(self.temp_companias) > 0): #enquanto todas as companias nao forem managers
                self.manager = self.temp_companias.pop() #pegamos o primeiro da lista para ser o manager
                print(f'[Gerenciador de manager] manager atual = {self.manager}')
                #como essa lista propagada pela rede toda vez que uma compania nova entra em contanto com alguma que esta na rede
                #todas as companias que esta conhecem tem a mesma lista
                if(self.manager == self.compania): #se for nossa companhia
                    self.start_resolver_pedidos() #liberamos para os nossos pedidos serem resolvidos
                else:
                    sleep(TEMPO_POR_COMPANIA_EM_S) #dormimos pelo período que a companhia será deixada como manager
                    #verificamos se o manager esta fazendo operação 
                    #    ( uma vez que o tempo acabo ele ira passa a vez para o proximo porem 
                    #      isso pode demora um pouco pois ele ainda esta fazendo uma operação 
                    #      e deve termina ela )
                    while(self.verificar_manager()): # se ele estiver fazendo
                        sleep(.2) # esperando 200 ms para pergunta dinovo
                # entao o loop continua passando para o proximo manger
            self.ciclo = False
            self.manager = None

    def start_resolver_pedidos(self):
        # if(len(self.trajetos_para_reservar) > 0): #se tivermos trajetos para resolver
            # print('[Gerenciador de manager] sou o cordenador')

            #As duas linhas sao passadas para dentro da thread q as usa para reduzir o tempo de operações antes do sleep
            # self.pode_fazer_reserva=True
            # self.semapharo_de_liberação_resolver_pedidos.acquire() #liberamos o semapharo

            semapharo_resolvendo_pedido:threading.Semaphore = self.init_thread_resolver_pedidos()
            sleep(TEMPO_POR_COMPANIA_EM_S) # esperamos o tempo
            self.semapharo_de_liberação_resolver_pedidos.release() # pegamos o semapharo de volta ( isso pode ter atraso caso um pedido ainda esteja sendo resolvido )
            semapharo_resolvendo_pedido.acquire() # esperamos se estiver terminando de resolver operação no momento que o tempo dele acabou
            # print('[Gerenciador de manager] deixei de ser o coordenador')
        # else: # se nao 
        #     sleep(TEMPO_POR_COMPANIA_EM_S/5) #esperamos um tempo ant


    def __resolver_reserva_trajeto__(self,estou_resolvendo_pedido:threading.Semaphore):
        self.pode_fazer_reserva = True
        self.semapharo_de_liberação_resolver_pedidos.acquire() #liberamos o semapharo
        while not self.semapharo_de_liberação_resolver_pedidos.acquire(False):
            # print(f'{lista_de_pedidos=}')
            if(self.pode_fazer_reserva):
                if(len(self.trajetos_para_reservar) > 0):
                    estou_resolvendo_pedido.acquire()
                    pedido = self.trajetos_para_reservar.pop()
                    pedido.reservar()
                    estou_resolvendo_pedido.release()
                else:
                    sleep(.1)
            else:
                break
        self.semapharo_de_liberação_resolver_pedidos.release()#solta o acquire q aconteceu na verificação de para ver se continuamos tentando resolver
        self.pode_fazer_reserva = False

    def init_thread_resolver_pedidos(self) -> threading.Semaphore:
        estou_resolvendo_pedido=threading.Semaphore()
        t = threading.Thread(target = self.__resolver_reserva_trajeto__, kwargs = {"estou_resolvendo_pedido":estou_resolvendo_pedido}, daemon = True)
        t.setDaemon(True)
        t.start()
        return estou_resolvendo_pedido

    def verificar_manager(self):
        try: #tentamos
            resp = get(f'{self.companias[self.manager]}/fazendo_operação', timeout = 1) # fazer um request para o manager se ele esta fazendo operação
        except Exception: #se der erro ele caiu entao nao esta
            return False #logo retornamos false
        return resp.status_code == 201 #teve resposta e ele nao passou a vez ainda ele ainda esta fazendo operação entao retornamos true

    def esperar_nova_rodada(self):
        temp_comp = self.companias.copy()
        # print('____________________________________')
        # print(temp_comp)
        # print('____________________________________')
        for compania, href in temp_comp.items():
            keep_going = True
            while keep_going: # neste loop esperamos ate que todos so servidores conectados concordem em iniciar um novo ciclo
                keep_going = False
                resp = None
                try: # tentamos
                    # print('_____________________________________')
                    # print(self.companias)
                    # print('_____________________________________')
                    print(f'[Gerenciador de manager] esperando por {compania=}')
                    resp = get(f'{href}/ciclo_iniciar', timeout = 1)# fazer um request para as companias que conhecemos perguntando se o ciclo deles acabou tambemx
                except Exception as e:
                    pass
                if(resp is not None and resp.status_code == 200): # se alguma das respostas nao for 
                    keep_going = True                    
                else:
                    sleep(.1)

    def __verificar_se_existe_manager__(self) -> bool:
        existe_manager = False
        comp_to_check = self.companias.copy() # para o caso de uma compania ser adicionada enquanto estamos iterando nao gerar um erro fazemos uma copia
        for compania,href in comp_to_check.items(): # para cada compania que conhecemos
            # print(f'[Gerenciador de manager] {compania=} : {href=}')
            try:
                resp = get(f'{href}/tem_manager', timeout = 1) #pedimos se esta compania tem um manager
            except Exception: # caso ela esteja desligada
                print(f'[Gerenciador de manager] {compania=} nao respondeu')
                continue # assim skipamos a parte abaixo
            # se algumas delas responder quer dizer que estao ligadas entao existe um manager
            # if(resp.status_code == 200):
                # print(f'[Gerenciador de manager] Existe manager, esperando notificação de {compania=}')
            existe_manager = True
            break # assi que acharmos manager em 1 companias podemos para de procuirar
        return existe_manager


if __name__ == "__main__":
    a = {1:12}
    gerenciador = Gerenciador_de_manager(a)
    print(f'{a=}  |  {gerenciador.companias=}')
    a[2]=21
    print(f'{a=}  |  {gerenciador.companias=}')