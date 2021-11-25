import threading as th
from time import sleep
import requests
from random import random

global eleição_ja_feita
eleição_ja_feita=False

class gerenciador_de_sincronia:
    '''
        Para essa classe temos uma singleton que controla a eleição e quem deve ser o proximo a atuar com prioridade de escrita
    '''
    _instancia=None
    def __new__(cls,*args,**kargs):
        '''
            Implementação de uma singleton
        '''
        if cls._instancia is None:
            cls._instancia= super().__new__(cls,*args,**kargs)
        return cls._instancia

    def eleição(self):
        for a in self.candidatos:
            requests.get(f'{a["href"]}/r')
        self.candidatos=[]
        pass

    def __main_thread_gerenciadora_de_eleição__(self):
        while self.semaphare.acquire(False):
            if(not eleição_ja_feita):
                self.eleição()
            sleep(self.tempo_de_tolerancia_eleição)

    def __init__(self,tempo_de_tolerancia_eleição=10):
        self.semapharo_thread_eleição = th.Semaphore()
        self.eleito=None
        self.semapharo_thread_eleição.acquire()
        self.tempo_de_tolerancia_eleição=tempo_de_tolerancia_eleição
        self.thread = th.Thread(target=self.__main_thread_gerenciadora_de_eleição__,args=(self))
        self.thread.setDaemon(True)
        self.thread.start()
        self.candidatos=[]
        self.prioridade=random()

    def add_candidato(self, candidato):
        self.candidatos.append(candidato)