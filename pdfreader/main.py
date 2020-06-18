from os import path, getcwd
from glob import glob
from PdfReader import MinerArticle
import numpy as np
from texttable import Texttable
from datetime import timedelta, datetime
import pdb

mypath = path.join(getcwd(), "dataset", "*.pdf")
files = glob(mypath)
erro_reading = []
propr_farmac = {}
inicio = datetime.now()
pdb.set_trace()
for file in files:
    inicio_mineracao = datetime.now()
    print(f"Nome do arquivo: {file.replace(path.join(getcwd(), 'dataset', ''), '')}\n")
    try:
        pdf = MinerArticle(file)
        colunas = [item for item in str(pdf).split("Propriedade Farmacêuticas: ") if item != '']
        for coluna in colunas:
            valores = [valor for valor in coluna.split("\n") if valor not in ['', ' ']]
            propr_farmac[valores[0]] = valores[1:]

        maxlen = max(len(propr_farmac['Hardness ']), len(propr_farmac['Friability ']),
                     len(propr_farmac['Disintegration ']))
        for prop in propr_farmac.keys():
            [propr_farmac[prop].append('Variable not found.') for x in range(maxlen - len(propr_farmac[prop]))]

        imprimir_tbl(propr_farmac)
        print(f'Tempo de mineração: {time_diff(inicio_mineracao)}\n')
    except:
        erro_reading.append(file.replace(path.join(getcwd(), 'dataset', ''), ''))

if len(erro_reading) > 0:
    print("\n**************************\nError reading files:")
    [print(erro + '\n') for erro in erro_reading]

print(f'Tempo Total gasto: {time_diff(inicio)}')

def imprimir_tbl(dados):
    tabela = Texttable()
    lista = [list(dados.keys())]
    for tupla in range(len(dados['Hardness '])):
        linha = []
        [linha.append(dados[chave][tupla]) for chave in dados.keys()]
        lista.append(linha)
    dados = np.array(lista).T
    tamanhos = [len(max(linha, key=len)) for linha in dados]
    tabela.set_cols_width(tamanhos)
    tabela.set_cols_align(["c", "c", "c"])
    tabela.add_rows(lista)
    print("Dados:\n" + tabela.draw())

def time_diff(ini):
    duracao = timedelta.total_seconds(datetime.now() - ini)
    return f'{duracao:.2f} segundos'