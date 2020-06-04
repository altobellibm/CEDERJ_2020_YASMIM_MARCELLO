import scrapy

class BularioAnvisaSpider(scrapy.Spider):
    name = 'bularioanvisa'
    #start_urls = [
    #    'http://quotes.toscrape.com/tag/humor/',
    #]
    # request_with_cookies = Request(url="http://www.example.com",
    #                            cookies=[{'name': 'currency',
    #                                     'value': 'USD',
    #                                     'domain': 'example.com',
    #                                     'path': '/currency'}])

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
        #print(response.css("#tblResultado tbody").getall())
        for quote in response.css("#tblResultado tbody tr"): #tabela de resultado possui a ID tblResultado
            print(quote.get())
        # pensando em como baixar o PDF
        # fVisualizarBula('6568522018', '10663733')
        # bate em http://www.anvisa.gov.br/datavisa/fila_bula/frmVisualizarBula.asp
        # com um POST recebendo FormData
        #pNuTransacao: 6568522018 (1o parametro)
        #pIdAnexo: 10663733 (2o parametro)

        #TODO: fazer primeiro uma requisição para identificar quantos registros são
        #Ex.: fazer uma requisição com 1 por página. Se derem 5 páginas, vamos fazer uma nova requisição com 5 para capturar tudo.
        #O bulário carrega as páginas seguintes com Javascript conforme o clique do botão, então é bem tranquilo e rápido fazer requisição
        #com 1 registro por página.

    def parse(self, response):
        for quote in response.css('div.quote'):
            yield {
                'author': quote.xpath('span/small/text()').get(),
                'text': quote.css('span.text::text').get(),
            }

        # next_page = response.css('li.next a::attr("href")').get()
        # if next_page is not None:
        #     yield response.follow(next_page, self.parse)