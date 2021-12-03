import threading
from requests import get, post
from time import sleep

TEMPO_POR_companhia_EM_S = 5 #quantidade de tempo que será destinada a cada companhia

class Gerenciador_de_manager:
    def __init__(self, companhias:dict, trajetos_para_reservar:list, who_am_i:str, semaphore_de_liberação_resolver_pedidos:threading.Semaphore, pode_fazer_reserva:bool):
        self.companhias = companhias
        self.companhia = who_am_i
        self.trajetos_para_reservar = trajetos_para_reservar
        self.semaphore_de_liberação_resolver_pedidos = semaphore_de_liberação_resolver_pedidos
        self.pode_fazer_reserva = pode_fazer_reserva
        self.manager =  None
        self.temp_companhias = list(companhias)
        self.ciclo = False
        self.thread = None
        ##Verificamos se existe um manager no sistema
        exist_manager = self.__verificar_se_existe_manager__()
        ##se não existir manager, começa um ciclo (isso acontece quando nenhuma das companhias que conhecemos está ativa)
        if(not exist_manager):
           self.init_circulo()
        ##Se já existir uma manager, esperamos o próximo ciclo para entrarmos na rotação

    def init_circulo(self):
        if(self.thread is None):
            semafaro = threading.Semaphore()
            semafaro.acquire()
            thread = threading.Thread(target=self.__main_loop__,kwargs={'semaphore':semafaro})
            thread.setDaemon(True)
            thread.start()
            self.thread = (thread,semafaro)

    def __main_loop__(self,semaphore:threading.Semaphore):
        while not semaphore.acquire(False):
            self.temp_companhias = list(self.companhias) # fazemos uma copia para o caso de ter alteração nao quebrar o loop ( assim companhias adicionadas depois ficariam para proxima rotação )
            self.esperar_nova_rodada()
            sleep(1)
            print('[Gerenciador de manager] rodada começada')
            self.ciclo = True
            while(len(self.temp_companhias) > 0): #enquanto todas as companhias não forem managers
                self.manager = self.temp_companhias.pop() #pegamos o primeiro da lista para ser o manager
                print(f'[Gerenciador de manager] manager atual = {self.manager}')
                #como essa lista propagada é pela rede, toda vez que uma companhia nova entra em contato com alguma que está na rede,
                #todas as companhias que esta conhecem tem a mesma lista
                if(self.manager == self.companhia): #se for nossa companhia
                    self.start_resolver_pedidos() #liberamos para os nossos pedidos serem resolvidos
                else:
                    sleep(TEMPO_POR_companhia_EM_S) #dormimos pelo período que a companhia será deixada como manager
                    #verificamos se o manager está fazendo operação 
                    #    (uma vez que o tempo acabou, ele irá passar a vez para o próximo, porém 
                    #    isso pode demorar um pouco, pois ele ainda está fazendo uma operação 
                    #    e deve terminar ela)
                    while(self.verificar_manager()): #se ele estiver fazendo
                        sleep(.2) #esperando 200 ms para perguntar novamente
                #então o loop continua passando para o próximo manager
            self.ciclo = False
        semaphore.release()
        del(semaphore)
        print(f"[Gerenciador Manager] finalizando")

    def start_resolver_pedidos(self):
        semaphore_resolvendo_pedido:threading.Semaphore = self.init_thread_resolver_pedidos()
        sleep(TEMPO_POR_companhia_EM_S) # esperamos o tempo
        self.semaphore_de_liberação_resolver_pedidos.release() # pegamos o semaphore de volta ( isso pode ter atraso caso um pedido ainda esteja sendo resolvido )
        semaphore_resolvendo_pedido.acquire() # esperamos se estiver terminando de resolver operação no momento que o tempo dele acabou



    def __resolver_reserva_trajeto__(self,estou_resolvendo_pedido:threading.Semaphore):
        self.pode_fazer_reserva=True
        self.semaphore_de_liberação_resolver_pedidos.acquire() # libramos o semaphore
        while not self.semaphore_de_liberação_resolver_pedidos.acquire(False):
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
        self.semaphore_de_liberação_resolver_pedidos.release() #solta o acquire que aconteceu na verificação de visualização se continuamos tentando resolver
        self.pode_fazer_reserva = False

    def init_thread_resolver_pedidos(self) -> threading.Semaphore:
        estou_resolvendo_pedido=threading.Semaphore()
        t = threading.Thread(target = self.__resolver_reserva_trajeto__, kwargs = {"estou_resolvendo_pedido":estou_resolvendo_pedido}, daemon = True)
        t.setDaemon(True)
        t.start()
        return estou_resolvendo_pedido

    def verificar_manager(self):
        try: #tentamos
            resp = get(f'{self.companhias[self.manager]}/fazendo_operação', timeout = 1) #fazer um request para o manager, se ele está fazendo operação
        except Exception: #se der erro, ele caiu, então não está
            return False #logo, retornamos false
        return resp.status_code == 201 #teve resposta e ele não passou a vez ainda, ele ainda está fazendo operação então retornamos true

    def esperar_nova_rodada(self):
        temp_comp = self.companhias.copy()
        for companhia,href in temp_comp.items():
            keep_going = True
            while keep_going: #neste loop, esperamos até que todos os servidores conectados concordem em iniciar um novo ciclo
                keep_going = False
                resp = None
                try: # tentamos
                    print(f'[Gerenciador de manager] esperando por {companhia=}')
                    resp = get(f'{href}/ciclo_iniciar',timeout=1)# fazer um request para as companhias que conhecemos perguntando se o ciclo deles acabou tambemx
                except Exception as e:
                    pass
                if(resp is not None and resp.status_code == 200): #se alguma das respostas não for 
                    keep_going = True                    
                else:
                    sleep(.1)

    def __verificar_se_existe_manager__(self) -> bool:
        existe_manager = False
        comp_to_check = self.companhias.copy() # para o caso de uma companhia ser adicionada enquanto estamos iterando nao gerar um erro fazemos uma copia
        for companhia,href in comp_to_check.items(): # para cada companhia que conhecemos
            try:
                resp = get(f'{href}/tem_manager',timeout=1) # pedimos se esta companhia tem um manager
            except Exception: # caso ela esteja desligada
                print(f'[Gerenciador de manager] {companhia=} nao respondeu')
                continue # assim skipamos a parte abaixo
            # se algumas delas responder quer dizer que estao ligadas entao existe um manager
            existe_manager=True
            break # assim que acharmos manager em 1 companhias podemos para de procuirar
        return existe_manager

    def end_afther_ciclo(self):
        thread,semafaro = self.thread
        semafaro.release()
        self.thread = None
        

if __name__ == "__main__":
    a = {1:12}
    gerenciador = Gerenciador_de_manager(a)
    print(f'{a=}  |  {gerenciador.companhias=}')
    a[2] = 21
    print(f'{a=}  |  {gerenciador.companhias=}')