# Descrição #
Projeto para a 3° PBL da diciplina TEC502 - MI - CONCORRÊNCIA E CONECTIVIDADE. A descrição do problema pode ser vista [aqui]() e o seu relatorio [aqui]()

Para solução deste problema foi desenvolvido um sistema descentralizado de companias de que oferecem voos, na qual em cada companhia é possivel ver os voos oferecidos por aquela companhia e pesquisar todos os trajetos possiveis entre 2 cidades ( considerando todos os voos conhecidos ). 
Este sistema funciona de forma descentralizada ( cada compania pode operar plenamente de forma separada ) porém existindo a opção de conectar companias ( adicionar uma compania a lista de conhecidas de outra ) e assim estas companhias passam a se conhecer e nas pesquisas de trajetos são considerados os voos de todas as companias conhecidas

---

# Sistema #

Este é um sistema decentralizado no qual cada compania pode funciona de forma separa. Em cada companias pode ser feito 5 operações principais, que seriam feitas por usuarios:

Adicionar Companias: na rota '/add_companhia' pode ser feito a adição de uma compania, na lista de companhias conhecidas por uma companhia. Esta operação seria feito pela empresa para configuração.

Adicionar Voo: na rota '/add_voo' pode ser criado um novo voo pela compania. Esta operação seria feita pela empresa para adição de novos voos.

Acessar home: na rota '/' é mostrado todos os voos desta companhia e é possivel fazer a pesquisa de trajeto ( encontra todos os voos para ir de uma cidade até outra ). Esta seria a rota que os clientes seriam direcionados ao entrar.

Pesquisa de trajetos: Na interfacie na qual o cliente interaje é possivel fazer a pesquisa de todos os trajetos ( conjunto de voos ) que ligam uma cidade a outra.

Fazer a compra: na interfacie é possivel fazer a compra da passagem de um voo ou de um trecho inteiro.

---

# Configuração #

Para ultilização deste sistema é nescessário ter o [Python, na versao 3.10](https://www.python.org/) instalado

Também para os testes locais foi usado o [Radmin](https://www.radmin-vpn.com/br/) para simulação de uma rede na qual os testes foram feitos durante o desenvolvimento.

## Configuração de ambiente ##

Com um terminal na pasta 'Malha-aeria---pbl-conectvidade-problema3' criamos inicialmente um ambiente virtual e instala as bibliotecas nescessarias atravez dos seguintes comandos:

			python -m venv env
			.\env\Scripts\activate
			python -m pip install -r requirements.txt

## Arquivo de Configuração ##

Para inicializar o sistema pode ser feito atravez de um arquivo de configurações txt, o qual segue este [Template](https://github.com/denielfer/Malha-aeria---pbl-conectvidade-problema3/blob/main/src/arquivos_de_configura%C3%A7%C3%B5es_txt/template.txt). 
Esta configuração pode ser feito de forma manual ( sem usar um arquivo, assim a configuração sera feita antes da inicialização do sistema pelo terminal ).
Esta inicialização pode ser feita apartir de um arquivo binario que é gerado durante a execução.

## Iniciar Servidor ##

Para iniciarmos uma companias ela pode ser feita de 3 formas:

### Iniciar por arquivo txt ###

Para iniciar o servidor de uma companhia atravez de um arquivo de configuração txt executando o seguinte comando:

			python .\src\server.py -c '__path_do_arquivo_de_configuração_em_txt__'

Ou seja, para rodarmos com esse txt colomos python e o path do arquivo server.py e colocamos a opção '-c' seguido de path do arquivo de configuração em txt entre ''

### Iniciar por arquivo binario ###

Para iniciar o servidor de uma companhia atravez de um arquivo de configuração binario executando o seguinte comando:

			python .\src\server.py -cb '__path_do_arquivo_de_configuração_em_binario__'

Ou seja, para rodarmos com esse txt colomos python e o path do arquivo server.py e colocamos a opção '-cb' seguido de path do arquivo de configuração binario entre ''

### Iniciar manualmente ###

Para iniciar o servidor atravez da configuração m:

			python .\src\server.py

Assim as configurações de nome da compania, ip e porta na qual a api ira rodar serao configurados manualmente no terminal na inicialização do servidor.