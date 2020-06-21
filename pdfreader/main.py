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
    device = TextConverter(pdf_resource_manager, retstr, codec='utf-8', laparams=LAParams())
    with open(path, 'rb') as fp:
        pdf_page_interpreter = PDFPageInterpreter(pdf_resource_manager, device)
        for page in PDFPage.get_pages(fp, set(), maxpages=0, password="", caching=True, check_extractable=True):
            pdf_page_interpreter.process_page(page)
        text = retstr.getvalue()
    device.close()
    retstr.close()
    return text

files_dir = os.path.join(CURRENT_PATH, os.pardir, "scrapy", "bula_download")
#my_file = os.path.join(files_dir, '2462371.pdf')
composition_start_index = -1
with open('pdf.txt', 'w', encoding='utf-8') as f:
    for filename in os.listdir(files_dir):
        f.write('**** Arquivo ' + filename + ' ****')
        print('**** Arquivo ' + filename + ' ****')
        pdf_text_content = convert_pdf_to_txt(os.path.abspath(os.path.join(files_dir, filename)))
        print('PDF lido')
        for i in range(pdf_text_content.count('COMPOSIÇÃO')):
            composition_start_index = pdf_text_content.find('COMPOSIÇÃO')
            print('Range start: ' + composition_start_index)
            composition_end_index = pdf_text_content.find('INFORMAÇÕES TÉCNICAS')
            print('Range end: ' + composition_end_index)
            if composition_end_index < composition_start_index:
                #se cairmos aqui eh devido ao 'informacoes tecnicas' vir antes da 'composicao'
                #neste caso, devemos procurar por 'indicacoes' para delimitar o fim da secao desejada
                composition_end_index = pdf_text_content.find('INDICAÇÕES')
            f.write(pdf_text_content[composition_start_index : composition_end_index])
#print(convert_pdf_to_txt(my_file))