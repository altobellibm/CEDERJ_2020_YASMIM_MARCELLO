import scrapy
import re
import pdb
import unicodedata
from pathlib import Path

CURRENT_FOLDER = Path(__file__).parent

class AnvisaBularioSpider(scrapy.Spider):
    name = 'anvisa_bulario'
    request_encoding = 'cp1252'
    custom_settings = {
        'LOG_LEVEL': 'INFO',
    }

    def start_requests(self):
        if not hasattr(self, "search"):
            raise Exception('Especifique o parametro com o principio ativo desejado')
        else:
            autocomplete_file_path = CURRENT_FOLDER / 'autocomplete' / 'medicamentos.txt'
            if autocomplete_file_path.is_file():
                suggestion_list = self.get_search_suggestions(autocomplete_file_path, self.search)
                if not suggestion_list:
                    raise Exception('Nenhum sugestao foi encontrada para o parametro de busca fornecido')
                for suggestion in suggestion_list:
                    first_page = 1
                    page_size = 10
                    self.clean_folder_recursive(CURRENT_FOLDER / 'bula_download')
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
                        encoding=self.request_encoding,
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
        return suggestions
                                   
    def crawl_result(self, response):
        current_page = int(response.request.headers['X-Current-Page'])
        self.logger.info('Resposta da pagina %d recebida', current_page)
        table_element_id = 'tblResultado'
        column_index = self.get_column_index(response, table_element_id, 'Bula do Profissional')
        
        table_cells_css_path = '#'+table_element_id+' tbody tr td:nth-child('+str(column_index)+')'
        result_cells = response.css(table_cells_css_path)
        if result_cells:
            search = response.request.headers['X-Med-Search'].decode(self.request_encoding)
            self.logger.info('Baixando PDFs da pagina %d do medicamento "%s"', current_page, search)
            for table_cells_selector in result_cells:
                file_link = table_cells_selector.css('a::attr(onclick)').get()
                file_arguments_list = self.get_file_arguments_list(file_link)
                transaction_number = self.get_transaction_number(file_arguments_list)
                attachment_number = self.get_attachment_number(file_arguments_list)
                yield scrapy.FormRequest('http://www.anvisa.gov.br/datavisa/fila_bula/frmVisualizarBula.asp',
                    formdata={
                        'pNuTransacao': transaction_number,
                        'pIdAnexo': attachment_number
                    },
                    headers={
                        'X-Med-Search': search,
                        'X-Attachment-Number': attachment_number
                    },
                    encoding=self.request_encoding,
                    callback=self.save_pdf
                )
            #proxima pagina
            page_size = response.request.headers['X-Page-Size'].decode(self.request_encoding)
            next_page_as_str = str(current_page+1)
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
                encoding=self.request_encoding,
                callback=self.crawl_result
            )

    def get_column_index(self, response, table_element_id, target_column_text):
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
            return column_index
        else:
            raise Exception('Nao foi possivel encontrar a coluna "%s"', target_column_text)

    def get_file_arguments_list(self, onclick_function):
        return re.findall(r'\d+', onclick_function)

    def get_transaction_number(self, file_arguments_list):
        return file_arguments_list[0]

    def get_attachment_number(self, file_arguments_list):
        return file_arguments_list[1]

    def save_pdf(self, response):
        folder = response.request.headers['X-Med-Search'].decode(self.request_encoding)
        output_path = CURRENT_FOLDER / 'bula_download' / folder
        filename = response.request.headers['X-Attachment-Number'].decode(self.request_encoding)
        file_path = (output_path / filename).with_suffix('.pdf')
        if not output_path.parent.exists():
            Path.mkdir(output_path.parent)
        if not output_path.exists():
            Path.mkdir(output_path)
        self.logger.debug('Salvando PDF %s', file_path)
        with open(file_path, 'wb') as f:
            f.write(response.body)

    def clean_folder_recursive(self, path):
        if path.exists():
            for content in path.glob('**/*'):
                if content.is_file():
                    content.unlink()
                else:
                    self.clean_folder_recursive(content)
                    content.rmdir()