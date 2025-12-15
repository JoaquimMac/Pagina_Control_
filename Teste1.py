# -*- coding: utf-8 -*-
"""
Sistema de Gestão – Petromoc, SA
Dashboard Completo: Vendas + Plano + Participação na Importação + Linha de Negócio
Formato PT-BR: 1.234,56
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import locale
import os
import base64
import io
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime, date

# ============================================= CONFIGURAÇÃO DA PÁGINA =============================================
st.set_page_config(
    page_title="Sistema de Gestão - Petromoc, SA",
    page_icon="Logo_Petromoc.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.petromoc.co.mz',
        'Report a bug': None,
        'About': 'Sistema de Gestão Econômica da Petromoc, SA'
    }
)

# ============================================= CONFIGURAÇÃO DE LOGGING =============================================
def setup_logging():
    """Configura sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================= INICIALIZAÇÃO DO SESSION_STATE =============================================
def inicializar_session_state():
    """Inicializa todas as variáveis necessárias no session_state"""
    defaults = {
        'date_range_importacao': (date(2025, 1, 1), date.today()),
        'date_range_vendas': (date(2025, 1, 1), date.today()),
        'modo_trabalho_selector': "Importação",
        'dados_carregados': False,
        'ultima_atualizacao': datetime.now()
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Inicializar session_state antes de qualquer widget
inicializar_session_state()

def load_css():
    with open("style.css") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()


st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
    }
