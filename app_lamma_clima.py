import pandas as pd
import streamlit as st
import requests
from io import BytesIO
from datetime import datetime, timedelta

# URL da logo do LAMMA para cabeçalho do app
LOGO_LAMMA_URL_HEADER = "https://lamma.com.br/wp-content/uploads/2024/08/lammapy-removebg-preview.png"

# URL da imagem do NASA POWER para a barra lateral
LOGO_NASA_POWER_URL_SIDEBAR = "https://www.earthdata.nasa.gov/s3fs-public/styles/small_third_320px_/public/2022-11/power_logo_event.png?VersionId=pZIOrAAZH6vCGOJMjhhwP91WJkg0sCus&itok=DrjfYom6"

# Função para buscar dados da API NASA POWER
def obter_dados_nasa(latitude, longitude, data_inicio, data_fim):
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters=PRECTOTCORR,RH2M,T2M,T2M_MAX,T2M_MIN,T2MDEW,WS2M,WS2M_MAX,WS2M_MIN,ALLSKY_SFC_SW_DWN,CLRSKY_SFC_SW_DWN&community=RE&longitude={longitude}&latitude={latitude}&start={data_inicio}&end={data_fim}&format=JSON"
    
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        # Organizando os dados que vêm da API
        parametros = dados['properties']['parameter']
        df = pd.DataFrame({
            'Data': list(parametros['T2M'].keys()),
            'P': parametros['PRECTOTCORR'].values(),  # Precipitação
            'UR': parametros['RH2M'].values(),        # Umidade Relativa
            'Tmed': parametros['T2M'].values(),       # Temperatura Média
            'Tmax': parametros['T2M_MAX'].values(),   # Temperatura Máxima
            'Tmin': parametros['T2M_MIN'].values(),   # Temperatura Mínima
            'Tdew': parametros['T2MDEW'].values(),    # Ponto de Orvalho
            'U2': parametros['WS2M'].values(),        # Velocidade do Vento a 2m
            'U2max': parametros['WS2M_MAX'].values(), # Velocidade Máxima do Vento a 2m
            'U2min': parametros['WS2M_MIN'].values(), # Velocidade Mínima do Vento a 2m
            'Qg': parametros['ALLSKY_SFC_SW_DWN'].values(), # Radiação Solar Incidente
            'Qo': parametros['CLRSKY_SFC_SW_DWN'].values()  # Radiação Solar na Superfície
        })
        return df
    else:
        return None

# Função para criar uma aba com as definições de cada variável
def criar_definicoes():
    definicoes = {
        "Variável": ['P', 'UR', 'Tmed', 'Tmax', 'Tmin', 'Tdew', 'U2', 'U2max', 'U2min', 'Qg', 'Qo'],
        "Descrição": [
            'Precipitação corrigida (mm)',
            'Umidade Relativa a 2 metros (%)',
            'Temperatura média a 2 metros (°C)',
            'Temperatura máxima a 2 metros (°C)',
            'Temperatura mínima a 2 metros (°C)',
            'Ponto de orvalho a 2 metros (°C)',
            'Velocidade do vento a 2 metros (m/s)',
            'Velocidade máxima do vento a 2 metros (m/s)',
            'Velocidade mínima do vento a 2 metros (m/s)',
            'Radiação solar incidente na superfície (W/m²)',
            'Radiação solar de céu claro na superfície (W/m²)'
        ]
    }
    df_definicoes = pd.DataFrame(definicoes)
    return df_definicoes

# Função para processar o arquivo Excel
def processar_excel(file, data_inicio, data_fim):
    df_input = pd.read_excel(file)
    resultados = []
    
    for i, row in df_input.iterrows():
        latitude = row['Latitude']
        longitude = row['Longitude']
        nome_local = row['Nome do Local']
        
        df_dados = obter_dados_nasa(latitude, longitude, data_inicio, data_fim)
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

st.sidebar.write("""
### Importância dos Dados Climáticos:
- Os dados climáticos são fundamentais para o planejamento agrícola, monitoramento ambiental e gestão de recursos naturais.
- O acesso a informações sobre temperatura, precipitação, umidade e radiação solar ajuda a entender padrões climáticos e otimizar atividades no campo.

### Objetivo do Aplicativo:
- Este aplicativo oferece uma maneira simples e prática de obter dados climáticos de qualquer local do mundo, utilizando as coordenadas geográficas e o período selecionado pelo usuário.
- O aplicativo permite baixar os dados diretamente em formato Excel, facilitando a análise e integração com outros sistemas.

### Sobre o NASA POWER:
- O *NASA POWER* (Prediction of Worldwide Energy Resources) é um sistema que fornece dados climáticos históricos e atuais a partir de satélites da NASA.
""")

