import scrapy
import re

class AnvisaSpider(scrapy.Spider):
    name = 'anvisa'

    def start_requests(self):
        form_data = {
            'txtMedicamento': 'dipirona',
            'txtEmpresa': '',
            'txtNuExpediente': '',
            'txtDataPublicacaoI': '',
            'txtDataPublicacaoF': '',
            'txtPageSize': '3',
            'btnPesquisar': ''
        }
        return [
            scrapy.FormRequest("http://www.anvisa.gov.br/datavisa/fila_bula/frmResultado.asp",
            formdata=form_data,
            callback=self.request_callback)
        ]
                                   

    def request_callback(self, response):
        download_pdf_url = "http://www.anvisa.gov.br/datavisa/fila_bula/frmVisualizarBula.asp"
        column_index = 1
        target_column_text = "Bula do Profissional"
        for table_headers_selector in response.css("#tblResultado thead tr th"): #tabela de resultado possui a ID tblResultado
            table_header_as_string = table_headers_selector.get().replace("<br>", " ")
            #print("table_header_text: "+table_header_as_string)
            if target_column_text in table_header_as_string:
                #print("achei no index", column_index)
                break
            else:
                column_index += 1
            #print(table_header_as_string)
        table_cells_css_path = "#tblResultado tbody tr td:nth-child("+str(column_index)+")"
        print(table_cells_css_path)
        for table_cells_selector in response.css(table_cells_css_path):
            file_link = table_cells_selector.css("a::attr(onclick)").get()
            file_arguments_list = self.get_file_arguments_list(file_link)
            transaction_number = self.get_transaction_number(file_arguments_list)
            attachment_number = self.get_attachment_number(file_arguments_list)
            print(file_link+" -> "+str(transaction_number)+" and "+str(attachment_number))
            #print(file_link)

    def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'author': quote.xpath('span/small/text()').get(),
                'text': quote.css('span.text::text').get(),
            }

        # next_page = response.css('li.next a::attr("href")').get()
        # if next_page is not None:
        #     yield response.follow(next_page, self.parse)

    def get_file_arguments_list(self, onclick_function):
        return re.findall("\d+", onclick_function)

    def get_transaction_number(self, file_arguments_list):
        return file_arguments_list[0]

    def get_attachment_number(self, file_arguments_list):
        return file_arguments_list[1]