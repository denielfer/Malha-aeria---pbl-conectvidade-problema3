from trecho import Trecho
import requests
class Reservador_trajeto:
    def __init__(self, trajeto:str, href_companhias:list[dict], do = None, undo = None):
        # print(f'{trajeto=}')
        cidades, companhias = trajeto.split('|')
        self.cidades = [cidade.strip('->') for cidade in cidades.split('->')]
        self.companhias = [companhia.strip('->') for companhia in companhias.split('->')][:-1]
        self.hrefs_action = []
        self.href_undo = []
        self.companhias_done = []
        self.do = do
        self.undo = undo
        self.status = 'esperando'
        self.text = ''
        # print("________________")
        # print(f'{self.companhias=},{companhias=},{self.cidades=},{cidades=}')
        for i, companhia in enumerate(self.companhias):
            # print(companhia in companhias)
            if companhia in href_companhias:
                self.hrefs_action.append(f'{href_companhias[companhia]}/ocupar/{self.cidades[i]}/{self.cidades[i+1]}/{companhia}')
                self.href_undo.append(f'{href_companhias[companhia]}/desocupar/{self.cidades[i]}/{self.cidades[i+1]}/{companhia}')
        # print()
        # print(self.hrefs_action)
        # print(self.href_undo)
        # print()
        # print("________________")
        if(do == None):
            def do_f():
                self.status = 'reservando'
                for i, companhia in enumerate(self.companhias):
                    try:
                        resp = requests.get(self.hrefs_action[i], timeout=10)
                    except:
                        t = self.hrefs_action[i].split('/')
                        saida, destino, companhia = t[-3:]
                        print(f'[OCUPAR] Vaga não ocupada por Exception: vaga de "{saida.strip("/")}" para "{destino.strip("/")}" pela companhia "{companhia.strip("/")}"')
                        self.undo()
                        return f"Erro em Reservar vagas, tente novamente mais tarde. Nenhuma vaga foi reservada.(Verifique se o servidor da companhia '{companhia}' está online)"
                    if(resp.status_code == 200):
                        self.companhias_done.append(companhia)
                    else:
                        t = self.hrefs_action[i].split('/')
                        saida, destino, companhia = t[-3:]
                        print(f'[OCUPAR] Erro em ocupar vaga de "{saida.strip("/")}" para "{destino.strip("/")}" pela companhia "{companhia.strip("/")}"')
                        self.undo()
                        return f'Erro em Reservar vagas, o número máximo de vagas do voo de "{saida.strip("/")}" para "{destino.strip("/")}" pela companhia "{companhia.strip("/")}". Nenhuma vaga foi reservada.'
                self.status = 'Reservado'
                return 'Vagas reservadas com sucesso'
            self.do = do_f
        if(undo == None):
            def undo_f():
                for i, companhia in enumerate(self.companhias_done):
                    try:
                        resp = requests.get(self.href_undo[i])
                    except:
                        t = self.href_undo[i].split('/')
                        saida, destino, companhia = t[-3:]
                        print(f'[DESOCUPAR] Exception em desocupar vaga de "{saida.strip("/")}" para "{destino.strip("/")}" pela companhia "{companhia.strip("/")}"')
                        pass
                    if(resp.status_code == 200):
                        pass
                    else:
                        print(f'[DESOCUPAR] Erro em desocupar vaga de "{saida.strip("/")}" para "{destino.strip("/")}" pela companhia "{companhia.strip("/")}"')
                self.status="Erro"
            self.undo = undo_f
    def reservar(self):
        self.text= self.do()
