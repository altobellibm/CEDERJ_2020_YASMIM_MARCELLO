import scrapy
import re
import pdb
import shutil

class AnvisaSpider(scrapy.Spider):
    name = 'anvisa'

    def start_requests(self):
        yield scrapy.FormRequest("http://www.anvisa.gov.br/datavisa/fila_bula/frmResultado.asp",
            formdata={
                'txtMedicamento': 'dipirona',
                'txtEmpresa': '',
                'txtNuExpediente': '',
                'txtDataPublicacaoI': '',
                'txtDataPublicacaoF': '',
                'hddPageSize': '10',
                'btnPesquisar': ''
            },
            callback=self.crawl_result
        )
                                   
    def crawl_result(self, response):
        self.logger.info("Resposta da busca recebida")
        table_element_id = "tblResultado"
        column_index = self.get_column_index(response, table_element_id, "Bula do Profissional")
        
        table_cells_css_path = "#"+table_element_id+" tbody tr td:nth-child("+str(column_index)+")"
        result_cells = response.css(table_cells_css_path)
        #pdb.set_trace()
        for table_cells_selector in result_cells:
            file_link = table_cells_selector.css("a::attr(onclick)").get()
            file_arguments_list = self.get_file_arguments_list(file_link)
            transaction_number = self.get_transaction_number(file_arguments_list)
            attachment_number = self.get_attachment_number(file_arguments_list)
            self.logger.info("Requisitando PDF ID %d", attachment_number)
            self.request_pdf(transaction_number, attachment_number)

    def get_column_index(self, response, table_element_id, target_column_text):
        self.logger.info("Procurando pelo titulo de coluna '%s'", target_column_text)
        column_index = 1
        column_found = False
        for table_headers_selector in response.css("#"+table_element_id+" thead tr th"): #tabela de resultado possui a ID tblResultado
            table_header_as_string = table_headers_selector.get().replace("<br>", " ")
            if target_column_text in table_header_as_string:
                column_found = True
                break
            else:
                column_index += 1
        if column_found:
            self.logger.info("Coluna encontrada no indice %d", column_index)
            return column_index
        else:
            raise Exception("Nao foi possivel encontrar a coluna '%s'", target_column_text)

    def request_pdf(self, transaction_number, attachment_number):
        yield scrapy.FormRequest("http://www.anvisa.gov.br/datavisa/fila_bula/frmVisualizarBula.asp",
            formdata={
                'pNuTransacao': transaction_number,
                'pIdAnexo': attachment_number
            },
            headers={'X-Attachment-Number': attachment_number},
            callback=self.save_pdf
        )

    def get_file_arguments_list(self, onclick_function):
        return re.findall("\d+", onclick_function)

    def get_transaction_number(self, file_arguments_list):
        return file_arguments_list[0]

    def get_attachment_number(self, file_arguments_list):
        return file_arguments_list[1]

    def save_pdf(self, response):
        folder = "bula_download"
        filename = response.request.headers['X-Attachment-Number']
        path = folder + "/" + filename + ".pdf"
        self.logger.info('Salvando PDF %s', path)
        with open(path, 'wb') as f:
            f.write(response.body)

    def clean_folder(self, folder):
        for filename in os.listdir(folder):
            os.remove(folder+"/"+filename)