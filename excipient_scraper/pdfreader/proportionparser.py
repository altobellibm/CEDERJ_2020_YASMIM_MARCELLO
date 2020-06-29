from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter, HTMLConverter, XMLConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO, BytesIO
from pathlib import Path
import os
import pdb
import json
import re

class ProportionParser:
    def convert_pdf_to_txt(self, path, pagenos=[]):
        pdf_resource_manager = PDFResourceManager()
        retstr = StringIO()
        laparams = LAParams(
            line_margin=3, #default 0.3
            char_margin=35 #default 2.0
        )
        device = TextConverter(pdf_resource_manager, retstr, codec='utf-8', laparams=laparams) #especificando o parametro line_margin para garantir a ordem correta de interpretacao do PDF
        with open(path, 'rb') as fp:
            pdf_page_interpreter = PDFPageInterpreter(pdf_resource_manager, device)
            for page in PDFPage.get_pages(fp, pagenos, maxpages=0, password="", caching=True, check_extractable=True):
                pdf_page_interpreter.process_page(page)
            text = retstr.getvalue()
        device.close()
        retstr.close()
        return text

    def convert_pdf(self, path, format='text', codec='utf-8', password='', pagenos=set()):
        rsrcmgr = PDFResourceManager()
        retstr = BytesIO()
        laparams = LAParams()
        if format == 'text':
            device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        elif format == 'html':
            device = HTMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        elif format == 'xml':
            device = XMLConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        else:
            raise ValueError('provide format, either text, html or xml!')
        fp = open(path, 'rb')
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        maxpages = 0
        caching = True
        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
            interpreter.process_page(page)

        text = retstr.getvalue().decode()
        fp.close()
        device.close()
        retstr.close()
        return text

    def write_to_file(self, path, mode, content):
        folder = path.parent
        if not folder.exists():
            Path.mkdir(folder)
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)

    def get_excipients_set(self, path):
        excipients_set = set()
        for folder in path.glob('*'):
            if folder.is_dir():
                for file in folder.glob('*'):
                    with open(file, 'r', encoding='utf-8') as f:
                        json_object_list = json.loads(f.read())
                        for json_object in json_object_list:
                            excipients = json_object['excipientes_ingles'].lstrip("['").rstrip("']").replace("', '", "','")
                            excipients_list = excipients.split("','")
                            for excipient in excipients_list:
                                excipients_set.add(excipient.strip())
        return excipients_set


    def excipients_pages_dict(self, excipients):
        summary_file = Path(__file__).parent / 'summary.json'
        result = {}
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = json.loads(f.read())
        
        for excipient in excipients:
            try:
                result[excipient] = content[excipient]
            except:        
                pass
        return result

    def get_excipient_pages(self, excipients):
        summary_file = Path(__file__).parent / 'summary.json'
        pagenos = set()
        with open(summary_file, 'r', encoding='utf-8') as f:
            content = json.loads(f.read())
        
        for excipient in excipients:
            try:
                pagenos.add(content[excipient])
            except:        
                pass
        return pagenos

    ''' Encontra a frase atual, com base no indice referencia, encontrando o primeiro caracter  '''
    def get_phrase(self, text, index):
        phrase_end_index = text.find('. ', index+1)
        phrase_start_index = text[:phrase_end_index].rfind('. ')
        if not phrase_start_index > -1:
            phrase_start_index = 0
        return text[phrase_start_index:phrase_end_index]

    def clean_folder(self, path):
        if path.exists():
            files = path.glob('*')
            for f in files:
                if f.is_file():
                    f.unlink()

    def parse_text(self, output_folder):
        translations_folder = Path(__file__).parent / 'translated_content'
        handbook_file = Path(__file__).parent / 'Handbook-of-Pharmaceutical-Excipients_6t.pdf'
        translated_excipients_set = self.get_excipients_set(translations_folder)
        excipients_pages_dict = self.excipients_pages_dict(translated_excipients_set)
        pagenos = self.get_excipient_pages(translated_excipients_set)
        print(len(pagenos), 'excipientes identificados no sumario')
        formulation_section_start_string = '7 Applications in Pharmaceutical Formulation or\nTechnology\n'
        formulation_section_end_string = '8 Description'
        self.clean_folder(output_folder)
        for excipient, page in excipients_pages_dict.items():
            print('Buscando por', excipient)
            #buscamos tambem na pagina seguinte, pois pode ser que a secao de formulacao so termine na proxima
            excipient_pages_content = self.convert_pdf_to_txt(handbook_file, [page, page+1])
            formulation_section_start_index = excipient_pages_content.find(formulation_section_start_string)
            if formulation_section_start_index > -1:
                formulation_section_end_index = excipient_pages_content.find(formulation_section_end_string, formulation_section_start_index)
                formulation_section = excipient_pages_content[(formulation_section_start_index + len(formulation_section_start_string)) : formulation_section_end_index]
                if not Path.exists(output_folder):
                    Path.mkdir(output_folder)
                with open((output_folder / excipient).with_suffix('.txt'), 'w', encoding='utf-8') as f:
                    f.write(formulation_section)
            else:
                print('Secao de formulacao nao encontrada para', excipient)

    def parse(self):
        output_folder = Path(__file__).parent / 'proportions'
        self.parse_text(output_folder)

        measures = ['%', 'w/w', 'w/v', 'mL']
        for file in output_folder.glob('*.txt'):
            if file.is_file():
                result = set()
                excipient = file.stem
                with open(file, 'r', encoding='utf-8') as f:
                    file_content = f.read()
                    file_content = file_content.replace('\n', ' ')
                    file_content = re.sub(r'[(]\d+[^A-Za-z0-9]\d+[)]', '', file_content)
                    file_content = re.sub(r'[(]\d+[)]', '', file_content)
                    for symbol in measures:
                        count = file_content.count(symbol)
                        last_index = 0
                        for i in range(count):
                            text_index = file_content.find(symbol, last_index)
                            phrase = self.get_phrase(file_content, text_index)
                            result.add(phrase)
                            last_index = text_index + 1
                
                with open((output_folder / excipient).with_suffix('.json'), 'w', encoding='utf-8') as f:
                    json_content = {excipient: list(result)}
                    f.write(json.dumps(json_content, indent=4))

        print('Fim da captura de proporcoes. Resultado em', output_folder)