from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pathlib import Path
import os
import pdb
import json

CURRENT_FILE_PATH = Path(__file__).parent

def convert_pdf_to_txt(path):
    pdf_resource_manager = PDFResourceManager()
    retstr = StringIO()
    laparams = LAParams(
        line_margin=4, #default 0.3
        char_margin=6 #default 2.0
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

def get_formulation(text_section):
    section_start_string = 'cada '
    section_end_string_list = [' contém', ' contem']
    formulation_start = text_section.find(section_start_string)
    if formulation_start > -1:
        formulation_end = text_section.find(section_end_string_list[0])
        if not formulation_end > -1:
            formulation_end = text_section.find(section_end_string_list[1])
        if formulation_end > -1:
            return text_section[(formulation_start + len(section_start_string)) : formulation_end]

    return ''

def clean_folder(path, folder):
    folder_path = CURRENT_FILE_PATH / folder
    if folder_path.exists():
        files = folder_path.glob('**/*')
        for f in files:
            if f.is_file():
                f.unlink()

def get_excipient(text_section):
    ## CASO 1 [Excipientes:, .]
    text_section = text_section.lower()
    search_string = 'excipientes:'
    section_start = text_section.find(search_string)
    section_end = text_section.find('.', section_start)
    if section_start > -1 and section_end > -1:
        excipient_as_text = text_section[(section_start + len(search_string)) : section_end]
        excipient_list = [x.replace('\n', '').strip() for x in excipient_as_text.split(',')]
        return excipient_list

    ## CASO 2 ['excipiente: ', .]
    search_string = 'excipiente:'
    section_start = text_section.find(search_string)
    section_end = text_section.find('.', section_start)
    if section_start > -1:
        if section_end > -1:
            #tentando achar o final por quebra de linha
            section_end = text_section.find('\n\n', section_start)
            if section_end < 0:
                section_end = text_section.find('\n \n', section_start)
            if section_end > -1:
                #final eh ponto
                excipient_as_text = text_section[(section_start + len(search_string)) : section_end]
                excipient_list = [x.replace('\n', '').strip() for x in excipient_as_text.split(',')]
                return excipient_list

    ## CASO 3 excipientes*
    search_string = 'excipientes*'
    string_occurrence = text_section.find(search_string)
    if string_occurrence > -1:
        start_string = '*'
        section_start = text_section.find(start_string, (string_occurrence + len(search_string)))
        section_end = text_section.find('.', section_start)
        if section_start > -1 and section_end > -1:
            excipient_as_text = text_section[(section_start + len(start_string)) : section_end]
            excipient_list = [x.replace('\n', '').strip() for x in excipient_as_text.split(',')]
            return excipient_list

    ## CASO 4 veículos:
    search_string = 'veículos:'
    section_start = text_section.find(search_string)
    section_end = text_section.find('.', section_start)
    if section_start > -1 and section_end > -1:
        excipient_as_text = text_section[(section_start + len(search_string)) : section_end]
        excipient_list = [x.replace('\n', '').strip() for x in excipient_as_text.split(';')]
        return excipient_list

    ## CASO 5 excipiente**
    search_string = 'excipiente**'
    string_occurrence = text_section.find(search_string)
    if string_occurrence > -1:
        start_string = '**'
        section_start = text_section.find(start_string, (string_occurrence + len(search_string)))
        section_end = text_section.find('.', section_start)
        if section_start > -1 and section_end > -1:
            excipient_as_text = text_section[(section_start + len(start_string)) : section_end]
            excipient_list = [x.replace('\n', '').strip() for x in excipient_as_text.split(',')]
            return excipient_list

    return []

pdf_files_dir = CURRENT_FILE_PATH.parent / "scrapy" / "bula_download"
txt_files_dir = CURRENT_FILE_PATH / "pdf_content"
clean_folder(txt_files_dir, 'pdf_content')
composition = 'composição'
technical_info = 'informações técnicas'
indications = 'indicações'
for file in pdf_files_dir.glob('*'):
    if file.is_file():
        filename_wo_extension = file.stem
        txt_file_path = (txt_files_dir / filename_wo_extension).with_suffix('.txt')
        print('**** Arquivo ' + str(file) + ' ****')
        clean_file(txt_file_path)
        pdf_text_content = convert_pdf_to_txt(file).lower()
        print('PDF lido')
        composition_occurrences_amount = pdf_text_content.count(composition)
        technical_info_occurrences_amount = pdf_text_content.count(technical_info)
        composition_start_index = 0
        composition_end_index = 0
        for i in range(min(composition_occurrences_amount, technical_info_occurrences_amount)):
            composition_start_index = pdf_text_content.find(composition, composition_start_index + 1)
            print('Range start: ' + str(composition_start_index))
            composition_end_index = pdf_text_content.find(technical_info, composition_start_index + 1)
            print('Range end: ' + str(composition_end_index))
            if composition_end_index < composition_start_index:
                #se cairmos aqui eh devido ao 'informacoes tecnicas' vir antes da 'composicao'
                #neste caso, devemos procurar por 'indicacoes' para delimitar o fim da secao desejada
                composition_end_index = pdf_text_content.find(indications)
                print('Range end ajustado: ' + str(composition_end_index))
            if composition_end_index > composition_start_index:
                #se apos a verificacao pelos fins de secao alguma for bem sucedida, o trecho eh valido
                composition_section = pdf_text_content[composition_start_index : composition_end_index]
                write_to_file(txt_file_path, 'a', composition_section)
                write_to_file(txt_file_path, 'a', '\nFORMULAÇÃO: ' + get_formulation(composition_section) + '\n')
                write_to_file(txt_file_path, 'a', '\nEXCIPIENTES: ' + str(get_excipient(composition_section)) + '\n')