import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta

# URL da logo do LAMMA para o cabeçalho do app
LOGO_LAMMA_URL_HEADER = "https://lamma.com.br/wp-content/uploads/2024/08/lammapy-removebg-preview.png"

# URL da imagem do NASA POWER para a barra lateral
LOGO_NASA_POWER_URL_SIDEBAR = "https://www.earthdata.nasa.gov/s3fs-public/styles/small_third_320px_/public/2022-11/power_logo_event.png?VersionId=pZIOrAAZH6vCGOJMjhhwP91WJkg0sCus&itok=DrjfYom6"

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
@st.cache_data(ttl=3600)
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

st.sidebar.write("""
### Importância dos Dados Climáticos:
- Os dados climáticos são fundamentais para o planejamento agrícola, monitoramento ambiental e gestão de recursos naturais.
- O acesso a informações sobre temperatura, precipitação, umidade e radiação solar ajuda a entender padrões climáticos e otimizar atividades no campo.

### Objetivo do Aplicativo:
- Este aplicativo oferece uma maneira simples e prática de obter dados climáticos de qualquer local do mundo, utilizando as coordenadas geográficas e o período selecionado pelo usuário.
- O aplicativo permite baixar os dados diretamente em formato Excel, facilitando a análise e integração com outros sistemas.
""")

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
                df_dados = obter_dados_nasa(lat, lon, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
                if df_dados is not None:
                    st.write("Dados obtidos com sucesso!")
                    st.write(df_dados)
                else:
                    st.error("Erro ao obter dados.")
            except ValueError:
                st.error("Por favor, insira coordenadas válidas.")
elif opcao == "Carregar arquivo Excel com múltiplos locais":
    arquivo = st.file_uploader("Faça upload de um arquivo Excel", type=['xlsx'])

    if arquivo is not None:
        with st.spinner('Processando os dados do arquivo...'):
            df_resultados = processar_excel(arquivo, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
            if df_resultados is not None:
                st.write("Dados obtidos com sucesso!")
Here is the **complete Streamlit script** for downloading NASA POWER climate data, addressing all previous issues with caching, data fetching, and ensuring smooth operation:

```python
import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta

# URL da logo do LAMMA para o cabeçalho do app
LOGO_LAMMA_URL_HEADER = "https://lamma.com.br/wp-content/uploads/2024/08/lammapy-removebg-preview.png"

# URL da imagem do NASA POWER para a barra lateral
LOGO_NASA_POWER_URL_SIDEBAR = "https://www.earthdata.nasa.gov/s3fs-public/styles/small_third_320px_/public/2022-11/power_logo_event.png?VersionId=pZIOrAAZH6vCGOJMjhhwP91WJkg0sCus&itok=DrjfYom6"

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
@st.cache_data(ttl=3600)
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

st.sidebar.write("""
### Importância dos Dados Climáticos:
- Os dados climáticos são fundamentais para o planejamento agrícola, monitoramento ambiental e gestão de recursos naturais.
- O acesso a informações sobre temperatura, precipitação, umidade e radiação solar ajuda a entender padrões climáticos e otimizar atividades no campo.

### Objetivo do Aplicativo:
- Este aplicativo oferece uma maneira simples e prática de obter dados climáticos de qualquer local do mundo, utilizando as coordenadas geográficas e o período selecionado pelo usuário.
- O aplicativo permite baixar os dados diretamente em formato Excel, facilitando a análise e integração com outros sistemas.
""")

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
                df_dados = obter_dados_nasa(lat, lon, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
                if df_dados is not None:
                    st.write("Dados obtidos com sucesso!")
                    st.write(df_dados)
                else:
                    st.error("Erro ao obter dados.")
            except ValueError:
                st.error("Por favor, insira coordenadas válidas.")
elif opcao == "Carregar arquivo Excel com múltiplos locais":
    arquivo = st.file_uploader("Faça upload de um arquivo Excel", type=['xlsx'])

    if arquivo is not None:
        with st.spinner('Processando os dados do arquivo...'):
            df_resultados = processar_excel(arquivo, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
            if df_resultados is not None:
                st.write("Dados obtidos com sucesso!")
                st.write(df_resultHere is the **complete and functional script** to download climate data from the NASA POWER API, optimized for use in a Streamlit application:

```python
import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta

# URL da logo do LAMMA para o cabeçalho do app
LOGO_LAMMA_URL_HEADER = "https://lamma.com.br/wp-content/uploads/2024/08/lammapy-removebg-preview.png"

# URL da imagem do NASA POWER para a barra lateral
LOGO_NASA_POWER_URL_SIDEBAR = "https://www.earthdata.nasa.gov/s3fs-public/styles/small_third_320px_/public/2022-11/power_logo_event.png?VersionId=pZIOrAAZH6vCGOJMjhhwP91WJkg0sCus&itok=DrjfYom6"

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
@st.cache_data(ttl=3600)
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

st.sidebar.write("""
### Importância dos Dados Climáticos:
- Os dados climáticos são fundamentais para o planejamento agrícola, monitoramento ambiental e gestão de recursos naturais.
- O acesso a informações sobre temperatura, precipitação, umidade e radiação solar ajuda a entender padrões climáticos e otimizar atividades no campo.

### Objetivo do Aplicativo:
- Este aplicativo oferece uma maneira simples e prática de obter dados climáticos de qualquer local do mundo, utilizando as coordenadas geográficas e o período selecionado pelo usuário.
- O aplicativo permite baixar os dados diretamente em formato Excel, facilitando a análise e integração com outros sistemas.
""")

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
                df_dados = obter_dados_nasa(lat, lon, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
                if df_dados is not None:
                    st.write("Dados obtidos com sucesso!")
                    st.write(df_dados)
                else:
                    st.error("Erro ao obter dados.")
            except ValueError:
                st.error("Por favor, insira coordenadas válidas.")
elif opcao == "Carregar arquivo Excel com múltiplos locais":
    arquivo = st.file_uploader("Faça upload de um arquivo Excel", type=['xlsx'])

    if arquivo is not None:
        with st.spinner('Processando os dados do arquivo...'):
            df_resultados = processar_excel(arquivo, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
            if df_resultados is not None:
                st.write("Dados obtidos com sucesso!")
                st.write(df_resultados)
``Here is the complete Streamlit script for downloading NASA POWER climate data, optimized with caching, data fetching, and error handling:

```python
import pandas as pd
import streamlit as st
import requests
from datetime import datetime, timedelta

# URL da logo do LAMMA para o cabeçalho do app
LOGO_LAMMA_URL_HEADER = "https://lamma.com.br/wp-content/uploads/2024/08/lammapy-removebg-preview.png"

# URL da imagem do NASA POWER para a barra lateral
LOGO_NASA_POWER_URL_SIDEBAR = "https://www.earthdata.nasa.gov/s3fs-public/styles/small_third_320px_/public/2022-11/power_logo_event.png?VersionId=pZIOrAAZH6vCGOJMjhhwP91WJkg0sCus&itok=DrjfYom6"

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
@st.cache_data(ttl=3600)
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

st.sidebar.write("""
### Importância dos Dados Climáticos:
- Os dados climáticos são fundamentais para o planejamento agrícola, monitoramento ambiental e gestão de recursos naturais.
- O acesso a informações sobre temperatura, precipitação, umidade e radiação solar ajuda a entender padrões climáticos e otimizar atividades no campo.

### Objetivo do Aplicativo:
- Este aplicativo oferece uma maneira simples e prática de obter dados climáticos de qualquer local do mundo, utilizando as coordenadas geográficas e o período selecionado pelo usuário.
- O aplicativo permite baixar os dados diretamente em formato Excel, facilitando a análise e integração com outros sistemas.
""")

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
                df_dados = obter_dados_nasa(lat, lon, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
                if df_dados is not None:
                    st.write("Dados obtidos com sucesso!")
                    st.write(df_dados)
                else:
                    st.error("Erro ao obter dados.")
            except ValueError:
                st.error("Por favor, insira coordenadas válidas.")
elif opcao == "Carregar arquivo Excel com múltiplos locais":
    arquivo = st.file_uploader("Faça upload de um arquivo Excel", type=['xlsx'])

    if arquivo is not None:
        with st.spinner('Processando os dados do arquivo...'):
            df_resultados = processar_excel(arquivo, data_inicio.strftime("%Y%m%d"), data_fim.strftime("%Y%m%d"), variaveis_selecionadas)
            if df_resultados is not None:
                st.write("Dados obtidos com sucesso!")
                st.write(df_resultados)


#streamlit run "c:/Users/Igor Vieira/App_Lamma/app_lamma_clima.py"
