'''
    Script to update all data and images from every card in Legends of Runeterra
    This script can be scheduled to run every date before a patch or a set launch
    This way, everything is updated with customized data through the config.json file
'''

from zipfile import ZipFile
import urllib.request
import shutil
import json
import io
import os
import re

card_data = []


class CardSet:
    def __init__(self, images_folder, card_set, language):
        self.name = card_set['name']
        self.url = card_set['url'].format(language)
        self.folder = card_set['folder']
        self.language = language

        self.images_path = os.path.join(os.path.dirname(
            __file__), self.folder, self.language, 'img', 'cards')
        self.file_path = os.path.join(os.path.dirname(
            __file__), self.folder, self.language, 'data', '{0}-{1}.json'.format(self.folder, self.language))
        self.output_folder = os.path.join(images_folder, self.language)


class Config:
    def __init__(self, config, config_language, config_champion_names):
        self.output_folder = config['output_folder']
        self.images_folder = os.path.join(
            self.output_folder, config['images_folder'])
        self.output_file = os.path.join(
            self.output_folder, config['output_file'])
        self.include_images = config['include_images'] == 'yes'
        self.included_languages = config['included_languages']

        self.card_sets = config['card_sets']
        self.dictionary = config_language
        self.champion_names = config_champion_names


def getPath(file):
    return os.path.join(os.path.dirname(__file__), file)


def setConfig():
    config = None

    with io.open(getPath('config.json'), 'r', encoding='utf-8') as file_config:
        config_file = json.load(file_config)
        with io.open(getPath('language.json'), 'r', encoding='utf-8') as file_language:
            config_language = json.load(file_language)
            with io.open(getPath('champion_names.json'), 'r', encoding='utf-8') as file_champion_names:
                config_champion_names = json.load(file_champion_names)
                config = Config(config_file, config_language,
                                config_champion_names)

    return config


def getDataFromCardSet(card_set, include_images, dictionary, champion_names):
    file_zip = getPath('{0}.zip'.format(card_set.folder))

    urllib.request.urlretrieve(card_set.url, file_zip)
    print('Files from set {0} downloaded successfully, resulting in file {1}.'.format(
        card_set.name, file_zip))

    with ZipFile(file_zip, 'r') as zipObj:
        if(include_images):
            zipObj.extractall(getPath(card_set.folder))
        else:
            zipObj.extract('{0}/data/{1}-{0}.json'.format(card_set.language,
                           card_set.folder), getPath(card_set.folder))
    print('Extraction of {0} finished.'.format(file_zip))

    os.remove(file_zip)

    with io.open(card_set.file_path, 'r', encoding='utf8') as file_json:
        fileData = json.load(file_json)
        for data in fileData:
            card_data.append(registerCard(dictionary, champion_names, data))
    print('Data from cards from set {0} obtained.'.format(card_set.name))

    if (include_images):
        if (not os.path.isdir(card_set.output_folder)):
            os.mkdir(card_set.output_folder)

        images = os.listdir(card_set.images_path)
        for image in images:
            source = os.path.join(card_set.images_path, image)
            destination = os.path.join(card_set.output_folder, image)
            shutil.move(source, destination)
        print('All card images from set {0} were transferred to folder {1}.'.format(
            card_set.name, card_set.output_folder))

    shutil.rmtree(card_set.folder, ignore_errors=True)


def removeTags(text):
    return re.sub('<[^>]*>', '', text)


def registerCard(dictionary, champion_names, card):
    regionRefs = [x.lower() for x in card['regionRefs']]
    nameRef = champion_names[card['cardCode']
                             ] if card['cardCode'] in champion_names else ''
    subtypes = [dictionary['subtypes']
                [removeTags(x)] for x in card['subtypes']]
    supertype = dictionary['types'][removeTags(card['supertype'])
                                    ] if card['supertype'] != '' else ''
    cardType = dictionary['types'][removeTags(card['type'])]

    return {
        'associatedCards': card['associatedCardRefs'],
        'artPath': [x['gameAbsolutePath'] for x in card['assets']],
        'fullArtPath': [x['fullAbsolutePath'] for x in card['assets']],
        'regions': regionRefs,
        'attack': card['attack'],
        'cost': card['cost'],
        'health': card['health'],
        'description': card['descriptionRaw'],
        'levelupDescription': card['levelupDescriptionRaw'],
        'flavorText': card['flavorText'],
        'artistName': card['artistName'],
        'name': card['name'],
        'nameRef': nameRef,
        'cardCode': card['cardCode'],
        'keywords': [x.lower() for x in card['keywordRefs']],
        'spellSpeed': card['spellSpeedRef'].lower(),
        'rarity': card['rarityRef'].lower(),
        'subtypes': subtypes,
        'supertype': supertype,
        'type': cardType,
        'collectible': card['collectible'],
        'set': card['set'].lower()
    }


config = setConfig()
if (config.include_images and not os.path.isdir(config.images_folder)):
    os.mkdir(config.images_folder)
for language in config.included_languages:
    card_data = []
    card_set_object = None
    for card_set in config.card_sets:
        card_set_object = CardSet(config.images_folder, card_set, language)
        print('Downloading files from set {0} in language {1}. This step may take some minutes.'.format(
            card_set_object.name, language))
        getDataFromCardSet(
            card_set_object, config.include_images, config.dictionary[language], config.champion_names)
    output_file = config.output_file.format(language)
    with io.open(output_file, 'w', encoding='utf8') as output:
        output.write(json.dumps(card_data, ensure_ascii=False))
    print('All data collected from set {0} in language {1}.'.format(
        card_set_object.name, language))

print('The script finished sucessfully. All data can be found at file {0}.{1}'.format(
    config.output_file, ' All card images are at folder {0}.'.format(config.images_folder) if config.include_images else ''))
