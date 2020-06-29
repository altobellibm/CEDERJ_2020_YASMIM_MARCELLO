import pandas as pd
import json
import datetime as dt
from pathlib import Path

def get_bulas_dataframe(bula_download_path, bulas_content_path):
    df = pd.DataFrame(columns=['Medicamento', 'Bula', 'Formulação', 'Formulação encontrada?', 'Excipientes', 'Excipientes encontrados?'])
    for folder in bula_download_path.glob('*'):
        if folder.is_dir():
            for file in folder.glob('*'):
                if file.is_file():
                    record = {
                        'Medicamento': folder.name,
                        'Bula': file.name,
                        'Formulação encontrada?': 'Não',
                        'Excipientes encontrados?': 'Não'
                    }
                    parsed_content_file = (bulas_content_path / folder.name / file.stem).with_suffix('.json')
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
    return df

def get_excipients_dataframe(proportions_path, excipients_dict):
    df = pd.DataFrame(columns=['Excipiente', 'Tradução', 'Ocorrência no livro'])
    for file in proportions_path.glob('*.json'):
        if file.is_file():
            try:
                excipient = excipients_dict[file.stem]
            except KeyError:
                excipient = ''
            
            with open(file, 'r', encoding='utf-8') as parsed:
                try:
                    parsed_content = json.loads(parsed.read())
                except:
                    parsed_content = ''
            if parsed_content[file.stem]:
                for book_ocurrence in parsed_content[file.stem]:
                    record = {
                        'Excipiente': excipient,
                        'Tradução': file.stem,
                        'Ocorrência no livro': book_ocurrence
                    }
                    df = df.append(record, ignore_index=True)
            else:
                record = {
                    'Excipiente': excipient,
                    'Tradução': file.stem,
                    'Ocorrência no livro': ''
                }
                df = df.append(record, ignore_index=True)
    return df

def save_to_excel(filepath, sheet, dataframe):
    with pd.ExcelWriter(filepath) as writer:  
        dataframe.to_excel(writer, index=False, sheet_name=sheet, engine='xlsxwriter')

def get_excipients_translation_dict(path):
        excipients_dict = {}
        for folder in path.glob('*'):
            if folder.is_dir():
                for file in folder.glob('*'):
                    with open(file, 'r', encoding='utf-8') as f:
                        json_object_list = json.loads(f.read())
                        for json_object in json_object_list:
                            excipientes_pt = json_object['excipientes'].lstrip("['").rstrip("']").replace("' , '", "','").replace("', '", "','").strip()
                            excipients_pt_list = excipientes_pt.split("','")

                            excipientes_ingles = json_object['excipientes_ingles'].lstrip("['").rstrip("']").replace("' , '", "','").replace("', '", "','").strip()
                            excipients_ingles_list = excipientes_ingles.split("','")
                            for index in range(len(excipients_pt_list)):
                                excipients_dict[excipients_ingles_list[index].strip()] = excipients_pt_list[index].strip()
        return excipients_dict

bula_download = Path(__file__).parent / 'scrapy' / 'bula_download'
bulas_content = Path(__file__).parent / 'pdfreader' / 'bulas_content'
df_bulas = get_bulas_dataframe(bula_download, bulas_content)
output_bulas_file = (Path(__file__).parent / 'bulas').with_suffix('.xlsx')
save_to_excel(output_bulas_file, 'Visao Bulas', df_bulas)

translated_content = Path(__file__).parent / 'pdfreader' / 'translated_content'
proportions = Path(__file__).parent / 'pdfreader' / 'proportions'
excipients_dict = get_excipients_translation_dict(translated_content)
df_excipientes = get_excipients_dataframe(proportions, excipients_dict)
output_excipients_file = (Path(__file__).parent / 'excipientes').with_suffix('.xlsx')
save_to_excel(output_excipients_file, 'Visão Excipientes', df_excipientes)

stop = 0