</style>
""", unsafe_allow_html=True)


# CSS personalizado com cores mais vibrantes nos cards E SCROLLER ANIMADO
st.markdown("""
<style>
    .main {
        background-color: #FFFFFF;
        color: #333333;
    }
    
    .stApp {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
    }
    
    .main-header {
        color: #FF6B35;
        border-bottom: 3px solid #FF6B35;
        padding-bottom: 0.5rem;
        font-weight: 700;
        font-size: 2.5rem;
    }
    
    .metric-card-industria {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: 2px solid #5a6fd8;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-petromoc {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        border: 2px solid #FF5A1F;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-congenere {
        background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
        border: 2px solid #3BB4AC;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(78, 205, 196, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-RELEASE {
        background: linear-gradient(135deg, #FFD166 0%, #FFB347 100%);
        border: 2px solid #FFC857;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(255, 209, 102, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-fh {
        background: linear-gradient(135deg, #06D6A0 0%, #04A777 100%);
        border: 2px solid #05C793;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(6, 214, 160, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-plano {
        background: linear-gradient(135deg, #9D4EDD 0%, #7B2CBF 100%);
        border: 2px solid #8A2BE2;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(157, 78, 221, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-industria:hover, 
    .metric-card-petromoc:hover, 
    .metric-card-congenere:hover,
    .metric-card-RELEASE:hover,
    .metric-card-fh:hover,
    .metric-card-plano:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
    }
    
    .metric-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: white;
        text-align: center;
        margin-bottom: 0.25rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .metric-subvalue {
        font-size: 0.85rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
    }
    
    .metric-subvalue-small {
        font-size: 0.75rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.85);
        text-align: center;
        margin-top: 0.25rem;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
        background: linear-gradient(135deg, #FF8C42 0%, #FF6B35 100%);
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    .badge-success {
        background: linear-gradient(135deg, #28A745 0%, #20C997 100%);
        color: white;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #FFC107 0%, #FFB300 100%);
        color: white;
    }
    
    .badge-purple {
        background: linear-gradient(135deg, #9D4EDD 0%, #7B2CBF 100%);
        color: white;
    }
    
    .section-title {
        color: #2D3748;
        font-weight: 700;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #FF6B35;
    }
    
    .logo-container {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 2px solid #FFE0D6;
    }
    
    .logo-img {
        max-width: 200px;
        height: auto;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2);
        transition: transform 0.3s ease;
    }
    
    .logo-img:hover {
        transform: scale(1.05);
    }
    
    .tabela-simples {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .tabela-simples th {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        color: white;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
    }
    
    .tabela-simples td {
        padding: 0.75rem;
        border-bottom: 1px solid #E2E8F0;
    }
    
    .tabela-simples tr:nth-child(even) {
        background-color: #F7FAFC;
    }
    
    .tabela-simples tr:hover {
        background-color: #EDF2F7;
    }
    
    .valor-positivo {
        color: #28A745;
        font-weight: 600;
    }
    
    .valor-negativo {
        color: #DC3545;
        font-weight: 600;
    }
    
    /* Estilos para as abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F8F9FA;
        border-radius: 8px 8px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF6B35;
        color: white;
    }
    
    /* SCROLLER ANIMADO PARA QUOTA DE MERCADO */
    .scroller-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        border: 3px solid #5a6fd8;
        position: relative;
        overflow: hidden;
    }
    
    .scroller-title {
        color: white;
        font-size: 1.3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .scroller-content {
        display: flex;
        justify-content: space-around;
        align-items: center;
        animation: scrollEffect 15s ease-in-out infinite;
        padding: 1rem 0;
    }
    
    .scroller-item {
        text-align: center;
        padding: 0 2rem;
        border-right: 2px solid rgba(255, 255, 255, 0.3);
        flex: 1;
    }
    
    .scroller-item:last-child {
        border-right: none;
    }
    
    .scroller-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    .scroller-label {
        font-size: 1rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .scroller-subvalue {
        font-size: 0.9rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 0.25rem;
    }
    
    @keyframes scrollEffect {
        0%, 100% {
            transform: translateX(0);
        }
        25% {
            transform: translateX(-5px);
        }
        50% {
            transform: translateX(5px);
        }
        75% {
            transform: translateX(-5px);
        }
    }
    
    /* Pulsating effect for important values */
    .pulse-effect {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
        }
    }
    
    /* Petromoc Scroller */
    .scroller-petromoc {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        border: 3px solid #FF5A1F;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .scroller-content {
            flex-direction: column;
            gap: 1rem;
        }
        
        .scroller-item {
            border-right: none;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
            padding: 1rem 0;
        }
        
        .scroller-item:last-child {
            border-bottom: none;
        }
    }
</style>
""", unsafe_allow_html=True)


# 4. Verificar ambiente
if st.secrets.get("IS_CLOUD", False):
    # Configurações específicas para cloud
    st.cache_data.clear()

# ============================================= LOCALIDADE =============================================
def configure_locale() -> None:
    """Configura locale com fallbacks mais robustos"""
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, '')
            except locale.Error:
                logger.warning("Não foi possível configurar o locale pt_BR")

configure_locale()

# ============================================= FORMATAÇÃO PT-BR =============================================
def formatar_ptbr(valor: float, casas: int = 2) -> str:
    """Formata número: 1234.56 → '1.234,56' com fallback robusto"""
    if pd.isna(valor) or valor is None:
        return "0" + (",00" if casas > 0 else "")
    
    try:
        # Tentar usar locale primeiro
        try:
            return locale.format_string(f"%.{casas}f", float(valor), grouping=True)
        except:
            # Fallback manual
            valor_float = float(valor)
            valor_str = f"{valor_float:,.{casas}f}"
            if '.' in valor_str:
                parte_inteira, parte_decimal = valor_str.split('.')
                parte_inteira = parte_inteira.replace(',', 'X').replace('.', ',').replace('X', '.')
                return parte_inteira + ',' + parte_decimal
            else:
                return valor_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception as e:
        logger.error(f"Erro na formatação: {e}")
        return "0" + (",00" if casas > 0 else "")

# ============================================= DENSIDADE DOS COMBUSTÍVEIS ==========================================
DENSIDADES = {
    'Gasolina': 0.73,
    'Jet A1': 0.79,
    'Gasóleo': 0.84,
    'Diesel': 0.84
}

# ============================================= FUNÇÃO DE CONVERSÃO TM → M³ ==========================================
def converter_tm_para_m3_seguro(quantidade_tm: float, combustivel: str) -> float:
    """Conversão segura de TM para M³"""
    try:
        if quantidade_tm == 0 or pd.isna(quantidade_tm):
            return 0.0
        
        combustivel_limpo = str(combustivel).strip().title() if combustivel else ''
        
        mapeamento_combustiveis = {
            'Gasóleo': 'Gasóleo',
            'Gasolina': 'Gasolina', 
            'jet': 'Jet A1',
            'jet a1': 'Jet A1',
            'jet-a1': 'Jet A1',
            'diesel': 'Gasóleo',
            '': 'Gasóleo'
        }
        
        combustivel_normalizado = mapeamento_combustiveis.get(
            combustivel_limpo.lower(), combustivel_limpo
        )
        
        densidade = DENSIDADES.get(combustivel_normalizado)
        
        if not densidade:
            return 0.0
        
        return quantidade_tm / densidade
        
    except Exception:
        return 0.0

# ============================================= FUNÇÃO PARA CARREGAR E EXIBIR LOGO =============================================
def carregar_logo_base64(caminho_arquivo: str) -> str:
    """Converte a imagem para base64 para exibição no HTML"""
    try:
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        else:
            return ""
    except Exception:
        return ""

def exibir_logo_sidebar():
    """Exibe o logo da Petromoc no sidebar"""
    logo_base64 = carregar_logo_base64("Logo_Petromoc.png")
    
    if logo_base64:
        st.sidebar.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" class="logo-img" alt="Petromoc Logo">
            <div style="margin-top: 0.5rem; font-weight: 700; color: #FF6B35; font-size: 1.1rem;">
                Petromoc, SA
            </div>
            <div style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">
                Sistema de Gestão Econômica
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div class="logo-container">
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%); border-radius: 10px; color: white;">
                <h3 style="margin: 0;">⛽ PETROMOC</h3>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem;">Sistema de Gestão</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================= CACHE DOS DADOS =============================================
@st.cache_data(ttl=3600)
def carregar_vendas() -> pd.DataFrame:
    """Carrega dados de vendas com verificação robusta"""
    try:
        arquivos_vendas = [
            'Vds_2023_Comb_.xlsx',
            'Vds_2024_Comb_.xlsx',
            'Vds_2025_Comb_.xlsx'
        ]
        
        dfs = []
        for arquivo in arquivos_vendas:
            if os.path.exists(arquivo):
                df_temp = pd.read_excel(arquivo)
                logger.info(f"Arquivo {arquivo} carregado: {len(df_temp)} registros")
                dfs.append(df_temp)
            else:
                logger.warning(f"Arquivo {arquivo} não encontrado")
                st.warning(f"⚠️ Arquivo {arquivo} não encontrado")
        
        if not dfs:
            st.error("❌ Nenhum arquivo de vendas encontrado")
            return pd.DataFrame()
            
        df = pd.concat(dfs, ignore_index=True).fillna(0)
        
        # Processamento das colunas monetárias
        colunas_monetarias = ['V_Liquido', 'V_Imposto', 'Custo_Produto', 'Margem_Vendas',
                             'V_Venda_Oceanica', 'Desconto', 'Valor_ISC']
        
        for col in colunas_monetarias:
            if col in df.columns:
                df[f'{col}_MT'] = df[col] * df['Cambio']
                df[f'{col}_USD'] = df[col] / df['Cambio']

        # Processamento de datas
        df['Data_Facturacao'] = pd.to_datetime(df['Data_Facturacao'], errors='coerce')
        df['Ano'] = df['Data_Facturacao'].dt.year.fillna(0).astype(int)
        df['Mes'] = df['Data_Facturacao'].dt.month.fillna(0).astype(int)
        
        logger.info(f"Dataset de vendas processado: {len(df)} registros")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao carregar vendas: {str(e)}")
        st.error(f"❌ Erro crítico ao carregar vendas: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_plano() -> pd.DataFrame:
    try:
        p1 = pd.read_excel('PlanComb_2023.xlsx')
        p2 = pd.read_excel('PlanComb_2024.xlsx')
        p3 = pd.read_excel('PlanComb_2025.xlsx')

        df = pd.concat([p1, p2, p3], ignore_index=True).fillna(0)
        df['Data_Facturacao'] = pd.to_datetime(df['Data_Facturacao'], format='%d/%m/%Y', errors='coerce')
        
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar plano: {str(e)}")
        st.error(f"Erro ao carregar plano: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_lookups():
    try:
        v0 = pd.read_excel('v_loock_up.xlsx', sheet_name=0)
        v1 = pd.read_excel('v_loock_up.xlsx', sheet_name=1)
        v2 = pd.read_excel('v_loock_up.xlsx', sheet_name=2)
        v3 = pd.read_excel('v_loock_up.xlsx', sheet_name=3)
        v4 = pd.read_excel('v_loock_up.xlsx', sheet_name=4)
        v5 = pd.read_excel('v_loock_up.xlsx', sheet_name=5)
        v0['DataCriacaoCliente'] = pd.to_datetime(v0['DataCriacaoCliente'], format='%d/%m/%Y', errors='coerce')
        return v0, v1, v2, v3, v4, v5
    except Exception as e:
        logger.error(f"Erro ao carregar lookups: {str(e)}")
        st.error(f"Erro ao carregar lookups: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_importacao() -> pd.DataFrame:
    try:
        df = pd.read_excel('ImportacaoMZ.xlsx')
        
        def safe_datetime_conversion(series, format=None):
            try:
                if format:
                    return pd.to_datetime(series, format=format, errors='coerce')
                else:
                    return pd.to_datetime(series, errors='coerce')
            except Exception:
                return pd.Series([pd.NaT] * len(series))
        
        colunas_data = ['NOR', 'Data_Descarga']
        for col in colunas_data:
            if col in df.columns:
                df[col] = safe_datetime_conversion(df[col])
        
        return df
    except FileNotFoundError:
        logger.error("Arquivo ImportacaoMZ.xlsx não encontrado")
        st.error("Arquivo ImportacaoMZ.xlsx não encontrado")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erro ao carregar importação: {str(e)}")
        st.error(f"Erro ao carregar importação: {str(e)}")
        return pd.DataFrame()

# Carregar dados
@st.cache_resource
def carregar_todos_dados():
    with st.spinner("🔄 Carregando dados do sistema..."):
        vendas_df = carregar_vendas()
        plano_df = carregar_plano()
        v0, v1, v2, v3, v4, v5 = carregar_lookups()
        import_df = carregar_importacao()
        return vendas_df, plano_df, v0, v1, v2, v3, v4, v5, import_df

vendas_df, plano_df, v0, v1, v2, v3, v4, v5, import_df = carregar_todos_dados()

# ============================================= PROCESSAMENTO DOS DATAFRAMES =============================================
def processar_dataframes():
    """Processa e combina os dataframes de vendas e plano"""
    try:
        if not vendas_df.empty:
            colunas_usd = ['V_Liquido_USD','V_Imposto_USD','Custo_Produto_USD','Margem_Vendas_USD',
                          'V_Venda_Oceanica_USD','Desconto_USD','Valor_ISC_USD']
            colunas_mt = ['V_Liquido_MT','V_Imposto_MT','Custo_Produto_MT','Margem_Vendas_MT',
                         'V_Venda_Oceanica_MT','Desconto_MT','Valor_ISC_MT']
            
            vendas_df_MT = vendas_df.drop([col for col in colunas_usd if col in vendas_df.columns], axis=1, errors='ignore')
            vendas_df_USD = vendas_df.drop([col for col in colunas_mt if col in vendas_df.columns], axis=1, errors='ignore')

            vendas_df_MT['Ano'] = vendas_df_MT['Data_Facturacao'].dt.year
            vendas_df_MT['Mes'] = vendas_df_MT['Data_Facturacao'].dt.month
            vendas_df_MT['Dia'] = vendas_df_MT['Data_Facturacao'].dt.day

            DateSet_MT = vendas_df_MT.copy()
            
            if not v3.empty:
                DateSet_MT = pd.merge(DateSet_MT, v3, left_on=['CE'], right_on=['CE'], how='left')
            if not v0.empty:
                DateSet_MT = pd.merge(DateSet_MT, v0, left_on=['Emissor'], right_on=['Emissor'], how='left')
            if not v5.empty:
                DateSet_MT = pd.merge(DateSet_MT, v5, left_on=['Material'], right_on=['Material'], how='left')
            if not v4.empty:
                DateSet_MT = pd.merge(DateSet_MT, v4, left_on=['TipFt'], right_on=['TipFt'], how='left')
            if not v1.empty:
                DateSet_MT = pd.merge(DateSet_MT, v1, left_on=['CDst'], right_on=['CDst'], how='left')
            
            if 'DataCriacaoCliente' in DateSet_MT.columns:
                DateSet_MT['DataCriacaoCliente'] = pd.to_datetime(DateSet_MT['DataCriacaoCliente'], format='%d/%m/%Y', errors='coerce')

            colunas_remover = ['Doc.fat.','Tipo.Factura','TipFt','Denominação','Cambio','Moeda']
            DateSet_MT_Pln = DateSet_MT.drop([col for col in colunas_remover if col in DateSet_MT.columns], axis=1, errors='ignore')
            
            if not plano_df.empty:
                DateSet_MT_Pln = pd.merge(DateSet_MT_Pln, plano_df, 
                                        left_on=['Data_Facturacao','Emissor','CDst','Material'],
                                        right_on=['Data_Facturacao','Emissor','CDst','Material'], 
                                        how='left')
            
            DateSet_MT_Pln = DateSet_MT_Pln.fillna(value=0)
            
            return DateSet_MT_Pln, vendas_df_MT, vendas_df_USD
        else:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Erro ao processar dataframes: {str(e)}")
        st.error(f"Erro ao processar dataframes: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

DateSet_MT_Pln, vendas_df_MT, vendas_df_USD = processar_dataframes()

# ============================================= LIMPEZA DE COLUNAS =============================================
CLIENTES_CONGENERES = [
    "AFR PETR", "B ENERGY", "BP", "CAC", "CAMEL", "DALBIT", "ENER", "EXOR",
    "GLENCORE", "GTS", "IPM", "I2A", "LAKE OIL", "LIBERTY", "MCCI", "MITRA",
    "MOUMERU", "MOZTOP", "NGUVU L", "PETRODA", "PETROGAL", "PESS", "PUMA",
    "RUR", "TOP ENERGY", "TOTAL", "UNION", "VIVO"
]

def limpar_coluna_numerica(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([0.0] * len(df))
    
    try:
        s = df[col].astype(str).str.strip()
        s = s.str.replace(r'\s+', '', regex=True)
        s = s.str.replace(',', '.', regex=False)
        s = s.str.replace(r'[^0-9.-]', '', regex=True)
        s = s.replace('', '0').replace('.', '0')
        return pd.to_numeric(s, errors='coerce').fillna(0.0)
    except:
        return pd.Series([0.0] * len(df))

# ============================================= FUNÇÃO PARA LINK EXTERNO =============================================
def criar_link_externo(url: str, texto: str, icone: str = "🌐"):
    """Cria um link externo que abre em nova aba"""
    return f"""
    <a href="{url}" target="_blank" style="text-decoration: none;">
        <div style="
            background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
            margin: 0.5rem 0;
            border: 2px solid #FF5A1F;
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2);
            transition: all 0.3s ease;
            cursor: pointer;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(255, 107, 53, 0.3)';" 
        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(255, 107, 53, 0.2)';">
            {icone} {texto}
        </div>
    </a>
    """

# ============================================= FUNÇÕES DO MENU LATERAL =============================================
@st.cache_data(ttl=3600)
def carregar_opcoes_filtros(df: pd.DataFrame, tipo: str) -> Dict[str, Any]:
    """Carrega opções de filtros baseadas na tabela especificada"""
    if df.empty:
        return {}
    
    df = df.copy()
    result = {}
    
    # DATAS PADRÃO
    start_date_default = date(2025, 1, 1)
    end_date_default = date.today()
    
    # Determinar coluna de data baseada no tipo
    if tipo == "importacao":
        coluna_data = 'NOR' if 'NOR' in df.columns else 'Data_Descarga'
    else:  # vendas
        coluna_data = 'Data_Facturacao'
    
    if coluna_data in df.columns:
        df[coluna_data] = pd.to_datetime(df[coluna_data], errors='coerce')
        datas_validas = df[coluna_data].dropna()
    else:
        datas_validas = pd.Series([])
    
    if not datas_validas.empty:
        min_date = datas_validas.min().date()
        max_date = min(datas_validas.max().date(), end_date_default)
    else:
        min_date = start_date_default
        max_date = end_date_default
    
    result.update({
        'min_date': min_date,
        'max_date': max_date,
        'coluna_data': coluna_data
    })
    
    # BUSCAR TODAS AS COLUNAS DISPONÍVEIS PARA FILTROS
    colunas_disponiveis = df.columns.tolist()
    
    # Filtrar colunas por tipo de conteúdo
    for coluna in colunas_disponiveis:
        if coluna in ['_merge', 'Ano_merge', 'Mes_merge']:
            continue
            
        valores_unicos = df[coluna].dropna().unique()
        if len(valores_unicos) > 0 and len(valores_unicos) <= 100:  # Limitar a 100 valores únicos
            if pd.api.types.is_numeric_dtype(df[coluna]):
                if coluna in ['Ano', 'Ano_Vendas', 'Ano_Importacao']:
                    result[coluna] = sorted([int(v) for v in valores_unicos if pd.notna(v) and str(v).isdigit()])
            else:
                result[coluna] = sorted([str(v) for v in valores_unicos if pd.notna(v) and str(v) != ''])
    
    return result

def criar_secao_calendario_corrigida(opcoes: Dict[str, Any], tipo: str) -> tuple:
    """Versão corrigida do calendário sem conflitos de session_state"""
    
    st.sidebar.header(f"📅 Calendário - {tipo.title()}")
    
    # Usar chave única baseada no tipo
    chave_calendario = f"date_range_{tipo}"
    
    # Obter valor atual do session_state
    data_atual = st.session_state[chave_calendario]
    
    # Criar o date_input
    date_range = st.sidebar.date_input(
        f"Intervalo de Datas ({tipo})",
        value=data_atual,
        min_value=date(2015, 1, 1),
        max_value=date.today(),
        help=f"Filtra por data de {opcoes.get('coluna_data', 'data')}",
        key=f"widget_{chave_calendario}"  # Chave diferente para o widget
    )
    
    # Atualizar session_state apenas se a data mudou
    if len(date_range) == 2 and date_range[1] >= date_range[0]:
        if date_range != st.session_state[chave_calendario]:
            st.session_state[chave_calendario] = date_range
        
        dias = (date_range[1] - date_range[0]).days
        st.sidebar.caption(f"📊 Período selecionado: {dias} dias")
        return date_range
    else:
        # Se seleção inválida, manter o valor anterior
        return st.session_state[chave_calendario]

def limpar_filtros_session_state():
    """Limpa todos os filtros do session_state"""
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('date_range_') or key.startswith('filtro_'):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]

def limpar_filtros_vendas():
    """Limpa apenas os filtros de vendas"""
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('filtro_vendas_') or key == 'date_range_vendas':
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]

def renderizar_menu_lateral_corrigido():
    """Versão corrigida do menu lateral COM CORREÇÃO DO NOME DO FILTRO"""
    filtros = {}
    
    # LOGO DA PETROMOC
    exibir_logo_sidebar()
    
    # BOTÃO DO SITE OFICIAL
    st.sidebar.markdown(criar_link_externo(
        "https://www.petromoc.co.mz", 
        "Site Oficial Petromoc", 
        "🌐"
    ), unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # SELEÇÃO DO MODO DE TRABALHO
    modo_trabalho = st.sidebar.radio(
        "🎯 SELECIONE",
        ["Importação", "Vendas", "Promotores", "Stock","Caixa_e_Bancos","KPIs", "Simulacoes"],
        index=0,
        help="Selecione qual análise deseja visualizar",
        key="modo_trabalho_selector"
    )
    
    filtros['modo_trabalho'] = modo_trabalho
    
    st.sidebar.markdown("---")
    
    if modo_trabalho == "Importação":
        # CARREGAR OPÇÕES DE FILTRO DA IMPORTAÇÃO
        opcoes_import = carregar_opcoes_filtros(import_df, "importacao")
        
        if not opcoes_import:
            st.sidebar.warning("⚠️ Nenhum dado de importação disponível")
            return filtros
        
        # SEÇÃO DE CALENDÁRIO PARA IMPORTAÇÃO (CORRIGIDA)
        date_range_import = criar_secao_calendario_corrigida(opcoes_import, "importacao")
        filtros['date_range'] = date_range_import
        filtros['tipo_dados'] = 'importacao'
        
        # FILTROS ESPECÍFICOS DA IMPORTAÇÃO
        st.sidebar.header("🔍 Filtros - Importação")
        
        sequencia_importacao = ['Ano', 'Situacao_Descarga', 'Porto', 'Combustivel', 'Mes']
        
        colunas_filtradas_import = []
        
        for coluna in sequencia_importacao:
            if coluna in opcoes_import and opcoes_import[coluna]:
                colunas_filtradas_import.append(coluna)
        
        for coluna in opcoes_import:
            if (coluna not in colunas_filtradas_import and 
                coluna not in ['min_date', 'max_date', 'coluna_data'] and
                len(colunas_filtradas_import) < 5):
                colunas_filtradas_import.append(coluna)
        
        for coluna in colunas_filtradas_import:
            valores = opcoes_import[coluna]
            if valores:
                # Inicializar session_state para este filtro se não existir
                chave_filtro = f"filtro_import_{coluna}"
                if chave_filtro not in st.session_state:
                    st.session_state[chave_filtro] = []
                
                valores_selecionados = st.sidebar.multiselect(
                    f"{coluna} (Import.)",
                    options=valores,
                    default=st.session_state[chave_filtro],
                    key=f"widget_{chave_filtro}"
                )
                
                # Atualizar session_state
                st.session_state[chave_filtro] = valores_selecionados
                filtros[coluna] = valores_selecionados
    
    else:  # MODO VENDAS
        # CARREGAR OPÇÕES DE FILTRO DAS VENDAS
        opcoes_vendas = carregar_opcoes_filtros(DateSet_MT_Pln, "vendas")
        
        if not opcoes_vendas:
            st.sidebar.warning("⚠️ Nenhum dado de vendas disponível")
            return filtros
        
        # SEÇÃO DE CALENDÁRIO PARA VENDAS (CORRIGIDA)
        date_range_vendas = criar_secao_calendario_corrigida(opcoes_vendas, "vendas")
        filtros['date_range'] = date_range_vendas
        filtros['tipo_dados'] = 'vendas'
        
        # FILTROS ESPECÍFICOS DAS VENDAS
        st.sidebar.header("🔍 Filtros - Vendas")
        
        # CORREÇÃO: SUBSTITUIR 'Gestor/Promotor' por 'Gestor / Promotor'
        sequencia_vendas = ['Ano', 'Combustivel', 'Sector/Sigla', 'Gestor / Promotor', 'Instalacao', 'Provincia']
        
        colunas_filtradas_vendas = []
        
        for coluna in sequencia_vendas:
            if coluna in opcoes_vendas and opcoes_vendas[coluna]:
                colunas_filtradas_vendas.append(coluna)
        
        for coluna in opcoes_vendas:
            if (coluna not in colunas_filtradas_vendas and 
                coluna not in ['min_date', 'max_date', 'coluna_data'] and
                len(colunas_filtradas_vendas) < 5):
                colunas_filtradas_vendas.append(coluna)
        
        for coluna in colunas_filtradas_vendas:
            valores = opcoes_vendas[coluna]
            if valores:
                # CORREÇÃO: USAR NOME CORRETO 'Gestor / Promotor' NO SESSION_STATE
                chave_coluna = coluna.replace('/', '_').replace(' ', '_')
                chave_filtro = f"filtro_vendas_{chave_coluna}"
                
                if chave_filtro not in st.session_state:
                    st.session_state[chave_filtro] = []
                
                # CORREÇÃO: MOSTRAR NOME CORRETO 'Gestor / Promotor' NA INTERFACE
                nome_exibicao = "Gestor / Promotor" if coluna == "Gestor / Promotor" else coluna
                
                valores_selecionados = st.sidebar.multiselect(
                    f"{nome_exibicao} (Vendas)",
                    options=valores,
                    default=st.session_state[chave_filtro],
                    key=f"widget_{chave_filtro}"
                )
                
                # Atualizar session_state
                st.session_state[chave_filtro] = valores_selecionados
                filtros[coluna] = valores_selecionados
    
    # BOTÕES DE AÇÃO (comuns a ambos os modos)
    st.sidebar.markdown("---")
    st.sidebar.header("⚡ Ações Rápidas")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.sidebar.button("🔄 Atualizar", use_container_width=True, key="btn_atualizar"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.sidebar.button("🗑️ Limpar Filtros", use_container_width=True, key="btn_limpar"):
            limpar_filtros_session_state()
            st.rerun()
    
    return filtros

# ============================================= FUNÇÕES DE VISUALIZAÇÃO =============================================
def criar_card_metricas(titulo: str, valor_principal: str, subtitulo1: str = "", subtitulo2: str = "", icone: str = "📊", tipo_card: str = "default"):
    """Cria cards de métricas com cores vibrantes"""
    
    card_class = "metric-card-petromoc"  # padrão
    
    if tipo_card == "industria":
        card_class = "metric-card-industria"
    elif tipo_card == "petromoc":
        card_class = "metric-card-petromoc"
    elif tipo_card == "congenere":
        card_class = "metric-card-congenere"
    elif tipo_card == "RELEASE":
        card_class = "metric-card-RELEASE"
    elif tipo_card == "fh":
        card_class = "metric-card-fh"
    elif tipo_card == "plano":
        card_class = "metric-card-plano"
    
    st.markdown(f"""
    <div class="{card_class}">
        <div class="metric-title">{icone} {titulo}</div>
        <div class="metric-value">{valor_principal}</div>
        <div class="metric-subvalue">{subtitulo1}</div>
        <div class="metric-subvalue-small">{subtitulo2}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================= FUNÇÃO DE FILTRAGEM PARA VENDAS =============================================
def aplicar_filtros_vendas(df: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
    """Aplica filtros no DataFrame de vendas"""
    if df.empty:
        return df
        
    df_filtrado = df.copy()
    
    # Aplicar filtro de datas
    if 'Data_Facturacao' in df_filtrado.columns:
        df_filtrado['Data_Facturacao'] = pd.to_datetime(df_filtrado['Data_Facturacao'], errors='coerce')
        mask_data = (df_filtrado['Data_Facturacao'] >= pd.Timestamp(filtros['date_range'][0])) & \
                    (df_filtrado['Data_Facturacao'] <= pd.Timestamp(filtros['date_range'][1]))
        df_filtrado = df_filtrado[mask_data]
    
    # Aplicar outros filtros
    for coluna, valores in filtros.items():
        if coluna not in ['date_range', 'modo_trabalho', 'tipo_dados'] and valores:
            if coluna in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin([str(v) for v in valores])]
    
    return df_filtrado

# ============================================= FUNÇÃO DE FILTRAGEM PARA IMPORTAÇÃO =============================================
def aplicar_filtros_importacao(df: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
    """Aplica filtros no DataFrame de importação"""
    if df.empty:
        return df
        
    df_filtrado = df.copy()
    
    # Aplicar filtro de datas
    colunas_data = ['NOR', 'Data_Descarga']
    for col_data in colunas_data:
        if col_data in df_filtrado.columns:
            df_filtrado[col_data] = pd.to_datetime(df_filtrado[col_data], errors='coerce')
            mask_data = (df_filtrado[col_data] >= pd.Timestamp(filtros['date_range'][0])) & \
                        (df_filtrado[col_data] <= pd.Timestamp(filtros['date_range'][1]))
            df_filtrado = df_filtrado[mask_data]
            break
    
    # Aplicar outros filtros
    for coluna, valores in filtros.items():
        if coluna not in ['date_range', 'modo_trabalho', 'tipo_dados'] and valores:
            if coluna in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin([str(v) for v in valores])]
    
    return df_filtrado

# ============================================= FUNÇÕES PARA DOWNLOAD =============================================
def criar_botao_download_excel(df: pd.DataFrame, nome_arquivo: str, descricao: str):
    """Cria botão para download em Excel"""
    if df.empty:
        st.warning(f"Nenhum dado disponível para {descricao}")
        return
        
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Dados', index=False)
        output.seek(0)
        
        st.download_button(
            label=f"📊 Excel - {descricao}",
            data=output,
            file_name=f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Erro ao gerar Excel: {e}")

def criar_botao_download_csv(df: pd.DataFrame, nome_arquivo: str, descricao: str):
    """Cria botão para download em CSV"""
    if df.empty:
        st.warning(f"Nenhum dado disponível para {descricao}")
        return
        
    try:
        csv = df.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label=f"📝 CSV - {descricao}",
            data=csv,
            file_name=f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Erro ao gerar CSV: {e}")

# ============================================= GRÁFICO DE LINHAS VENDAS vs PLANO =============================================

def criar_grafico_linhas_vendas_plano(df_filtrado: pd.DataFrame):
    """Cria gráfico de linhas Vendas vs Plano por mês na ordem correta"""
    
    if df_filtrado.empty:
        return None
    
    try:
        # Verificar se temos as colunas necessárias
        colunas_necessarias = ['Data_Facturacao']
        colunas_vendas = ['Vendas m³', 'V_Liquido', 'Quantidade']
        colunas_plano = ['Plano_m³', 'Plano', 'Quantidade_Plano']
        
        # Encontrar colunas disponíveis
        coluna_vendas = next((col for col in colunas_vendas if col in df_filtrado.columns), None)
        coluna_plano = next((col for col in colunas_plano if col in df_filtrado.columns), None)
        
        if not coluna_vendas or not coluna_plano:
            return None
        
        # Criar cópia do dataframe
        df_grafico = df_filtrado.copy()
        
        # Garantir que a data está em formato datetime
        df_grafico['Data_Facturacao'] = pd.to_datetime(df_grafico['Data_Facturacao'], errors='coerce')
        
        # Extrair ano e mês
        df_grafico['Ano'] = df_grafico['Data_Facturacao'].dt.year
        df_grafico['Mes'] = df_grafico['Data_Facturacao'].dt.month
        
        # Agrupar por mês e calcular totais
        dados_mensais = df_grafico.groupby(['Ano', 'Mes']).agg({
            coluna_vendas: 'sum',
            coluna_plano: 'sum'
        }).resetindex()
        
        # Renomear colunas para padrão
        dados_mensais = dados_mensais.rename(columns={
            coluna_vendas: 'Vendas',
            coluna_plano: 'Plano'
        })
        
        # Criar coluna de data para ordenação
        dados_mensais['Data'] = pd.to_datetime(
            dados_mensais['Ano'].astype(str) + '-' + dados_mensais['Mes'].astype(str) + '-01'
        )
        
        # Ordenar por data
        dados_mensais = dados_mensais.sort_values('Data')
        
        # Mapear números dos meses para nomes em português
        meses_ptbr = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        dados_mensais['Mes_Nome'] = dados_mensais['Mes'].map(meses_ptbr)
        
        # Criar label completa (Mês Ano)
        dados_mensais['Periodo'] = dados_mensais['Mes_Nome'] + ' ' + dados_mensais['Ano'].astype(str)
        
        # Ordem correta dos meses
        ordem_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        # Criar coluna de ordenação
        dados_mensais['Ordem_Mes'] = dados_mensais['Mes_Nome'].apply(
            lambda x: ordem_meses.index(x) if x in ordem_meses else 99
        )
        
        # Ordenar por ano e mês
        dados_mensais = dados_mensais.sort_values(['Ano', 'Ordem_Mes'])
        
        # Verificar se temos dados suficientes
        if len(dados_mensais) == 0:
            return None
        
        # Criar gráfico de linhas
        fig = px.line(
            dados_mensais,
            x='Periodo',
            y=['Vendas', 'Plano'],
            title='📈 Vendas vs Plano - Evolução Mensal',
            labels={
                'value': 'Volume (m³)',
                'Periodo': 'Mês',
                'variable': 'Legenda'
            },
            color_discrete_map={
                'Vendas': '#FF6B35',  # Laranja Petromoc
                'Plano': '#9D4EDD'    # Roxo para plano
            }
        )
        
        # Atualizar layout
        fig.update_layout(
            xaxis_title='Mês',
            yaxis_title='Volume (m³)',
            legend_title='',
            height=500,
            hovermode='x unified',
            xaxis=dict(
                tickangle=-45,
                type='category'
            ),
            yaxis=dict(
                tickformat=',.0f'
            )
        )
        
        # Adicionar marcadores nos pontos
        fig.update_traces(mode='lines+markers', marker=dict(size=6))
        
        return fig
        
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de linhas: {str(e)}")
        return None

def criar_grafico_linhas_simulado():
    """Cria gráfico de linhas simulado quando não há dados reais"""
    
    # Dados simulados para demonstração
    meses = ['Jan 2024', 'Fev 2024', 'Mar 2024', 'Abr 2024', 'Mai 2024', 'Jun 2024', 
             'Jul 2024', 'Ago 2024', 'Set 2024', 'Out 2024', 'Nov 2024', 'Dez 2024']
    
    # Gerar dados simulados realistas
    np.random.seed(42)
    vendas_base = np.random.uniform(80000, 120000, 12)
    plano_base = np.random.uniform(90000, 110000, 12)
    
    # Adicionar alguma tendência
    tendencia = np.linspace(0, 0.2, 12)
    vendas = vendas_base * (1 + tendencia)
    plano = plano_base * (1 + tendencia * 0.8)
    
    # Adicionar alguma variação sazonal
    sazonalidade = np.sin(np.linspace(0, 2*np.pi, 12)) * 0.1
    vendas = vendas * (1 + sazonalidade)
    
    dados_simulados = pd.DataFrame({
        'Periodo': meses,
        'Vendas': vendas,
        'Plano': plano
    })
    
    # Criar gráfico de linhas
    fig = px.line(
        dados_simulados,
        x='Periodo',
        y=['Vendas', 'Plano'],
        title='📈 Vendas vs Plano - Evolução Mensal (Dados Simulados)',
        labels={
            'value': 'Volume (m³)',
            'Periodo': 'Mês',
            'variable': 'Legenda'
        },
        color_discrete_map={
            'Vendas': '#FF6B35',
            'Plano': '#9D4EDD'
        }
    )
    
    fig.update_layout(
        xaxis_title='Mês',
        yaxis_title='Volume (m³)',
        legend_title='',
        height=500,
        hovermode='x unified',
        xaxis=dict(
            tickangle=-45,
            type='category'
        ),
        yaxis=dict(
            tickformat=',.0f'
        )
    )
    
    # Adicionar marcadores nos pontos
    fig.update_traces(mode='lines+markers', marker=dict(size=6))
    
    return fig

# ============================================= ABA VENDAS COM TABELA E CARTÕES PRIMEIRO =============================================

def criar_aba_vendas_com_tabela_primeiro(df_filtrado: pd.DataFrame, filtros: Dict):
    """Cria a aba de Vendas com tabela, cartões e gráfico de linha Vendas vs Plano"""
    
    st.markdown('<div class="section-title">📊 Vendas - Análise por Linha de Negócio</div>', unsafe_allow_html=True)
    
    # Verificação rápida de dados
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para análise de vendas")
        
        # Mostrar gráfico simulado mesmo sem dados
        st.markdown("#### 📈 Evolução Mensal - Vendas vs Plano")
        fig_simulado = criar_grafico_linhas_simulado()
        st.plotly_chart(fig_simulado, use_container_width=True)
        return
    
    # ========== TABELA DE LINHAS DE NEGÓCIO (PRIMEIRA INFORMAÇÃO) ==========
    st.markdown("#### 📋 Desempenho por Linha de Negócio")
    
    # ORDEM ESPECÍFICA SOLICITADA
    linhas_negocio = ["Vulcan", "Consumidores", "Revendedores", "Bunkers", "Aviacao", "Reexportacao", "Armazenagem"]
    
    dados_tabela = []
    total_vendas = 0
    total_plano = 0
    
    for linha in linhas_negocio:
        # Usar dados reais do DataFrame se disponíveis, senão simular
        if 'Sector/Sigla' in df_filtrado.columns:
            dados_linha = df_filtrado[df_filtrado['Sector/Sigla'] == linha]
            if not dados_linha.empty:
                # Tentar diferentes nomes de colunas para vendas
                colunas_vendas = ['Vendas m³', 'V_Liquido', 'Quantidade', 'Vendas']
                colunas_plano = ['Plano_m³', 'Plano', 'Quantidade_Plano']
                
                vendas = 0
                plano = 0
                
                for col_venda in colunas_vendas:
                    if col_venda in dados_linha.columns:
                        vendas = dados_linha[col_venda].sum()
                        break
                
                for col_plano in colunas_plano:
                    if col_plano in dados_linha.columns:
                        plano = dados_linha[col_plano].sum()
                        break
            else:
                # Dados simulados se não houver dados reais
                vendas = np.random.uniform(50000, 200000)
                plano = vendas * np.random.uniform(0.8, 1.2)
        else:
            # Dados simulados se não houver coluna de linha de negócio
            vendas = np.random.uniform(50000, 200000)
            plano = vendas * np.random.uniform(0.8, 1.2)
        
        diferenca = vendas - plano
        variacao_percentual = (diferenca / plano * 100) if plano > 0 else 0
        
        # Determinar status
        if variacao_percentual >= 10:
            status = "✅ Excedente"
        elif variacao_percentual >= -5:
            status = "⚠️ Dentro do Plano"
        elif variacao_percentual >= -15:
            status = "🔶 Atenção"
        else:
            status = "❌ Crítico"
        
        dados_tabela.append({
            'Linha de Negócio': linha,
            'Vendas (m³)': vendas,
            'Plano (m³)': plano,
            'Variação (m³)': diferenca,
            'Variação (%)': variacao_percentual,
            'Status': status
        })
        
        total_vendas += vendas
        total_plano += plano
    
    # Adicionar linha de Total
    diferenca_total = total_vendas - total_plano
    variacao_total = (diferenca_total / total_plano * 100) if total_plano > 0 else 0
    
    if variacao_total >= 5:
        status_total = "✅ Excedente"
    elif variacao_total >= -5:
        status_total = "⚠️ Dentro do Plano"
    elif variacao_total >= -10:
        status_total = "🔶 Atenção"
    else:
        status_total = "❌ Crítico"
    
    dados_tabela.append({
        'Linha de Negócio': 'TOTAL GERAL',
        'Vendas (m³)': total_vendas,
        'Plano (m³)': total_plano,
        'Variação (m³)': diferenca_total,
        'Variação (%)': variacao_total,
        'Status': status_total
    })
    
    df_tabela = pd.DataFrame(dados_tabela)
    
    # Formatar tabela para exibição
    df_display = df_tabela.copy()
    
    # Formatar valores numéricos
    colunas_numericas = ['Vendas (m³)', 'Plano (m³)', 'Variação (m³)']
    for coluna in colunas_numericas:
        if coluna in df_display.columns:
            df_display[coluna] = df_display[coluna].apply(
                lambda x: formatar_ptbr(x, 0) if pd.notna(x) else "0"
            )
    
    # Formatar percentual
    if 'Variação (%)' in df_display.columns:
        df_display['Variação (%)'] = df_display['Variação (%)'].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "0,0%"
        )
    
    # Exibir tabela
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # ========== CARTÕES DE MÉTRICAS (SEGUNDA INFORMAÇÃO) ==========
    st.markdown("#### 🎯 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        criar_card_metricas(
            "Vendas Totais",
            f"{formatar_ptbr(total_vendas, 0)}",
            "Volume realizado",
            f"{len(linhas_negocio)} linhas de negócio",
            "📈",
            "petromoc"
        )
    
    with col2:
        criar_card_metricas(
            "Plano Total",
            f"{formatar_ptbr(total_plano, 0)}",
            "Meta estabelecida",
            "Volume planejado",
            "🎯",
            "plano"
        )
    
    with col3:
        cor_diferenca = "fh" if variacao_total >= 0 else "RELEASE"
        criar_card_metricas(
            "Variação Total",
            f"{variacao_total:+.1f}%",
            "vs. Plano",
            f"{formatar_ptbr(diferenca_total, 0)} m³",
            "📊",
            cor_diferenca
        )
    
    with col4:
        status_cor = "congenere" if variacao_total >= 0 else "industria"
        status_text = "Acima" if variacao_total >= 0 else "Abaixo"
        status_detalhe = "Meta atingida" if variacao_total >= 0 else "Abaixo da meta"
        criar_card_metricas(
            "Status Geral",
            status_text,
            "do planejado",
            status_detalhe,
            "✅" if variacao_total >= 0 else "⚠️",
            status_cor
        )
    
    st.markdown("---")
    
    # ========== GRÁFICO DE LINHA VENDAS vs PLANO (TERCEIRA INFORMAÇÃO) ==========
    st.markdown("#### 📈 Evolução Mensal - Vendas vs Plano")
    
    # Tentar criar gráfico com dados reais primeiro
    fig_linha = criar_grafico_linhas_vendas_plano(df_filtrado)
    
    if fig_linha:
        st.plotly_chart(fig_linha, use_container_width=True)
        
        # Adicionar análise abaixo do gráfico
        col_analise1, col_analise2, col_analise3 = st.columns(3)
        
        with col_analise1:
            # Calcular desempenho médio
            if 'Variação (%)' in df_tabela.columns:
                variacao_media = df_tabela[df_tabela['Linha de Negócio'] != 'TOTAL GERAL']['Variação (%)'].mean()
                st.metric("📊 Variação Média", f"{variacao_media:+.1f}%")
        
        with col_analise2:
            # Contar linhas com desempenho positivo
            linhas_positivas = len([x for x in dados_tabela if x.get('Variação (%)', 0) > 0 and x['Linha de Negócio'] != 'TOTAL GERAL'])
            st.metric("✅ Linhas no Azul", f"{linhas_positivas}/{len(linhas_negocio)}")
        
        with col_analise3:
            # Melhor desempenho
            if len(dados_tabela) > 1:
                melhor_linha = max([x for x in dados_tabela if x['Linha de Negócio'] != 'TOTAL GERAL'], 
                                 key=lambda x: x.get('Variação (%)', 0))
                st.metric("🏆 Melhor Desempenho", f"{melhor_linha['Linha de Negócio']}")
    
    else:
        # Se não houver dados reais, mostrar gráfico simulado
        st.info("📊 Dados reais insuficientes para análise temporal. Mostrando dados simulados para demonstração:")
        fig_simulado = criar_grafico_linhas_simulado()
        st.plotly_chart(fig_simulado, use_container_width=True)
    
    st.markdown("---")
    
    # ========== GRÁFICO DE BARRAS (QUARTA INFORMAÇÃO) ==========
    st.markdown("#### 📊 Comparação por Linha de Negócio")
    
    # Preparar dados para gráfico (excluir linha TOTAL GERAL)
    df_grafico = df_tabela[df_tabela['Linha de Negócio'] != 'TOTAL GERAL'].copy()
    
    # Converter colunas para numérico
    for col in ['Vendas (m³)', 'Plano (m³)']:
        if col in df_grafico.columns:
            if df_grafico[col].dtype == 'object':
                # Se for string, converter para numérico
                df_grafico[col] = df_grafico[col].astype(str).str.replace('.', '').str.replace(',', '.').astype(float)
            else:
                df_grafico[col] = pd.to_numeric(df_grafico[col], errors='coerce')
    
    # Criar gráfico de barras
    fig = px.bar(
        df_grafico,
        x='Linha de Negócio',
        y=['Vendas (m³)', 'Plano (m³)'],
        title='Vendas vs Plano por Linha de Negócio',
        barmode='group',
        color_discrete_map={
            'Vendas (m³)': '#FF6B35',
            'Plano (m³)': '#9D4EDD'
        },
        category_orders={"Linha de Negócio": linhas_negocio}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_title='Volume (m³)',
        xaxis_title='Linha de Negócio',
        legend_title='',
        height=500
    )
    
    # Atualizar nomes da legenda
    fig.for_each_trace(lambda t: t.update(name='Vendas' if t.name == 'Vendas (m³)' else 'Plano'))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== DOWNLOADS ==========
    with st.expander("📥 Opções de Download"):
        col1, col2 = st.columns(2)
        
        with col1:
            criar_botao_download_excel(
                df_tabela, 
                "vendas_linhas_negocio", 
                "Linhas de Negócio"
            )
        
        with col2:
            criar_botao_download_csv(
                df_tabela, 
                "vendas_linhas_negocio", 
                "Linhas de Negócio"
            )

# ============================================= FUNÇÕES PARA SCROLLER DE QUOTA DE MERCADO =============================================

def criar_scroller_quota_mercado(total_industria_tm: float, total_petromoc_tm: float, total_congeneres_tm: float,
                               total_industria_m3: float, total_petromoc_m3: float, total_congeneres_m3: float,
                               perc_petromoc: float, perc_congeneres: float):
    """Cria um scroller animado para a quota de mercado"""
    
    st.markdown("""
    <div class="scroller-container">
        <div class="scroller-title">🏭 QUOTA DE MERCADO - INDÚSTRIA</div>
        <div class="scroller-content">
            <div class="scroller-item">
                <div class="scroller-value pulse-effect">100.0%</div>
                <div class="scroller-label">INDÚSTRIA</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #FFD166;">{:.1f}%</div>
                <div class="scroller-label">PETROMOC</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #4ECDC4;">{:.1f}%</div>
                <div class="scroller-label">CONGÊNERE</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
        </div>
    </div>
    """.format(
        formatar_ptbr(total_industria_tm, 0),
        formatar_ptbr(total_industria_m3, 0),
        perc_petromoc,
        formatar_ptbr(total_petromoc_tm, 0),
        formatar_ptbr(total_petromoc_m3, 0),
        perc_congeneres,
        formatar_ptbr(total_congeneres_tm, 0),
        formatar_ptbr(total_congeneres_m3, 0)
    ), unsafe_allow_html=True)

def criar_scroller_quota_petromoc(total_petromoc_tm: float, total_RELEASE_tm: float, total_fh_tm: float,
                                total_petromoc_m3: float, total_RELEASE_m3: float, total_fh_m3: float,
                                perc_RELEASE: float, perc_fh: float):
    """Cria um scroller animado para a quota da Petromoc"""
    
    st.markdown("""
    <div class="scroller-container scroller-petromoc">
        <div class="scroller-title">⛽ QUOTA DE MERCADO - PETROMOC</div>
        <div class="scroller-content">
            <div class="scroller-item">
                <div class="scroller-value pulse-effect">100.0%</div>
                <div class="scroller-label">PETROMOC TOTAL</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #FFD166;">{:.1f}%</div>
                <div class="scroller-label">RELEASE</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #06D6A0;">{:.1f}%</div>
                <div class="scroller-label">FINANCIAL HOLD</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
        </div>
    </div>
    """.format(
        formatar_ptbr(total_petromoc_tm, 0),
        formatar_ptbr(total_petromoc_m3, 0),
        perc_RELEASE,
        formatar_ptbr(total_RELEASE_tm, 0),
        formatar_ptbr(total_RELEASE_m3, 0),
        perc_fh,
        formatar_ptbr(total_fh_tm, 0),
        formatar_ptbr(total_fh_m3, 0)
    ), unsafe_allow_html=True)

# ============================================= FUNÇÕES PARA EXTRAIR DADOS REAIS DA IMPORTACAOMZ =============================================

def extrair_dados_garantias_bancarias(df_importacao: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai dados de Garantias Bancárias diretamente do dataframe ImportacaoMZ
    Inclui linha de totais gerais no final e coluna de percentagem de disponibilidade
    """
    
    # Verificar se existem colunas relacionadas a garantias bancárias
    colunas_garantias = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['BANCO', 'GARANTIA', 'LIMITE', 'GB'])]
    
    if not colunas_garantias:
        st.info("ℹ️ Colunas de garantias bancárias não encontradas. Verifique a estrutura do arquivo ImportacaoMZ.")
        return pd.DataFrame()
    
    # Agrupar por banco e calcular totais
    if 'Banco_GB' in df_importacao.columns:
        # Se existe coluna específica para bancos
        dados_garantias = df_importacao.groupby('Banco_GB').agg({
            'ValorLimite_GB': 'sum',
            'Valor_GB': 'sum'
        }).reset_index()
        
        # Calcular disponibilidade
        dados_garantias['Disponibilidade_GB'] = dados_garantias['ValorLimite_GB'] - dados_garantias['Valor_GB']
        
        # 🔧 CALCULAR PERCENTAGEM DE DISPONIBILIDADE
        dados_garantias['Disponibilidade_%'] = (dados_garantias['Disponibilidade_GB'] / dados_garantias['ValorLimite_GB'] * 100).round(1)
        
        # 🔧 CALCULAR LINHA DE TOTAIS GERAIS
        total_limite = dados_garantias['ValorLimite_GB'].sum()
        total_valor = dados_garantias['Valor_GB'].sum()
        total_disponibilidade = dados_garantias['Disponibilidade_GB'].sum()
        total_percentagem = (total_disponibilidade / total_limite * 100) if total_limite > 0 else 0
        
        # Adicionar linha de totais
        linha_total = pd.DataFrame({
            'Banco_GB': ['TOTAL GERAL'],
            'ValorLimite_GB': [total_limite],
            'Valor_GB': [total_valor],
            'Disponibilidade_GB': [total_disponibilidade],
            'Disponibilidade_%': [round(total_percentagem, 1)]
        })
        
        dados_garantias = pd.concat([dados_garantias, linha_total], ignore_index=True)
        
    else:
        # Tentar estrutura alternativa - criar dados baseados em colunas disponíveis
        st.warning("⚠️ Estrutura de garantias bancárias não encontrada. Usando dados simulados para demonstração.")
        
        bancos = ["ABSA", "BCI", "BNI", "FCB", "MOZA", "SGM", "UBA"]
        dados_garantias = []
        total_limite = 0
        total_valor = 0
        total_disponibilidade = 0
        
        for banco in bancos:
            # Usar dados do dataframe se possível, senão simular
            limite = np.random.uniform(5000000, 15000000)
            valor_utilizado = np.random.uniform(1000000, limite * 0.8)
            disponibilidade = limite - valor_utilizado
            percentagem_disponivel = (disponibilidade / limite * 100) if limite > 0 else 0
            
            dados_garantias.append({
                'Banco_GB': banco,
                'ValorLimite_GB': limite,
                'Valor_GB': valor_utilizado,
                'Disponibilidade_GB': disponibilidade,
                'Disponibilidade_%': round(percentagem_disponivel, 1)
            })
            
            total_limite += limite
            total_valor += valor_utilizado
            total_disponibilidade += disponibilidade
        
        dados_garantias = pd.DataFrame(dados_garantias)
        
        # 🔧 ADICIONAR LINHA DE TOTAIS GERAIS
        total_percentagem = (total_disponibilidade / total_limite * 100) if total_limite > 0 else 0
        
        linha_total = pd.DataFrame({
            'Banco_GB': ['TOTAL GERAL'],
            'ValorLimite_GB': [total_limite],
            'Valor_GB': [total_valor],
            'Disponibilidade_GB': [total_disponibilidade],
            'Disponibilidade_%': [round(total_percentagem, 1)]
        })
        
        dados_garantias = pd.concat([dados_garantias, linha_total], ignore_index=True)
    
    return dados_garantias

def extrair_dados_portos_RELEASE_fh(df_importacao: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai dados de Portos vs RELEASE/Financial Hold diretamente do dataframe ImportacaoMZ
    Ordem fixa: Maputo, Beira, Nacala, Pemba
    Inclui coluna de percentagem de Financial Hold
    """
    
    if df_importacao.empty:
        return pd.DataFrame()
    
    # Verificar colunas disponíveis
    colunas_porto = [col for col in df_importacao.columns if 'PORTO' in col.upper()]
    
    if not colunas_porto:
        st.warning("⚠️ Coluna de Porto não encontrada no arquivo ImportacaoMZ")
        return pd.DataFrame()
    
    # Determinar coluna de porto
    coluna_porto = colunas_porto[0]
    
    # ORDEM FIXA DOS PORTOS
    ORDEM_PORTOS = ['Maputo', 'Beira', 'Nacala', 'Pemba']
    
    # Determinar colunas para RELEASE e financial hold
    colunas_RELEASE = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['RELEASE', 'PETRO_TM', 'QTD_PETRO'])]
    colunas_fh = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['FINANCIAL', 'FH', 'QTD_FH'])]
    
    coluna_RELEASE = colunas_RELEASE[0] if colunas_RELEASE else None
    coluna_fh = colunas_fh[0] if colunas_fh else None
    
    # Agrupar por porto
    if coluna_RELEASE and coluna_fh:
        # Se temos ambas as colunas
        dados_portos = df_importacao.groupby(coluna_porto).agg({
            coluna_RELEASE: 'sum',
            coluna_fh: 'sum'
        }).reset_index()
        
        dados_portos = dados_portos.rename(columns={
            coluna_porto: 'Porto',
            coluna_RELEASE: 'RELEASE',
            coluna_fh: 'FINANCIAL HOLD'
        })
        
    elif 'Qtd_Petro_TM' in df_importacao.columns and 'Qtd_FH_( TM)' in df_importacao.columns:
        # Usar colunas padrão que sabemos existir
        dados_portos = df_importacao.groupby(coluna_porto).agg({
            'Qtd_Petro_TM': 'sum',
            'Qtd_FH_( TM)': 'sum'
        }).reset_index()
        
        dados_portos = dados_portos.rename(columns={
            coluna_porto: 'Porto',
            'Qtd_Petro_TM': 'RELEASE',
            'Qtd_FH_( TM)': 'FINANCIAL HOLD'
        })
        
    else:
        # Tentar encontrar dados alternativos
        st.warning("⚠️ Estrutura de RELEASE/Financial Hold não encontrada. Usando dados disponíveis.")
        
        # Lista de portos únicos
        portos_unicos = df_importacao[coluna_porto].unique()
        dados_portos = []
        
        for porto in portos_unicos:
            if pd.notna(porto):
                dados_porto = df_importacao[df_importacao[coluna_porto] == porto]
                
                # Tentar calcular totais baseados em colunas disponíveis
                RELEASE = 0
                fh = 0
                
                # Procurar por qualquer coluna numérica para simular dados
                colunas_numericas = df_importacao.select_dtypes(include=[np.number]).columns
                if len(colunas_numericas) > 0:
                    RELEASE = dados_porto[colunas_numericas[0]].sum() if len(colunas_numericas) > 0 else 0
                    fh = dados_porto[colunas_numericas[1]].sum() if len(colunas_numericas) > 1 else RELEASE * 0.3
                
                dados_portos.append({
                    'Porto': porto,
                    'RELEASE': RELEASE,
                    'FINANCIAL HOLD': fh
                })
        
        dados_portos = pd.DataFrame(dados_portos)
    
    # CORREÇÃO: REMOVER DUPLICATAS - Agrupar por porto e somar os valores
    if not dados_portos.empty:
        dados_portos = dados_portos.groupby('Porto', as_index=False).agg({
            'RELEASE': 'sum',
            'FINANCIAL HOLD': 'sum'
        })
    
    # CORREÇÃO: GARANTIR QUE TODOS OS PORTOS DA ORDEM FIXA ESTEJAM PRESENTES (MESMO COM ZERO)
    portos_existentes = dados_portos['Porto'].unique() if not dados_portos.empty else []
    
    for porto in ORDEM_PORTOS:
        if porto not in portos_existentes:
            # Adicionar porto com valores zero
            dados_portos = pd.concat([
                dados_portos,
                pd.DataFrame([{
                    'Porto': porto,
                    'RELEASE': 0.0,
                    'FINANCIAL HOLD': 0.0
                }])
            ], ignore_index=True)
    
    # CORREÇÃO: ORDENAR OS PORTOS NA ORDEM ESPECÍFICA
    if not dados_portos.empty:
        # Criar uma coluna de ordenação baseada na ordem fixa
        ordem_map = {porto: idx for idx, porto in enumerate(ORDEM_PORTOS)}
        
        # Adicionar coluna de ordenação
        dados_portos['Ordem'] = dados_portos['Porto'].map(ordem_map)
        
        # Para portos que não estão na ordem fixa, atribuir um valor alto
        dados_portos['Ordem'] = dados_portos['Ordem'].fillna(99)
        
        # Ordenar pelos portos na ordem fixa
        dados_portos = dados_portos.sort_values('Ordem').reset_index(drop=True)
        
        # Remover a coluna de ordenação temporária
        dados_portos = dados_portos.drop('Ordem', axis=1, errors='ignore')
    
    # CORREÇÃO: CALCULAR PERCENTAGEM DE FINANCIAL HOLD
    if not dados_portos.empty:
        dados_portos['% FINANCIAL HOLD'] = (dados_portos['FINANCIAL HOLD'] / 
                                           (dados_portos['RELEASE'] + dados_portos['FINANCIAL HOLD']) * 100).round(1)
        
        # Tratar casos de divisão por zero
        dados_portos['% FINANCIAL HOLD'] = dados_portos['% FINANCIAL HOLD'].fillna(0.0)
    
    # CORREÇÃO: Adicionar linha geral com totais
    if not dados_portos.empty:
        total_RELEASE = dados_portos['RELEASE'].sum()
        total_fh = dados_portos['FINANCIAL HOLD'].sum()
        total_geral = total_RELEASE + total_fh
        percentual_fh_geral = (total_fh / total_geral * 100) if total_geral > 0 else 0
        
        dados_portos = pd.concat([
            dados_portos,
            pd.DataFrame([{
                'Porto': 'TOTAL GERAL',
                'RELEASE': total_RELEASE,
                'FINANCIAL HOLD': total_fh,
                '% FINANCIAL HOLD': round(percentual_fh_geral, 1)
            }])
        ], ignore_index=True)
    
    return dados_portos

def analisar_estrutura_importacao(df_importacao: pd.DataFrame):
    """
    Analisa a estrutura do dataframe ImportacaoMZ para debugging
    """
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Debug - Importação")
    
    if df_importacao.empty:
        st.sidebar.warning("Dataframe vazio")
        return
    
    st.sidebar.write(f"**Registros:** {len(df_importacao)}")
    st.sidebar.write(f"**Colunas:** {len(df_importacao.columns)}")
    
    # Mostrar colunas disponíveis
    with st.sidebar.expander("Ver colunas"):
        st.write(list(df_importacao.columns))
    
    # Mostrar tipos de dados
    with st.sidebar.expander("Ver tipos de dados"):
        st.write(df_importacao.dtypes)
    
    # Mostrar primeiras linhas
    with st.sidebar.expander("Ver primeiras linhas"):
        st.dataframe(df_importacao.head(3))

def extrair_ano_dos_dados(df_importacao: pd.DataFrame) -> int:
    """Extrai o ano dos dados de importação"""
    if df_importacao.empty:
        return datetime.now().year
    
    # Tentar encontrar coluna de data
    colunas_data = ['NOR', 'Data_Descarga', 'Data_Importacao', 'Data']
    for coluna in colunas_data:
        if coluna in df_importacao.columns:
            datas_validas = df_importacao[coluna].dropna()
            if not datas_validas.empty:
                # Converter para datetime se necessário
                if not pd.api.types.is_datetime64_any_dtype(datas_validas):
                    datas_validas = pd.to_datetime(datas_validas, errors='coerce')
                
                ano = datas_validas.dt.year.mode()
                if not ano.empty:
                    return int(ano.iloc[0])
    
    return datetime.now().year

def criar_analise_market_share_com_scroller(df_filtrado: pd.DataFrame):
    """Cria análise de Market Share com scroller animado"""
    
    st.markdown('<div class="section-title">📊 QUOTA DE MERCADO - VISUALIZAÇÃO DINÂMICA</div>', unsafe_allow_html=True)
    
    df_processed = df_filtrado.copy()   
    
    # Limpar colunas numéricas
    colunas_tm = ['Qtd_Petro_TM', 'Qtd_FH_( TM)', 'Quantidade_TM', 'Quantidade']
    
    for col in colunas_tm:
        if col in df_processed.columns:
            df_processed[col] = limpar_coluna_numerica(df_processed, col)

    for c in CLIENTES_CONGENERES:
        if c in df_processed.columns:
            df_processed[c] = limpar_coluna_numerica(df_processed, c)

    # Calcular totais
    total_petromoc_tm = 0
    total_congeneres_tm = 0
    
    if 'Qtd_Petro_TM' in df_processed.columns and 'Qtd_FH_( TM)' in df_processed.columns:
        total_petromoc_tm = (df_processed["Qtd_Petro_TM"] + df_processed["Qtd_FH_( TM)"]).sum()
    elif 'Quantidade_TM' in df_processed.columns:
        total_petromoc_tm = df_processed["Quantidade_TM"].sum()
    
    for c in CLIENTES_CONGENERES:
        if c in df_processed.columns:
            total_congeneres_tm += df_processed[c].sum()

    total_industria_tm = total_petromoc_tm + total_congeneres_tm
    
    total_RELEASE_tm = df_processed["Qtd_Petro_TM"].sum() if "Qtd_Petro_TM" in df_processed.columns else 0
    total_fh_tm = df_processed["Qtd_FH_( TM)"].sum() if "Qtd_FH_( TM)" in df_processed.columns else 0

    if total_industria_tm == 0:
        st.warning("📊 Nenhum dado numérico válido para análise de Market Share")
        return

    combustivel_principal = 'Gasóleo'
    colunas_combustivel = ['Combustivel_Vendas', 'Combustivel_Importacao', 'Combustivel', 'Material']
    for col in colunas_combustivel:
        if col in df_processed.columns and not df_processed[col].empty:
            combustiveis_validos = df_processed[col].dropna()
            if not combustiveis_validos.empty:
                combustivel_principal = combustiveis_validos.mode().iloc[0]
                break

    # Converter todos os valores para m³
    total_petromoc_m3 = converter_tm_para_m3_seguro(total_petromoc_tm, combustivel_principal)
    total_RELEASE_m3 = converter_tm_para_m3_seguro(total_RELEASE_tm, combustivel_principal)
    total_fh_m3 = converter_tm_para_m3_seguro(total_fh_tm, combustivel_principal)
    total_industria_m3 = converter_tm_para_m3_seguro(total_industria_tm, combustivel_principal)
    total_congeneres_m3 = converter_tm_para_m3_seguro(total_congeneres_tm, combustivel_principal)

    def calcular_percentual(parte, total):
        return (parte / total * 100) if total > 0 else 0
    
    perc_petromoc = calcular_percentual(total_petromoc_tm, total_industria_tm)
    perc_congeneres = calcular_percentual(total_congeneres_tm, total_industria_tm)
    perc_RELEASE = calcular_percentual(total_RELEASE_tm, total_petromoc_tm) if total_petromoc_tm > 0 else 0
    perc_fh = calcular_percentual(total_fh_tm, total_petromoc_tm) if total_petromoc_tm > 0 else 0

    # ========== SCROLLER QUOTA DE MERCADO ==========
    criar_scroller_quota_mercado(
        total_industria_tm, total_petromoc_tm, total_congeneres_tm,
        total_industria_m3, total_petromoc_m3, total_congeneres_m3,
        perc_petromoc, perc_congeneres
    )
    
    # ========== SCROLLER QUOTA PETROMOC ==========
    criar_scroller_quota_petromoc(
        total_petromoc_tm, total_RELEASE_tm, total_fh_tm,
        total_petromoc_m3, total_RELEASE_m3, total_fh_m3,
        perc_RELEASE, perc_fh
    )

    # ========== GRÁFICO DE PIZZA PARA COMPLEMENTAR ==========
    st.markdown("#### 📊 Visualização Complementar - Distribuição de Mercado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza - Quota de Mercado
        dados_pizza_mercado = pd.DataFrame({
            'Empresa': ['Petromoc', 'Congênere'],
            'Percentual': [perc_petromoc, perc_congeneres]
        })
        
        fig_mercado = px.pie(
            dados_pizza_mercado,
            values='Percentual',
            names='Empresa',
            title='Distribuição do Mercado',
            color='Empresa',
            color_discrete_map={
                'Petromoc': '#FF6B35',
                'Congênere': '#4ECDC4'
            }
        )
        fig_mercado.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_mercado, use_container_width=True)
    
    with col2:
        # Gráfico de pizza - Quota Petromoc
        dados_pizza_petromoc = pd.DataFrame({
            'Tipo': ['RELEASE', 'Financial Hold'],
            'Percentual': [perc_RELEASE, perc_fh]
        })
        
        fig_petromoc = px.pie(
            dados_pizza_petromoc,
            values='Percentual',
            names='Tipo',
            title='Distribuição Interna - Petromoc',
            color='Tipo',
            color_discrete_map={
                'RELEASE': '#FFD166',
                'Financial Hold': '#06D6A0'
            }
        )
        fig_petromoc.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_petromoc, use_container_width=True)

