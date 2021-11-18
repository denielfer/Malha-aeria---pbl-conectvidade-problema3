from trecho import Trecho
import requests

class Reservador_trajeto:
    def __init__(self,trajeto:str,href_companias:list[dict],do=None,undo=None):
        cidades,companias = trajeto.split('|')
        self.cidades = [a.strip('->') for a in cidades.split('->')]
        self.companias = [a.strip('->') for a in companias.split('->')][:-1]
        self.hrefs_action=[]
        self.href_undo=[]
        self.companias_done=[]
        self.do= do
        self.undo = undo
        for n,a in enumerate(companias):
            if a in href_companias:
                self.hrefs_action.append(f'{href_companias[a]}/ocupar/{self.cidades[n]}/{self.cidades[n+1]}/{a}')
                self.href_undo.append(f'{href_companias[a]}/desocupar/{self.cidades[n]}/{self.cidades[n+1]}/{a}')
        if(do == None):
            def do_f():
                for n,a in enumerate(self.companias):
                    try:
                        resp = requests.get(self.hrefs_action[n],timeout=10)
                    except:
                        t=self.hrefs_action[n].split('/')
                        s,d,c = t[-3:]
                        print(f'[OCUPAR] Vaga nao ocupada por Exception: vaga de "{s.strip("/")}" para "{d.strip("/")}" pela compania "{c.strip("/")}"')
                        self.undo()
                        return f"Erro em Reservar vagas tente novamente mais tarde. Nenhuma vaga foi reservada. ( Verifique se o servidor da compania '{c}' esta online )"
                    if(resp.status_code == 200):
                        self.companias_done.append(a)
                    else:
                        t=self.hrefs_action[n].split('/')
                        s,d,c = t[-3:]
                        print(f'[OCUPAR] Erro em ocupar vaga de "{s.strip("/")}" para "{d.strip("/")}" pela compania "{c.strip("/")}"')
                        self.undo()
                        return f'Erro em Reservar vagas, o numero maximo de vagas do voo de "{s.strip("/")}" para "{d.strip("/")}" pela compania "{c.strip("/")}". Nenhuma vaga foi reservada.'
                return 'Vagas reservadas com sucesso'
            self.do = do_f
        if(undo == None):
            def undo_f():
                for n,a in enumerate(self.companias_done):
                    try:
                        resp = requests.get(self.href_undo[n])
                    except:
                        t=self.href_undo[n].split('/')
                        s,d,c = t[-3:]
                        print(f'[DESOCUPAR] Except em desocupar vaga de "{s.strip("/")}" para "{d.strip("/")}" pela compania "{c.strip("/")}"')
                        pass
                    if(resp.status_code == 200):
                        self.companias_done.append(a)
                    else:
                        print(f'[DESOCUPAR] Erro em desocupar vaga de "{s.strip("/")}" para "{d.strip("/")}" pela compania "{c.strip("/")}"')
            self.undo = undo_f
    def reservar(self) -> bool:
        return self.do()