st.sidebar.write("""
**RESPONSÁVEIS:**  
- Prof. Dr. Rouverson Pereira da Silva – FCAV/UNESP [Linkedin](https://www.linkedin.com/in/rouverson-pereira-da-silva/)
- Msc. Igor Cristian de Oliveira Vieira - FCAV/UNESP [Linkedin](https://www.linkedin.com/in/eng-igor-vieira/)
- Msc. Lucas Eduardo Zonfrilli - FCAV/UNESP [Linkedin](https://www.linkedin.com/in/lucas-eduardo-zonfrilli/) 
""")

# Sidebar "REALIZAÇÃO"
st.sidebar.subheader("REALIZAÇÃO")
st.sidebar.image("http://lamma.com.br/wp-content/uploads/2024/02/IMG_1713-300x81.png")
st.sidebar.write("[Visite o site do LAMMA](https://lamma.com.br/)")
st.sidebar.write("[Visite o instagram do LAMMA](https://www.instagram.com/lamma.unesp/)")
st.sidebar.write("[Visite o site do RSRG](https://www.rsrg.net.br/)")

# Inputs para intervalo de datas
hoje = datetime.today()
trinta_anos_atras = hoje - timedelta(days=30 * 365)

data_inicio = st.date_input("Data de início", value=trinta_anos_atras, min_value=datetime(1990, 1, 1), max_value=hoje)
data_fim = st.date_input("Data de fim", value=hoje, min_value=data_inicio, max_value=hoje)

# Converter datas para o formato YYYYMMDD
data_inicio_formatada = data_inicio.strftime("%Y%m%d")
data_fim_formatada = data_fim.strftime("%Y%m%d")

# Opção de inserir um local manualmente ou carregar um arquivo Excel
opcao = st.radio("Escolha a forma de inserir os dados:", ("Inserir um local manualmente", "Carregar arquivo Excel com múltiplos locais"))

if opcao == "Inserir um local manualmente":
    # Inputs para latitude e longitude
    latitude = st.number_input("Latitude", format="%.6f", value=st.session_state.get('latitude', -21.7946))
    longitude = st.number_input("Longitude", format="%.6f", value=st.session_state.get('longitude', -48.1766))

    # Botão para buscar dados
    if st.button("Buscar dados"):
        st.session_state['dados'] = obter_dados_nasa(latitude, longitude, data_inicio_formatada, data_fim_formatada)
        
        if st.session_state['dados'] is not None:
            st.success("Dados obtidos com sucesso!")
            st.write(st.session_state['dados'])
            
            # Criando a aba de definições das variáveis
            df_definicoes = criar_definicoes()
            
            # Permitir download dos dados em formato Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state['dados'].to_excel(writer, sheet_name="Dados_Climaticos", index=False)
                df_definicoes.to_excel(writer, sheet_name="Definicoes", index=False)
            output.seek(0)

            st.download_button(
                label="Baixar dados como Excel",
                data=output,
                file_name="dados_climaticos.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Erro ao buscar dados da NASA POWER.")

elif opcao == "Carregar arquivo Excel com múltiplos locais":
    # Upload de arquivo Excel
    file = st.file_uploader("Faça upload de um arquivo Excel com colunas: 'Nome do Local', 'Latitude', 'Longitude'")

    if file:
        # Processar o arquivo e obter dados climáticos para todos os locais
        st.session_state['dados'] = processar_excel(file, data_inicio_formatada, data_fim_formatada)
        
        if st.session_state['dados'] is not None:
            st.success("Dados obtidos com sucesso!")
            st.write(st.session_state['dados'])
            
            # Criando a aba de definições das variáveis
            df_definicoes = criar_definicoes()
            
            # Download dos dados e definições em formato Excel
            output = BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                st.session_state['dados'].to_excel(writer, sheet_name="Dados_Climaticos", index=False)
                df_definicoes.to_excel(writer, sheet_name="Definicoes", index=False)
            output.seek(0)

            st.download_button(
                label="Baixar dados como Excel",
                data=output,
                file_name="dados_climaticos_multiplos_locais.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.error("Erro ao processar o arquivo ou buscar dados da NASA POWER.")



#streamlit run "c:/Users/Igor Vieira/App_Lamma/app_lamma_clima.py"