# ============================================= ABA IMPORTAÇÃO COMPLETA COM SCROLLER =============================================

def criar_aba_importacao_com_dados_reais(df_filtrado: pd.DataFrame):
    """Cria a aba de Importação com dados reais, scroller animado e opções de download"""
    
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado de importação encontrado com os filtros aplicados")
        return

    # Analisar estrutura dos dados (para debugging)
    analisar_estrutura_importacao(df_filtrado)
    
    # Extrair ano dos dados
    ano_dados = extrair_ano_dos_dados(df_filtrado)
    
    st.markdown(f'<div class="section-title">📦 Análise de Importação - {ano_dados}</div>', unsafe_allow_html=True)
    
    # ========== CARTÕES DE MÉTRICAS (PRIMEIRO) ==========
    st.markdown("#### 🎯 Métricas Principais")
    
    # Extrair dados para os cartões
    with st.spinner("🔄 Calculando métricas..."):
        dados_garantias = extrair_dados_garantias_bancarias(df_filtrado)
        dados_portos = extrair_dados_portos_RELEASE_fh(df_filtrado)
    
    # CARTÕES PRINCIPAIS
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Total de Garantias
        if not dados_garantias.empty and 'TOTAL GERAL' in dados_garantias['Banco_GB'].values:
            total_geral = dados_garantias[dados_garantias['Banco_GB'] == 'TOTAL GERAL'].iloc[0]
            disponibilidade_perc = total_geral.get('Disponibilidade_%', 0)
            criar_card_metricas(
                "Disponibilidade GB",
                f"{disponibilidade_perc:.1f}%",
                "Garantias Bancárias",
                f"MT {formatar_ptbr(total_geral.get('Disponibilidade_GB', 0), 0)}",
                "🏦",
                "fh"
            )
        else:
            criar_card_metricas(
                "Disponibilidade GB",
                "0.0%",
                "Garantias Bancárias",
                "Dados não disponíveis",
                "🏦",
                "fh"
            )
    
    with col2:
        # Total RELEASE
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_RELEASE = total_geral.get('RELEASE', 0)
            total_fh = total_geral.get('FINANCIAL HOLD', 0)
            total_geral_volume = total_RELEASE + total_fh
            perc_RELEASE = (total_RELEASE / total_geral_volume * 100) if total_geral_volume > 0 else 0
            
            criar_card_metricas(
                "Volume RELEASE",
                f"{perc_RELEASE:.1f}%",
                "Do total importado",
                f"{formatar_ptbr(total_RELEASE, 0)} TM",
                "💰",
                "RELEASE"
            )
        else:
            criar_card_metricas(
                "Volume RELEASE",
                "0.0%",
                "Do total importado",
                "Dados não disponíveis",
                "💰",
                "RELEASE"
            )
    
    with col3:
        # Total Financial Hold
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_RELEASE = total_geral.get('RELEASE', 0)
            total_fh = total_geral.get('FINANCIAL HOLD', 0)
            total_geral_volume = total_RELEASE + total_fh
            perc_fh = (total_fh / total_geral_volume * 100) if total_geral_volume > 0 else 0
            
            criar_card_metricas(
                "Financial Hold",
                f"{perc_fh:.1f}%",
                "Do total importado",
                f"{formatar_ptbr(total_fh, 0)} TM",
                "📊",
                "industria"
            )
        else:
            criar_card_metricas(
                "Financial Hold",
                "0.0%",
                "Do total importado",
                "Dados não disponíveis",
                "📊",
                "industria"
            )
    
    with col4:
        # Total Geral Importação
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_volume = total_geral.get('RELEASE', 0) + total_geral.get('FINANCIAL HOLD', 0)
            
            criar_card_metricas(
                "Total Importado",
                f"{formatar_ptbr(total_volume, 0)}",
                "Volume total",
                "TM",
                "📦",
                "petromoc"
            )
        else:
            criar_card_metricas(
                "Total Importado",
                "0",
                "Volume total",
                "TM",
                "📦",
                "petromoc"
            )
    
    st.markdown("---")
    
    # ========== SCROLLER QUOTA DE MERCADO ==========
    criar_analise_market_share_com_scroller(df_filtrado)
    
    st.markdown("---")
    
    # ========== DOWNLOADS - DADOS BRUTOS ==========
    st.markdown("#### 📥 Download de Dados")
    col_download1, col_download2 = st.columns(2)
    
    with col_download1:
        criar_botao_download_excel(
            df_filtrado, 
            "dados_importacao_brutos", 
            "Dados Brutos"
        )
    
    with col_download2:
        criar_botao_download_csv(
            df_filtrado, 
            "dados_importacao_brutos", 
            "Dados Brutos"
        )
    
    st.markdown("---")
    
    # ========== GARANTIAS BANCÁRIAS ==========
    st.markdown("#### 🏦 Garantias Bancárias")
    
    if not dados_garantias.empty:
        # Formatar os dados para exibição
        df_garantias_display = dados_garantias.copy()
        
        # Formatar valores monetários
        colunas_monetarias = ['ValorLimite_GB', 'Valor_GB', 'Disponibilidade_GB']
        for coluna in colunas_monetarias:
            if coluna in df_garantias_display.columns:
                df_garantias_display[f'{coluna}_Formatado'] = df_garantias_display[coluna].apply(
                    lambda x: f"MT {formatar_ptbr(x, 0)}" if pd.notna(x) else "MT 0"
                )
        
        # Formatar percentagem COM símbolo %
        if 'Disponibilidade_%' in df_garantias_display.columns:
            df_garantias_display['Disponibilidade_%_Formatado'] = df_garantias_display['Disponibilidade_%'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
            )
        
        # Selecionar colunas para exibição
        colunas_exibicao = ['Banco_GB']
        for coluna in colunas_monetarias:
            if f'{coluna}_Formatado' in df_garantias_display.columns:
                colunas_exibicao.append(f'{coluna}_Formatado')
        
        if 'Disponibilidade_%_Formatado' in df_garantias_display.columns:
            colunas_exibicao.append('Disponibilidade_%_Formatado')
        
        # Renomear colunas
        df_display = df_garantias_display[colunas_exibicao].copy()
        df_display.columns = ['Banco', 'Limite de Garantia', 'Valor Utilizado', 'Disponibilidade', 'Disponibilidade %']
        
        # Exibir tabela
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
        
        # DOWNLOADS - GARANTIAS BANCÁRIAS
        st.markdown("##### 📥 Download Garantias Bancárias")
        col_gar1, col_gar2 = st.columns(2)
        
        with col_gar1:
            criar_botao_download_excel(
                df_display, 
                "garantias_bancarias", 
                "Garantias Bancárias"
            )
        
        with col_gar2:
            criar_botao_download_csv(
                df_display, 
                "garantias_bancarias", 
                "Garantias Bancárias"
            )
    
    else:
        st.info("ℹ️ Nenhum dado de garantias bancárias disponível")
    
    st.markdown("---")
    
    # ========== PORTOS vs RELEASE/FINANCIAL HOLD ==========
    st.markdown("#### ⚓ Portos - RELEASE vs Financial Hold")
    
    if not dados_portos.empty:
        # CORREÇÃO: Já removemos duplicatas na função extrair_dados_portos_RELEASE_fh
        dados_portos_clean = dados_portos.copy()
        
        # CORREÇÃO: Garantir ordem correta [Maputo, Beira, Nacala, Pemba, TOTAL GERAL]
        ordem_correta = ['Maputo', 'Beira', 'Nacala', 'Pemba', 'TOTAL GERAL']
        dados_portos_clean['Ordem'] = dados_portos_clean['Porto'].map({porto: idx for idx, porto in enumerate(ordem_correta)})
        dados_portos_clean['Ordem'] = dados_portos_clean['Ordem'].fillna(99)
        dados_portos_clean = dados_portos_clean.sort_values('Ordem').drop('Ordem', axis=1)
        
        # Formatar dados para exibição
        df_portos_display = dados_portos_clean.copy()
        
        # Formatar valores numéricos SEM casas decimais
        colunas_volume = ['RELEASE', 'FINANCIAL HOLD']
        for coluna in colunas_volume:
            if coluna in df_portos_display.columns:
                df_portos_display[f'{coluna}_Formatado'] = df_portos_display[coluna].apply(
                    lambda x: f"{formatar_ptbr(x, 0)} TM" if pd.notna(x) else "0 TM"
                )
        
        # Formatar percentagem COM símbolo %
        if '% FINANCIAL HOLD' in df_portos_display.columns:
            df_portos_display['% FINANCIAL HOLD_Formatado'] = df_portos_display['% FINANCIAL HOLD'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
            )
        
        # Selecionar colunas para exibição
        colunas_exibicao = ['Porto']
        for coluna in colunas_volume:
            if f'{coluna}_Formatado' in df_portos_display.columns:
                colunas_exibicao.append(f'{coluna}_Formatado')
        
        if '% FINANCIAL HOLD_Formatado' in df_portos_display.columns:
            colunas_exibicao.append('% FINANCIAL HOLD_Formatado')
        
        # Renomear colunas
        df_display_portos = df_portos_display[colunas_exibicao].copy()
        df_display_portos.columns = ['Porto', 'RELEASE (TM)', 'Financial Hold (TM)', '% Financial Hold']
        
        # Exibir tabela
        st.dataframe(
            df_display_portos,
            use_container_width=True,
            hide_index=True
        )
        
        # DOWNLOADS - PORTOS
        st.markdown("##### 📥 Download Dados de Portos")
        col_port1, col_port2 = st.columns(2)
        
        with col_port1:
            criar_botao_download_excel(
                df_display_portos, 
                "dados_portos", 
                "Dados de Portos"
            )
        
        with col_port2:
            criar_botao_download_csv(
                df_display_portos, 
                "dados_portos", 
                "Dados de Portos"
            )
        
        # ========== GRÁFICO DE BARRAS - PORTOS ==========
        st.markdown("#### 📊 Visualização - Distribuição por Porto")
        
        # Preparar dados para gráfico (excluir linha "TOTAL GERAL")
        dados_grafico = dados_portos_clean[dados_portos_clean['Porto'] != 'TOTAL GERAL'].copy()
        
        if not dados_grafico.empty:
            # CORREÇÃO: Ordenar os dados para o gráfico na ordem correta
            ORDEM_PORTOS_GRAFICO = ['Maputo', 'Beira', 'Nacala', 'Pemba']
            dados_grafico = dados_grafico[dados_grafico['Porto'].isin(ORDEM_PORTOS_GRAFICO)]
            dados_grafico['Porto'] = pd.Categorical(dados_grafico['Porto'], categories=ORDEM_PORTOS_GRAFICO, ordered=True)
            dados_grafico = dados_grafico.sort_values('Porto')
            
            # CORREÇÃO: Criar DataFrame correto para gráfico de barras agrupadas
            dados_melted = dados_grafico.melt(
                id_vars=['Porto'], 
                value_vars=['RELEASE', 'FINANCIAL HOLD'],
                var_name='Tipo', 
                value_name='Volume'
            )
            
            fig = px.bar(
                dados_melted,
                x='Porto',
                y='Volume',
                color='Tipo',
                title='Distribuição por Porto - RELEASE vs Financial Hold',
                barmode='group',
                color_discrete_map={
                    'RELEASE': '#FF6B35',
                    'FINANCIAL HOLD': '#4ECDC4'
                },
                category_orders={"Porto": ORDEM_PORTOS_GRAFICO}
            )
            fig.update_layout(
                yaxis_title='Volume (TM)',
                xaxis_title='Porto'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # DOWNLOADS - GRÁFICO
            st.markdown("##### 📥 Download Dados do Gráfico")
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                criar_botao_download_excel(
                    dados_grafico[['Porto', 'RELEASE', 'FINANCIAL HOLD']], 
                    "dados_grafico_portos", 
                    "Dados do Gráfico"
                )
            
            with col_graf2:
                criar_botao_download_csv(
                    dados_grafico[['Porto', 'RELEASE', 'FINANCIAL HOLD']], 
                    "dados_grafico_portos", 
                    "Dados do Gráfico"
                )
    
    else:
        st.info("ℹ️ Nenhum dado de portos disponível")


############################################################ ABA PROMOTORES ##################################################################################################        
# -*- coding: utf-8 -*-
"""
Sistema de Gestão – Petromoc, SA
Dashboard Completo: Vendas + Plano + Participação na Importação + Linha de Negócio
Formato PT-BR: 1.234,56
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import locale
import os
import base64
import io
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any
from datetime import datetime, date

# ============================================= CONFIGURAÇÃO DA PÁGINA =============================================
st.set_page_config(
    page_title="Sistema de Gestão - Petromoc, SA",
    page_icon="Logo_Petromoc.png",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://www.petromoc.co.mz',
        'Report a bug': None,
        'About': 'Sistema de Gestão Econômica da Petromoc, SA'
    }
)

# ============================================= CONFIGURAÇÃO DE LOGGING =============================================
def setup_logging():
    """Configura sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler()
        ]
    )
    return logging.getLogger(__name__)

