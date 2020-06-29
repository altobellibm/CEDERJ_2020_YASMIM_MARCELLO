from googletrans import Translator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pathlib import Path
import json
import re

CURRENT_FILE_PATH = Path(__file__).parent

class TranslationManager:
    input_files_dir = CURRENT_FILE_PATH / "bulas_content"
    output_files_dir = CURRENT_FILE_PATH / "translated_content"

    def translate_excipients(self, input_files_dir, output_files_dir):
        translator = Translator()
        for content in input_files_dir.glob('*'):
            if content.is_dir():
                for file in content.glob('*'):
                    if file.is_file():
                        file_with_folder = str(file.parent.name) + '/' + file.name
                        output_file = output_files_dir / file_with_folder
                        if not output_files_dir.exists():
                                Path.mkdir(output_files_dir.parent)
                        with open(file, 'r') as input_file:
                            try:
                                json_list = json.loads(input_file.read())
                            except:
                                json_list = ''
                        if json_list:
                            translated_json_list = []
                            for obj in json_list:
                                translated_obj = obj
                                try:
                                    translated_excipientes = translator.translate(obj['excipientes'], src='pt', dest='en')
                                    translated_obj['excipientes_ingles'] = translated_excipientes.text
                                    translated_json_list.append(translated_obj)
                                except:
                                    pass
                            if not output_file.parent.exists():
                                Path.mkdir(output_file.parent)
                            with open(output_file, 'w') as output:
                                output.write(json.dumps(translated_json_list, indent=4))
                            print('Excipientes do arquivo ', file_with_folder, ' traduzidos')
                        else:
                            print('Erro na traducao do arquivo ', file_with_folder)

    def clean_folder_recursive(self, path):
        if path.exists():
            for content in path.glob('**/*'):
                if content.is_file():
                    content.unlink()
                else:
                    self.clean_folder_recursive(content)
                    content.rmdir()

    def translate(self):
        self.clean_folder_recursive(self.output_files_dir)
        self.translate_excipients(self.input_files_dir, self.output_files_dir)