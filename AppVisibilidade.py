import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, LineString, Polygon
import numpy as np
import fiona
import time
import customtkinter as ctk
import webbrowser
import requests
from tkinter.filedialog import askopenfilename, askdirectory
from tkinter import messagebox, ttk, Label
from tkinter import *
from pathlib import Path
from PIL import Image, ImageTk
from io import BytesIO

# Tema para a janela criada
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

# Interface gráfica para iteração com o usuário
janela = ctk.CTk()
janela.title("EVU 1.0")
janela.geometry("755x425")
janela.rowconfigure(0, weight=1)
janela.columnconfigure([0, 1], weight=1)
janela.resizable(width=False, height=False)

# Função para carregar imagem da URL
def carregar_imagem(url, largura, altura):
    response = requests.get(url)
    image_data = response.content
    image = Image.open(BytesIO(image_data))
    image = image.resize((largura, altura))
    return ImageTk.PhotoImage(image)

# URL da imagem
url_imagem = "https://docs.google.com/uc?export=download&id=15vAZ8QAk7wYXuyRt5HiEO1V3K00JMDzH"

# Dimensões da imagem
largura_imagem = 400
altura_imagem = 400

# Carregando a imagem da URL
imagem = carregar_imagem(url_imagem, largura_imagem, altura_imagem)

# Exibindo a imagem em um widget Label
label_imagem = Label(janela, image=imagem)
label_imagem.place(x=340, y=10)

texto = Label(janela, text="Estudo de Visibilidade de Ultrapassagem", font=("Helvetica", 12, "bold"), background=janela.cget("bg"), fg="white")
texto.place(x=10, y=398)

# Função para criar entry
def criar_entry(janela, placeholder, x, y):
    valor = ctk.CTkEntry(
        janela,
        placeholder_text=placeholder,
        placeholder_text_color="white",
        text_color="white",
        border_width=3,
        corner_radius=10,
        width=320)
    valor.place(x=x, y=y)
    return valor

# Função para criar combobox
def criar_combobox(janela, valores, x, y, width, height):
    combobox = ttk.Combobox(janela, values=valores, state='readonly', width=width, height=height)
    combobox.set("Escolha a Zona UTM conforme o Mapa")  # Define o texto padrão exibido no ComboBox
    combobox.place(x=x, y=y)
    return combobox

# Caixas para inserção de valores
valor_velocidade = criar_entry(janela, "Informe a velocidade em km/h", 10, 100)
valor_proibicao = criar_entry(janela, "Informe a distância mínima de proibição em Metros", 10, 138)
valor_faixa = criar_entry(janela, "Informe a largura da faixa em Metros", 10, 176)
valor_acost = criar_entry(janela, "Informe a largura do acostamento em Metros", 10, 214)
valor_obst = criar_entry(janela, "Informe a distância de obstáculo em Metros", 10, 252)
combobox_crs = criar_combobox(janela, ['Zona 18', 'Zona 19N', 'Zona 19', 'Zona 20N', 'Zona 20', 'Zona 21N', 'Zona 21', 'Zona 22N', 'Zona 22', 'Zona 23', 'Zona 24', 'Zona 25'], 10, 290, 50, 35)
valor_nome_arquivo = criar_entry(janela, "Informe o nome dos arquivos a serem gerados", 10, 320)

# Variáveis para caminhos
caminho_plan = None
caminho_alt = None
caminho_dxf = None
caminho_salvar = None

# Functions para executar ações
def importar_txt():
    global caminho_plan, caminho_alt, caminho_dxf
    caminho_plan = askopenfilename(title="Selecione o arquivo correspondente ao relatório de Planimetria!")
    caminho_alt = askopenfilename(title="Selecione o arquivo correspondente ao relatório de Altimetria!")
    caminho_dxf = askopenfilename(title="Selecione o arquivo correspondente ao DXF que contém o Eixo!")

def selecionar_pasta():
    global caminho_salvar
    caminho_salvar = askdirectory(title="Selecione uma Pasta para Salvar")

def abrir_nuvem():
    url_do_site = 'https://drive.google.com/drive/folders/1zto8zSvGU3hQv6o5vbRzpDZ19DJdhR4c?usp=sharing'
    webbrowser.open(url_do_site)

