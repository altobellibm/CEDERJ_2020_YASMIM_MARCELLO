import scrapy
import re
import pdb
import os
import shutil
import sys
from scrapy.crawler import CrawlerProcess, CrawlerRunner
from scrapy.utils.log import configure_logging
from twisted.internet import reactor, defer

SPIDER_DIR = os.path.dirname(os.path.abspath(__file__))
class AnvisaSpider(scrapy.Spider):
    name = 'anvisa'

    def start_requests(self):
        if not hasattr(self, "search"):
            raise Exception('Especifique o parametro com o principio ativo desejado')
            ##TODO: se possivel, vamos especificar essa excecao
        else:
            autocomplete_file_path = os.path.join(SPIDER_DIR, "autocomplete", "medicamentos.txt")
            if os.path.isfile(autocomplete_file_path):
                suggestion_list = self.get_search_suggestions(autocomplete_file_path, self.search)
                if not suggestion_list:
                    raise Exception('Nenhum resultado disponivel para a busca')
                for suggestion in suggestion_list:

                    first_page = 1
                    page_size = 10
                    self.clean_folder()
                    yield scrapy.FormRequest('http://www.anvisa.gov.br/datavisa/fila_bula/frmResultado.asp',
                        formdata={
                            'txtMedicamento': suggestion,
                            'hddPageSize': str(page_size),
                            'hddPageAbsolute': str(first_page),
                        },
                        headers={
                            'X-Current-Page': str(first_page),
                            'X-Med-Search': suggestion,
                            'X-Page-Size': str(page_size)
                        },
                        callback=self.crawl_result
                    )
            else:
                raise Exception('Arquivo de autocomplete nao encontrado')

    def get_search_suggestions(self, file_path, search):
        suggestions = []
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                if search.upper() in line.upper(): #caso as sugestoes passem a vir com algum caracter minusculo, ja garantimos que nao dara problema
                    suggestions.append(line.rstrip("\n"))
        #pdb.set_trace()
        return suggestions
                                   
    def crawl_result(self, response):
        current_page = int(response.request.headers['X-Current-Page'])
        self.logger.info('Resposta da pagina %d recebida', current_page)
        table_element_id = 'tblResultado'
        column_index = self.get_column_index(response, table_element_id, 'Bula do Profissional')
        
        table_cells_css_path = '#'+table_element_id+' tbody tr td:nth-child('+str(column_index)+')'
        result_cells = response.css(table_cells_css_path)
        #pdb.set_trace()
        if result_cells:
            for table_cells_selector in result_cells:
                file_link = table_cells_selector.css('a::attr(onclick)').get()
                file_arguments_list = self.get_file_arguments_list(file_link)
                transaction_number = self.get_transaction_number(file_arguments_list)
                attachment_number = self.get_attachment_number(file_arguments_list)
                self.logger.info('Requisitando PDF ID %s', attachment_number)
                yield scrapy.FormRequest('http://www.anvisa.gov.br/datavisa/fila_bula/frmVisualizarBula.asp',
                    formdata={
                        'pNuTransacao': transaction_number,
                        'pIdAnexo': attachment_number
                    },
                    headers={'X-Attachment-Number': attachment_number},
                    callback=self.save_pdf
                )
            #proxima pagina
            search = response.request.headers['X-Med-Search'].decode("utf-8")
            page_size = response.request.headers['X-Page-Size'].decode("utf-8")
            next_page_as_str = str(current_page+1)
            pdb.set_trace()
            yield scrapy.FormRequest('http://www.anvisa.gov.br/datavisa/fila_bula/frmResultado.asp',
                formdata={
                    'txtMedicamento': search,
                    'hddPageSize': page_size,
                    'hddPageAbsolute': next_page_as_str,
                },
                headers={
                    'X-Current-Page': next_page_as_str,
                    'X-Med-Search': search,
                    'X-Page-Size': page_size
                },
                callback=self.crawl_result
            )

    def get_column_index(self, response, table_element_id, target_column_text):
        self.logger.info('Procurando pelo titulo de coluna "%s"', target_column_text)
        column_index = 1
        column_found = False
        for table_headers_selector in response.css('#'+table_element_id+' thead tr th'): #tabela de resultado possui a ID tblResultado
            table_header_as_string = table_headers_selector.get().replace('<br>', ' ')
            if target_column_text in table_header_as_string:
                column_found = True
                break
            else:
                column_index += 1
        if column_found:
            self.logger.info('Coluna encontrada no indice %d', column_index)
            return column_index
        else:
            raise Exception('Nao foi possivel encontrar a coluna "%s"', target_column_text)

    def get_file_arguments_list(self, onclick_function):
        return re.findall('\d+', onclick_function)

    def get_transaction_number(self, file_arguments_list):
        return file_arguments_list[0]

    def get_attachment_number(self, file_arguments_list):
        return file_arguments_list[1]

    def save_pdf(self, response):
        folder = "bula_download"
        filename = response.request.headers['X-Attachment-Number']
        path = os.path.join(SPIDER_DIR, folder, filename.decode("utf-8") + '.pdf')
        if not os.path.exists(folder):
            os.makedirs(folder)
        self.logger.info('Salvando PDF %s', path)
        with open(path, 'wb') as f:
            f.write(response.body)

    def clean_folder(self):
        folder = os.path.join(SPIDER_DIR, "bula_download")
        if os.path.exists(folder):
            shutil.rmtree(folder)

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
        folder = 'autocomplete'
        filepath = os.path.join(SPIDER_DIR, folder, 'medicamentos.txt')
        if not os.path.exists(os.path.join(SPIDER_DIR, folder)):
            os.makedirs(os.path.join(SPIDER_DIR, folder))
        self.logger.info('Salvando arquivo %s', filepath)
        with open(filepath, 'w', encoding='utf-8') as f:
            for suggestion in suggestions_list:
                f.write(suggestion.replace('"','').replace('[','').replace(']',''))
                f.write('\n')

configure_logging()
runner = CrawlerRunner()

@defer.inlineCallbacks
def crawl():
    yield runner.crawl(AutocompleteSpider)
    #pdb.set_trace()
    yield runner.crawl(AnvisaSpider, search=sys.argv[1])
    reactor.stop()

crawl()
reactor.run() # the script will block here until the last crawl call is finished
