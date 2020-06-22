from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pathlib import Path
import os
import pdb

CURRENT_FILE_PATH = os.path.abspath(os.path.dirname(__file__))

def convert_pdf_to_txt(path):
    pdf_resource_manager = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams(
        line_margin=5 #default 0.3
    )
    device = TextConverter(pdf_resource_manager, retstr, codec='utf-8', laparams=laparams) #especificando o parametro line_margin para garantir a ordem correta de interpretacao do PDF
    with open(path, 'rb') as fp:
        pdf_page_interpreter = PDFPageInterpreter(pdf_resource_manager, device)
        #pagenos = [5]
        pagenos = []
        for page in PDFPage.get_pages(fp, pagenos, maxpages=0, password="", caching=True, check_extractable=True):
            pdf_page_interpreter.process_page(page)
        text = retstr.getvalue()
    device.close()
    retstr.close()
    return text

def clean_file(path):
    if path.is_file():
        open(path, 'w').close()

def write_to_file(path, mode, content):
    folder = path.parent
    if not folder.exists():
        Path.mkdir(folder)
    with open(path, mode, encoding='utf-8') as f:
        f.write(content)

pdf_files_dir = Path(CURRENT_FILE_PATH, os.pardir, "scrapy", "bula_download")
txt_files_dir = os.path.join(CURRENT_FILE_PATH, "pdf_content")
for filename in os.listdir(pdf_files_dir):
    filename_wo_extension = os.path.splitext(filename)[0]
    txt_file_path = Path(txt_files_dir+'/'+filename_wo_extension).with_suffix('.txt')
    print('**** Arquivo ' + filename + ' ****')
    clean_file(txt_file_path)
    pdf_text_content = convert_pdf_to_txt(os.path.abspath(os.path.join(pdf_files_dir, filename)))
    print('PDF lido')
    composition_occurrences_amount = pdf_text_content.count('COMPOSIÇÃO')
    technical_info_occurrences_amount = pdf_text_content.count('INFORMAÇÕES TÉCNICAS')
    composition_start_index = 0
    composition_end_index = 0
    for i in range(min(composition_occurrences_amount, technical_info_occurrences_amount)):
        composition_start_index = pdf_text_content.find('COMPOSIÇÃO', composition_start_index+1)
        print('Range start: ' + str(composition_start_index))
        composition_end_index = pdf_text_content.find('INFORMAÇÕES TÉCNICAS', composition_start_index+1)
        print('Range end: ' + str(composition_end_index))
        if composition_end_index < composition_start_index:
            #se cairmos aqui eh devido ao 'informacoes tecnicas' vir antes da 'composicao'
            #neste caso, devemos procurar por 'indicacoes' para delimitar o fim da secao desejada
            composition_end_index = pdf_text_content.find('INDICAÇÕES')
            print('Range end ajustado: ' + str(composition_end_index))
        if composition_end_index > composition_start_index:
            #se apos a verificacao pelos fins de secao alguma for bem sucedida, o trecho eh valido
            write_to_file(txt_file_path, 'a', pdf_text_content[composition_start_index : composition_end_index])
