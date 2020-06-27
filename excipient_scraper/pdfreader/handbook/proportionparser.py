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

    def write_to_file(self, path, mode, content):
        folder = path.parent
        if not folder.exists():
            Path.mkdir(folder)
        with open(path, mode, encoding='utf-8') as f:
            f.write(content)

    def get_excipients_set(self, folder):
        excipients_set = set()
        for file in folder.glob('*'):
            if file.is_file():
                with open(file, encoding='utf-8') as f:
                    json_content = json.loads(f.read())
                    excipients_list = json_content['excipientes_ingles'].lstrip("['").rstrip("']").split("', '")
                    for excipient in excipients_list:
                        excipients_set.add(excipient.strip())
        return excipients_set

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

    def parse(self):
        translations_folder = Path(__file__).parent / 'translated_content'
        handbook_file = Path(__file__).parent / 'Handbook-of-Pharmaceutical-Excipients_6t.pdf'
        measures = ['%', 'mL']
        excipients_set = self.get_excipients_set(translations_folder)
        pagenos = self.get_excipient_pages(excipients_set)
        summary = self.convert_pdf_to_txt(handbook_file, pagenos)
        print(len(pagenos), 'excipientes identificados no sumario')
        formulation_section = 'Applications in Pharmaceutical Formulation or Technology'
        summary_garbage_end_index = summary.find(formulation_section)
        summary = summary[(summary_garbage_end_index + len(formulation_section)):]
        self.write_to_file(Path(__file__).parent / 'summary.txt', 'w', summary)
        summary_dict = {}
        real_page_offset = 29
        txt_output = Path(__file__).parent / 'summary.txt'
        with open(txt_output, encoding='utf-8') as f:
            for line in f.readlines():
                if not 'Appendix' in line and not 'Contents' in line:
                    line = line.rstrip('\n').strip('\f')
                    last_space_index = line.rfind(' ')
                    excipient = line[:last_space_index]
                    pageno = line[last_space_index+1:]
                    if len(excipient) > 0 and len(pageno) > 0:
                        try:
                            summary_dict[excipient] = int(pageno) + real_page_offset
                        except:
                            summary_dict[excipient] = pageno
        print('Apendices e cabecalhos removidos')
        txt_output.unlink()

        json_output = Path(__file__).parent / 'summary.json'
        with open(json_output, 'w', encoding='utf-8') as f:
            f.write(json.dumps(summary_dict, indent=4))

        print('Fim da conversao do sumario. Resultado em', json_output)