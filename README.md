# Descrição #
Projeto desenvolvido para o 3° PBL da diciplina TEC502 - MI - CONCORRÊNCIA E CONECTIVIDADE. A descrição do problema pode ser vista [aqui](https://github.com/denielfer/Malha-aeria---pbl-conectvidade-problema3/blob/main/arquivos_pdf/prob_3.pdf) e o seu relatorio [aqui](https://github.com/denielfer/Malha-aeria---pbl-conectvidade-problema3/blob/main/arquivos_pdf/Relatorio%20problema%203%20-%20Malha%20aeria.pdf)

Para solução deste problema foi desenvolvido um sistema descentralizado de companhias aéreas, nas quais em cada companhia é possivel ver os voos oferecidos por aquela companhia e pesquisar todos os trajetos possíveis entre 2 cidades (considerando todos os voos conhecidos).
Este sistema funciona de forma descentralizada (cada companhia pode operar plenamente e de forma separada), porém, existindo a opção de conectar companhias (adicionar uma compania a lista de conhecidas de outra) e assim, estas companhias passam a se conhecer e nas pesquisas de trajetos são considerados os voos de todas as companhias conhecidas.

---

# Sistema #

Este é um sistema decentralizado no qual cada companhia pode funcionar de forma separada. Na interface gráfica de cada companhia, os desenvolvedores e/ou usuários do sistema podem realizar 5 operações principais:

Adicionar Companias: na rota '/add_companhia' pode ser feito a adição de uma compania na lista de companhias conhecidas por tal companhia. Esta operação seria feita pela equipe de desenvolvimento ou manutenção da empresa para configuração.

Adicionar Voo: na rota '/add_voo' pode ser criado um novo voo pela companhia. Esta operação seria feita pela equipe de desenvolvimento ou manutenção da empresa, para adição de novos voos.

Acessar home: na rota '/' é mostrado todos os voos desta companhia e é possivel fazer a pesquisa de trajeto (encontrar todos os voos para ir de uma cidade até outra). Esta seria a rota que os clientes seriam redirecionados ao entrar.

Pesquisa de trajetos: na página na qual o cliente interage, é possivel fazer a pesquisa de todos os trajetos (conjunto de voos) que ligam uma cidade a outra.

Fazer a compra: na página é possivel fazer a compra da passagem de um voo ou de um trecho inteiro.

---

# Configuração #

Para ultilização deste sistema é nescessário ter o [Python, na versao 3.10](https://www.python.org/) instalado

Também para os testes locais foi usado o [Radmin](https://www.radmin-vpn.com/br/) para simulação de uma mesma rede na qual os testes foram feitos durante o desenvolvimento.

## Configuração de ambiente ##

Com um terminal na pasta 'Malha-aeria---pbl-conectvidade-problema3' criamos inicialmente um ambiente virtual e instala as bibliotecas nescessárias através dos seguintes comandos:

			python -m venv env
			.\env\Scripts\activate
			python -m pip install -r requirements.txt

## Arquivo de Configuração ##

Para inicializar o sistema pode ser feito através de um arquivo de configurações .txt, o qual segue este [Template](https://github.com/denielfer/Malha-aeria---pbl-conectvidade-problema3/blob/main/src/arquivos_de_configura%C3%A7%C3%B5es_txt/template.txt).
Esta configuração pode ser feita de forma manual (sem usar um arquivo, assim, a configuração sera feita antes da inicialização do sistema pelo terminal).
Esta inicialização pode ser feita a partir de um arquivo binário que é gerado durante a execução.

## Iniciar Servidor ##

Para a inicialização de uma companhia pode ser feita de 3 formas:

### Iniciar por arquivo txt ###

Para iniciar o servidor de uma companhia através de um arquivo de configuração .txt executando o seguinte comando:

			python .\src\server.py -c '__path_do_arquivo_de_configuração_em_txt__'

Ou seja, para rodarmos com esse .txt colocamos python e o path do arquivo server.py e colocamos a opção '-c' seguido de path do arquivo de configuração em txt entre ''(aspas simples).

### Iniciar por arquivo binário ###

Para iniciar o servidor de uma companhia através de um arquivo de configuração binário executa-se o seguinte comando:

			python .\src\server.py -cb '__path_do_arquivo_de_configuração_em_binario__'

Ou seja, para rodarmos com esse binário colocamos python e o path do arquivo server.py e colocamos a opção '-cb' seguido de path do arquivo de configuração binario entre ''(aspas simples).

### Iniciar manualmente ###

Para iniciar o servidor através da configuração manual:

			python .\src\server.py

Assim, as configurações de nome da companhia, ip e porta na qual a API irá rodar serão configurados manualmente no terminal durante a inicialização do servidor.
