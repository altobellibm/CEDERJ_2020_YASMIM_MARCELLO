import pandas as pd
import json
import datetime as dt
from pathlib import Path

bula_download = Path(__file__).parent / 'scrapy' / 'bula_download'
bulas_content = Path(__file__).parent / 'pdfreader' / 'bulas_content'
df = pd.DataFrame(columns=['Medicamento', 'Bula', 'Formulação', 'Formulação encontrada?', 'Excipientes', 'Excipientes encontrados?'])
for folder in bula_download.glob('*'):
    if folder.is_dir():
        for file in folder.glob('*'):
            if file.is_file():
                record = {
                    'Medicamento': folder.name,
                    'Bula': file.name,
                    'Formulação encontrada?': 'Não',
                    'Excipientes encontrados?': 'Não'
                }
                parsed_content_file = (bulas_content / folder.name / file.stem).with_suffix('.json')
                if parsed_content_file.exists() and parsed_content_file.is_file():
                    with open(parsed_content_file, 'r', encoding='utf-8') as parsed:
                        try:
                            parsed_content = json.loads(parsed.read())
                        except:
                            parsed_content = ''
                    if parsed_content:
                        for json_record in parsed_content:
                            formulation = json_record['formulacao']
                            record['Formulação'] = formulation
                            if formulation:
                                record['Formulação encontrada?'] = 'Sim'
                            excipients = json_record['excipientes'].lstrip('[').rstrip(']')
                            record['Excipientes'] = excipients
                            if excipients:
                                record['Excipientes encontrados?'] = 'Sim'
                            df = df.append(record, ignore_index=True)
                    else:
                        df = df.append(record, ignore_index=True)

with pd.ExcelWriter((Path(__file__).parent / 'output').with_suffix('.xlsx')) as writer:  
    df.to_excel(writer, sheet_name='Visão Bulas')

stop = 0