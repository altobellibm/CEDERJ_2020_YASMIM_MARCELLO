from googletrans import Translator
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from io import StringIO
from pathlib import Path
import os
import pdb
import json
import re

CURRENT_FILE_PATH = Path(__file__).parent

def translate_excipients(input_files_dir, output_files_dir):
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

translate_excipients(CURRENT_FILE_PATH.parent / "bulas" / "pdf_content", CURRENT_FILE_PATH / "translated_content")