def verificar():
    try:
        velocidade = int(valor_velocidade.get())
        proibicao = int(valor_proibicao.get())
        faixa = valor_faixa.get().replace(',', '.')
        faixa = float(faixa)
        acost = valor_acost.get().replace(',', '.')
        acost = float(acost)
        obst = valor_obst.get().replace(',', '.')
        obst = float(obst)
        crs = (combobox_crs.get())
        # Ajuste para definir o valor baseado na seleção do combobox
        if crs == 'Zona 18':
            crs = 31978
        elif crs == 'Zona 19N':
            crs = 31973
        elif crs == 'Zona 19':
            crs = 31979
        elif crs == 'Zona 20N':
            crs = 31974
        elif crs == 'Zona 20':
            crs = 31980
        elif crs == 'Zona 21N':
            crs = 31975
        elif crs == 'Zona 21':
            crs = 31981
        elif crs == 'Zona 22N':
            crs = 31976
        elif crs == 'Zona 22':
            crs = 31982
        elif crs == 'Zona 23':
            crs = 31983
        elif crs == 'Zona 24':
            crs = 31984
        elif crs == 'Zona 25':
            crs = 31985
    except ValueError as e:
        campo_errado = str(e).split("'")[1]
        messagebox.showerror("Erro", f"O campo '{campo_errado}' foi preenchido incorretamente. Por favor, preencha todos os campos corretamente!")
        return

    nome_arquivo = valor_nome_arquivo.get()
    largura_total = faixa + acost + obst

    global caminho_plan, caminho_alt, caminho_dxf
    if caminho_plan is None or caminho_alt is None or caminho_dxf is None:
        messagebox.showerror("Erro", "Por favor, importe os arquivos necessários!")
        return
    
    global caminho_salvar
    if caminho_salvar is None:
        messagebox.showerror("Erro", "Por favor, selecione uma pasta para salvar os arquivos!")
        return

    messagebox.showinfo('Estudo de Visibilidade de Ultrapassagem', 'Aguarde enquanto o estudo é realizado. Isso pode levar alguns minutos.')

    ti = time.time()

    df_planimetria = pd.read_excel(caminho_plan)
    df_altimetria = pd.read_excel(caminho_alt)
    ponto_inicial = df_altimetria["Estaca"].min()
    ponto_final = df_altimetria["Estaca"].max()
    pontos_analise = list(range(ponto_inicial, ponto_final + 20, 20))
    df_analise = pd.DataFrame(pontos_analise, columns=["Estaca"])

    df_planimetria["Ponto"] = [Point(round(row[3], 4), round(row[2], 4)) for row in df_planimetria.itertuples()]
    df_altimetria["Ponto"] = [Point(row[1], row[2]) for row in df_altimetria.itertuples()]

    eixo = LineString(df_planimetria["Ponto"])
    eixo_esq = eixo.parallel_offset(largura_total, "left")
    eixo_dir = eixo.parallel_offset(largura_total, "right")

    linha_alt = LineString(df_altimetria["Ponto"])

    gdf_planimetria = gpd.GeoDataFrame(df_planimetria, geometry="Ponto")
    gdf_altimetria = gpd.GeoDataFrame(df_altimetria, geometry="Ponto")

    dict_velocidades = {
        40: 140,
        50: 160,
        60: 180,
        70: 210,
        80: 245,
        90: 280,
        100: 320,
        110: 355,
    }

    df_velocidades = pd.DataFrame.from_dict(dict_velocidades, orient="index", columns=["Distância"]).reset_index(names=["Velocidade"])

    def verificar_alt(pto, sentido):
        if pto in df_altimetria["Estaca"].values:
            ponto = df_altimetria[df_altimetria["Estaca"] == pto]["Ponto"].values[0]

            raio = df_velocidades[df_velocidades["Velocidade"] == velocidade]["Distância"].values[0]
            circle = ponto.buffer(raio)

            intersection = linha_alt.intersection(circle)
            x, y = intersection.xy

            if sentido == "C":
                ponto_sentido = Point(x[-1], y[-1])
                diagonal = LineString((ponto, ponto_sentido))
            else:
                ponto_sentido = Point(x[0], y[0])
                diagonal = LineString((ponto_sentido, ponto))

            diagonal_offset = diagonal.parallel_offset(1.2, "left")

            if diagonal_offset.intersection(intersection):
                # poly = linha_verificada.intersection(linha_regua)
                typeline = 1
            else:
                typeline = 2

            return typeline
        else:
            return None

    cache = {}

    def verificar_plan(pto, sentido):
        try:
            if pto in df_planimetria["Estaca"].values:
                ponto = df_planimetria[df_planimetria["Estaca"] == pto]["Ponto"].values[0]

                raio = df_velocidades[df_velocidades["Velocidade"] == velocidade]["Distância"].values[0]
                circle = ponto.buffer(raio)

                intersection = eixo.intersection(circle)
                x, y = intersection.xy

                if sentido == "C":
                    ponto_sentido = Point(x[-1], y[-1])
                else:
                    ponto_sentido = Point(x[0], y[0])

                diagonal = LineString((ponto, ponto_sentido))

                if diagonal.intersection(eixo_dir) or diagonal.intersection(eixo_esq):
                    typeline = 1
                else:
                    typeline = 2

                cache[pto] = typeline
                return typeline
            else:
                return None
        except:
            return cache[pto - 20]

    dict_analise = {}
    dict_sh = {}
    typeline_ref = 0
    indice = 0

    for row in df_analise.itertuples():
        estaca = row[1]

        alt_c = verificar_alt(estaca, "C")
        alt_d = verificar_alt(estaca, "D")
        plan_c = verificar_plan(estaca, "C")
        plan_d = verificar_plan(estaca, "D")

        typeline_c = min(alt_c, plan_c)
        typeline_d = min(alt_d, plan_d)

        dict_analise[estaca] = [alt_c, plan_c, typeline_c, alt_d, plan_d, typeline_d]

        if typeline_c == 1 and typeline_d == 1:
            typeline = 3
            layer = "LFO-3"
        elif typeline_c == 1 and typeline_d == 2:
            typeline = 4
            layer = "LFO-4D"
        elif typeline_c == 2 and typeline_d == 1:
            typeline = 5
            layer = "LFO-4C"
        elif typeline_c == 2 and typeline_d == 2:
            typeline = 2
            layer = "LFO-2"

        if typeline_ref == 0:
            typeline_ref = typeline
            estaca_ref = estaca
            layer_ref = layer
        elif typeline_ref != typeline:
            dict_sh[indice] = [estaca_ref, estaca, typeline_ref, layer_ref]
            indice += 1
            estaca_ref = estaca
            typeline_ref = typeline
            layer_ref = layer

    df_excel = pd.DataFrame.from_dict(
        dict_analise,
        orient="index",
        columns=[
            "Altimetria Crescente",
            "Planimetria Crescente",
            "Typeline Crescente",
            "Altimetria Decrescente",
            "Planimetria Decrescente",
            "Typeline Decrescente",
        ]).reset_index(names="Estaca")

    df_dwg = pd.DataFrame.from_dict(dict_sh, orient="index", columns=["Km Inicial", "Km Final", "Typeline", "Layer"])
    df_dwg["Extensão"] = df_dwg["Km Final"] - df_dwg["Km Inicial"]

    df_dwg['Extensão'] = df_dwg['Extensão'].astype(str) + 'm'

    nome_excel = caminho_salvar + "\\" + nome_arquivo + ".xlsx"
    df_dwg.to_excel(nome_excel, sheet_name='Resultado', index=False)

    gdf_eixo = gpd.read_file(caminho_dxf)
    gdf_eixo = gdf_eixo[gdf_eixo["Layer"] == "EIXO"]
    gdf_eixo = gdf_eixo[["geometry"]]

    lista_coord = list(eixo.coords)
    df_coords = pd.DataFrame(lista_coord, columns=["Easting", "Northing"])
    df_coords["Ponto"] = [Point(round(row[1], 4), round(row[2], 4)) for row in df_coords.itertuples()]
    df_coords = df_coords[["Ponto"]]
    df_planimetria = df_planimetria[["Estaca", "Ponto"]]

    list_linhas = []

    for row in df_dwg.itertuples():
        kmi = row[1]
        kmf = row[2]
        filtro = df_planimetria.loc[(df_planimetria["Estaca"] == kmi) | (df_planimetria["Estaca"] == kmf)]
        linha = LineString(list(set(filtro["Ponto"].values)))
        midpoint = linha.centroid
        raio = linha.length / 2
        circle = midpoint.buffer(raio)
        intersection = eixo.intersection(circle)
        list_linhas.append(intersection)

    df_dwg["Linha"] = list_linhas

    df_dwg["Name"] = range(len(df_dwg))
    df_dwg = df_dwg[["Name", "Layer", "Linha"]]

    gdf_dwg = gpd.GeoDataFrame(df_dwg, geometry="Linha", crs=crs)
    gdf_dwg["Name"] = gdf_dwg["Name"].astype(str)

    # Geração do GeoDataFrame a partir do gdf_defeitos KML
    fiona.drvsupport.supported_drivers["KML"] = "rw"

    nome_kml = caminho_salvar + "\\" + nome_arquivo + ".kml"
    gdf_dwg.to_file(nome_kml,driver="KML")

    tf = time.time()

    tempo_total = tf - ti
    
    messagebox.showinfo("Estudo de Visibilidade de Ultrapassagem","Análise concluída com sucesso! Tempo de execução: {:.2f} segundos".format(tempo_total))

    janela.destroy()

def fechar():
    janela.destroy()

def criar_button(janela, texto, comando, x, y, fg_cor, hover_cor, width, height):
    botao = ctk.CTkButton(
        janela,
        text=texto,
        font=("Helvetica", 16, "bold"),
        command=comando,
        width=width,
        height=height,
        fg_color=fg_cor,
        hover_color=hover_cor)
    botao.place(x=x, y=y)
    return botao

# Buttons
but_arquivos = criar_button(janela, "Arquivos", abrir_nuvem, 10, 10, None, None, width=320, height=35)
but_abrir_txt = criar_button(janela, "Importar", importar_txt, 10, 55, None, None, width=155, height=35)
but_selecionar_pasta = criar_button(janela, "Salvar", selecionar_pasta, 175, 55, None, None, width=155, height=35)
but_verificar = criar_button(janela, "Verificar", verificar, 10, 357, None, None, width=155, height=35)
but_fechar = criar_button(janela, "Fechar", fechar, 175, 357, "red", "#960000", width=155, height=35)

janela.mainloop()