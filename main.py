'''
    Script para atualizar os dados e as imagens de todas as cartas do Legends of Runeterra
    Esse script pode ser agendado para rodar toda data de patch/lançamento de expansão
    Dessa forma, tudo é atualizado automaticamente com os dados personalizáveis através do arquivo config.json
'''

from zipfile import ZipFile
import urllib.request
import shutil
import json
import sys
import os

# Classe para ajudar a lidar com os diferentes conjuntos de cartas
class Conjunto:
    def __init__(self, conjunto, linguagem):
        self.nome = conjunto['nome']
        self.url = conjunto['url'].format(linguagem)
        self.pasta = conjunto['pasta']

# Classe para ajudar a lidar com as pastas de cada ZIP, tendo funções para retornar onde está o arquivo JSON e onde está a pasta de imagens
# Ela também lida com a informação de onde vão ficar a pasta de imagens e o arquivo JSON, com suporte a subpastas
class Configuracao:
    def __init__(self, config, config_linguagem):
        self.base = os.getcwd()
        self.linguagem = config['linguagem']
        propriedades = [x for x in config_linguagem if x['linguagem'] == self.linguagem][0]['propriedades']

        self.pasta_imagens = config['pasta_imagens']
        self.arquivo_saida = config['arquivo_saida']

        self.nome_ovonivia = propriedades['nome_ovonivia']
        self.nome_unidade = propriedades['nome_unidade']
        self.nome_campeao = propriedades['nome_campeao']
        self.campeao_nivel_2 = propriedades['campeao_nivel_2']

        self.ids_ignorados = config['ids_ignorados']
    
    def arquivoDados(self, pasta_set):
        return os.path.join(self.base, '__sets', pasta_set, self.linguagem, 'data', '{0}-{1}.json'.format(pasta_set, self.linguagem))
    
    def pastaImagens(self, pasta_set):
        return os.path.join(self.base, '__sets', pasta_set, self.linguagem, 'img', 'cards')

# Decide como (ou se) a carta vai ser registrada ou não no arquivo JSON
def cadastrarCarta(carta):
    nome = carta['name']
    codigo = carta['cardCode']

    if codigo in configuracao.ids_ignorados:
        return None
    
    if (carta['type'] == configuracao.nome_unidade) and (carta['supertype'] == configuracao.nome_campeao) and (carta['collectible'] == False):
        if (carta['name'] != configuracao.nome_ovonivia):
            nome += ' {0}'.format(configuracao.campeao_nivel_2)
    
    return { "name": nome, "cardCode": codigo }

# O arquivo JSON config.json que vem junto com esse script é um arquivo que te permite customizar esse script como quiser
with open('config.json', 'r', encoding='utf8') as arquivo_config:
    config = json.load(arquivo_config)
    with open ('language.json', 'r', encoding='utf8') as arquivo_linguagem:
        config_linguagem = json.load(arquivo_linguagem)
        configuracao = Configuracao(config, config_linguagem)
        conjuntos = [Conjunto(conjunto, configuracao.linguagem) for conjunto in config['conjuntos']]

codigos = []

for conjunto in conjuntos:
    print('Baixando os arquivos das cartas da expansão {0}. Essa etapa pode demorar um pouco.'.format(conjunto.nome))
    arquivo_zip = '{0}.zip'.format(conjunto.pasta)

    # Vai lá no link e faz download do arquivo (é sério, é só essa linha mesmo)
    urllib.request.urlretrieve(conjunto.url, arquivo_zip)
    print('Arquivos da expansão {0} baixados com sucesso, resultando no arquivo {1}.'.format(conjunto.nome, arquivo_zip))

    # Extrai os arquivos em uma única pasta __sets, onde cada expansão vai ter sua própria pasta dentro dessa
    with ZipFile(arquivo_zip, 'r') as zipObj:
        zipObj.extractall(os.path.join('__sets', conjunto.pasta))
    print('Extração do arquivo {0} concluída.'.format(arquivo_zip))

    # Exclui o arquivo ZIP pois a partir daqui não precisaremos mais dele
    os.remove(arquivo_zip)

    # Acessa o arquivo JSON dentro da pasta da expansão a fim de pegar a relação de nome com o ID de cada carta
    with open(configuracao.arquivoDados(conjunto.pasta), 'r', encoding='utf8') as arquivo_json:
        dados = json.load(arquivo_json)
        for dado in dados:
            carta = cadastrarCarta(dado)
            if carta != None:
                codigos.append(carta)
    print('Informações das cartas da expansão {0} obtidas.'.format(conjunto.nome))

    # Verifica se existe a pasta de imagens e se não existir, cria uma
    if (not os.path.isdir(configuracao.pasta_imagens)):
        os.mkdir(configuracao.pasta_imagens)

    # Transfere todas as imagens da pasta img para uma pasta única onde vai ficar as imagens das cartas de todas as expansões
    imagens = os.listdir(configuracao.pastaImagens(conjunto.pasta))
    for imagem in imagens:
        saida = os.path.join(configuracao.pastaImagens(conjunto.pasta), imagem)
        destino = os.path.join(configuracao.pasta_imagens, imagem)
        shutil.move(saida, destino)
    print('Todas as imagens das cartas da expansão {0} foram passadas para a pasta {1}.'.format(conjunto.nome, configuracao.pasta_imagens))

# Escreve todas as cartas obtidas no arquivo sets.json
with open(configuracao.arquivo_saida, 'w', encoding='utf8') as saida:
    json.dump(codigos, saida, ensure_ascii=False)

# Exclui a pasta __sets pois não precisaremos mais dela
shutil.rmtree('__sets', ignore_errors=True)

# Excluindo imagens desnecessárias (as imagens das cartas que foram ignoradas, ou seja, as que estão em ids_ignorados e artes alternativas)
for ignorado in configuracao.ids_ignorados:
    print('{0}.png removido'.format(ignorado))
    remocao = os.path.join(configuracao.pasta_imagens, '{0}.png'.format(ignorado))
    os.remove(remocao)
imagens = os.listdir(configuracao.pasta_imagens)
for imagem in imagens:
    if '-alt' in imagem:
        remocao = os.path.join(configuracao.pasta_imagens, imagem)
        os.remove(remocao)

print('O script terminou de executar com sucesso. Todos os dados podem ser encontrados no arquivo {0}. Todas as imagens das cartas estão na pasta {1}.'.format(configuracao.arquivo_saida, configuracao.pasta_imagens))