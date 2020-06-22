import scrapy
import pdb
from pathlib import Path

CURRENT_FOLDER = Path(__file__).parent

class AutocompleteSpider(scrapy.Spider):
    name = 'autocomplete'
    start_urls = [
        'http://www.anvisa.gov.br/datavisa/fila_bula/funcoes/ajax.asp?opcao=getsuggestion&ptipo=1'
    ]

    def parse(self, response):
        suggestions_list = response.text.split(',')
        self.logger.info('%d sugestoes de medicamentos encontradas', len(suggestions_list))
        self.save_to_file(suggestions_list)

    def save_to_file(self, suggestions_list):
        folder_path = CURRENT_FOLDER / 'autocomplete'
        filepath = folder_path / 'medicamentos.txt'
        if not folder_path.exists():
            Path.mkdir(folder_path)
        self.logger.info('Salvando arquivo %s', filepath)
        with open(filepath, 'w', encoding='utf-8') as f:
            for suggestion in suggestions_list:
                f.write(suggestion.replace('"','').replace('[','').replace(']',''))
                f.write('\n')