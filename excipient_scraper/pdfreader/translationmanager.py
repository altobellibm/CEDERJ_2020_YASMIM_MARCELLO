from googletrans import Translator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pathlib import Path
#from excipient_scraper.filemanager import FileManager
import os
import pdb
import json
import re

CURRENT_FILE_PATH = Path(__file__).parent

class TranslationManager:

    def translate_excipients(self, input_files_dir, output_files_dir):
        translator = Translator()
        for file in input_files_dir.glob('*'):
            if file.is_file():
                with open(file, 'r') as input_file:
                    original_json = json.loads(input_file.read())
                translated_excipientes = translator.translate(original_json['excipientes'], src='pt', dest='en')
                original_json['excipientes_ingles'] = translated_excipientes.text
                if not output_files_dir.exists():
                    Path.mkdir(output_files_dir)
                with open(output_files_dir / file.name, 'w') as output_file:
                    output_file.write(json.dumps(original_json, indent=4))
                print('Arquivo ', file.name, ' traduzido')

    def clean_folder_recursive(self, path):
        if path.exists():
            if path.is_dir():
                files = path.glob('**/*')
                for f in files:
                    if f.is_file():
                        f.unlink()

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

    def translate(self):
        output_files_dir = CURRENT_FILE_PATH / "translated_content"
        self.clean_folder_recursive(output_files_dir)
        self.translate_excipients(CURRENT_FILE_PATH / "bulas" / "pdf_content", CURRENT_FILE_PATH / "translated_content")