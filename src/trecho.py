from threading import Semaphore
from random import random
class Trecho:
    def __init__(self,saida:str,destino:str,custo:float,tempo:float,empresa:str, quantidade_maxima_de_vagas:int,quantidade_de_vagas_ocupadas:int=0, *args,**kargs):
        self.saida = saida
        self.destino = destino
        self.custo = custo
        self.tempo = tempo
        self.empresa = empresa
        self.quantidade_maxima_de_vagas = quantidade_maxima_de_vagas
        self.quantidade_de_vagas_ocupadas = quantidade_de_vagas_ocupadas
        self.mutex = Semaphore()
    
    def get_peso(self,is_custo:bool) -> None:
        return self.custo if is_custo else self.tempo
    
    def ocupar_vaga(self) -> bool:
        self.mutex.acquire()
        returned = False
        if(self.quantidade_maxima_de_vagas-self.quantidade_de_vagas_ocupadas > 0):
            self.quantidade_de_vagas_ocupadas+=1
            returned = True
        self.mutex.release()
        return returned
    
    def liberar_vaga(self) -> bool:
        self.mutex.acquire()
        returned = False
        if(self.quantidade_de_vagas_ocupadas > 0):
            self.quantidade_de_vagas_ocupadas-=1
            returned=True
        self.mutex.release()
        return returned

    def get_vagas_livres(self):
        return self.quantidade_maxima_de_vagas-self.quantidade_de_vagas_ocupadas

    def get_info(self):
        return {"saida":self.saida ,"destino":self.destino,"custo":self.custo,"tempo":self.tempo,"empresa":self.empresa,"quantidade_maxima_de_vagas":self.quantidade_maxima_de_vagas,'quantidade_de_vagas_ocupadas':self.quantidade_de_vagas_ocupadas}

if(__name__ == "__main__"):
    t = Trecho(saida='a',destino='b',custo=10,tempo=3,empresa='A',quantidade_maxima_de_vagas=2)
    from threading import Thread
    from time import sleep
    def thread_function(t:Trecho):
        print(f'uma vaga foi ocupada? R:{t.ocupar_vaga()}')
    for _ in range(4):
        Thread(target=thread_function,args=[t]).start()
    sleep(.5)
    print(f' Esperase que a quantidade seja 2, quantidade:{t.quantidade_de_vagas_ocupadas} ')
    for a in range(4):
        print(f'a vaga foi liberada? R:{t.liberar_vaga()}')
    print(f' Esperase que a quantidade seja 0, quantidade:{t.quantidade_de_vagas_ocupadas} ')
    print(f'é esperado 10: {t.get_peso(True)}')
    print(f'é esperado 3: {t.get_peso(False)}')