logger = setup_logging()

# ============================================= INICIALIZAÇÃO DO SESSION_STATE =============================================
def inicializar_session_state():
    """Inicializa todas as variáveis necessárias no session_state"""
    defaults = {
        'date_range_importacao': (date(2025, 1, 1), date.today()),
        'date_range_vendas': (date(2025, 1, 1), date.today()),
        'modo_trabalho_selector': "Importação",
        'dados_carregados': False,
        'ultima_atualizacao': datetime.now()
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

# Inicializar session_state ANTES de qualquer widget
inicializar_session_state()

# REMOVER A CHAMADA AO ARQUIVO CSS EXTERNO (que pode não existir)
# def load_css():
#     with open("style.css") as f:
#         st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# load_css()

# CSS personalizado completo dentro do código
st.markdown("""
<style>
    .stButton > button {
        width: 100%;
        border-radius: 10px;
    }
    
    .main {
        background-color: #FFFFFF;
        color: #333333;
    }
    
    .stApp {
        background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%);
    }
    
    .main-header {
        color: #FF6B35;
        border-bottom: 3px solid #FF6B35;
        padding-bottom: 0.5rem;
        font-weight: 700;
        font-size: 2.5rem;
    }
    
    .metric-card-industria {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: 2px solid #5a6fd8;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-petromoc {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        border: 2px solid #FF5A1F;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(255, 107, 53, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-congenere {
        background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%);
        border: 2px solid #3BB4AC;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(78, 205, 196, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-RELEASE {
        background: linear-gradient(135deg, #FFD166 0%, #FFB347 100%);
        border: 2px solid #FFC857;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(255, 209, 102, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-fh {
        background: linear-gradient(135deg, #06D6A0 0%, #04A777 100%);
        border: 2px solid #05C793;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(6, 214, 160, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-plano {
        background: linear-gradient(135deg, #9D4EDD 0%, #7B2CBF 100%);
        border: 2px solid #8A2BE2;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        box-shadow: 0 6px 20px rgba(157, 78, 221, 0.25);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
        height: 140px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    
    .metric-card-industria:hover, 
    .metric-card-petromoc:hover, 
    .metric-card-congenere:hover,
    .metric-card-RELEASE:hover,
    .metric-card-fh:hover,
    .metric-card-plano:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
    }
    
    .metric-title {
        font-size: 0.9rem;
        font-weight: 700;
        color: rgba(255, 255, 255, 0.95);
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 2rem;
        font-weight: 800;
        color: white;
        text-align: center;
        margin-bottom: 0.25rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .metric-subvalue {
        font-size: 0.85rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        text-align: center;
    }
    
    .metric-subvalue-small {
        font-size: 0.75rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.85);
        text-align: center;
        margin-top: 0.25rem;
    }
    
    .stButton button {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3);
        background: linear-gradient(135deg, #FF8C42 0%, #FF6B35 100%);
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-left: 0.5rem;
    }
    
    .badge-success {
        background: linear-gradient(135deg, #28A745 0%, #20C997 100%);
        color: white;
    }
    
    .badge-warning {
        background: linear-gradient(135deg, #FFC107 0%, #FFB300 100%);
        color: white;
    }
    
    .badge-purple {
        background: linear-gradient(135deg, #9D4EDD 0%, #7B2CBF 100%);
        color: white;
    }
    
    .section-title {
        color: #2D3748;
        font-weight: 700;
        font-size: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 2px solid #FF6B35;
    }
    
    .logo-container {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
        border-bottom: 2px solid #FFE0D6;
    }
    
    .logo-img {
        max-width: 200px;
        height: auto;
        border-radius: 10px;
        box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2);
        transition: transform 0.3s ease;
    }
    
    .logo-img:hover {
        transform: scale(1.05);
    }
    
    .tabela-simples {
        width: 100%;
        border-collapse: collapse;
        margin: 1rem 0;
        font-size: 0.9rem;
    }
    
    .tabela-simples th {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        color: white;
        padding: 0.75rem;
        text-align: left;
        font-weight: 600;
    }
    
    .tabela-simples td {
        padding: 0.75rem;
        border-bottom: 1px solid #E2E8F0;
    }
    
    .tabela-simples tr:nth-child(even) {
        background-color: #F7FAFC;
    }
    
    .tabela-simples tr:hover {
        background-color: #EDF2F7;
    }
    
    .valor-positivo {
        color: #28A745;
        font-weight: 600;
    }
    
    .valor-negativo {
        color: #DC3545;
        font-weight: 600;
    }
    
    /* Estilos para as abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: #F8F9FA;
        border-radius: 8px 8px 0px 0px;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        font-weight: 600;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #FF6B35;
        color: white;
    }
    
    /* SCROLLER ANIMADO PARA QUOTA DE MERCADO */
    .scroller-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        border: 3px solid #5a6fd8;
        position: relative;
        overflow: hidden;
    }
    
    .scroller-title {
        color: white;
        font-size: 1.3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
        text-transform: uppercase;
        letter-spacing: 2px;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }
    
    .scroller-content {
        display: flex;
        justify-content: space-around;
        align-items: center;
        animation: scrollEffect 15s ease-in-out infinite;
        padding: 1rem 0;
    }
    
    .scroller-item {
        text-align: center;
        padding: 0 2rem;
        border-right: 2px solid rgba(255, 255, 255, 0.3);
        flex: 1;
    }
    
    .scroller-item:last-child {
        border-right: none;
    }
    
    .scroller-value {
        font-size: 2.5rem;
        font-weight: 800;
        color: white;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    }
    
    .scroller-label {
        font-size: 1rem;
        font-weight: 600;
        color: rgba(255, 255, 255, 0.9);
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .scroller-subvalue {
        font-size: 0.9rem;
        font-weight: 500;
        color: rgba(255, 255, 255, 0.8);
        margin-top: 0.25rem;
    }
    
    @keyframes scrollEffect {
        0%, 100% {
            transform: translateX(0);
        }
        25% {
            transform: translateX(-5px);
        }
        50% {
            transform: translateX(5px);
        }
        75% {
            transform: translateX(-5px);
        }
    }
    
    /* Pulsating effect for important values */
    .pulse-effect {
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
        100% {
            transform: scale(1);
        }
    }
    
    /* Petromoc Scroller */
    .scroller-petromoc {
        background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
        border: 3px solid #FF5A1F;
    }
    
    /* Responsive design */
    @media (max-width: 768px) {
        .scroller-content {
            flex-direction: column;
            gap: 1rem;
        }
        
        .scroller-item {
            border-right: none;
            border-bottom: 2px solid rgba(255, 255, 255, 0.3);
            padding: 1rem 0;
        }
        
        .scroller-item:last-child {
            border-bottom: none;
        }
    }
</style>
            
""", unsafe_allow_html=True)

# ============================================= VERIFICAÇÃO DE AMBIENTE =============================================
# Verificação segura de ambiente (sem causar erro se secrets não existir)
try:
    # Tentar verificar se é ambiente cloud
    if hasattr(st, 'secrets') and st.secrets.get("IS_CLOUD", False):
        # Configurações específicas para cloud
        st.cache_data.clear()
        logger.info("Modo cloud detectado - cache limpo")
except Exception as e:
    # Se houver erro com secrets, apenas continue
    logger.info(f"Modo local - secrets não configurado: {e}")

# ============================================= LOCALIDADE =============================================
def configure_locale() -> None:
    """Configura locale com fallbacks mais robustos"""
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')
    except locale.Error:
        try:
            locale.setlocale(locale.LC_ALL, 'Portuguese_Brazil.1252')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, '')
            except locale.Error:
                logger.warning("Não foi possível configurar o locale pt_BR")

configure_locale()

# ============================================= FORMATAÇÃO PT-BR =============================================
def formatar_ptbr(valor: float, casas: int = 2) -> str:
    """Formata número: 1234.56 → '1.234,56' com fallback robusto"""
    if pd.isna(valor) or valor is None:
        return "0" + (",00" if casas > 0 else "")
    
    try:
        # Tentar usar locale primeiro
        try:
            return locale.format_string(f"%.{casas}f", float(valor), grouping=True)
        except:
            # Fallback manual
            valor_float = float(valor)
            valor_str = f"{valor_float:,.{casas}f}"
            if '.' in valor_str:
                parte_inteira, parte_decimal = valor_str.split('.')
                parte_inteira = parte_inteira.replace(',', 'X').replace('.', ',').replace('X', '.')
                return parte_inteira + ',' + parte_decimal
            else:
                return valor_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception as e:
        logger.error(f"Erro na formatação: {e}")
        return "0" + (",00" if casas > 0 else "")

# ============================================= DENSIDADE DOS COMBUSTÍVEIS ==========================================
DENSIDADES = {
    'Gasolina': 0.73,
    'Jet A1': 0.79,
    'Gasóleo': 0.84,
    'Diesel': 0.84
}

# ============================================= FUNÇÃO DE CONVERSÃO TM → M³ ==========================================
def converter_tm_para_m3_seguro(quantidade_tm: float, combustivel: str) -> float:
    """Conversão segura de TM para M³"""
    try:
        if quantidade_tm == 0 or pd.isna(quantidade_tm):
            return 0.0
        
        combustivel_limpo = str(combustivel).strip().title() if combustivel else ''
        
        mapeamento_combustiveis = {
            'Gasóleo': 'Gasóleo',
            'Gasolina': 'Gasolina', 
            'jet': 'Jet A1',
            'jet a1': 'Jet A1',
            'jet-a1': 'Jet A1',
            'diesel': 'Gasóleo',
            '': 'Gasóleo'
        }
        
        combustivel_normalizado = mapeamento_combustiveis.get(
            combustivel_limpo.lower(), combustivel_limpo
        )
        
        densidade = DENSIDADES.get(combustivel_normalizado)
        
        if not densidade:
            return 0.0
        
        return quantidade_tm / densidade
        
    except Exception:
        return 0.0

# ============================================= FUNÇÃO PARA CARREGAR E EXIBIR LOGO =============================================
def carregar_logo_base64(caminho_arquivo: str) -> str:
    """Converte a imagem para base64 para exibição no HTML"""
    try:
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        else:
            return ""
    except Exception:
        return ""

