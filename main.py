'''
    Script to update all data and images from every card in Legends of Runeterra
    This script can be scheduled to run every date before a patch or a set launch
    This way, everything is updated with customized data through the config.json file
'''

from zipfile import ZipFile
import urllib.request
import shutil
import codecs
import json
import sys
import io
import os

languages = [ "pt_br", "en_us", "es_es", "es_mx", "fr_fr", "it_it", "de_de", "ko_kr", "ja_jp", "pl_pl", "th_th", "tr_tr", "ru_ru", "zh_tw", "vi_vn" ]

class CardSet:
    def __init__(self, card_set, language):
        self.name = card_set['name']
        self.url = card_set['url'].format(language)
        self.folder = card_set['folder']

class Config:
    def __init__(self, config, config_language, language):
        self.base = os.getcwd()
        self.language = language
        properties = [x for x in config_language if x['language'] == self.language][0]['properties']

        self.output_folder = config['output_folder']
        self.root_images_folder = os.path.join(self.output_folder, config['images_folder'])
        self.images_folder = os.path.join(self.root_images_folder, self.language)
        self.output_file = os.path.join(self.output_folder, config['output_file'].format(self.language))

        self.types = {}
        for (key, value) in properties['types'].items():
            self.types[key] = value
        self.champion_level_2 = properties['champion_level_2']
        self.champion_level_3 = properties['champion_level_3']

        self.champions_without_level_2 = config['champions_without_level_2']
        self.champions_with_level_3 = config['champions_with_level_3']
        self.ignored_ids = config['ignored_ids']

    def dataFile(self, set_folder):
        return os.path.join(self.base, '__sets', set_folder, self.language, 'data', '{0}-{1}.json'.format(set_folder, self.language))

    def imagesFolder(self, set_folder):
        return os.path.join(self.base, '__sets', set_folder, self.language, 'img', 'cards')

def getPath(file):
	return os.path.join(os.path.dirname(__file__), file)

def registerCard(card):
    mana = card['cost']
    name = card['name']
    code = card['cardCode']
    region = card['regionRef'].lower()
    cardType = card['type']
    supertype = card['supertype']
    associatedCards = card['associatedCardRefs']

    if code in config.ignored_ids:
        return None
    
    if (config.types.get(cardType) == 'follower') and (config.types.get(supertype) == 'champion'):
        cardType = supertype
        if (card['collectible'] == False):
            if (not code in config.champions_without_level_2):
                if (code in config.champions_with_level_3):
                    name += ' {0}'.format(config.champion_level_3)
                else:
                    name += ' {0}'.format(config.champion_level_2)
    
    return { "name": name, "mana": mana, "cardCode": code, "region": region, "type": config.types.get(cardType, ''), "associatedCards": associatedCards }

for language in languages:
    with io.open(getPath('config.json'), 'r', encoding='utf-8') as file_config:
        config_file = json.load(file_config)
        with io.open(getPath('language.json'), 'r', encoding='utf-8') as file_language:
            config_language = json.load(file_language)
            config = Config(config_file, config_language, language)
            card_sets = [CardSet(card_set, config.language) for card_set in config_file['card_sets']]
    
    codes = []
    
    for card_set in card_sets:
        print('Downloading files from set {0} in language {1}. This step may take some minutes.'.format(card_set.name, config.language))
        file_zip = getPath('{0}.zip'.format(card_set.folder))
    
        urllib.request.urlretrieve(card_set.url, file_zip)
        print('Files from set {0} downloaded successfully, resulting in file {1}.'.format(card_set.name, file_zip))
    
        if (not os.path.isdir(getPath('__sets'))):
    	    os.mkdir(getPath('__sets'), 777)
    
        with ZipFile(file_zip, 'r') as zipObj:
            zipObj.extractall(os.path.join(config.base, '__sets', card_set.folder))
        print('Extraction of {0} finished.'.format(file_zip))
    
        os.remove(file_zip)
    
        with io.open(config.dataFile(card_set.folder), 'r', encoding='utf8') as file_json:
            fileData = json.load(file_json)
            for data in fileData:
                card = registerCard(data)
                if card != None:
                    codes.append(card)
        print('Data from cards from set {0} obtained.'.format(card_set.name))
    
        if (not os.path.isdir(config.root_images_folder)):
            os.mkdir(config.root_images_folder)
        if (not os.path.isdir(config.images_folder)):
            os.mkdir(config.images_folder)
    
        images = os.listdir(config.imagesFolder(card_set.folder))
        for image in images:
            output = os.path.join(config.imagesFolder(card_set.folder), image)
            outputPath = os.path.join(config.images_folder, image)
            shutil.move(output, outputPath)
        print('All card images from set {0} were transferred to folder {1}.'.format(card_set.name, config.images_folder))
        
    with io.open(config.output_file, 'w', encoding='utf8') as output:
        output.write(json.dumps(codes, ensure_ascii=False))
    
    shutil.rmtree(getPath('__sets'), ignore_errors=True)
    
    for ignored in config.ignored_ids:
        toBeRemoved = os.path.join(config.images_folder, '{0}.png'.format(ignored))
        os.remove(toBeRemoved)
        print('{0}.png removed'.format(ignored))
    images = os.listdir(config.images_folder)
    for image in images:
        if '-alt' in image:
            toBeRemoved = os.path.join(config.images_folder, image)
            os.remove(toBeRemoved)
            print('{0}.png removed'.format(image))

print('The script finished sucessfully. All data can be found at file {0}. All card images are at folder {1}.'.format(config.output_file, config.images_folder))