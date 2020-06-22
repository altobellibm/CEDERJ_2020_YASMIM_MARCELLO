from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
import os
import pdb

CURRENT_PATH = os.path.abspath(os.path.dirname(__file__))

def convert_pdf_to_txt(path):
    pdf_resource_manager = PDFResourceManager()
    retstr = StringIO()
    device = TextConverter(pdf_resource_manager, retstr, codec='utf-8', laparams=LAParams(line_margin=0.1)) #especificando o parametro line_margin para garantir a ordem correta de interpretacao do PDF
    with open(path, 'rb') as fp:
        pdf_page_interpreter = PDFPageInterpreter(pdf_resource_manager, device)
        for page in PDFPage.get_pages(fp, set(), maxpages=0, password="", caching=True, check_extractable=True):
            pdf_page_interpreter.process_page(page)
        text = retstr.getvalue()
    device.close()
    retstr.close()
    return text

files_dir = os.path.join(CURRENT_PATH, os.pardir, "scrapy", "bula_download")
for filename in os.listdir(files_dir):
    if filename == '4922996.pdf':
        with open('pdf'+filename+'.txt', 'w', encoding='utf-8') as f:
            f.write('\n**** Arquivo ' + filename + ' ****\n')
            print('**** Arquivo ' + filename + ' ****')
            pdf_text_content = convert_pdf_to_txt(os.path.abspath(os.path.join(files_dir, filename)))
            print('PDF lido')
            composition_occurrences_amount = pdf_text_content.count('COMPOSIÇÃO')
            composition_start_index = 0
            composition_end_index = 0
            for i in range(composition_occurrences_amount):
                composition_start_index = pdf_text_content.find('COMPOSIÇÃO', composition_start_index)
                print('Range start: ' + str(composition_start_index))
                composition_end_index = pdf_text_content.find('INFORMAÇÕES TÉCNICAS', composition_start_index)
                print('Range end: ' + str(composition_end_index))
                #if composition_end_index < composition_start_index:
                #    #se cairmos aqui eh devido ao 'informacoes tecnicas' vir antes da 'composicao'
                #    #neste caso, devemos procurar por 'indicacoes' para delimitar o fim da secao desejada
                #    composition_end_index = pdf_text_content.find('INDICAÇÕES')
                #    print('Range end ajustado: ' + str(composition_end_index))
                f.write(pdf_text_content[composition_start_index : composition_end_index])
#print(convert_pdf_to_txt(my_file))