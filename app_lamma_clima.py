import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from datetime import datetime, timedelta

# URL da logo do LAMMA para cabeçalho do app
LOGO_LAMMA_URL_HEADER = "https://lamma.com.br/wp-content/uploads/2024/08/lammapy-removebg-preview.png"

# URL da imagem do NASA POWER para a barra lateral
LOGO_NASA_POWER_URL_SIDEBAR = "https://www.earthdata.nasa.gov/s3fs-public/styles/small_third_320px_/public/2022-11/power_logo_event.png?VersionId=pZIOrAAZH6vCGOJMjhhwP91WJkg0sCus&itok=DrjfYom6"

# URL do arquivo de modelo para download
MODELO_ARQUIVO_URL = "https://github.com/igoragro00/teste_app_clima/blob/main/Modelo_arquivo_entrada.xlsx?raw=true"

# Dicionário de variáveis disponíveis para download
VARIAVEIS_DISPONIVEIS = {
    'P': 'PRECTOTCORR',  # Precipitação corrigida
    'UR': 'RH2M',        # Umidade Relativa a 2 metros
    'Tmed': 'T2M',       # Temperatura média a 2 metros
    'Tmax': 'T2M_MAX',   # Temperatura máxima a 2 metros
    'Tmin': 'T2M_MIN',   # Temperatura mínima a 2 metros
    'Tdew': 'T2MDEW',    # Ponto de Orvalho
    'U2': 'WS2M',        # Velocidade do Vento a 2m
    'U2max': 'WS2M_MAX', # Velocidade Máxima do Vento a 2m
    'U2min': 'WS2M_MIN', # Velocidade Mínima do Vento a 2m
    'Qg': 'ALLSKY_SFC_SW_DWN', # Radiação Solar Incidente
    'Qo': 'CLRSKY_SFC_SW_DWN'  # Radiação Solar de Céu Claro
}

# Função para buscar dados da API NASA POWER
def obter_dados_nasa(latitude, longitude, data_inicio, data_fim, variaveis):
    parametros = ','.join([VARIAVEIS_DISPONIVEIS[v] for v in variaveis])
    
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters={parametros}&community=RE&longitude={longitude}&latitude={latitude}&start={data_inicio}&end={data_fim}&format=JSON"
    
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        parametros = dados['properties']['parameter']
        
        if all(var in parametros for var in [VARIAVEIS_DISPONIVEIS[v] for v in variaveis]):
            df = pd.DataFrame({'Data': list(parametros[VARIAVEIS_DISPONIVEIS[variaveis[0]]].keys())})
            for v in variaveis:
                df[v] = parametros[VARIAVEIS_DISPONIVEIS[v]].values()
            return df
        else:
            st.error("Algumas das variáveis selecionadas não estão disponíveis no resultado da API.")
            return None
    else:
        st.error("Erro ao buscar dados da API NASA POWER. Verifique sua conexão ou tente novamente mais tarde.")
        return None

# Função para processar o arquivo Excel
def processar_excel(file, data_inicio, data_fim, variaveis):
    df_input = pd.read_excel(file)
    resultados = []
    
    for i, row in df_input.iterrows():
        latitude = row['Latitude']
        longitude = row['Longitude']
        nome_local = row['Nome do Local']
        
        df_dados = obter_dados_nasa(latitude, longitude, data_inicio, data_fim, variaveis)
        if df_dados is not None:
            df_dados['Local'] = nome_local
            resultados.append(df_dados)
        else:
            st.error(f"Erro ao buscar dados para o local {nome_local}.")
    
    if resultados:
        return pd.concat(resultados, ignore_index=True)
    else:
        return None

# Interface do Streamlit
st.image(LOGO_LAMMA_URL_HEADER, use_column_width=True)

st.subheader("Aplicativo desenvolvido pelo LAMMA - Laboratório de Máquinas e Mecanização Agrícola da UNESP/Jaboticabal")

st.title("NASA POWER - Download de Dados Climáticos")

# Barra lateral
st.sidebar.title("Informações sobre o App")
st.sidebar.image(LOGO_NASA_POWER_URL_SIDEBAR, use_column_width=True)

# Inputs para intervalo de datas
hoje = datetime.today()
trinta_anos_atras = hoje - timedelta(days=30 * 365)

data_inicio = st.date_input("Data de início", value=trinta_anos_atras, min_value=datetime(1990, 1, 1), max_value=hoje)
data_fim = st.date_input("Data de fim", value=hoje, min_value=data_inicio, max_value=hoje)

# Seletor de variáveis para download
variaveis_selecionadas = st.multiselect(
    "Selecione as variáveis climáticas que deseja baixar:",
    options=list(VARIAVEIS_DISPONIVEIS.keys()),
    default=list(VARIAVEIS_DISPONIVEIS.keys())
)

# Exibir botão de limpar cache
if st.button("Limpar Cache"):
    st.cache_data.clear()
    st.success("Cache limpo com sucesso!")

# Exibir descrição das variáveis selecionadas
st.markdown("### Descrição das variáveis selecionadas:")
for var in variaveis_selecionadas:
    st.write(f"{var}: {DESCRICAO_VARIAVEIS[var]}")

# Opção de inserir um local manualmente ou carregar um arquivo Excel
opcao = st.radio("Escolha a forma de inserir os dados:", ("Inserir um local manualmente", "Carregar arquivo Excel com múltiplos locais"))

if opcao == "Inserir um local manualmente":
    latitude = st.text_input("Latitude", value="-21.794600")
    longitude = st.text_input("Longitude", value="-48.176600")

    if st.button("Buscar dados"):
        with st.spinner('Estamos processando seus dados. Aguarde.'):
            try:
                lat = float(latitude)
                lon = float(longitude)
                dados = obter_dados_nasa(lat, lon, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
                if dados is not None:
                    st.write(dados)
                    # Download dos dados
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                        dados.to_excel(writer, sheet_name="Dados_Climaticos", index=False)
                    output.seek(0)
                    st.download_button(label="Baixar dados como Excel", data=output, file_name="dados_climaticos.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            except ValueError:
                st.error("Por favor, insira valores válidos para latitude e longitude.")

elif opcao == "Carregar arquivo Excel com múltiplos locais":
    st.markdown(f"[Baixe o modelo de arquivo aqui]({MODELO_ARQUIVO_URL}) para inserir múltiplos locais.")
    
    file = st.file_uploader("Faça upload de um arquivo Excel com colunas: 'Nome do Local', 'Latitude', 'Longitude'")
    if file:
        with st.spinner('Estamos processando seus dados. Aguarde.'):
            dados = processar_excel(file, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
            if dados is not None:
                st.write(dados)
                output = BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    dados.to_excel(writer, sheet_name="Dados_Climaticos", index=False)
                output.seek(0)
                st.download_button(label="Baixar dados como Excel", data=output, file_name="dados_climaticos_multiplos_locais.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
            else:
                st.error("Erro ao processar o arquivo ou buscar dados da NASA POWER.")


#streamlit run "c:/Users/Igor Vieira/App_Lamma/app_lamma_clima.py"