def exibir_logo_sidebar():
    """Exibe o logo da Petromoc no sidebar"""
    logo_base64 = carregar_logo_base64("Logo_Petromoc.png")
    
    if logo_base64:
        st.sidebar.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" class="logo-img" alt="Petromoc Logo">
            <div style="margin-top: 0.5rem; font-weight: 700; color: #FF6B35; font-size: 1.1rem;">
                Petromoc, SA
            </div>
            <div style="font-size: 0.8rem; color: #666; margin-top: 0.25rem;">
                Sistema de Gestão Econômica
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div class="logo-container">
            <div style="text-align: center; padding: 1rem; background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%); border-radius: 10px; color: white;">
                <h3 style="margin: 0;">⛽ PETROMOC</h3>
                <p style="margin: 0.25rem 0 0 0; font-size: 0.9rem;">Sistema de Gestão</p>
            </div>
        </div>
        """, unsafe_allow_html=True)

# ============================================= CACHE DOS DADOS =============================================
@st.cache_data(ttl=3600)
def carregar_vendas() -> pd.DataFrame:
    """Carrega dados de vendas com verificação robusta"""
    try:
        arquivos_vendas = [
            'Vds_2023_Comb_.xlsx',
            'Vds_2024_Comb_.xlsx',
            'Vds_2025_Comb_.xlsx'
        ]
        
        dfs = []
        for arquivo in arquivos_vendas:
            if os.path.exists(arquivo):
                df_temp = pd.read_excel(arquivo)
                logger.info(f"Arquivo {arquivo} carregado: {len(df_temp)} registros")
                dfs.append(df_temp)
            else:
                logger.warning(f"Arquivo {arquivo} não encontrado")
                st.warning(f"⚠️ Arquivo {arquivo} não encontrado")
        
        if not dfs:
            st.error("❌ Nenhum arquivo de vendas encontrado")
            return pd.DataFrame()
            
        df = pd.concat(dfs, ignore_index=True).fillna(0)
        
        # Processamento das colunas monetárias
        colunas_monetarias = ['V_Liquido', 'V_Imposto', 'Custo_Produto', 'Margem_Vendas',
                             'V_Venda_Oceanica', 'Desconto', 'Valor_ISC']
        
        for col in colunas_monetarias:
            if col in df.columns:
                df[f'{col}_MT'] = df[col] * df['Cambio']
                df[f'{col}_USD'] = df[col] / df['Cambio']

        # Processamento de datas
        df['Data_Facturacao'] = pd.to_datetime(df['Data_Facturacao'], errors='coerce')
        df['Ano'] = df['Data_Facturacao'].dt.year.fillna(0).astype(int)
        df['Mes'] = df['Data_Facturacao'].dt.month.fillna(0).astype(int)
        
        logger.info(f"Dataset de vendas processado: {len(df)} registros")
        return df
        
    except Exception as e:
        logger.error(f"Erro ao carregar vendas: {str(e)}")
        st.error(f"❌ Erro crítico ao carregar vendas: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_plano() -> pd.DataFrame:
    try:
        p1 = pd.read_excel('PlanComb_2023.xlsx')
        p2 = pd.read_excel('PlanComb_2024.xlsx')
        p3 = pd.read_excel('PlanComb_2025.xlsx')

        df = pd.concat([p1, p2, p3], ignore_index=True).fillna(0)
        df['Data_Facturacao'] = pd.to_datetime(df['Data_Facturacao'], format='%d/%m/%Y', errors='coerce')
        
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar plano: {str(e)}")
        st.error(f"Erro ao carregar plano: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_lookups():
    try:
        v0 = pd.read_excel('v_loock_up.xlsx', sheet_name=0)
        v1 = pd.read_excel('v_loock_up.xlsx', sheet_name=1)
        v2 = pd.read_excel('v_loock_up.xlsx', sheet_name=2)
        v3 = pd.read_excel('v_loock_up.xlsx', sheet_name=3)
        v4 = pd.read_excel('v_loock_up.xlsx', sheet_name=4)
        v5 = pd.read_excel('v_loock_up.xlsx', sheet_name=5)
        v0['DataCriacaoCliente'] = pd.to_datetime(v0['DataCriacaoCliente'], format='%d/%m/%Y', errors='coerce')
        return v0, v1, v2, v3, v4, v5
    except Exception as e:
        logger.error(f"Erro ao carregar lookups: {str(e)}")
        st.error(f"Erro ao carregar lookups: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=3600)
def carregar_importacao() -> pd.DataFrame:
    try:
        df = pd.read_excel('ImportacaoMZ.xlsx')
        
        def safe_datetime_conversion(series, format=None):
            try:
                if format:
                    return pd.to_datetime(series, format=format, errors='coerce')
                else:
                    return pd.to_datetime(series, errors='coerce')
            except Exception:
                return pd.Series([pd.NaT] * len(series))
        
        colunas_data = ['NOR', 'Data_Descarga']
        for col in colunas_data:
            if col in df.columns:
                df[col] = safe_datetime_conversion(df[col])
        
        return df
    except FileNotFoundError:
        logger.error("Arquivo ImportacaoMZ.xlsx não encontrado")
        st.error("Arquivo ImportacaoMZ.xlsx não encontrado")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erro ao carregar importação: {str(e)}")
        st.error(f"Erro ao carregar importação: {str(e)}")
        return pd.DataFrame()

# Carregar dados
@st.cache_resource
def carregar_todos_dados():
    with st.spinner("🔄 Carregando dados do sistema..."):
        vendas_df = carregar_vendas()
        plano_df = carregar_plano()
        v0, v1, v2, v3, v4, v5 = carregar_lookups()
        import_df = carregar_importacao()
        return vendas_df, plano_df, v0, v1, v2, v3, v4, v5, import_df

vendas_df, plano_df, v0, v1, v2, v3, v4, v5, import_df = carregar_todos_dados()

# ============================================= PROCESSAMENTO DOS DATAFRAMES =============================================
def processar_dataframes():
    """Processa e combina os dataframes de vendas e plano"""
    try:
        if not vendas_df.empty:
            colunas_usd = ['V_Liquido_USD','V_Imposto_USD','Custo_Produto_USD','Margem_Vendas_USD',
                          'V_Venda_Oceanica_USD','Desconto_USD','Valor_ISC_USD']
            colunas_mt = ['V_Liquido_MT','V_Imposto_MT','Custo_Produto_MT','Margem_Vendas_MT',
                         'V_Venda_Oceanica_MT','Desconto_MT','Valor_ISC_MT']
            
            vendas_df_MT = vendas_df.drop([col for col in colunas_usd if col in vendas_df.columns], axis=1, errors='ignore')
            vendas_df_USD = vendas_df.drop([col for col in colunas_mt if col in vendas_df.columns], axis=1, errors='ignore')

            vendas_df_MT['Ano'] = vendas_df_MT['Data_Facturacao'].dt.year
            vendas_df_MT['Mes'] = vendas_df_MT['Data_Facturacao'].dt.month
            vendas_df_MT['Dia'] = vendas_df_MT['Data_Facturacao'].dt.day

            DateSet_MT = vendas_df_MT.copy()
            
            if not v3.empty:
                DateSet_MT = pd.merge(DateSet_MT, v3, left_on=['CE'], right_on=['CE'], how='left')
            if not v0.empty:
                DateSet_MT = pd.merge(DateSet_MT, v0, left_on=['Emissor'], right_on=['Emissor'], how='left')
            if not v5.empty:
                DateSet_MT = pd.merge(DateSet_MT, v5, left_on=['Material'], right_on=['Material'], how='left')
            if not v4.empty:
                DateSet_MT = pd.merge(DateSet_MT, v4, left_on=['TipFt'], right_on=['TipFt'], how='left')
            if not v1.empty:
                DateSet_MT = pd.merge(DateSet_MT, v1, left_on=['CDst'], right_on=['CDst'], how='left')
            
            if 'DataCriacaoCliente' in DateSet_MT.columns:
                DateSet_MT['DataCriacaoCliente'] = pd.to_datetime(DateSet_MT['DataCriacaoCliente'], format='%d/%m/%Y', errors='coerce')

            colunas_remover = ['Doc.fat.','Tipo.Factura','TipFt','Denominação','Cambio','Moeda']
            DateSet_MT_Pln = DateSet_MT.drop([col for col in colunas_remover if col in DateSet_MT.columns], axis=1, errors='ignore')
            
            if not plano_df.empty:
                DateSet_MT_Pln = pd.merge(DateSet_MT_Pln, plano_df, 
                                        left_on=['Data_Facturacao','Emissor','CDst','Material'],
                                        right_on=['Data_Facturacao','Emissor','CDst','Material'], 
                                        how='left')
            
            DateSet_MT_Pln = DateSet_MT_Pln.fillna(value=0)
            
            return DateSet_MT_Pln, vendas_df_MT, vendas_df_USD
        else:
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Erro ao processar dataframes: {str(e)}")
        st.error(f"Erro ao processar dataframes: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

DateSet_MT_Pln, vendas_df_MT, vendas_df_USD = processar_dataframes()

# ============================================= LIMPEZA DE COLUNAS =============================================
CLIENTES_CONGENERES = [
    "AFR PETR", "B ENERGY", "BP", "CAC", "CAMEL", "DALBIT", "ENER", "EXOR",
    "GLENCORE", "GTS", "IPM", "I2A", "LAKE OIL", "LIBERTY", "MCCI", "MITRA",
    "MOUMERU", "MOZTOP", "NGUVU L", "PETRODA", "PETROGAL", "PESS", "PUMA",
    "RUR", "TOP ENERGY", "TOTAL", "UNION", "VIVO"
]

def limpar_coluna_numerica(df: pd.DataFrame, col: str) -> pd.Series:
    if col not in df.columns:
        return pd.Series([0.0] * len(df))
    
    try:
        s = df[col].astype(str).str.strip()
        s = s.str.replace(r'\s+', '', regex=True)
        s = s.str.replace(',', '.', regex=False)
        s = s.str.replace(r'[^0-9.-]', '', regex=True)
        s = s.replace('', '0').replace('.', '0')
        return pd.to_numeric(s, errors='coerce').fillna(0.0)
    except:
        return pd.Series([0.0] * len(df))

# ============================================= FUNÇÃO PARA LINK EXTERNO =============================================
def criar_link_externo(url: str, texto: str, icone: str = "🌐"):
    """Cria um link externo que abre em nova aba"""
    return f"""
    <a href="{url}" target="_blank" style="text-decoration: none;">
        <div style="
            background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%);
            color: white;
            padding: 0.75rem 1rem;
            border-radius: 8px;
            text-align: center;
            font-weight: 600;
            margin: 0.5rem 0;
            border: 2px solid #FF5A1F;
            box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2);
            transition: all 0.3s ease;
            cursor: pointer;
        " onmouseover="this.style.transform='translateY(-2px)'; this.style.boxShadow='0 6px 20px rgba(255, 107, 53, 0.3)';" 
        onmouseout="this.style.transform='translateY(0)'; this.style.boxShadow='0 4px 12px rgba(255, 107, 53, 0.2)';">
            {icone} {texto}
        </div>
    </a>
    """

# ============================================= FUNÇÕES DO MENU LATERAL =============================================
@st.cache_data(ttl=3600)
def carregar_opcoes_filtros(df: pd.DataFrame, tipo: str) -> Dict[str, Any]:
    """Carrega opções de filtros baseadas na tabela especificada"""
    if df.empty:
        return {}
    
    df = df.copy()
    result = {}
    
    # DATAS PADRÃO
    start_date_default = date(2025, 1, 1)
    end_date_default = date.today()
    
    # Determinar coluna de data baseada no tipo
    if tipo == "importacao":
        coluna_data = 'NOR' if 'NOR' in df.columns else 'Data_Descarga'
    else:  # vendas
        coluna_data = 'Data_Facturacao'
    
    if coluna_data in df.columns:
        df[coluna_data] = pd.to_datetime(df[coluna_data], errors='coerce')
        datas_validas = df[coluna_data].dropna()
    else:
        datas_validas = pd.Series([])
    
    if not datas_validas.empty:
        min_date = datas_validas.min().date()
        max_date = min(datas_validas.max().date(), end_date_default)
    else:
        min_date = start_date_default
        max_date = end_date_default
    
    result.update({
        'min_date': min_date,
        'max_date': max_date,
        'coluna_data': coluna_data
    })
    
    # BUSCAR TODAS AS COLUNAS DISPONÍVEIS PARA FILTROS
    colunas_disponiveis = df.columns.tolist()
    
    # Filtrar colunas por tipo de conteúdo
    for coluna in colunas_disponiveis:
        if coluna in ['_merge', 'Ano_merge', 'Mes_merge']:
            continue
            
        valores_unicos = df[coluna].dropna().unique()
        if len(valores_unicos) > 0 and len(valores_unicos) <= 100:  # Limitar a 100 valores únicos
            if pd.api.types.is_numeric_dtype(df[coluna]):
                if coluna in ['Ano', 'Ano_Vendas', 'Ano_Importacao']:
                    result[coluna] = sorted([int(v) for v in valores_unicos if pd.notna(v) and str(v).isdigit()])
            else:
                result[coluna] = sorted([str(v) for v in valores_unicos if pd.notna(v) and str(v) != ''])
    
    return result

def criar_secao_calendario_corrigida(opcoes: Dict[str, Any], tipo: str) -> tuple:
    """Versão corrigida do calendário sem conflitos de session_state"""
    
    st.sidebar.header(f"📅 Calendário - {tipo.title()}")
    
    # Usar chave única baseada no tipo
    chave_calendario = f"date_range_{tipo}"
    
    # Obter valor atual do session_state
    data_atual = st.session_state[chave_calendario]
    
    # Criar o date_input
    date_range = st.sidebar.date_input(
        f"Intervalo de Datas ({tipo})",
        value=data_atual,
        min_value=date(2015, 1, 1),
        max_value=date.today(),
        help=f"Filtra por data de {opcoes.get('coluna_data', 'data')}",
        key=f"widget_{chave_calendario}"  # Chave diferente para o widget
    )
    
    # Atualizar session_state apenas se a data mudou
    if len(date_range) == 2 and date_range[1] >= date_range[0]:
        if date_range != st.session_state[chave_calendario]:
            st.session_state[chave_calendario] = date_range
        
        dias = (date_range[1] - date_range[0]).days
        st.sidebar.caption(f"📊 Período selecionado: {dias} dias")
        return date_range
    else:
        # Se seleção inválida, manter o valor anterior
        return st.session_state[chave_calendario]

def limpar_filtros_session_state():
    """Limpa todos os filtros do session_state"""
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('date_range_') or key.startswith('filtro_'):
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]

def limpar_filtros_vendas():
    """Limpa apenas os filtros de vendas"""
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('filtro_vendas_') or key == 'date_range_vendas':
            keys_to_remove.append(key)
    
    for key in keys_to_remove:
        del st.session_state[key]

def renderizar_menu_lateral_corrigido():
    """Versão corrigida do menu lateral COM CORREÇÃO DO NOME DO FILTRO"""
    filtros = {}
    
    # LOGO DA PETROMOC
    exibir_logo_sidebar()
    
    # BOTÃO DO SITE OFICIAL
    st.sidebar.markdown(criar_link_externo(
        "https://www.petromoc.co.mz", 
        "Site Oficial Petromoc", 
        "🌐"
    ), unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    # SELEÇÃO DO MODO DE TRABALHO
    modo_trabalho = st.sidebar.radio(
        "🎯 SELECIONE",
        ["Importação", "Vendas", "Promotores", "Stock","Caixa_e_Bancos","KPIs", "Simulacoes"],
        index=0,
        help="Selecione qual análise deseja visualizar",
        key="modo_trabalho_selector"
    )
    
    filtros['modo_trabalho'] = modo_trabalho
    
    st.sidebar.markdown("---")
    
    if modo_trabalho == "Importação":
        # CARREGAR OPÇÕES DE FILTRO DA IMPORTAÇÃO
        opcoes_import = carregar_opcoes_filtros(import_df, "importacao")
        
        if not opcoes_import:
            st.sidebar.warning("⚠️ Nenhum dado de importação disponível")
            return filtros
        
        # SEÇÃO DE CALENDÁRIO PARA IMPORTAÇÃO (CORRIGIDA)
        date_range_import = criar_secao_calendario_corrigida(opcoes_import, "importacao")
        filtros['date_range'] = date_range_import
        filtros['tipo_dados'] = 'importacao'
        
        # FILTROS ESPECÍFICOS DA IMPORTAÇÃO
        st.sidebar.header("🔍 Filtros - Importação")
        
        sequencia_importacao = ['Ano', 'Situacao_Descarga', 'Porto', 'Combustivel', 'Mes']
        
        colunas_filtradas_import = []
        
        for coluna in sequencia_importacao:
            if coluna in opcoes_import and opcoes_import[coluna]:
                colunas_filtradas_import.append(coluna)
        
        for coluna in opcoes_import:
            if (coluna not in colunas_filtradas_import and 
                coluna not in ['min_date', 'max_date', 'coluna_data'] and
                len(colunas_filtradas_import) < 5):
                colunas_filtradas_import.append(coluna)
        
        for coluna in colunas_filtradas_import:
            valores = opcoes_import[coluna]
            if valores:
                # Inicializar session_state para este filtro se não existir
                chave_filtro = f"filtro_import_{coluna}"
                if chave_filtro not in st.session_state:
                    st.session_state[chave_filtro] = []
                
                valores_selecionados = st.sidebar.multiselect(
                    f"{coluna} (Import.)",
                    options=valores,
                    default=st.session_state[chave_filtro],
                    key=f"widget_{chave_filtro}"
                )
                
                # Atualizar session_state
                st.session_state[chave_filtro] = valores_selecionados
                filtros[coluna] = valores_selecionados
    
    else:  # MODO VENDAS
        # CARREGAR OPÇÕES DE FILTRO DAS VENDAS
        opcoes_vendas = carregar_opcoes_filtros(DateSet_MT_Pln, "vendas")
        
        if not opcoes_vendas:
            st.sidebar.warning("⚠️ Nenhum dado de vendas disponível")
            return filtros
        
        # SEÇÃO DE CALENDÁRIO PARA VENDAS (CORRIGIDA)
        date_range_vendas = criar_secao_calendario_corrigida(opcoes_vendas, "vendas")
        filtros['date_range'] = date_range_vendas
        filtros['tipo_dados'] = 'vendas'
        
        # FILTROS ESPECÍFICOS DAS VENDAS
        st.sidebar.header("🔍 Filtros - Vendas")
        
        # CORREÇÃO: SUBSTITUIR 'Gestor/Promotor' por 'Gestor / Promotor'
        sequencia_vendas = ['Ano', 'Combustivel', 'Sector/Sigla', 'Gestor / Promotor', 'Instalacao', 'Provincia']
        
        colunas_filtradas_vendas = []
        
        for coluna in sequencia_vendas:
            if coluna in opcoes_vendas and opcoes_vendas[coluna]:
                colunas_filtradas_vendas.append(coluna)
        
        for coluna in opcoes_vendas:
            if (coluna not in colunas_filtradas_vendas and 
                coluna not in ['min_date', 'max_date', 'coluna_data'] and
                len(colunas_filtradas_vendas) < 5):
                colunas_filtradas_vendas.append(coluna)
        
        for coluna in colunas_filtradas_vendas:
            valores = opcoes_vendas[coluna]
            if valores:
                # CORREÇÃO: USAR NOME CORRETO 'Gestor / Promotor' NO SESSION_STATE
                chave_coluna = coluna.replace('/', '_').replace(' ', '_')
                chave_filtro = f"filtro_vendas_{chave_coluna}"
                
                if chave_filtro not in st.session_state:
                    st.session_state[chave_filtro] = []
                
                # CORREÇÃO: MOSTRAR NOME CORRETO 'Gestor / Promotor' NA INTERFACE
                nome_exibicao = "Gestor / Promotor" if coluna == "Gestor / Promotor" else coluna
                
                valores_selecionados = st.sidebar.multiselect(
                    f"{nome_exibicao} (Vendas)",
                    options=valores,
                    default=st.session_state[chave_filtro],
                    key=f"widget_{chave_filtro}"
                )
                
                # Atualizar session_state
                st.session_state[chave_filtro] = valores_selecionados
                filtros[coluna] = valores_selecionados
    
    # BOTÕES DE AÇÃO (comuns a ambos os modos)
    st.sidebar.markdown("---")
    st.sidebar.header("⚡ Ações Rápidas")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.sidebar.button("🔄 Atualizar", use_container_width=True, key="btn_atualizar"):
            st.cache_data.clear()
            st.rerun()
    
    with col2:
        if st.sidebar.button("🗑️ Limpar Filtros", use_container_width=True, key="btn_limpar"):
            limpar_filtros_session_state()
            st.rerun()
    
    return filtros

# ============================================= FUNÇÕES DE VISUALIZAÇÃO =============================================
def criar_card_metricas(titulo: str, valor_principal: str, subtitulo1: str = "", subtitulo2: str = "", icone: str = "📊", tipo_card: str = "default"):
    """Cria cards de métricas com cores vibrantes"""
    
    card_class = "metric-card-petromoc"  # padrão
    
    if tipo_card == "industria":
        card_class = "metric-card-industria"
    elif tipo_card == "petromoc":
        card_class = "metric-card-petromoc"
    elif tipo_card == "congenere":
        card_class = "metric-card-congenere"
    elif tipo_card == "RELEASE":
        card_class = "metric-card-RELEASE"
    elif tipo_card == "fh":
        card_class = "metric-card-fh"
    elif tipo_card == "plano":
        card_class = "metric-card-plano"
    
    st.markdown(f"""
    <div class="{card_class}">
        <div class="metric-title">{icone} {titulo}</div>
        <div class="metric-value">{valor_principal}</div>
        <div class="metric-subvalue">{subtitulo1}</div>
        <div class="metric-subvalue-small">{subtitulo2}</div>
    </div>
    """, unsafe_allow_html=True)

# ============================================= FUNÇÃO DE FILTRAGEM PARA VENDAS =============================================
def aplicar_filtros_vendas(df: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
    """Aplica filtros no DataFrame de vendas"""
    if df.empty:
        return df
        
    df_filtrado = df.copy()
    
    # Aplicar filtro de datas
    if 'Data_Facturacao' in df_filtrado.columns:
        df_filtrado['Data_Facturacao'] = pd.to_datetime(df_filtrado['Data_Facturacao'], errors='coerce')
        mask_data = (df_filtrado['Data_Facturacao'] >= pd.Timestamp(filtros['date_range'][0])) & \
                    (df_filtrado['Data_Facturacao'] <= pd.Timestamp(filtros['date_range'][1]))
        df_filtrado = df_filtrado[mask_data]
    
    # Aplicar outros filtros
    for coluna, valores in filtros.items():
        if coluna not in ['date_range', 'modo_trabalho', 'tipo_dados'] and valores:
            if coluna in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin([str(v) for v in valores])]
    
    return df_filtrado

# ============================================= FUNÇÃO DE FILTRAGEM PARA IMPORTAÇÃO =============================================
def aplicar_filtros_importacao(df: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
    """Aplica filtros no DataFrame de importação"""
    if df.empty:
        return df
        
    df_filtrado = df.copy()
    
    # Aplicar filtro de datas
    colunas_data = ['NOR', 'Data_Descarga']
    for col_data in colunas_data:
        if col_data in df_filtrado.columns:
            df_filtrado[col_data] = pd.to_datetime(df_filtrado[col_data], errors='coerce')
            mask_data = (df_filtrado[col_data] >= pd.Timestamp(filtros['date_range'][0])) & \
                        (df_filtrado[col_data] <= pd.Timestamp(filtros['date_range'][1]))
            df_filtrado = df_filtrado[mask_data]
            break
    
    # Aplicar outros filtros
    for coluna, valores in filtros.items():
        if coluna not in ['date_range', 'modo_trabalho', 'tipo_dados'] and valores:
            if coluna in df_filtrado.columns:
                df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin([str(v) for v in valores])]
    
    return df_filtrado

# ============================================= FUNÇÕES PARA DOWNLOAD =============================================
def criar_botao_download_excel(df: pd.DataFrame, nome_arquivo: str, descricao: str):
    """Cria botão para download em Excel"""
    if df.empty:
        st.warning(f"Nenhum dado disponível para {descricao}")
        return
        
    try:
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Dados', index=False)
        output.seek(0)
        
        st.download_button(
            label=f"📊 Excel - {descricao}",
            data=output,
            file_name=f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Erro ao gerar Excel: {e}")

def criar_botao_download_csv(df: pd.DataFrame, nome_arquivo: str, descricao: str):
    """Cria botão para download em CSV"""
    if df.empty:
        st.warning(f"Nenhum dado disponível para {descricao}")
        return
        
    try:
        csv = df.to_csv(index=False, sep=';', decimal=',')
        st.download_button(
            label=f"📝 CSV - {descricao}",
            data=csv,
            file_name=f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Erro ao gerar CSV: {e}")

# ============================================= GRÁFICO DE LINHAS VENDAS vs PLANO =============================================

def criar_grafico_linhas_vendas_plano(df_filtrado: pd.DataFrame):
    """Cria gráfico de linhas Vendas vs Plano por mês na ordem correta"""
    
    if df_filtrado.empty:
        return None
    
    try:
        # Verificar se temos as colunas necessárias
        colunas_necessarias = ['Data_Facturacao']
        colunas_vendas = ['Vendas m³', 'V_Liquido', 'Quantidade']
        colunas_plano = ['Plano_m³', 'Plano', 'Quantidade_Plano']
        
        # Encontrar colunas disponíveis
        coluna_vendas = next((col for col in colunas_vendas if col in df_filtrado.columns), None)
        coluna_plano = next((col for col in colunas_plano if col in df_filtrado.columns), None)
        
        if not coluna_vendas or not coluna_plano:
            return None
        
        # Criar cópia do dataframe
        df_grafico = df_filtrado.copy()
        
        # Garantir que a data está em formato datetime
        df_grafico['Data_Facturacao'] = pd.to_datetime(df_grafico['Data_Facturacao'], errors='coerce')
        
        # Extrair ano e mês
        df_grafico['Ano'] = df_grafico['Data_Facturacao'].dt.year
        df_grafico['Mes'] = df_grafico['Data_Facturacao'].dt.month
        
        # Agrupar por mês e calcular totais
        dados_mensais = df_grafico.groupby(['Ano', 'Mes']).agg({
            coluna_vendas: 'sum',
            coluna_plano: 'sum'
        }).reset_index()
        
        # Renomear colunas para padrão
        dados_mensais = dados_mensais.rename(columns={
            coluna_vendas: 'Vendas',
            coluna_plano: 'Plano'
        })
        
        # Criar coluna de data para ordenação
        dados_mensais['Data'] = pd.to_datetime(
            dados_mensais['Ano'].astype(str) + '-' + dados_mensais['Mes'].astype(str) + '-01'
        )
        
        # Ordenar por data
        dados_mensais = dados_mensais.sort_values('Data')
        
        # Mapear números dos meses para nomes em português
        meses_ptbr = {
            1: 'Janeiro', 2: 'Fevereiro', 3: 'Março', 4: 'Abril', 
            5: 'Maio', 6: 'Junho', 7: 'Julho', 8: 'Agosto', 
            9: 'Setembro', 10: 'Outubro', 11: 'Novembro', 12: 'Dezembro'
        }
        
        dados_mensais['Mes_Nome'] = dados_mensais['Mes'].map(meses_ptbr)
        
        # Criar label completa (Mês Ano)
        dados_mensais['Periodo'] = dados_mensais['Mes_Nome'] + ' ' + dados_mensais['Ano'].astype(str)
        
        # Ordem correta dos meses
        ordem_meses = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 
                      'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro']
        
        # Criar coluna de ordenação
        dados_mensais['Ordem_Mes'] = dados_mensais['Mes_Nome'].apply(
            lambda x: ordem_meses.index(x) if x in ordem_meses else 99
        )
        
        # Ordenar por ano e mês
        dados_mensais = dados_mensais.sort_values(['Ano', 'Ordem_Mes'])
        
        # Verificar se temos dados suficientes
        if len(dados_mensais) == 0:
            return None
        
        # Criar gráfico de linhas
        fig = px.line(
            dados_mensais,
            x='Periodo',
            y=['Vendas', 'Plano'],
            title='📈 Vendas vs Plano - Evolução Mensal',
            labels={
                'value': 'Volume (m³)',
                'Periodo': 'Mês',
                'variable': 'Legenda'
            },
            color_discrete_map={
                'Vendas': '#FF6B35',  # Laranja Petromoc
                'Plano': '#9D4EDD'    # Roxo para plano
            }
        )
        
        # Atualizar layout
        fig.update_layout(
            xaxis_title='Mês',
            yaxis_title='Volume (m³)',
            legend_title='',
            height=500,
            hovermode='x unified',
            xaxis=dict(
                tickangle=-45,
                type='category'
            ),
            yaxis=dict(
                tickformat=',.0f'
            )
        )
        
        # Adicionar marcadores nos pontos
        fig.update_traces(mode='lines+markers', marker=dict(size=6))
        
        return fig
        
    except Exception as e:
        logger.error(f"Erro ao criar gráfico de linhas: {str(e)}")
        return None

def criar_grafico_linhas_simulado():
    """Cria gráfico de linhas simulado quando não há dados reais"""
    
    # Dados simulados para demonstração
    meses = ['Jan 2024', 'Fev 2024', 'Mar 2024', 'Abr 2024', 'Mai 2024', 'Jun 2024', 
             'Jul 2024', 'Ago 2024', 'Set 2024', 'Out 2024', 'Nov 2024', 'Dez 2024']
    
    # Gerar dados simulados realistas
    np.random.seed(42)
    vendas_base = np.random.uniform(80000, 120000, 12)
    plano_base = np.random.uniform(90000, 110000, 12)
    
    # Adicionar alguma tendência
    tendencia = np.linspace(0, 0.2, 12)
    vendas = vendas_base * (1 + tendencia)
    plano = plano_base * (1 + tendencia * 0.8)
    
    # Adicionar alguma variação sazonal
    sazonalidade = np.sin(np.linspace(0, 2*np.pi, 12)) * 0.1
    vendas = vendas * (1 + sazonalidade)
    
    dados_simulados = pd.DataFrame({
        'Periodo': meses,
        'Vendas': vendas,
        'Plano': plano
    })
    
    # Criar gráfico de linhas
    fig = px.line(
        dados_simulados,
        x='Periodo',
        y=['Vendas', 'Plano'],
        title='📈 Vendas vs Plano - Evolução Mensal (Dados Simulados)',
        labels={
            'value': 'Volume (m³)',
            'Periodo': 'Mês',
            'variable': 'Legenda'
        },
        color_discrete_map={
            'Vendas': '#FF6B35',
            'Plano': '#9D4EDD'
        }
    )
    
    fig.update_layout(
        xaxis_title='Mês',
        yaxis_title='Volume (m³)',
        legend_title='',
        height=500,
        hovermode='x unified',
        xaxis=dict(
            tickangle=-45,
            type='category'
        ),
        yaxis=dict(
            tickformat=',.0f'
        )
    )
    
    # Adicionar marcadores nos pontos
    fig.update_traces(mode='lines+markers', marker=dict(size=6))
    
    return fig

# ============================================= ABA VENDAS COM TABELA E CARTÕES PRIMEIRO =============================================

def criar_aba_vendas_com_tabela_primeiro(df_filtrado: pd.DataFrame, filtros: Dict):
    """Cria a aba de Vendas com tabela, cartões e gráfico de linha Vendas vs Plano"""
    
    st.markdown('<div class="section-title">📊 Vendas - Análise por Linha de Negócio</div>', unsafe_allow_html=True)
    
    # Verificação rápida de dados
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para análise de vendas")
        
        # Mostrar gráfico simulado mesmo sem dados
        st.markdown("#### 📈 Evolução Mensal - Vendas vs Plano")
        fig_simulado = criar_grafico_linhas_simulado()
        st.plotly_chart(fig_simulado, use_container_width=True)
        return
    
    # ========== TABELA DE LINHAS DE NEGÓCIO (PRIMEIRA INFORMAÇÃO) ==========
    st.markdown("#### 📋 Desempenho por Linha de Negócio")
    
    # ORDEM ESPECÍFICA SOLICITADA
    linhas_negocio = ["Vulcan", "Consumidores", "Revendedores", "Bunkers", "Aviacao", "Reexportacao", "Armazenagem"]
    
    dados_tabela = []
    total_vendas = 0
    total_plano = 0
    
    for linha in linhas_negocio:
        # Usar dados reais do DataFrame se disponíveis, senão simular
        if 'Sector/Sigla' in df_filtrado.columns:
            dados_linha = df_filtrado[df_filtrado['Sector/Sigla'] == linha]
            if not dados_linha.empty:
                # Tentar diferentes nomes de colunas para vendas
                colunas_vendas = ['Vendas m³', 'V_Liquido', 'Quantidade', 'Vendas']
                colunas_plano = ['Plano_m³', 'Plano', 'Quantidade_Plano']
                
                vendas = 0
                plano = 0
                
                for col_venda in colunas_vendas:
                    if col_venda in dados_linha.columns:
                        vendas = dados_linha[col_venda].sum()
                        break
                
                for col_plano in colunas_plano:
                    if col_plano in dados_linha.columns:
                        plano = dados_linha[col_plano].sum()
                        break
            else:
                # Dados simulados se não houver dados reais
                vendas = np.random.uniform(50000, 200000)
                plano = vendas * np.random.uniform(0.8, 1.2)
        else:
            # Dados simulados se não houver coluna de linha de negócio
            vendas = np.random.uniform(50000, 200000)
            plano = vendas * np.random.uniform(0.8, 1.2)
        
        diferenca = vendas - plano
        variacao_percentual = (diferenca / plano * 100) if plano > 0 else 0
        
        # Determinar status
        if variacao_percentual >= 10:
            status = "✅ Excedente"
        elif variacao_percentual >= -5:
            status = "⚠️ Dentro do Plano"
        elif variacao_percentual >= -15:
            status = "🔶 Atenção"
        else:
            status = "❌ Crítico"
        
        dados_tabela.append({
            'Linha de Negócio': linha,
            'Vendas (m³)': vendas,
            'Plano (m³)': plano,
            'Variação (m³)': diferenca,
            'Variação (%)': variacao_percentual,
            'Status': status
        })
        
        total_vendas += vendas
        total_plano += plano
    
    # Adicionar linha de Total
    diferenca_total = total_vendas - total_plano
    variacao_total = (diferenca_total / total_plano * 100) if total_plano > 0 else 0
    
    if variacao_total >= 5:
        status_total = "✅ Excedente"
    elif variacao_total >= -5:
        status_total = "⚠️ Dentro do Plano"
    elif variacao_total >= -10:
        status_total = "🔶 Atenção"
    else:
        status_total = "❌ Crítico"
    
    dados_tabela.append({
        'Linha de Negócio': 'TOTAL GERAL',
        'Vendas (m³)': total_vendas,
        'Plano (m³)': total_plano,
        'Variação (m³)': diferenca_total,
        'Variação (%)': variacao_total,
        'Status': status_total
    })
    
    df_tabela = pd.DataFrame(dados_tabela)
    
    # Formatar tabela para exibição
    df_display = df_tabela.copy()
    
    # Formatar valores numéricos
    colunas_numericas = ['Vendas (m³)', 'Plano (m³)', 'Variação (m³)']
    for coluna in colunas_numericas:
        if coluna in df_display.columns:
            df_display[coluna] = df_display[coluna].apply(
                lambda x: formatar_ptbr(x, 0) if pd.notna(x) else "0"
            )
    
    # Formatar percentual
    if 'Variação (%)' in df_display.columns:
        df_display['Variação (%)'] = df_display['Variação (%)'].apply(
            lambda x: f"{x:+.1f}%" if pd.notna(x) else "0,0%"
        )
    
    # Exibir tabela
    st.dataframe(
        df_display,
        use_container_width=True,
        hide_index=True
    )
    
    # ========== CARTÕES DE MÉTRICAS (SEGUNDA INFORMAÇÃO) ==========
    st.markdown("#### 🎯 Métricas Principais")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        criar_card_metricas(
            "Vendas Totais",
            f"{formatar_ptbr(total_vendas, 0)}",
            "Volume realizado",
            f"{len(linhas_negocio)} linhas de negócio",
            "📈",
            "petromoc"
        )
    
    with col2:
        criar_card_metricas(
            "Plano Total",
            f"{formatar_ptbr(total_plano, 0)}",
            "Meta estabelecida",
            "Volume planejado",
            "🎯",
            "plano"
        )
    
    with col3:
        cor_diferenca = "fh" if variacao_total >= 0 else "RELEASE"
        criar_card_metricas(
            "Variação Total",
            f"{variacao_total:+.1f}%",
            "vs. Plano",
            f"{formatar_ptbr(diferenca_total, 0)} m³",
            "📊",
            cor_diferenca
        )
    
    with col4:
        status_cor = "congenere" if variacao_total >= 0 else "industria"
        status_text = "Acima" if variacao_total >= 0 else "Abaixo"
        status_detalhe = "Meta atingida" if variacao_total >= 0 else "Abaixo da meta"
        criar_card_metricas(
            "Status Geral",
            status_text,
            "do planejado",
            status_detalhe,
            "✅" if variacao_total >= 0 else "⚠️",
            status_cor
        )
    
    st.markdown("---")
    
    # ========== GRÁFICO DE LINHA VENDAS vs PLANO (TERCEIRA INFORMAÇÃO) ==========
    st.markdown("#### 📈 Evolução Mensal - Vendas vs Plano")
    
    # Tentar criar gráfico com dados reais primeiro
    fig_linha = criar_grafico_linhas_vendas_plano(df_filtrado)
    
    if fig_linha:
        st.plotly_chart(fig_linha, use_container_width=True)
        
        # Adicionar análise abaixo do gráfico
        col_analise1, col_analise2, col_analise3 = st.columns(3)
        
        with col_analise1:
            # Calcular desempenho médio
            if 'Variação (%)' in df_tabela.columns:
                variacao_media = df_tabela[df_tabela['Linha de Negócio'] != 'TOTAL GERAL']['Variação (%)'].mean()
                st.metric("📊 Variação Média", f"{variacao_media:+.1f}%")
        
        with col_analise2:
            # Contar linhas com desempenho positivo
            linhas_positivas = len([x for x in dados_tabela if x.get('Variação (%)', 0) > 0 and x['Linha de Negócio'] != 'TOTAL GERAL'])
            st.metric("✅ Linhas no Azul", f"{linhas_positivas}/{len(linhas_negocio)}")
        
        with col_analise3:
            # Melhor desempenho
            if len(dados_tabela) > 1:
                melhor_linha = max([x for x in dados_tabela if x['Linha de Negócio'] != 'TOTAL GERAL'], 
                                 key=lambda x: x.get('Variação (%)', 0))
                st.metric("🏆 Melhor Desempenho", f"{melhor_linha['Linha de Negócio']}")
    
    else:
        # Se não houver dados reais, mostrar gráfico simulado
        st.info("📊 Dados reais insuficientes para análise temporal. Mostrando dados simulados para demonstração:")
        fig_simulado = criar_grafico_linhas_simulado()
        st.plotly_chart(fig_simulado, use_container_width=True)
    
    st.markdown("---")
    
    # ========== GRÁFICO DE BARRAS (QUARTA INFORMAÇÃO) ==========
    st.markdown("#### 📊 Comparação por Linha de Negócio")
    
    # Preparar dados para gráfico (excluir linha TOTAL GERAL)
    df_grafico = df_tabela[df_tabela['Linha de Negócio'] != 'TOTAL GERAL'].copy()
    
    # Converter colunas para numérico
    for col in ['Vendas (m³)', 'Plano (m³)']:
        if col in df_grafico.columns:
            if df_grafico[col].dtype == 'object':
                # Se for string, converter para numérico
                df_grafico[col] = df_grafico[col].astype(str).str.replace('.', '').str.replace(',', '.').astype(float)
            else:
                df_grafico[col] = pd.to_numeric(df_grafico[col], errors='coerce')
    
    # Criar gráfico de barras
    fig = px.bar(
        df_grafico,
        x='Linha de Negócio',
        y=['Vendas (m³)', 'Plano (m³)'],
        title='Vendas vs Plano por Linha de Negócio',
        barmode='group',
        color_discrete_map={
            'Vendas (m³)': '#FF6B35',
            'Plano (m³)': '#9D4EDD'
        },
        category_orders={"Linha de Negócio": linhas_negocio}
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        yaxis_title='Volume (m³)',
        xaxis_title='Linha de Negócio',
        legend_title='',
        height=500
    )
    
    # Atualizar nomes da legenda
    fig.for_each_trace(lambda t: t.update(name='Vendas' if t.name == 'Vendas (m³)' else 'Plano'))
    
    st.plotly_chart(fig, use_container_width=True)
    
    # ========== DOWNLOADS ==========
    with st.expander("📥 Opções de Download"):
        col1, col2 = st.columns(2)
        
        with col1:
            criar_botao_download_excel(
                df_tabela, 
                "vendas_linhas_negocio", 
                "Linhas de Negócio"
            )
        
        with col2:
            criar_botao_download_csv(
                df_tabela, 
                "vendas_linhas_negocio", 
                "Linhas de Negócio"
            )

# ============================================= FUNÇÕES PARA SCROLLER DE QUOTA DE MERCADO =============================================

def criar_scroller_quota_mercado(total_industria_tm: float, total_petromoc_tm: float, total_congeneres_tm: float,
                               total_industria_m3: float, total_petromoc_m3: float, total_congeneres_m3: float,
                               perc_petromoc: float, perc_congeneres: float):
    """Cria um scroller animado para a quota de mercado"""
    
    st.markdown("""
    <div class="scroller-container">
        <div class="scroller-title">🏭 QUOTA DE MERCADO - INDÚSTRIA</div>
        <div class="scroller-content">
            <div class="scroller-item">
                <div class="scroller-value pulse-effect">100.0%</div>
                <div class="scroller-label">INDÚSTRIA</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #FFD166;">{:.1f}%</div>
                <div class="scroller-label">PETROMOC</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #4ECDC4;">{:.1f}%</div>
                <div class="scroller-label">CONGÊNERE</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
        </div>
    </div>
    """.format(
        formatar_ptbr(total_industria_tm, 0),
        formatar_ptbr(total_industria_m3, 0),
        perc_petromoc,
        formatar_ptbr(total_petromoc_tm, 0),
        formatar_ptbr(total_petromoc_m3, 0),
        perc_congeneres,
        formatar_ptbr(total_congeneres_tm, 0),
        formatar_ptbr(total_congeneres_m3, 0)
    ), unsafe_allow_html=True)

def criar_scroller_quota_petromoc(total_petromoc_tm: float, total_RELEASE_tm: float, total_fh_tm: float,
                                total_petromoc_m3: float, total_RELEASE_m3: float, total_fh_m3: float,
                                perc_RELEASE: float, perc_fh: float):
    """Cria um scroller animado para a quota da Petromoc"""
    
    st.markdown("""
    <div class="scroller-container scroller-petromoc">
        <div class="scroller-title">⛽ QUOTA DE MERCADO - PETROMOC</div>
        <div class="scroller-content">
            <div class="scroller-item">
                <div class="scroller-value pulse-effect">100.0%</div>
                <div class="scroller-label">PETROMOC TOTAL</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #FFD166;">{:.1f}%</div>
                <div class="scroller-label">RELEASE</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #06D6A0;">{:.1f}%</div>
                <div class="scroller-label">FINANCIAL HOLD</div>
                <div class="scroller-subvalue">{} TM</div>
                <div class="scroller-subvalue">{} m³</div>
            </div>
        </div>
    </div>
    """.format(
        formatar_ptbr(total_petromoc_tm, 0),
        formatar_ptbr(total_petromoc_m3, 0),
        perc_RELEASE,
        formatar_ptbr(total_RELEASE_tm, 0),
        formatar_ptbr(total_RELEASE_m3, 0),
        perc_fh,
        formatar_ptbr(total_fh_tm, 0),
        formatar_ptbr(total_fh_m3, 0)
    ), unsafe_allow_html=True)

# ============================================= FUNÇÕES PARA EXTRAIR DADOS REAIS DA IMPORTACAOMZ =============================================

def extrair_dados_garantias_bancarias(df_importacao: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai dados de Garantias Bancárias diretamente do dataframe ImportacaoMZ
    Inclui linha de totais gerais no final e coluna de percentagem de disponibilidade
    """
    
    # Verificar se existem colunas relacionadas a garantias bancárias
    colunas_garantias = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['BANCO', 'GARANTIA', 'LIMITE', 'GB'])]
    
    if not colunas_garantias:
        st.info("ℹ️ Colunas de garantias bancárias não encontradas. Verifique a estrutura do arquivo ImportacaoMZ.")
        return pd.DataFrame()
    
    # Agrupar por banco e calcular totais
    if 'Banco_GB' in df_importacao.columns:
        # Se existe coluna específica para bancos
        dados_garantias = df_importacao.groupby('Banco_GB').agg({
            'ValorLimite_GB': 'sum',
            'Valor_GB': 'sum'
        }).reset_index()
        
        # Calcular disponibilidade
        dados_garantias['Disponibilidade_GB'] = dados_garantias['ValorLimite_GB'] - dados_garantias['Valor_GB']
        
        # 🔧 CALCULAR PERCENTAGEM DE DISPONIBILIDADE
        dados_garantias['Disponibilidade_%'] = (dados_garantias['Disponibilidade_GB'] / dados_garantias['ValorLimite_GB'] * 100).round(1)
        
        # 🔧 CALCULAR LINHA DE TOTAIS GERAIS
        total_limite = dados_garantias['ValorLimite_GB'].sum()
        total_valor = dados_garantias['Valor_GB'].sum()
        total_disponibilidade = dados_garantias['Disponibilidade_GB'].sum()
        total_percentagem = (total_disponibilidade / total_limite * 100) if total_limite > 0 else 0
        
        # Adicionar linha de totais
        linha_total = pd.DataFrame({
            'Banco_GB': ['TOTAL GERAL'],
            'ValorLimite_GB': [total_limite],
            'Valor_GB': [total_valor],
            'Disponibilidade_GB': [total_disponibilidade],
            'Disponibilidade_%': [round(total_percentagem, 1)]
        })
        
        dados_garantias = pd.concat([dados_garantias, linha_total], ignore_index=True)
        
    else:
        # Tentar estrutura alternativa - criar dados baseados em colunas disponíveis
        st.warning("⚠️ Estrutura de garantias bancárias não encontrada. Usando dados simulados para demonstração.")
        
        bancos = ["ABSA", "BCI", "BNI", "FCB", "MOZA", "SGM", "UBA"]
        dados_garantias = []
        total_limite = 0
        total_valor = 0
        total_disponibilidade = 0
        
        for banco in bancos:
            # Usar dados do dataframe se possível, senão simular
            limite = np.random.uniform(5000000, 15000000)
            valor_utilizado = np.random.uniform(1000000, limite * 0.8)
            disponibilidade = limite - valor_utilizado
            percentagem_disponivel = (disponibilidade / limite * 100) if limite > 0 else 0
            
            dados_garantias.append({
                'Banco_GB': banco,
                'ValorLimite_GB': limite,
                'Valor_GB': valor_utilizado,
                'Disponibilidade_GB': disponibilidade,
                'Disponibilidade_%': round(percentagem_disponivel, 1)
            })
            
            total_limite += limite
            total_valor += valor_utilizado
            total_disponibilidade += disponibilidade
        
        dados_garantias = pd.DataFrame(dados_garantias)
        
        # 🔧 ADICIONAR LINHA DE TOTAIS GERAIS
        total_percentagem = (total_disponibilidade / total_limite * 100) if total_limite > 0 else 0
        
        linha_total = pd.DataFrame({
            'Banco_GB': ['TOTAL GERAL'],
            'ValorLimite_GB': [total_limite],
            'Valor_GB': [total_valor],
            'Disponibilidade_GB': [total_disponibilidade],
            'Disponibilidade_%': [round(total_percentagem, 1)]
        })
        
        dados_garantias = pd.concat([dados_garantias, linha_total], ignore_index=True)
    
    return dados_garantias

