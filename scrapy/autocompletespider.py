import scrapy
import re
import pdb
import shutil
import os
from ast import literal_eval

class AutocompleteSpider(scrapy.Spider):
    name = 'autocomplete'
    custom_settings = literal_eval(open('settings.json', 'r', encoding='utf-8').read())
    start_urls = [
        custom_settings['autocomplete_medicamentos']['url']
    ]

    def parse(self, response):
        suggestions_list = response.text.split(',')
        self.logger.info('%d sugestoes de medicamentos encontradas', len(suggestions_list))
        self.save_to_file(suggestions_list)

    def save_to_file(self, suggestions_list):
        folder = 'autocomplete'
        filepath = os.path.join(folder, 'medicamentos.txt')
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.logger.info('Salvando arquivo %s', filepath)
        with open(filepath, 'w') as f:
            for suggestion in suggestions_list:
                f.write(suggestion.replace('"','').replace('[','').replace(']',''))
                f.write('\n')
    