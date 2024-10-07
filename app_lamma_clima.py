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

# Descrição das variáveis
DESCRICAO_VARIAVEIS = {
    'P': 'Precipitação corrigida (mm)',
    'UR': 'Umidade Relativa a 2 metros (%)',
    'Tmed': 'Temperatura média a 2 metros (°C)',
    'Tmax': 'Temperatura máxima a 2 metros (°C)',
    'Tmin': 'Temperatura mínima a 2 metros (°C)',
    'Tdew': 'Ponto de orvalho a 2 metros (°C)',
    'U2': 'Velocidade do vento a 2 metros (m/s)',
    'U2max': 'Velocidade máxima do vento a 2 metros (m/s)',
    'U2min': 'Velocidade mínima do vento a 2 metros (m/s)',
    'Qg': 'Radiação solar incidente na superfície (W/m²)',
    'Qo': 'Radiação solar de céu claro na superfície (W/m²)'
}

# Função para buscar dados da API NASA POWER
def obter_dados_nasa(latitude, longitude, data_inicio, data_fim, variaveis):
    # Cria a lista de parâmetros selecionados pelo usuário
    parametros = ','.join([VARIAVEIS_DISPONIVEIS[v] for v in variaveis])
    
    url = f"https://power.larc.nasa.gov/api/temporal/daily/point?parameters={parametros}&community=RE&longitude={longitude}&latitude={latitude}&start={data_inicio}&end={data_fim}&format=JSON"
    
    response = requests.get(url)
    if response.status_code == 200:
        dados = response.json()
        parametros = dados['properties']['parameter']
        
        # Verificar se os parâmetros selecionados estão no resultado
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

# Função para criar uma aba com as definições de cada variável
def criar_definicoes(variaveis):
    definicoes = {
        "Variável": variaveis,
        "Descrição": [DESCRICAO_VARIAVEIS[v] for v in variaveis]
    }
    df_definicoes = pd.DataFrame(definicoes)
    return df_definicoes

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

# Seletor de variáveis para download
variaveis_selecionadas = st.multiselect(
    "Selecione as variáveis climáticas que deseja baixar:",
    options=list(VARIAVEIS_DISPONIVEIS.keys()),
    default=list(VARIAVEIS_DISPONIVEIS.keys())
)

# Exibir descrição das variáveis selecionadas
st.markdown("### Descrição das variáveis selecionadas:")
for var in variaveis_selecionadas:
    st.write(f"**{var}**: {DESCRICAO_VARIAVEIS[var]}")

# Exibir observação sobre o tempo de processamento dependendo da quantidade de dados
st.markdown(
    """
    <p style='color:red;'>
    Observação: Dependendo da quantidade de locais e anos de dados, o processo de download pode demorar. 
    Por exemplo, para 20 locais e 30 anos de dados, pode levar em torno de 10 minutos para completar o download.
    </p>
    """, unsafe_allow_html=True
)

# Exibir observação sobre coordenadas em graus decimais
st.markdown(
    """
    <p style='color:red;'>
    Importante: As coordenadas devem estar em graus decimais. Exemplo: Latitude -21.7946, Longitude -48.1766
    </p>
    """, unsafe_allow_html=True
)

# Exibir observação sobre coordenadas em graus decimais
st.markdown(
    """
    <p style='color:red;'>
    Atenção aos Dados Climáticos da NASA POWER

Os dados da NASA POWER têm um atraso de 6 dias e uma resolução espacial de 0,5° x 0,5° (aproximadamente 55 km).
Isso pode afetar a precisão em áreas menores ou análises muito recentes. 
Considere essas características ao utilizar os dados para suas atividades.
    </p>
    """, unsafe_allow_html=True
)

# Opção de inserir um local manualmente ou carregar um arquivo Excel
opcao = st.radio("Escolha a forma de inserir os dados:", ("Inserir um local manualmente", "Carregar arquivo Excel com múltiplos locais"))

if opcao == "Inserir um local manualmente":
    # Inputs para latitude e longitude com precisão de seis casas decimais
    latitude = st.text_input("Latitude", value="-21.794600")
    longitude = st.text_input("Longitude", value="-48.176600")

    # Botão para buscar dados
    if st.button("Buscar dados"):
        with st.spinner('Estamos processando seus dados. Aguarde.'):
            try:
                lat = float(latitude)
                lon = float(longitude)
                st.session_state['dados'] = obter_dados_nasa(lat, lon, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
            except ValueError:
                st.error("Por favor, insira valores válidos para latitude e longitude.")
        
        if st.session_state.get('dados') is not None:
            st.success("Dados obtidos com sucesso!")
            st.write(st.session_state['dados'])
            
            # Criando a aba de definições das variáveis
            df_definicoes = criar_definicoes(variaveis_selecionadas)
            
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
    # Exibir link para download do modelo de arquivo
    st.markdown(f"[Baixe o modelo de arquivo aqui]({MODELO_ARQUIVO_URL}) para inserir múltiplos locais.")
    
    # Upload de arquivo Excel
    file = st.file_uploader("Faça upload de um arquivo Excel com colunas: 'Nome do Local', 'Latitude', 'Longitude'")

    if file:
        with st.spinner('Estamos processando seus dados. Aguarde.'):
            # Processar o arquivo e obter dados climáticos para todos os locais
            st.session_state['dados'] = processar_excel(file, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
        
        if st.session_state.get('dados') is not None:
            st.success("Dados obtidos com sucesso!")
            st.write(st.session_state['dados'])
            
            # Criando a aba de definições das variáveis
            df_definicoes = criar_definicoes(variaveis_selecionadas)
            
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