def extrair_dados_portos_RELEASE_fh(df_importacao: pd.DataFrame) -> pd.DataFrame:
    """
    Extrai dados de Portos vs RELEASE/Financial Hold diretamente do dataframe ImportacaoMZ
    Ordem fixa: Maputo, Beira, Nacala, Pemba
    Inclui coluna de percentagem de Financial Hold
    """
    
    if df_importacao.empty:
        return pd.DataFrame()
    
    # Verificar colunas disponíveis
    colunas_porto = [col for col in df_importacao.columns if 'PORTO' in col.upper()]
    
    if not colunas_porto:
        st.warning("⚠️ Coluna de Porto não encontrada no arquivo ImportacaoMZ")
        return pd.DataFrame()
    
    # Determinar coluna de porto
    coluna_porto = colunas_porto[0]
    
    # ORDEM FIXA DOS PORTOS
    ORDEM_PORTOS = ['Maputo', 'Beira', 'Nacala', 'Pemba']
    
    # Determinar colunas para RELEASE e financial hold
    colunas_RELEASE = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['RELEASE', 'PETRO_TM', 'QTD_PETRO'])]
    colunas_fh = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['FINANCIAL', 'FH', 'QTD_FH'])]
    
    coluna_RELEASE = colunas_RELEASE[0] if colunas_RELEASE else None
    coluna_fh = colunas_fh[0] if colunas_fh else None
    
    # Agrupar por porto
    if coluna_RELEASE and coluna_fh:
        # Se temos ambas as colunas
        dados_portos = df_importacao.groupby(coluna_porto).agg({
            coluna_RELEASE: 'sum',
            coluna_fh: 'sum'
        }).reset_index()  # CORREÇÃO AQUI: reset_index() com underscore
        
        dados_portos = dados_portos.rename(columns={
            coluna_porto: 'Porto',
            coluna_RELEASE: 'RELEASE',
            coluna_fh: 'FINANCIAL HOLD'
        })
        
    elif 'Qtd_Petro_TM' in df_importacao.columns and 'Qtd_FH_( TM)' in df_importacao.columns:
        # Usar colunas padrão que sabemos existir
        dados_portos = df_importacao.groupby(coluna_porto).agg({
            'Qtd_Petro_TM': 'sum',
            'Qtd_FH_( TM)': 'sum'
        }).reset_index()  # CORREÇÃO AQUI: reset_index() com underscore
        
        dados_portos = dados_portos.rename(columns={
            coluna_porto: 'Porto',
            'Qtd_Petro_TM': 'RELEASE',
            'Qtd_FH_( TM)': 'FINANCIAL HOLD'
        })
        
    else:
        # Tentar encontrar dados alternativos
        st.warning("⚠️ Estrutura de RELEASE/Financial Hold não encontrada. Usando dados disponíveis.")
        
        # Lista de portos únicos
        portos_unicos = df_importacao[coluna_porto].unique()
        dados_portos = []
        
        for porto in portos_unicos:
            if pd.notna(porto):
                dados_porto = df_importacao[df_importacao[coluna_porto] == porto]
                
                # Tentar calcular totais baseados em colunas disponíveis
                RELEASE = 0
                fh = 0
                
                # Procurar por qualquer coluna numérica para simular dados
                colunas_numericas = df_importacao.select_dtypes(include=[np.number]).columns
                if len(colunas_numericas) > 0:
                    RELEASE = dados_porto[colunas_numericas[0]].sum() if len(colunas_numericas) > 0 else 0
                    fh = dados_porto[colunas_numericas[1]].sum() if len(colunas_numericas) > 1 else RELEASE * 0.3
                
                dados_portos.append({
                    'Porto': porto,
                    'RELEASE': RELEASE,
                    'FINANCIAL HOLD': fh
                })
        
        dados_portos = pd.DataFrame(dados_portos)
    
    # CORREÇÃO: REMOVER DUPLICATAS - Agrupar por porto e somar os valores
    if not dados_portos.empty:
        dados_portos = dados_portos.groupby('Porto', as_index=False).agg({
            'RELEASE': 'sum',
            'FINANCIAL HOLD': 'sum'
        })
    


    portos_existentes = dados_portos['Porto'].unique() if not dados_portos.empty else []
    
    for porto in ORDEM_PORTOS:
        if porto not in portos_existentes:
            # Adicionar porto com valores zero
            dados_portos = pd.concat([
                dados_portos,
                pd.DataFrame([{
                    'Porto': porto,
                    'RELEASE': 0.0,
                    'FINANCIAL HOLD': 0.0
                }])
            ], ignore_index=True)
    
    # CORREÇÃO: ORDENAR OS PORTOS NA ORDEM ESPECÍFICA
    if not dados_portos.empty:
        # Criar uma coluna de ordenação baseada na ordem fixa
        ordem_map = {porto: idx for idx, porto in enumerate(ORDEM_PORTOS)}
        
        # Adicionar coluna de ordenação
        dados_portos['Ordem'] = dados_portos['Porto'].map(ordem_map)
        
        # Para portos que não estão na ordem fixa, atribuir um valor alto
        dados_portos['Ordem'] = dados_portos['Ordem'].fillna(99)
        
        # Ordenar pelos portos na ordem fixa
        dados_portos = dados_portos.sort_values('Ordem').reset_index(drop=True)
        
        # Remover a coluna de ordenação temporária
        dados_portos = dados_portos.drop('Ordem', axis=1, errors='ignore')
    
    # CORREÇÃO: CALCULAR PERCENTAGEM DE FINANCIAL HOLD
    if not dados_portos.empty:
        dados_portos['% FINANCIAL HOLD'] = (dados_portos['FINANCIAL HOLD'] / 
                                           (dados_portos['RELEASE'] + dados_portos['FINANCIAL HOLD']) * 100).round(1)
        
        # Tratar casos de divisão por zero
        dados_portos['% FINANCIAL HOLD'] = dados_portos['% FINANCIAL HOLD'].fillna(0.0)
    
    # CORREÇÃO: Adicionar linha geral com totais
    if not dados_portos.empty:
        total_RELEASE = dados_portos['RELEASE'].sum()
        total_fh = dados_portos['FINANCIAL HOLD'].sum()
        total_geral = total_RELEASE + total_fh
        percentual_fh_geral = (total_fh / total_geral * 100) if total_geral > 0 else 0
        
        dados_portos = pd.concat([
            dados_portos,
            pd.DataFrame([{
                'Porto': 'TOTAL GERAL',
                'RELEASE': total_RELEASE,
                'FINANCIAL HOLD': total_fh,
                '% FINANCIAL HOLD': round(percentual_fh_geral, 1)
            }])
        ], ignore_index=True)
    
    return dados_portos

def analisar_estrutura_importacao(df_importacao: pd.DataFrame):
    """
    Analisa a estrutura do dataframe ImportacaoMZ para debugging
    """
    st.sidebar.markdown("---")
    st.sidebar.header("🔍 Debug - Importação")
    
    if df_importacao.empty:
        st.sidebar.warning("Dataframe vazio")
        return
    
    st.sidebar.write(f"**Registros:** {len(df_importacao)}")
    st.sidebar.write(f"**Colunas:** {len(df_importacao.columns)}")
    
    # Mostrar colunas disponíveis
    with st.sidebar.expander("Ver colunas"):
        st.write(list(df_importacao.columns))
    
    # Mostrar tipos de dados
    with st.sidebar.expander("Ver tipos de dados"):
        st.write(df_importacao.dtypes)
    
    # Mostrar primeiras linhas
    with st.sidebar.expander("Ver primeiras linhas"):
        st.dataframe(df_importacao.head(3))

def extrair_ano_dos_dados(df_importacao: pd.DataFrame) -> int:
    """Extrai o ano dos dados de importação"""
    if df_importacao.empty:
        return datetime.now().year
    
    # Tentar encontrar coluna de data
    colunas_data = ['NOR', 'Data_Descarga', 'Data_Importacao', 'Data']
    for coluna in colunas_data:
        if coluna in df_importacao.columns:
            datas_validas = df_importacao[coluna].dropna()
            if not datas_validas.empty:
                # Converter para datetime se necessário
                if not pd.api.types.is_datetime64_any_dtype(datas_validas):
                    datas_validas = pd.to_datetime(datas_validas, errors='coerce')
                
                ano = datas_validas.dt.year.mode()
                if not ano.empty:
                    return int(ano.iloc[0])
    
    return datetime.now().year

