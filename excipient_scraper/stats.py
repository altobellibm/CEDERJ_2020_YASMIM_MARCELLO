import pandas as pd
import json
from pathlib import Path

bula_download = Path(__file__).parent / 'scrapy' / 'bula_download'
bulas_content = Path(__file__).parent / 'pdfreader' / 'bulas_content'
df = pd.DataFrame(columns=['Medicamento', 'Bula', 'Formulação', 'Excipientes'])
for folder in bula_download.glob('*'):
    if folder.is_dir():
        for file in folder.glob('*'):
            if file.is_file():
                record = {'Medicamento': folder.name, 'Bula': file.name}
                parsed_content_file = (bulas_content / folder.name / file.stem).with_suffix('.json')
                if parsed_content_file.exists() and parsed_content_file.is_file():
                    with open(parsed_content_file, 'r', encoding='utf-8') as parsed:
                        try:
                            parsed_content = json.loads(parsed.read())
                        except:
                            parsed_content = ''
                    if parsed_content:
                        for json_record in parsed_content:
                            record['Formulação'] = json_record['formulacao']
                            record['Excipientes'] = json_record['excipientes']
                            df = df.append(record, ignore_index=True)
                    else:
                        df = df.append(record, ignore_index=True)

with pd.ExcelWriter('output.xlsx') as writer:  
    df.to_excel(writer, sheet_name='Visão Bulas')

stop = 0