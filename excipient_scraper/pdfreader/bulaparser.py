from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pathlib import Path
import json
import re

CURRENT_FILE_PATH = Path(__file__).parent

class BulaParser:
    def convert_pdf_to_txt(self, path):
        pdf_resource_manager = PDFResourceManager()
        retstr = StringIO()
        laparams = LAParams(
            line_margin=4, #default 0.3
            char_margin=6 #default 2.0
        )
        device = TextConverter(pdf_resource_manager, retstr, codec='utf-8', laparams=laparams) #especificando o parametro line_margin para garantir a ordem correta de interpretacao do PDF
        with open(path, 'rb') as fp:
            pdf_page_interpreter = PDFPageInterpreter(pdf_resource_manager, device)
            pagenos = []
            for page in PDFPage.get_pages(fp, pagenos, maxpages=0, password="", caching=True, check_extractable=True):
                pdf_page_interpreter.process_page(page)
            text = retstr.getvalue()
        device.close()
        retstr.close()
        return text

    def write_to_file(self, path, mode, content):
        folder = path.parent
        if not folder.exists():
            Path.mkdir(folder)
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)

    def get_formulation(self, text_section, start_index=0):
        section_start_string = 'cada '
        section_end_string_list = [' contém', ' contem']
        text_section = text_section[start_index:]
        formulation_start = text_section.find(section_start_string)
        if formulation_start > -1:
            for section_end in section_end_string_list:
                formulation_end = text_section.find(section_end, formulation_start+1)
                if formulation_end > -1:
                    break
            if formulation_end > -1:
                start_index = (formulation_start + len(section_start_string))
                return [formulation_end, text_section[start_index : formulation_end]]

        return [-1, '']

    def get_formulation_ocurrences(self, text_section, start_index=0):
        section_start_string = 'cada '
        section_end_string_list = [' contém', ' contem']
        formulation_start_index = text_section.find(section_start_string)
        count = 0
        while formulation_start_index > -1:
            for section_end in section_end_string_list:
                formulation_end_index = text_section.find(section_end, formulation_start_index)
                if formulation_end_index > -1:
                    formulation_start_index = text_section.find(section_start_string, formulation_end_index+1)
                    count += 1
                    break
            if not formulation_end_index > -1:
                break

        return count

    def clean_string(self, text):
        return re.sub('[\n.()]', '', text).strip()

    def get_double_line_break_index(self, text, start_index):
        line_breaks = ['\n\n', '\n \n']
        index = text.find(line_breaks[0], start_index)
        if not index > -1:
            index = text.find(line_breaks[1], start_index)
        return index

    def parse_excipient_list(self, text, start_string, start_index, end_index, separator):
        excipient_as_text = text[(start_index + len(start_string)) : end_index]
        excipient_as_text = excipient_as_text.replace(' e ', separator)
        excipient_list = [self.clean_string(x) for x in excipient_as_text.split(separator)]
        return excipient_list

    def get_excipient(self, text_section, start_index=0):
        text_section = text_section[start_index:]
        ## CASO 1 [Excipientes:, .]
        text_section = text_section.lower()
        search_string = 'excipientes:'
        section_start_index = text_section.find(search_string)
        if section_start_index > -1:
            section_end_index = self.get_double_line_break_index(text_section, section_start_index)
            if not section_end_index > -1:
                section_end_index = text_section.find('.', section_start_index)
                if section_end_index > -1:
                    #final encontrado
                    return self.parse_excipient_list(text_section, search_string, section_start_index, section_end_index, ',')
            else:
                #final encontrado
                return self.parse_excipient_list(text_section, search_string, section_start_index, section_end_index, ',')

        ## CASO 2 ['excipiente: ', .]
        search_string = 'excipiente:'
        section_start_index = text_section.find(search_string)
        if section_start_index > -1:
            section_end_index = self.get_double_line_break_index(text_section, section_start_index)
            if not section_end_index > -1:
                section_end_index = text_section.find('.', section_start_index)
                if section_end_index > -1:
                    #final encontrado
                    return self.parse_excipient_list(text_section, search_string, section_start_index, section_end_index, ',')
            else:
                #final encontrado
                return self.parse_excipient_list(text_section, search_string, section_start_index, section_end_index, ',')

        ## CASO 3 excipientes*
        search_string = 'excipientes*'
        string_occurrence = text_section.find(search_string)
        if string_occurrence > -1:
            start_string = '*'
            section_start_index = text_section.find(start_string, (string_occurrence + len(search_string)))
            section_end_index = text_section.find('.', section_start_index)
            if section_start_index > -1 and section_end_index > -1:
                return self.parse_excipient_list(text_section, start_string, section_start_index, section_end_index, ',')


        ## CASO 4 veículos:
        search_string = 'veículos:'
        section_start_index = text_section.find(search_string)
        section_end_index = text_section.find('.', section_start_index)
        if section_start_index > -1 and section_end_index > -1:
            return self.parse_excipient_list(text_section, search_string, section_start_index, section_end_index, ';')


        ## CASO 5 excipiente**
        search_string = 'excipiente**'
        string_occurrence = text_section.find(search_string)
        if string_occurrence > -1:
            start_string = '**'
            section_start_index = text_section.find(start_string, (string_occurrence + len(search_string)))
            section_end_index = text_section.find('.', section_start_index)
            if section_start_index > -1 and section_end_index > -1:
                return self.parse_excipient_list(text_section, start_string, section_start_index, section_end_index, ',')


        ## CASO 6 excipientes ... (
        search_string = 'excipientes'
        string_occurrence = text_section.find(search_string)
        if string_occurrence > -1:
            start_string = '('
            section_start_index = text_section.find(start_string, (string_occurrence + len(search_string)))
            section_end_index = text_section.find(')', section_start_index)
            if section_start_index > -1 and section_end_index > -1:
                return self.parse_excipient_list(text_section, start_string, section_start_index, section_end_index, ',')


        ## CASO 7 excipiente ... (
        search_string = 'excipiente'
        string_occurrence = text_section.find(search_string)
        if string_occurrence > -1:
            start_string = '('
            section_start_index = text_section.find(start_string, (string_occurrence + len(search_string)))
            section_end_index = text_section.find(')', section_start_index)
            if section_start_index > -1 and section_end_index > -1:
                return self.parse_excipient_list(text_section, start_string, section_start_index, section_end_index, ',')


        ## CASO 8 veículo ... (
        search_string = 'veículo'
        string_occurrence = text_section.find(search_string)
        if string_occurrence > -1:
            start_string = '('
            section_start_index = text_section.find(start_string, (string_occurrence + len(search_string)))
            section_end_index = text_section.find(')', section_start_index)
            if section_start_index > -1 and section_end_index > -1:
                return self.parse_excipient_list(text_section, start_string, section_start_index, section_end_index, ',')

        ## CASO 9 contém quantidade suficiente de ... como
        search_string = 'quantidade suficiente de'
        string_occurrence = text_section.find(search_string)
        if string_occurrence > -1:
            start_string = 'quantidade suficiente de'
            section_start_index = text_section.find(start_string, (string_occurrence + len(search_string)))
            section_end_index = text_section.find('como', section_start_index)
            if section_start_index > -1 and section_end_index > -1:
                return self.parse_excipient_list(text_section, start_string, section_start_index, section_end_index, ',')

        return []

    def clean_folder_recursive(self, path):
        if path.exists():
            for content in path.glob('**/*'):
                if content.is_file():
                    content.unlink()
                else:
                    self.clean_folder_recursive(content)
                    content.rmdir()

    def parse(self):
        input_files_dir = CURRENT_FILE_PATH.parent / "scrapy" / "bula_download"
        output_files_dir = CURRENT_FILE_PATH / 'bulas_content'
        if not output_files_dir.exists():
            Path.mkdir(output_files_dir)
        self.clean_folder_recursive(output_files_dir)
        composition = 'composição'
        composition_section_end_list = ['informações técnicas', 'informações ao profissional', 'indicações']
        for content in input_files_dir.glob('*'):
            if content.is_dir():
                for file in content.glob('*'):
                    if file.is_file():
                        filename_wo_extension = file.stem
                        output_file_path = (output_files_dir / content.stem / filename_wo_extension).with_suffix('.json')
                        print('Lendo arquivo ' + str(file.parent.name + '/' + file.name))
                        if output_file_path.exists():
                            output_file_path.unlink()
                        pdf_text_content = self.convert_pdf_to_txt(file).lower()
                        composition_occurrences_amount = pdf_text_content.count(composition)
                        for section_end in composition_section_end_list:
                            technical_info_occurrences_amount = pdf_text_content.count(section_end)
                            if technical_info_occurrences_amount > 0:
                                technical_info = section_end
                                break
                        composition_start_index = 0
                        composition_end_index = 0
                        output = []
                        for i in range(min(composition_occurrences_amount, technical_info_occurrences_amount)):
                            composition_start_index = pdf_text_content.find(composition, composition_start_index + 1)
                            composition_end_index = pdf_text_content.find(technical_info, composition_start_index + 1)
                            if composition_end_index > composition_start_index:
                                #se apos a verificacao pelos fins de secao alguma for bem sucedida, o trecho eh valido
                                composition_section = pdf_text_content[composition_start_index : composition_end_index]
                                formulation_ocurrences = self.get_formulation_ocurrences(composition_section)
                                formulation_index = 0
                                for i in range(formulation_ocurrences):
                                    formulation_list = self.get_formulation(composition_section, formulation_index+1)
                                    excipients = str(self.get_excipient(composition_section, formulation_index+1))
                                    output.append({
                                        "formulacao": formulation_list[1],
                                        "excipientes": excipients
                                    })
                                    print('Formulacao: ' + formulation_list[1])
                                    print('Excipientes: ' + excipients)
                                    formulation_index = formulation_list[0]
                                self.write_to_file(output_file_path, 'w', json.dumps(output, indent=4))