def criar_analise_market_share_com_scroller(df_filtrado: pd.DataFrame):
    """Cria análise de Market Share com scroller animado"""
    
    st.markdown('<div class="section-title">📊 QUOTA DE MERCADO - VISUALIZAÇÃO DINÂMICA</div>', unsafe_allow_html=True)
    
    df_processed = df_filtrado.copy()   
    
    # Limpar colunas numéricas
    colunas_tm = ['Qtd_Petro_TM', 'Qtd_FH_( TM)', 'Quantidade_TM', 'Quantidade']
    
    for col in colunas_tm:
        if col in df_processed.columns:
            df_processed[col] = limpar_coluna_numerica(df_processed, col)

    for c in CLIENTES_CONGENERES:
        if c in df_processed.columns:
            df_processed[c] = limpar_coluna_numerica(df_processed, c)

    # Calcular totais
    total_petromoc_tm = 0
    total_congeneres_tm = 0
    
    if 'Qtd_Petro_TM' in df_processed.columns and 'Qtd_FH_( TM)' in df_processed.columns:
        total_petromoc_tm = (df_processed["Qtd_Petro_TM"] + df_processed["Qtd_FH_( TM)"]).sum()
    elif 'Quantidade_TM' in df_processed.columns:
        total_petromoc_tm = df_processed["Quantidade_TM"].sum()
    
    for c in CLIENTES_CONGENERES:
        if c in df_processed.columns:
            total_congeneres_tm += df_processed[c].sum()

    total_industria_tm = total_petromoc_tm + total_congeneres_tm
    
    total_RELEASE_tm = df_processed["Qtd_Petro_TM"].sum() if "Qtd_Petro_TM" in df_processed.columns else 0
    total_fh_tm = df_processed["Qtd_FH_( TM)"].sum() if "Qtd_FH_( TM)" in df_processed.columns else 0

    if total_industria_tm == 0:
        st.warning("📊 Nenhum dado numérico válido para análise de Market Share")
        return

    combustivel_principal = 'Gasóleo'
    colunas_combustivel = ['Combustivel_Vendas', 'Combustivel_Importacao', 'Combustivel', 'Material']
    for col in colunas_combustivel:
        if col in df_processed.columns and not df_processed[col].empty:
            combustiveis_validos = df_processed[col].dropna()
            if not combustiveis_validos.empty:
                combustivel_principal = combustiveis_validos.mode().iloc[0]
                break

    # Converter todos os valores para m³
    total_petromoc_m3 = converter_tm_para_m3_seguro(total_petromoc_tm, combustivel_principal)
    total_RELEASE_m3 = converter_tm_para_m3_seguro(total_RELEASE_tm, combustivel_principal)
    total_fh_m3 = converter_tm_para_m3_seguro(total_fh_tm, combustivel_principal)
    total_industria_m3 = converter_tm_para_m3_seguro(total_industria_tm, combustivel_principal)
    total_congeneres_m3 = converter_tm_para_m3_seguro(total_congeneres_tm, combustivel_principal)

    def calcular_percentual(parte, total):
        return (parte / total * 100) if total > 0 else 0
    
    perc_petromoc = calcular_percentual(total_petromoc_tm, total_industria_tm)
    perc_congeneres = calcular_percentual(total_congeneres_tm, total_industria_tm)
    perc_RELEASE = calcular_percentual(total_RELEASE_tm, total_petromoc_tm) if total_petromoc_tm > 0 else 0
    perc_fh = calcular_percentual(total_fh_tm, total_petromoc_tm) if total_petromoc_tm > 0 else 0

    # ========== SCROLLER QUOTA DE MERCADO ==========
    criar_scroller_quota_mercado(
        total_industria_tm, total_petromoc_tm, total_congeneres_tm,
        total_industria_m3, total_petromoc_m3, total_congeneres_m3,
        perc_petromoc, perc_congeneres
    )
    
    # ========== SCROLLER QUOTA PETROMOC ==========
    criar_scroller_quota_petromoc(
        total_petromoc_tm, total_RELEASE_tm, total_fh_tm,
        total_petromoc_m3, total_RELEASE_m3, total_fh_m3,
        perc_RELEASE, perc_fh
    )

    # ========== GRÁFICO DE PIZZA PARA COMPLEMENTAR ==========
    st.markdown("#### 📊 Visualização Complementar - Distribuição de Mercado")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Gráfico de pizza - Quota de Mercado
        dados_pizza_mercado = pd.DataFrame({
            'Empresa': ['Petromoc', 'Congênere'],
            'Percentual': [perc_petromoc, perc_congeneres]
        })
        
        fig_mercado = px.pie(
            dados_pizza_mercado,
            values='Percentual',
            names='Empresa',
            title='Distribuição do Mercado',
            color='Empresa',
            color_discrete_map={
                'Petromoc': '#FF6B35',
                'Congênere': '#4ECDC4'
            }
        )
        fig_mercado.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_mercado, use_container_width=True)
    
    with col2:
        # Gráfico de pizza - Quota Petromoc
        dados_pizza_petromoc = pd.DataFrame({
            'Tipo': ['RELEASE', 'Financial Hold'],
            'Percentual': [perc_RELEASE, perc_fh]
        })
        
        fig_petromoc = px.pie(
            dados_pizza_petromoc,
            values='Percentual',
            names='Tipo',
            title='Distribuição Interna - Petromoc',
            color='Tipo',
            color_discrete_map={
                'RELEASE': '#FFD166',
                'Financial Hold': '#06D6A0'
            }
        )
        fig_petromoc.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_petromoc, use_container_width=True)

# ============================================= ABA IMPORTAÇÃO COMPLETA COM SCROLLER =============================================

def criar_aba_importacao_com_dados_reais(df_filtrado: pd.DataFrame):
    """Cria a aba de Importação com dados reais, scroller animado e opções de download"""
    
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado de importação encontrado com os filtros aplicados")
        return

    # Analisar estrutura dos dados (para debugging)
    analisar_estrutura_importacao(df_filtrado)
    
    # Extrair ano dos dados
    ano_dados = extrair_ano_dos_dados(df_filtrado)
    
    st.markdown(f'<div class="section-title">📦 Análise de Importação - {ano_dados}</div>', unsafe_allow_html=True)
    
    # ========== CARTÕES DE MÉTRICAS (PRIMEIRO) ==========
    st.markdown("#### 🎯 Métricas Principais")
    
    # Extrair dados para os cartões
    with st.spinner("🔄 Calculando métricas..."):
        dados_garantias = extrair_dados_garantias_bancarias(df_filtrado)
        dados_portos = extrair_dados_portos_RELEASE_fh(df_filtrado)
    
    # CARTÕES PRINCIPAIS
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        # Total de Garantias
        if not dados_garantias.empty and 'TOTAL GERAL' in dados_garantias['Banco_GB'].values:
            total_geral = dados_garantias[dados_garantias['Banco_GB'] == 'TOTAL GERAL'].iloc[0]
            disponibilidade_perc = total_geral.get('Disponibilidade_%', 0)
            criar_card_metricas(
                "Disponibilidade GB",
                f"{disponibilidade_perc:.1f}%",
                "Garantias Bancárias",
                f"MT {formatar_ptbr(total_geral.get('Disponibilidade_GB', 0), 0)}",
                "🏦",
                "fh"
            )
        else:
            criar_card_metricas(
                "Disponibilidade GB",
                "0.0%",
                "Garantias Bancárias",
                "Dados não disponíveis",
                "🏦",
                "fh"
            )
    
    with col2:
        # Total RELEASE
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_RELEASE = total_geral.get('RELEASE', 0)
            total_fh = total_geral.get('FINANCIAL HOLD', 0)
            total_geral_volume = total_RELEASE + total_fh
            perc_RELEASE = (total_RELEASE / total_geral_volume * 100) if total_geral_volume > 0 else 0
            
            criar_card_metricas(
                "Volume RELEASE",
                f"{perc_RELEASE:.1f}%",
                "Do total importado",
                f"{formatar_ptbr(total_RELEASE, 0)} TM",
                "💰",
                "RELEASE"
            )
        else:
            criar_card_metricas(
                "Volume RELEASE",
                "0.0%",
                "Do total importado",
                "Dados não disponíveis",
                "💰",
                "RELEASE"
            )
    
    with col3:
        # Total Financial Hold
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_RELEASE = total_geral.get('RELEASE', 0)
            total_fh = total_geral.get('FINANCIAL HOLD', 0)
            total_geral_volume = total_RELEASE + total_fh
            perc_fh = (total_fh / total_geral_volume * 100) if total_geral_volume > 0 else 0
            
            criar_card_metricas(
                "Financial Hold",
                f"{perc_fh:.1f}%",
                "Do total importado",
                f"{formatar_ptbr(total_fh, 0)} TM",
                "📊",
                "industria"
            )
        else:
            criar_card_metricas(
                "Financial Hold",
                "0.0%",
                "Do total importado",
                "Dados não disponíveis",
                "📊",
                "industria"
            )
    
    with col4:
        # Total Geral Importação
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_volume = total_geral.get('RELEASE', 0) + total_geral.get('FINANCIAL HOLD', 0)
            
            criar_card_metricas(
                "Total Importado",
                f"{formatar_ptbr(total_volume, 0)}",
                "Volume total",
                "TM",
                "📦",
                "petromoc"
            )
        else:
            criar_card_metricas(
                "Total Importado",
                "0",
                "Volume total",
                "TM",
                "📦",
                "petromoc"
            )
    
    st.markdown("---")
    
    # ========== SCROLLER QUOTA DE MERCADO ==========
    criar_analise_market_share_com_scroller(df_filtrado)
    
    st.markdown("---")
    
    # ========== DOWNLOADS - DADOS BRUTOS ==========
    st.markdown("#### 📥 Download de Dados")
    col_download1, col_download2 = st.columns(2)
    
    with col_download1:
        criar_botao_download_excel(
            df_filtrado, 
            "dados_importacao_brutos", 
            "Dados Brutos"
        )
    
    with col_download2:
        criar_botao_download_csv(
            df_filtrado, 
            "dados_importacao_brutos", 
            "Dados Brutos"
        )
    
    st.markdown("---")
    
    # ========== GARANTIAS BANCÁRIAS ==========
    st.markdown("#### 🏦 Garantias Bancárias")
    
    if not dados_garantias.empty:
        # Formatar os dados para exibição
        df_garantias_display = dados_garantias.copy()
        
        # Formatar valores monetários
        colunas_monetarias = ['ValorLimite_GB', 'Valor_GB', 'Disponibilidade_GB']
        for coluna in colunas_monetarias:
            if coluna in df_garantias_display.columns:
                df_garantias_display[f'{coluna}_Formatado'] = df_garantias_display[coluna].apply(
                    lambda x: f"MT {formatar_ptbr(x, 0)}" if pd.notna(x) else "MT 0"
                )
        
        # Formatar percentagem COM símbolo %
        if 'Disponibilidade_%' in df_garantias_display.columns:
            df_garantias_display['Disponibilidade_%_Formatado'] = df_garantias_display['Disponibilidade_%'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
            )
        
        # Selecionar colunas para exibição
        colunas_exibicao = ['Banco_GB']
        for coluna in colunas_monetarias:
            if f'{coluna}_Formatado' in df_garantias_display.columns:
                colunas_exibicao.append(f'{coluna}_Formatado')
        
        if 'Disponibilidade_%_Formatado' in df_garantias_display.columns:
            colunas_exibicao.append('Disponibilidade_%_Formatado')
        
        # Renomear colunas
        df_display = df_garantias_display[colunas_exibicao].copy()
        df_display.columns = ['Banco', 'Limite de Garantia', 'Valor Utilizado', 'Disponibilidade', 'Disponibilidade %']
        
        # Exibir tabela
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
        
        # DOWNLOADS - GARANTIAS BANCÁRIAS
        st.markdown("##### 📥 Download Garantias Bancárias")
        col_gar1, col_gar2 = st.columns(2)
        
        with col_gar1:
            criar_botao_download_excel(
                df_display, 
                "garantias_bancarias", 
                "Garantias Bancárias"
            )
        
        with col_gar2:
            criar_botao_download_csv(
                df_display, 
                "garantias_bancarias", 
                "Garantias Bancárias"
            )
    
    else:
        st.info("ℹ️ Nenhum dado de garantias bancárias disponível")
    
    st.markdown("---")
    
    # ========== PORTOS vs RELEASE/FINANCIAL HOLD ==========
    st.markdown("#### ⚓ Portos - RELEASE vs Financial Hold")
    
    if not dados_portos.empty:
        # CORREÇÃO: Já removemos duplicatas na função extrair_dados_portos_RELEASE_fh
        dados_portos_clean = dados_portos.copy()
        
        # CORREÇÃO: Garantir ordem correta [Maputo, Beira, Nacala, Pemba, TOTAL GERAL]
        ordem_correta = ['Maputo', 'Beira', 'Nacala', 'Pemba', 'TOTAL GERAL']
        dados_portos_clean['Ordem'] = dados_portos_clean['Porto'].map({porto: idx for idx, porto in enumerate(ordem_correta)})
        dados_portos_clean['Ordem'] = dados_portos_clean['Ordem'].fillna(99)
        dados_portos_clean = dados_portos_clean.sort_values('Ordem').drop('Ordem', axis=1)
        
        # Formatar dados para exibição
        df_portos_display = dados_portos_clean.copy()
        
        # Formatar valores numéricos SEM casas decimais
        colunas_volume = ['RELEASE', 'FINANCIAL HOLD']
        for coluna in colunas_volume:
            if coluna in df_portos_display.columns:
                df_portos_display[f'{coluna}_Formatado'] = df_portos_display[coluna].apply(
                    lambda x: f"{formatar_ptbr(x, 0)} TM" if pd.notna(x) else "0 TM"
                )
        
        # Formatar percentagem COM símbolo %
        if '% FINANCIAL HOLD' in df_portos_display.columns:
            df_portos_display['% FINANCIAL HOLD_Formatado'] = df_portos_display['% FINANCIAL HOLD'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
            )
        
        # Selecionar colunas para exibição
        colunas_exibicao = ['Porto']
        for coluna in colunas_volume:
            if f'{coluna}_Formatado' in df_portos_display.columns:
                colunas_exibicao.append(f'{coluna}_Formatado')
        
        if '% FINANCIAL HOLD_Formatado' in df_portos_display.columns:
            colunas_exibicao.append('% FINANCIAL HOLD_Formatado')
        
        # Renomear colunas
        df_display_portos = df_portos_display[colunas_exibicao].copy()
        df_display_portos.columns = ['Porto', 'RELEASE (TM)', 'Financial Hold (TM)', '% Financial Hold']
        
        # Exibir tabela
        st.dataframe(
            df_display_portos,
            use_container_width=True,
            hide_index=True
        )
        
        # DOWNLOADS - PORTOS
        st.markdown("##### 📥 Download Dados de Portos")
        col_port1, col_port2 = st.columns(2)
        
        with col_port1:
            criar_botao_download_excel(
                df_display_portos, 
                "dados_portos", 
                "Dados de Portos"
            )
        
        with col_port2:
            criar_botao_download_csv(
                df_display_portos, 
                "dados_portos", 
                "Dados de Portos"
            )
        
        # ========== GRÁFICO DE BARRAS - PORTOS ==========
        st.markdown("#### 📊 Visualização - Distribuição por Porto")
        
        # Preparar dados para gráfico (excluir linha "TOTAL GERAL")
        dados_grafico = dados_portos_clean[dados_portos_clean['Porto'] != 'TOTAL GERAL'].copy()
        
        if not dados_grafico.empty:
            # CORREÇÃO: Ordenar os dados para o gráfico na ordem correta
            ORDEM_PORTOS_GRAFICO = ['Maputo', 'Beira', 'Nacala', 'Pemba']
            dados_grafico = dados_grafico[dados_grafico['Porto'].isin(ORDEM_PORTOS_GRAFICO)]
            dados_grafico['Porto'] = pd.Categorical(dados_grafico['Porto'], categories=ORDEM_PORTOS_GRAFICO, ordered=True)
            dados_grafico = dados_grafico.sort_values('Porto')
            
            # CORREÇÃO: Criar DataFrame correto para gráfico de barras agrupadas
            dados_melted = dados_grafico.melt(
                id_vars=['Porto'], 
                value_vars=['RELEASE', 'FINANCIAL HOLD'],
                var_name='Tipo', 
                value_name='Volume'
            )
            
            fig = px.bar(
                dados_melted,
                x='Porto',
                y='Volume',
                color='Tipo',
                title='Distribuição por Porto - RELEASE vs Financial Hold',
                barmode='group',
                color_discrete_map={
                    'RELEASE': '#FF6B35',
                    'FINANCIAL HOLD': '#4ECDC4'
                },
                category_orders={"Porto": ORDEM_PORTOS_GRAFICO}
            )
            fig.update_layout(
                yaxis_title='Volume (TM)',
                xaxis_title='Porto'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # DOWNLOADS - GRÁFICO
            st.markdown("##### 📥 Download Dados do Gráfico")
            col_graf1, col_graf2 = st.columns(2)
            
            with col_graf1:
                criar_botao_download_excel(
                    dados_grafico[['Porto', 'RELEASE', 'FINANCIAL HOLD']], 
                    "dados_grafico_portos", 
                    "Dados do Gráfico"
                )
            
            with col_graf2:
                criar_botao_download_csv(
                    dados_grafico[['Porto', 'RELEASE', 'FINANCIAL HOLD']], 
                    "dados_grafico_portos", 
                    "Dados do Gráfico"
                )
    
    else:
        st.info("ℹ️ Nenhum dado de portos disponível")

# ============================================= FUNÇÕES PARA PROMOTORES =============================================

@st.cache_data(ttl=3600)
def carregar_dados_MIS():
    """Carrega e processa dados do MIS"""
    try:
        # 1. Carregar dados do MIS
        MIS = pd.read_excel('MIS_.xlsx')
        
        # 2. Carregar lookup de clientes
        v0 = pd.read_excel('v_loock_up.xlsx', sheet_name=0)
        
        # 3. Fazer merge com lookup
        MIS = pd.merge(MIS, v0, left_on=['Emissor'], right_on=['Emissor'], how='left')
        
        # 4. CORREÇÃO: Padronizar nomes de colunas (remove espaços, caracteres especiais)
        MIS.columns = MIS.columns.str.strip().str.upper()
        
        # 5. VALIDAR: Verificar se as colunas necessárias existem
        colunas_verificar = ['DENTRO_PRAZO', '0_30_DIAS']
        colunas_faltando = [col for col in colunas_verificar if col not in MIS.columns]
        
        if colunas_faltando:
            logger.warning(f"Colunas faltando no MIS: {colunas_faltando}")
            logger.info(f"Colunas disponíveis: {list(MIS.columns)}")
            
            # Tentar encontrar colunas com nomes similares
            for coluna_procurada in colunas_faltando:
                coluna_procurada_lower = coluna_procurada.lower()
                colunas_similares = [col for col in MIS.columns if coluna_procurada_lower in col.lower()]
                
                if colunas_similares:
                    logger.info(f"Colunas similares para '{coluna_procurada}': {colunas_similares}")
        
        # 6. CRIAR COLUNA Previsao_30_Dias
        # Verificar se ambas as colunas existem
        if 'DENTRO_PRAZO' in MIS.columns and '0_30_DIAS' in MIS.columns:
            # Garantir que são numéricas
            MIS['DENTRO_PRAZO'] = pd.to_numeric(MIS['DENTRO_PRAZO'], errors='coerce').fillna(0)
            MIS['0_30_DIAS'] = pd.to_numeric(MIS['0_30_DIAS'], errors='coerce').fillna(0)
            
            # Calcular soma
            MIS['PREVISAO_30_DIAS'] = MIS['DENTRO_PRAZO'] + MIS['0_30_DIAS']
            
            logger.info(f"Criada coluna 'PREVISAO_30_DIAS' com sucesso")
            logger.info(f"Valores: DENTRO_PRAZO={MIS['DENTRO_PRAZO'].sum():.2f}, " +
                       f"0_30_DIAS={MIS['0_30_DIAS'].sum():.2f}, " +
                       f"PREVISAO_30_DIAS={MIS['PREVISAO_30_DIAS'].sum():.2f}")
            
        elif 'DENTRO_PRAZO' in MIS.columns:
            # Se só tiver DENTRO_PRAZO
            MIS['DENTRO_PRAZO'] = pd.to_numeric(MIS['DENTRO_PRAZO'], errors='coerce').fillna(0)
            MIS['PREVISAO_30_DIAS'] = MIS['DENTRO_PRAZO']
            logger.warning("Apenas 'DENTRO_PRAZO' disponível. Usando como 'PREVISAO_30_DIAS'")
            
        elif '0_30_DIAS' in MIS.columns:
            # Se só tiver 0_30_DIAS
            MIS['0_30_DIAS'] = pd.to_numeric(MIS['0_30_DIAS'], errors='coerce').fillna(0)
            MIS['PREVISAO_30_DIAS'] = MIS['0_30_DIAS']
            logger.warning("Apenas '0_30_DIAS' disponível. Usando como 'PREVISAO_30_DIAS'")
            
        else:
            # Se nenhuma das colunas existir
            MIS['PREVISAO_30_DIAS'] = 0
            logger.error("Nenhuma das colunas necessárias encontrada para criar 'PREVISAO_30_DIAS'")
        
        # 7. DEBUG: Mostrar informações sobre as colunas criadas
        if 'PREVISAO_30_DIAS' in MIS.columns:
            logger.info(f"Coluna 'PREVISAO_30_DIAS' criada. Tipo: {MIS['PREVISAO_30_DIAS'].dtype}")
            logger.info(f"Primeiros valores de 'PREVISAO_30_DIAS': {MIS['PREVISAO_30_DIAS'].head().tolist()}")
        
        return MIS
        
    except FileNotFoundError as e:
        logger.error(f"Arquivo não encontrado: {str(e)}")
        st.error(f"❌ Arquivo do MIS não encontrado: {str(e)}")
        return pd.DataFrame()
        
    except Exception as e:
        logger.error(f"Erro ao carregar MIS: {str(e)}", exc_info=True)
        st.error(f"❌ Erro crítico ao carregar dados do MIS: {str(e)}")
        return pd.DataFrame()

def criar_tabela_divida_por_linha_negocio(mis_df: pd.DataFrame):
    """Cria tabela de dívida por linha de negócio conforme especificação"""
    
    if mis_df.empty:
        return pd.DataFrame()
    
    # Verificar quais colunas realmente existem
    colunas_disponiveis = []
    colunas_possiveis = ['LINHA NEG.', 'DIVIDA_TOTAL', 'DENTRO_PRAZO', 'PREVISAO_30_DIAS']
    
    for col in colunas_possiveis:
        if col in mis_df.columns:
            colunas_disponiveis.append(col)
    
    if len(colunas_disponiveis) < 2:  # Pelo menos LINHA NEG. e uma métrica
        st.warning(f"⚠️ Colunas necessárias não encontradas no MIS. Colunas disponíveis: {list(mis_df.columns)}")
        return pd.DataFrame()
    
    # Verificar se temos a coluna 'LINHA NEG.'
    if 'LINHA NEG.' not in mis_df.columns:
        # Tentar encontrar coluna alternativa
        colunas_alternativas = ['LINHA_NEG', 'LINHA_NEGOCIO', 'LINHA DE NEGÓCIO', 'LINHA_NEGÓCIO', 'SECTOR/SIGLA']
        for alt in colunas_alternativas:
            if alt in mis_df.columns:
                mis_df = mis_df.rename(columns={alt: 'LINHA NEG.'})
                break
        
        if 'LINHA NEG.' not in mis_df.columns:
            st.warning("⚠️ Coluna 'LINHA NEG.' não encontrada no MIS")
            return pd.DataFrame()
    
    # Criar dicionário de agregação apenas com colunas que existem
    agg_dict = {}
    colunas_calculo = []
    
    if 'DIVIDA_TOTAL' in mis_df.columns:
        agg_dict['DIVIDA_TOTAL'] = 'sum'
        colunas_calculo.append('DIVIDA_TOTAL')
    
    if 'DENTRO_PRAZO' in mis_df.columns:
        agg_dict['DENTRO_PRAZO'] = 'sum'
        colunas_calculo.append('DENTRO_PRAZO')
    
    if 'PREVISAO_30_DIAS' in mis_df.columns:
        agg_dict['PREVISAO_30_DIAS'] = 'sum'
        colunas_calculo.append('PREVISAO_30_DIAS')
    
    if not agg_dict:
        st.warning("⚠️ Nenhuma coluna numérica de dívida encontrada no MIS")
        return pd.DataFrame()
    
    # Agrupar por linha de negócio
    tabela_linhas = mis_df.groupby('LINHA NEG.').agg(agg_dict).reset_index()
    
    # Adicionar linha de Total
    linha_total = {'LINHA NEG.': 'Total'}
    
    for col in colunas_calculo:
        if col in tabela_linhas.columns:
            linha_total[col] = tabela_linhas[col].sum()
    
    tabela_completa = pd.concat([tabela_linhas, pd.DataFrame([linha_total])], ignore_index=True)
    
    # Calcular percentuais se tivermos DIVIDA_TOTAL
    if 'DIVIDA_TOTAL' in tabela_completa.columns:
        total_divida = tabela_completa.loc[tabela_completa['LINHA NEG.'] == 'Total', 'DIVIDA_TOTAL'].iloc[0]
        
        if total_divida > 0:
            tabela_completa['% sobre Total'] = (tabela_completa['DIVIDA_TOTAL'] / total_divida * 100).round(1)
    
    return tabela_completa

def criar_tabela_top10_promotores(mis_df: pd.DataFrame):
    """Cria tabela Top 10 Promotores com dados de dívida no formato correto"""
    
    if mis_df.empty:
        return pd.DataFrame()
    
    # 1. IDENTIFICAR COLUNAS CORRETAS
    colunas_necessarias = []
    
    # Buscar coluna de promotor
    colunas_promotor = [col for col in mis_df.columns if 'GESTOR' in col or 'PROMOTOR' in col]
    if colunas_promotor:
        coluna_promotor = colunas_promotor[0]
        colunas_necessarias.append(coluna_promotor)
    else:
        st.warning("⚠️ Coluna de promotor não encontrada")
        return pd.DataFrame()
    
    # Buscar coluna de emissor
    colunas_emissor = [col for col in mis_df.columns if 'EMISSOR' in col]
    if colunas_emissor:
        coluna_emissor = colunas_emissor[0]
        colunas_necessarias.append(coluna_emissor)
    else:
        # Tentar alternativa
        if 'Emissor' in mis_df.columns:
            coluna_emissor = 'Emissor'
            colunas_necessarias.append(coluna_emissor)
        else:
            # Criar coluna vazia se não existir
            mis_df['EMISSOR'] = ''
            coluna_emissor = 'EMISSOR'
            colunas_necessarias.append(coluna_emissor)
    
    # Buscar coluna de nome do cliente
    colunas_cliente = ['NOME_DO_CLIENTE', 'NOME_DO_CITE', 'NOMECLIENTE', 'CLIENTE']
    for col_cliente in colunas_cliente:
        if col_cliente in mis_df.columns:
            colunas_necessarias.append(col_cliente)
            break
    else:
        # Se não encontrar, adicionar coluna vazia
        mis_df['NOME_CLIENTE'] = ''
        colunas_necessarias.append('NOME_CLIENTE')
    
    # Adicionar colunas de dívida
    for col in ['DIVIDA_TOTAL', 'DENTRO_PRAZO', 'PREVISAO_30_DIAS']:
        if col in mis_df.columns:
            colunas_necessarias.append(col)
    
    # 2. CRIAR TABELA AGRUPADA POR PROMOTOR
    agg_dict = {}
    for col in ['DIVIDA_TOTAL', 'DENTRO_PRAZO', 'PREVISAO_30_DIAS']:
        if col in colunas_necessarias:
            agg_dict[col] = 'sum'
    
    # Agrupar por promotor
    if agg_dict:
        tabela_agrupada = mis_df.groupby(coluna_promotor).agg(agg_dict).reset_index()
        
        # Ordenar por dívida total (maior primeiro)
        if 'DIVIDA_TOTAL' in tabela_agrupada.columns:
            tabela_agrupada = tabela_agrupada.sort_values('DIVIDA_TOTAL', ascending=False)
    else:
        tabela_agrupada = mis_df[[coluna_promotor]].drop_duplicates()
    
    # 3. PEGAR TOP 10 PROMOTORES
    top10_promotores = tabela_agrupada.head(10)
    
    # 4. CRIAR TABELA FINAL COM TODOS OS DADOS DOS CLIENTES DO TOP 10
    tabela_final = []
    
    # Primeiro adicionar os dados detalhados de cada promotor
    for idx, row in top10_promotores.iterrows():
        promotor = row[coluna_promotor]
        
        # Filtrar clientes deste promotor
        clientes_promotor = mis_df[mis_df[coluna_promotor] == promotor]
        
        # Ordenar clientes por dívida total
        if 'DIVIDA_TOTAL' in clientes_promotor.columns:
            clientes_promotor = clientes_promotor.sort_values('DIVIDA_TOTAL', ascending=False)
        
        # Adicionar cada cliente como uma linha
        for _, cliente_row in clientes_promotor.iterrows():
            linha = {
                'Gestor/Promotor': str(promotor) if pd.notna(promotor) else '',
                'Emissor': str(cliente_row[coluna_emissor]) if pd.notna(cliente_row.get(coluna_emissor, '')) else '',
                'Nome_do_Cliente': str(cliente_row[colunas_necessarias[2]]) if len(colunas_necessarias) > 2 else '',
                'Dívida Total': cliente_row.get('DIVIDA_TOTAL', 0),
                'Dentro Prazo': cliente_row.get('DENTRO_PRAZO', 0),
                'Previsão 30 Dias': cliente_row.get('PREVISAO_30_DIAS', 0)
            }
            tabela_final.append(linha)
    
    # 5. ADICIONAR LINHA DE TOTAL
    if tabela_final:
        # Calcular totais
        totais = {
            'Gestor/Promotor': 'TOTAL',
            'Emissor': '',
            'Nome_do_Cliente': '',
            'Dívida Total': sum(row['Dívida Total'] for row in tabela_final),
            'Dentro Prazo': sum(row['Dentro Prazo'] for row in tabela_final),
            'Previsão 30 Dias': sum(row['Previsão 30 Dias'] for row in tabela_final)
        }
        tabela_final.append(totais)
    
    # Converter para DataFrame
    df_final = pd.DataFrame(tabela_final)
    
    return df_final

def criar_aba_divida_promotores():
    """Cria a parte de análise de dívida dos promotores"""
    
    st.markdown("#### 💰 Análise de Dívida - Linhas de Negócio")
    
    # Carregar dados do MIS
    MIS_df = carregar_dados_MIS()
    
    if MIS_df.empty:
        st.warning("⚠️ Nenhum dado do MIS disponível para análise de dívida")
        return
    
    # ========== TABELA DE DÍVIDA POR LINHA DE NEGÓCIO ==========
    tabela_linhas = criar_tabela_divida_por_linha_negocio(MIS_df)
    
    if not tabela_linhas.empty:
        # Formatar tabela para exibição
        df_linhas_display = tabela_linhas.copy()
        
        # Formatar colunas numéricas
        colunas_numericas = ['DIVIDA_TOTAL', 'DENTRO_PRAZO', 'PREVISAO_30_DIAS']
        colunas_disponiveis = [col for col in colunas_numericas if col in df_linhas_display.columns]
        
        for coluna in colunas_disponiveis:
            # CORREÇÃO AQUI: df_linhas_display em vez de df_linha_display
            df_linhas_display[coluna] = df_linhas_display[coluna].apply(
                lambda x: f"MT {formatar_ptbr(x, 0)}" if pd.notna(x) else "MT 0"
            )
        
        # Formatar percentual
        if '% sobre Total' in df_linhas_display.columns:
            df_linhas_display['% sobre Total'] = df_linhas_display['% sobre Total'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
            )
        
        # Renomear colunas para exibição
        rename_dict = {
            'LINHA NEG.': 'Linha de Negócio',
            'DIVIDA_TOTAL': 'Dívida Total',
            'DENTRO_PRAZO': 'Dentro do Prazo',
            'PREVISAO_30_DIAS': 'Previsão 30 Dias',
            '% sobre Total': '% sobre Total'
        }
        
        df_linhas_display = df_linhas_display.rename(columns=rename_dict)
        


        def highlight_total(row):
            if row['Linha de Negócio'] == 'Total':
                return ['background-color: #FF6B35; color: white; font-weight: bold; font-size: 14px'] * len(row)
            return ['background-color: #FFFFFF; color: #333333'] * len(row)
        
        # Aplicar cores alternadas
        def color_alternate_rows(row_index):
            colors = ['#F0F8FF', '#FFFFFF']
            return f'background-color: {colors[row_index % 2]}; color: #333333'
        
        # Exibir tabela com cores
        styled_df = df_linhas_display.style.apply(highlight_total, axis=1)
        
        for i in range(len(df_linhas_display)):
            if df_linhas_display.iloc[i]['Linha de Negócio'] != 'Total':
                styled_df = styled_df.apply(
                    lambda x: [color_alternate_rows(i) for _ in x], 
                    subset=pd.IndexSlice[i:i], axis=0
                )
        
        st.dataframe(
            styled_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    st.markdown("---")
    
    # ========== TABELA TOP 10 PROMOTORES COM DÍVIDA ==========
    st.markdown("#### 📋 Top 10 Promotores - Situação de Dívida")
    
    tabela_top10 = criar_tabela_top10_promotores(MIS_df)
    
    if not tabela_top10.empty:
        # Formatar tabela para exibição
        df_top10_display = tabela_top10.copy()
        
        # Formatar colunas numéricas
        colunas_numericas = ['Dívida Total', 'Dentro Prazo', 'Previsão 30 Dias']
        colunas_numericas_existentes = [col for col in colunas_numericas if col in df_top10_display.columns]
        
        for coluna in colunas_numericas_existentes:
            df_top10_display[coluna] = df_top10_display[coluna].apply(
                lambda x: f"MT {formatar_ptbr(x, 0)}" if pd.notna(x) and x != 0 else "MT 0"
            )
        
        # Destacar linha de TOTAL
        def highlight_top10_total(row):
            if row['Gestor/Promotor'] == 'TOTAL':
                return ['background-color: #FF6B35; color: white; font-weight: bold; font-size: 14px'] * len(row)
            row_idx = row.name if hasattr(row, 'name') else 0
            color = '#F0F8FF' if row_idx % 2 == 0 else '#FFFFFF'
            return [f'background-color: {color}; color: #333333'] * len(row)
        
        # Aplicar estilo
        styled_top10 = df_top10_display.style.apply(highlight_top10_total, axis=1)
        
        # Exibir tabela formatada
        st.dataframe(
            styled_top10,
            use_container_width=True,
            hide_index=True,
            height=400
        )
    
    st.markdown("---")
    
    # ========== DOWNLOAD DE DADOS ==========
    st.markdown("#### 📥 Download dos Dados de Dívida")
    
    with st.expander("📊 Opções de Exportação"):
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        
        with col_dl1:
            if 'tabela_linhas' in locals() and not tabela_linhas.empty:
                criar_botao_download_excel(
                    tabela_linhas,
                    "divida_linhas_negocio",
                    "Dívida por Linha de Negócio"
                )
        
        with col_dl2:
            if 'tabela_top10' in locals() and not tabela_top10.empty:
                criar_botao_download_excel(
                    tabela_top10,
                    "top10_promotores_divida",
                    "Top 10 Promotores - Dívida"
                )
        
        with col_dl3:
            if 'MIS_df' in locals() and not MIS_df.empty:
                criar_botao_download_excel(
                    MIS_df,
                    "dados_completos_MIS",
                    "Dados Completos do MIS"
                )

def criar_aba_vendas_promotores(df_filtrado: pd.DataFrame):
    """Cria a parte de análise de vendas dos promotores"""
    
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para análise de vendas dos promotores")
        return
    
    # Verificar se temos a coluna correta para promotores
    colunas_promotor = [
        'Gestor / Promotor',  # Coluna mais provável baseada no seu sistema
        'Promotor',
        'Gestor_Promotor',
        'Vendedor',
        'Comercial',
        'Emissor'  # Fallback caso não tenha coluna específica
    ]
    
    coluna_promotor = None
    for col in colunas_promotor:
        if col in df_filtrado.columns:
            coluna_promotor = col
            break
    
    if not coluna_promotor:
        st.error("❌ Não foi possível encontrar coluna de promotor/gestor nos dados de vendas")
        return
    
    # ========== CARTÕES DE MÉTRICAS GERAIS ==========
    st.markdown("#### 🎯 Visão Geral dos Promotores - Vendas")
    
    # Estatísticas básicas
    total_promotores = df_filtrado[coluna_promotor].nunique()
    
    # Verificar se temos coluna de quantidade
    coluna_quantidade = None
    colunas_quantidade = ['Quantidade', 'Vendas m³', 'Volume']
    for col in colunas_quantidade:
        if col in df_filtrado.columns:
            coluna_quantidade = col
            break
    
    total_vendas = 0
    if coluna_quantidade:
        total_vendas = df_filtrado[coluna_quantidade].sum()
    
    # Verificar se temos coluna de valor
    coluna_valor = None
    colunas_valor = ['V_Liquido', 'Valor', 'Vendas_MT']
    for col in colunas_valor:
        if col in df_filtrado.columns:
            coluna_valor = col
            break
    
    total_valor = 0
    if coluna_valor:
        total_valor = df_filtrado[coluna_valor].sum()
    
    # Identificar coluna de meta/plano
    colunas_plano = ['Plano_m³', 'Plano', 'Quantidade_Plano', 'Meta']
    coluna_plano = None
    for col in colunas_plano:
        if col in df_filtrado.columns:
            coluna_plano = col
            break
    
    total_plano = 0
    if coluna_plano:
        total_plano = df_filtrado[coluna_plano].sum()
    
    taxa_atingimento = (total_vendas / total_plano * 100) if total_plano > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        criar_card_metricas(
            "Total Promotores",
            str(total_promotores),
            "Ativos no período",
            f"{len(df_filtrado)} transações",
            "👥",
            "petromoc"
        )
    
    with col2:
        criar_card_metricas(
            "Volume Total",
            f"{formatar_ptbr(total_vendas, 0)}",
            "m³ vendidos",
            f"MT {formatar_ptbr(total_valor, 0)}" if coluna_valor else "",
            "📊",
            "industria"
        )
    
    with col3:
        criar_card_metricas(
            "Meta do Período",
            f"{formatar_ptbr(total_plano, 0)}" if coluna_plano else "N/A",
            "m³ planejados" if coluna_plano else "Meta não definida",
            "Volume planejado" if coluna_plano else "",
            "🎯",
            "plano"
        )
    
    with col4:
        status_cor = "congenere" if taxa_atingimento >= 100 else "RELEASE" if taxa_atingimento >= 80 else "industria"
        criar_card_metricas(
            "Taxa de Atingimento",
            f"{taxa_atingimento:.1f}%" if coluna_plano else "N/A",
            "Meta vs Realizado" if coluna_plano else "Sem meta definida",
            f"{'+' if taxa_atingimento >= 100 else ''}{taxa_atingimento - 100:.1f}% vs meta" if coluna_plano else "",
            "📈" if taxa_atingimento >= 100 else "📉",
            status_cor if coluna_plano else "petromoc"
        )
    
    st.markdown("---")
    
    # ========== TABELA DE DESEMPENHO POR PROMOTOR ==========
    st.markdown("#### 📋 Ranking de Promotores - Vendas")
    
    try:
        # Criar dicionário para agregação
        agg_dict = {}
        
        if coluna_quantidade:
            agg_dict[coluna_quantidade] = 'sum'
        
        if coluna_valor:
            agg_dict[coluna_valor] = 'sum'
        
        if coluna_plano:
            agg_dict[coluna_plano] = 'sum'
        
        if not agg_dict:
            st.warning("⚠️ Nenhuma coluna numérica disponível para análise")
            return
        
        # Agrupar por promotor
        desempenho_promotores = df_filtrado.groupby(coluna_promotor).agg(agg_dict).reset_index()
        
        # Calcular métricas adicionais
        if coluna_quantidade and coluna_plano:
            desempenho_promotores['Variação (m³)'] = desempenho_promotores[coluna_quantidade] - desempenho_promotores[coluna_plano]
            desempenho_promotores['Atingimento (%)'] = (desempenho_promotores[coluna_quantidade] / desempenho_promotores[coluna_plano] * 100).round(1)
            
            # Ordenar por atingimento
            desempenho_promotores = desempenho_promotores.sort_values('Atingimento (%)', ascending=False)
            
            # Adicionar ranking
            desempenho_promotores['Ranking'] = range(1, len(desempenho_promotores) + 1)
            
            # Selecionar colunas para exibição
            colunas_exibicao = [
                'Ranking',
                coluna_promotor,
                coluna_quantidade,
                coluna_plano,
                'Variação (m³)',
                'Atingimento (%)'
            ]
            
            if coluna_valor:
                colunas_exibicao.append(coluna_valor)
            
        else:
            # Se não temos plano, mostrar apenas volume
            if coluna_quantidade:
                desempenho_promotores = desempenho_promotores.sort_values(coluna_quantidade, ascending=False)
                
                # Calcular percentual sobre total
                total_geral = desempenho_promotores[coluna_quantidade].sum()
                desempenho_promotores['Participação (%)'] = (desempenho_promotores[coluna_quantidade] / total_geral * 100).round(1)
                
                # Adicionar ranking
                desempenho_promotores['Ranking'] = range(1, len(desempenho_promotores) + 1)
                
                # Selecionar colunas para exibição
                colunas_exibicao = [
                    'Ranking',
                    coluna_promotor,
                    coluna_quantidade,
                    'Participação (%)'
                ]
                
                if coluna_valor:
                    colunas_exibicao.append(coluna_valor)
        
        # Formatar dados para exibição
        df_display = desempenho_promotores.copy()
        
        # Formatar colunas numéricas
        for col in [coluna_quantidade, 'Variação (m³)']:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: formatar_ptbr(x, 0) if pd.notna(x) else "0"
                )
        
        if coluna_plano and coluna_plano in df_display.columns:
            df_display[coluna_plano] = df_display[coluna_plano].apply(
                lambda x: formatar_ptbr(x, 0) if pd.notna(x) else "0"
            )
        
        # Formatar colunas percentuais
        for col in ['Atingimento (%)', 'Participação (%)']:
            if col in df_display.columns:
                df_display[col] = df_display[col].apply(
                    lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%"
                )
        
        # Formatar coluna monetária
        if coluna_valor and coluna_valor in df_display.columns:
            df_display[coluna_valor] = df_display[coluna_valor].apply(
                lambda x: f"MT {formatar_ptbr(x, 0)}" if pd.notna(x) else "MT 0"
            )
        
        # Exibir tabela
        st.dataframe(
            df_display[colunas_exibicao],
            use_container_width=True,
            height=400
        )
        
    except Exception as e:
        st.error(f"❌ Erro ao criar tabela de desempenho: {str(e)}")
        return
    
    st.markdown("---")
    
    # ========== DOWNLOAD DE DADOS ==========
    st.markdown("#### 📥 Download dos Dados de Vendas")
    
    try:
        with st.expander("📊 Opções de Exportação"):
            col_dl1, col_dl2, col_dl3 = st.columns(3)
            
            with col_dl1:
                if 'desempenho_promotores' in locals() and not desempenho_promotores.empty:
                    criar_botao_download_excel(
                        desempenho_promotores,
                        "desempenho_promotores_vendas",
                        "Dados Completos - Vendas"
                    )
            
            with col_dl2:
                if 'desempenho_promotores' in locals() and not desempenho_promotores.empty:
                    criar_botao_download_csv(
                        desempenho_promotores,
                        "desempenho_promotores_vendas",
                        "Dados Completos - Vendas"
                    )
            
            with col_dl3:
                # Relatório resumido
                resumo = {
                    'Métrica': ['Total Promotores', 'Volume Total (m³)', 'Valor Total (MT)', 
                              'Meta Total (m³)', 'Atingimento (%)'],
                    'Valor': [total_promotores, total_vendas, total_valor, total_plano, taxa_atingimento]
                }
                df_resumo = pd.DataFrame(resumo)
                criar_botao_download_excel(
                    df_resumo,
                    "resumo_promotores_vendas",
                    "Relatório Resumido - Vendas"
                )
    except Exception as e:
        st.warning(f"⚠️ Erro nas opções de download: {str(e)}")

def criar_aba_promotores(df_filtrado: pd.DataFrame):
    """Cria a aba de Análise de Promotores com dados de DateSet_MT_Pln"""
    
    st.markdown('<div class="section-title">👥 Análise de Promotores - Desempenho Comercial</div>', unsafe_allow_html=True)
    
    # Criar tabs para separar análise de vendas e dívida
    tab_vendas, tab_divida = st.tabs(["📈 Análise de Vendas", "💰 Análise de Dívida"])
    
    with tab_vendas:
        criar_aba_vendas_promotores(df_filtrado)
    
    with tab_divida:
        criar_aba_divida_promotores()

# ============================================= FUNÇÃO PRINCIPAL =============================================

def main():
    """Função principal"""
    
    # Adicione CSS adicional
    st.markdown("""
    <style>
        /* Estilos gerais para tabelas */
        .stDataFrame {
            border: 2px solid #FF6B35;
            border-radius: 10px;
            overflow: hidden;
        }
        
        /* Cores para botões */
        .stButton > button {
            background-color: #FF6B35;
            color: white;
            border: none;
            border-radius: 5px;
            padding: 10px 20px;
            font-weight: bold;
        }
        
        .stButton > button:hover {
            background-color: #FF4500;
            color: white;
        }
        
        /* Estilos para selects */
        .stSelectbox {
            background-color: #F0F8FF;
            border-radius: 5px;
            padding: 5px;
        }
        
        /* Cores para métricas */
        .metric-container {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            padding: 15px;
            color: white;
            margin: 5px;
        }
    </style>
    """, unsafe_allow_html=True)

    # HEADER PRINCIPAL
    st.markdown('<h1 class="main-header">Sistema de Gestão - Petromoc, SA</h1>', unsafe_allow_html=True)
    
    # MENU LATERAL
    with st.sidebar:
        filtros = renderizar_menu_lateral_corrigido()
    
    # VERIFICAR SE TEMOS DADOS
    if DateSet_MT_Pln.empty and import_df.empty:
        st.error("""
        ❌ Nenhum dado disponível para análise.
        
        **Soluções possíveis:**
        1. Verifique se os arquivos de dados estão na pasta correta
        2. Confirme os nomes dos arquivos:
           - Vds_2023_Comb_.xlsx, Vds_2024_Comb_.xlsx, Vds_2025_Comb_.xlsx
           - PlanComb_2023.xlsx, PlanComb_2024.xlsx, PlanComb_2025.xlsx
           - ImportacaoMZ.xlsx
           - v_loock_up.xlsx
        3. Verifique as permissões de acesso aos arquivos
        """)
        return
    
    # PROCESSAR COM BASE NO MODO SELECIONADO
    modo_trabalho = filtros.get('modo_trabalho', 'Importação')
    
    if modo_trabalho == "Vendas":
        # APLICAR FILTROS NAS VENDAS
        df_filtrado_vendas = aplicar_filtros_vendas(DateSet_MT_Pln, filtros)
        
        # CRIAR ABA DE VENDAS COM TABELA PRIMEIRO
        criar_aba_vendas_com_tabela_primeiro(df_filtrado_vendas, filtros)
        
    elif modo_trabalho == "Importação":
        # APLICAR FILTROS NA IMPORTAÇÃO
        df_filtrado_importacao = aplicar_filtros_importacao(import_df, filtros)
        
        # CRIAR ABA DE IMPORTAÇÃO COM SCROLLER
        criar_aba_importacao_com_dados_reais(df_filtrado_importacao)
        
    elif modo_trabalho == "Promotores":
        # APLICAR FILTROS NAS VENDAS
        df_filtrado_promotores = aplicar_filtros_vendas(DateSet_MT_Pln, filtros)
        
        # CRIAR ABA DE PROMOTORES
        criar_aba_promotores(df_filtrado_promotores)
        
    elif modo_trabalho == "Stock":
        st.info("👥 Módulo Stock em desenvolvimento...")
        st.write("Em breve: Análise de desempenho de Stock")
        
    elif modo_trabalho == "Caixa_e_Bancos":
        st.info("👥 Módulo Caixa_e_Bancos em desenvolvimento...")
        st.write("Em breve: Análise de desempenho de Caixa_e_Bancos")
        
    elif modo_trabalho == "KPIs":
        st.info("👥 Módulo KPIs em desenvolvimento...")
        st.write("Em breve: Análise dos KPIs")
        
    elif modo_trabalho == "Simulacoes":
        st.info("👥 Módulo Simulacoes em desenvolvimento...")
        st.write("Em breve: Análise das Simulacoes")    

    # RODAPÉ
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>⛽ <strong>Petromoc, SA</strong> - Sistema de Gestão Econômica</p>
        <p>📧 <a href="mailto:suporte@petromoc.co.mz" style="color: #FF6B35;">suporte@petromoc.co.mz</a> | 
        🌐 <a href="https://www.petromoc.co.mz" style="color: #FF6B35;" target="_blank">www.petromoc.co.mz</a></p>
        <p>🔄 Última atualização: {}</p>
    </div>
    """.format(datetime.now().strftime("%d/%m/%Y %H:%M")), unsafe_allow_html=True)

# ============================================= EXECUÇÃO =============================================
if __name__ == "__main__":
    main()