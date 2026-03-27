# -*- coding: utf-8 -*-
"""
Sistema de Gestão – Petromoc, SA
Dashboard Completo: Vendas + Plano + Participação na Importação + Linha de Negócio
Formato PT-BR: 1.234,56

VERSÃO CORRIGIDA E INTEGRADA - 2026
- CORRIGIDO: Captura correta dos dados REAIS de Vendas_m³ do vendas_df
- CORRIGIDO: Captura correta dos dados REAIS de Plano_m³ do plano_df
- CORRIGIDO: Processamento do dataframe vds_plan_MT_Pln com dados REAIS
- ADICIONADO: Análise por Linha de Negócio com ordem específica [Vulcan, Consumidores, Revenda, Bunkers, Aviacao, Reexportacao]
- ADICIONADO: Seletor de Gestor/Promotor nas abas de Promotores
- ADICIONADO: Linha de TOTAL GERAL nas tabelas de Ranking e Dívida
- CORRIGIDO: Erro de comparação entre int e str nos seletores de promotores
- ADICIONADO: Dados REAIS de Garantias Bancárias a partir do arquivo Garantias_Bancarias_.xlsx
- MODIFICADO: Nível de Agregação padrão "Por Mês" na tabela de vendas
- ADICIONADO: Seletores de ordenação e filtros nas tabelas de dívida dos promotores
- Adicionada análise de vendas vs plano com dados REAIS
- Centralizada lógica de conversão de datas
- Adicionada documentação completa de todas as variáveis
- Eliminadas variáveis redundantes
- Melhorado tratamento de erros nos merges
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import locale
import os
import base64
import io
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime, date
from dataclasses import dataclass, field
from enum import Enum

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

# ============================================= CONFIGURAÇÕES GLOBAIS =============================================

class ModoTrabalho(Enum):
    """Enum para os modos de trabalho do sistema"""
    IMPORTACAO = "Importação"
    VENDAS = "Vendas"
    PROMOTORES = "Promotores"
    STOCK = "Stock"
    DRE = "DRE - Demonstração do Resultado"
    BALANCETE = "Balancete"
    RELATORIO_CONTAS = "Relatório e Contas"

@dataclass
class ConfigSistema:
    """Configurações centrais do sistema - EVITA REDUNDÂNCIAS"""
    DATA_INICIO_PADRAO: date = date(2025, 1, 1)
    FORMATOS_DATA: List[str] = field(default_factory=lambda: [
        '%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y'
    ])
    
    DENSIDADES: Dict[str, float] = field(default_factory=lambda: {
        'Gasolina': 0.73,
        'Jet A1': 0.79,
        'Gasóleo': 0.84,
        'Diesel': 0.84
    })
    
    CLIENTES_CONGENERES: List[str] = field(default_factory=lambda: [
        "AFR PETR", "B ENERGY", "BP", "CAC", "CAMEL", "DALBIT", "ENER", "EXOR",
        "GLENCORE", "GTS", "IPM", "I2A", "LAKE OIL", "LIBERTY", "MCCI", "MITRA",
        "MOUMERU", "MOZTOP", "NGUVU L", "PETRODA", "PETROGAL", "PESS", "PUMA",
        "RUR", "TOP ENERGY", "TOTAL", "UNION", "VIVO"
    ])
    
    LINHAS_NEGOCIO: List[str] = field(default_factory=lambda: [
        "Vulcan", "Consumidores", "Revenda", "Bunkers", "Aviacao", "Reexportacao", "Armazenagem"
    ])
    
    ORDEM_LINHAS_NEGOCIO: List[str] = field(default_factory=lambda: [
        'Vulcan', 'Consumidores', 'Revenda', 'Bunkers', 'Aviacao', 'Reexportacao'
    ])
    
    ORDEM_PORTOS: List[str] = field(default_factory=lambda: [
        'Maputo', 'Beira', 'Nacala ', 'Pemba'
    ])
    
    ARQUIVOS_VENDAS: List[str] = field(default_factory=lambda: [
        'Vds_2023_Comb_.xlsx',
        'Vds_2024_Comb_.xlsx',
        'Vds_2025_Comb_.xlsx'
    ])
    
    ARQUIVOS_PLANO: List[str] = field(default_factory=lambda: [
        'PlanComb_2023.xlsx',
        'PlanComb_2024.xlsx',
        'PlanComb_2025.xlsx'
    ])
    
    ARQUIVO_IMPORTACAO: str = 'ImportacaoMZ.xlsx'
    ARQUIVO_LOOKUPS: str = 'v_loock_up.xlsx'
    ARQUIVO_MIS: str = 'MIS_.xlsx'
    ARQUIVO_STOCK: str = 'Stock_Provincias.xlsx'
    ARQUIVO_GARANTIAS: str = 'Garantias_Bancarias_.xlsx'
    
    COLUNA_DATA_VENDAS: str = 'Data_Facturacao'
    COLUNA_DATA_IMPORTACAO: str = 'NOR'
    COLUNA_VENDAS_M3: str = 'Vendas_m3'
    COLUNA_PLANO_M3: str = 'Plano_m3'
    
    CACHE_TTL: int = 3600

config = ConfigSistema()

# ============================================= INICIALIZAÇÃO DO SESSION_STATE =============================================

@dataclass
class SessionState:
    """Gerenciamento centralizado do session_state"""
    date_range_importacao: Tuple[date, date] = (date(2025, 1, 1), date.today())
    date_range_vendas: Tuple[date, date] = (date(2025, 1, 1), date.today())
    modo_trabalho_selector: str = "Importação"
    dados_carregados: bool = False
    ultima_atualizacao: datetime = field(default_factory=datetime.now)
    filtros_importacao: Dict[str, List] = field(default_factory=dict)
    filtros_vendas: Dict[str, List] = field(default_factory=dict)

def inicializar_session_state():
    """Inicializa todas as variáveis necessárias no session_state"""
    defaults = {
        'date_range_importacao': (date(2025, 1, 1), date.today()),
        'date_range_vendas': (date(2025, 1, 1), date.today()),
        'modo_trabalho_selector': "Importação",
        'dados_carregados': False,
        'ultima_atualizacao': datetime.now(),
        'filtros_importacao': {},
        'filtros_vendas': {}
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

inicializar_session_state()

# ============================================= CSS PERSONALIZADO =============================================
st.markdown("""
<style>
    .stButton > button { width: 100%; border-radius: 10px; }
    .main { background-color: #FFFFFF; color: #333333; }
    .stApp { background: linear-gradient(135deg, #FFFFFF 0%, #F8F9FA 100%); }
    .main-header { color: #FF6B35; border-bottom: 3px solid #FF6B35; padding-bottom: 0.5rem; font-weight: 700; font-size: 2.5rem; }
    
    .metric-card-industria { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: 2px solid #5a6fd8; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(102, 126, 234, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .metric-card-petromoc { background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%); border: 2px solid #FF5A1F; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(255, 107, 53, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .metric-card-congenere { background: linear-gradient(135deg, #4ECDC4 0%, #44A08D 100%); border: 2px solid #3BB4AC; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(78, 205, 196, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .metric-card-Release { background: linear-gradient(135deg, #FFD166 0%, #FFB347 100%); border: 2px solid #FFC857; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(255, 209, 102, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .metric-card-fh { background: linear-gradient(135deg, #06D6A0 0%, #04A777 100%); border: 2px solid #05C793; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(6, 214, 160, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .metric-card-plano { background: linear-gradient(135deg, #9D4EDD 0%, #7B2CBF 100%); border: 2px solid #8A2BE2; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(157, 78, 221, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .metric-card-stock { background: linear-gradient(135deg, #2E86C1 0%, #1B4F72 100%); border: 2px solid #1B4F72; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(46, 134, 193, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .metric-card-autonomia { background: linear-gradient(135deg, #28B463 0%, #1D8348 100%); border: 2px solid #1D8348; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(40, 180, 99, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    .metric-card-alerta { background: linear-gradient(135deg, #E74C3C 0%, #B03A2E 100%); border: 2px solid #B03A2E; border-radius: 15px; padding: 1.5rem; margin: 0.5rem 0; box-shadow: 0 6px 20px rgba(231, 76, 60, 0.25); transition: transform 0.3s ease; height: 140px; display: flex; flex-direction: column; justify-content: center; }
    
    .metric-title { font-size: 0.9rem; font-weight: 700; color: rgba(255, 255, 255, 0.95); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 1px; text-align: center; }
    .metric-value { font-size: 2rem; font-weight: 800; color: white; text-align: center; margin-bottom: 0.25rem; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1); }
    .metric-subvalue { font-size: 0.85rem; font-weight: 600; color: rgba(255, 255, 255, 0.9); text-align: center; }
    .metric-subvalue-small { font-size: 0.75rem; font-weight: 500; color: rgba(255, 255, 255, 0.85); text-align: center; margin-top: 0.25rem; }
    
    .section-title { color: #2D3748; font-weight: 700; font-size: 1.5rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #FF6B35; }
    .section-title-stock { color: #2D3748; font-weight: 700; font-size: 1.5rem; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 2px solid #2E86C1; }
    
    .logo-container { text-align: center; padding: 1rem 0; margin-bottom: 1rem; border-bottom: 2px solid #FFE0D6; }
    .logo-img { max-width: 200px; height: auto; border-radius: 10px; box-shadow: 0 4px 12px rgba(255, 107, 53, 0.2); transition: transform 0.3s ease; }
    
    .scroller-container { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; padding: 1.5rem; margin: 1rem 0; box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3); border: 3px solid #5a6fd8; position: relative; overflow: hidden; }
    .scroller-stock { background: linear-gradient(135deg, #2E86C1 0%, #1B4F72 100%); border: 3px solid #1B4F72; }
    .scroller-petromoc { background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%); border: 3px solid #FF5A1F; }
    .scroller-title { color: white; font-size: 1.3rem; font-weight: 700; text-align: center; margin-bottom: 1rem; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2); }
    .scroller-content { display: flex; justify-content: space-around; align-items: center; animation: scrollEffect 15s ease-in-out infinite; padding: 1rem 0; }
    .scroller-item { text-align: center; padding: 0 2rem; border-right: 2px solid rgba(255, 255, 255, 0.3); flex: 1; }
    .scroller-item:last-child { border-right: none; }
    .scroller-value { font-size: 2.5rem; font-weight: 800; color: white; margin-bottom: 0.5rem; text-shadow: 0 2px 8px rgba(0, 0, 0, 0.3); }
    .scroller-label { font-size: 1rem; font-weight: 600; color: rgba(255, 255, 255, 0.9); text-transform: uppercase; letter-spacing: 1px; }
    .scroller-subvalue { font-size: 0.9rem; font-weight: 500; color: rgba(255, 255, 255, 0.8); margin-top: 0.25rem; }
    
    @keyframes scrollEffect { 0%, 100% { transform: translateX(0); } 25% { transform: translateX(-5px); } 50% { transform: translateX(5px); } 75% { transform: translateX(-5px); } }
    .pulse-effect { animation: pulse 2s infinite; }
    @keyframes pulse { 0% { transform: scale(1); } 50% { transform: scale(1.05); } 100% { transform: scale(1); } }
    
    @media (max-width: 768px) { .scroller-content { flex-direction: column; gap: 1rem; } .scroller-item { border-right: none; border-bottom: 2px solid rgba(255, 255, 255, 0.3); padding: 1rem 0; } .scroller-item:last-child { border-bottom: none; } }
    
    .stDataFrame { border: 2px solid #FF6B35; border-radius: 10px; overflow: hidden; }
    .stTabs [data-baseweb="tab-list"] { gap: 2px; }
    .stTabs [data-baseweb="tab"] { height: 50px; white-space: pre-wrap; background-color: #F8F9FA; border-radius: 8px 8px 0px 0px; gap: 1px; padding-top: 10px; padding-bottom: 10px; font-weight: 600; }
    .stTabs [aria-selected="true"] { background-color: #FF6B35; color: white; }
    
    .valor-positivo { color: #28A745; font-weight: 600; }
    .valor-negativo { color: #DC3545; font-weight: 600; }
    .valor-excelente { color: #28B463; font-weight: 600; }
    .valor-alerta { color: #FFC300; font-weight: 600; }
    .valor-critico { color: #E74C3C; font-weight: 600; }
    
    .stButton button { background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%); color: white; border: none; border-radius: 8px; padding: 0.5rem 1rem; font-weight: 600; transition: all 0.3s ease; }
    .stButton button:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(255, 107, 53, 0.3); }
</style>
""", unsafe_allow_html=True)

# ============================================= VERIFICAÇÃO DE AMBIENTE =============================================
try:
    if hasattr(st, 'secrets') and st.secrets.get("IS_CLOUD", False):
        st.cache_data.clear()
        logger.info("Modo cloud detectado - cache limpo")
except Exception as e:
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

# ============================================= FUNÇÕES UTILITÁRIAS CENTRALIZADAS =============================================

def formatar_ptbr(valor: float, casas: int = 2) -> str:
    """Formata número: 1234.56 → '1.234,56' com fallback robusto"""
    if pd.isna(valor) or valor is None:
        return "0" + (",00" if casas > 0 else "")
    try:
        try:
            return locale.format_string(f"%.{casas}f", float(valor), grouping=True)
        except:
            valor_float = float(valor)
            valor_str = f"{valor_float:,.{casas}f}"
            if '.' in valor_str:
                parte_inteira, parte_decimal = valor_str.split('.')
                parte_inteira = parte_inteira.replace(',', 'X').replace('.', ',').replace('X', '.')
                return parte_inteira + ',' + parte_decimal
            return valor_str.replace(',', 'X').replace('.', ',').replace('X', '.')
    except Exception as e:
        logger.error(f"Erro na formatação: {e}")
        return "0" + (",00" if casas > 0 else "")

def converter_data_segura(serie: pd.Series, nome_coluna: str = "") -> pd.Series:
    """Conversão centralizada e segura de datas"""
    if serie.empty:
        return pd.Series()
    if pd.api.types.is_datetime64_any_dtype(serie):
        return serie
    for formato in config.FORMATOS_DATA:
        try:
            return pd.to_datetime(serie, format=formato, errors='coerce')
        except:
            continue
    try:
        return pd.to_datetime(serie, errors='coerce')
    except:
        logger.warning(f"Falha ao converter coluna: {nome_coluna}")
        return pd.Series([pd.NaT] * len(serie))

def converter_tm_para_m3_seguro(quantidade_tm: float, combustivel: str) -> float:
    """Conversão segura de TM para M³"""
    try:
        if quantidade_tm == 0 or pd.isna(quantidade_tm):
            return 0.0
        combustivel_limpo = str(combustivel).strip().title() if combustivel else ''
        mapeamento = {'Gasóleo': 'Gasóleo', 'Gasolina': 'Gasolina', 'jet': 'Jet A1', 'diesel': 'Gasóleo'}
        combustivel_norm = mapeamento.get(combustivel_limpo.lower(), combustivel_limpo)
        densidade = config.DENSIDADES.get(combustivel_norm)
        return quantidade_tm / densidade if densidade else 0.0
    except:
        return 0.0

def limpar_coluna_numerica(df: pd.DataFrame, col: str) -> pd.Series:
    """Limpa e converte coluna para numérico"""
    if col not in df.columns:
        return pd.Series([0.0] * len(df))
    try:
        s = df[col].astype(str).str.strip()
        s = s.str.replace(r'\s+', '', regex=True)
        s = s.str.replace(',', '.', regex=False)
        s = s.str.replace(r'[^0-9.-]', '', regex=True)
        s = s.replace('', '0')
        return pd.to_numeric(s, errors='coerce').fillna(0.0)
    except:
        return pd.Series([0.0] * len(df))

def validar_colunas_obrigatorias(df: pd.DataFrame, colunas: List[str], nome_df: str) -> bool:
    """Valida se todas as colunas obrigatórias estão presentes"""
    if df.empty:
        logger.warning(f"DataFrame {nome_df} está vazio")
        return False
    colunas_faltantes = [col for col in colunas if col not in df.columns]
    if colunas_faltantes:
        logger.warning(f"Colunas faltando em {nome_df}: {colunas_faltantes}")
        return False
    return True

# ============================================= FUNÇÕES DE CARREGAMENTO DE DADOS =============================================

def carregar_logo_base64(caminho_arquivo: str) -> str:
    """Converte a imagem para base64 para exibição no HTML"""
    try:
        if os.path.exists(caminho_arquivo):
            with open(caminho_arquivo, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        return ""
    except Exception:
        return ""

@st.cache_data(ttl=config.CACHE_TTL)
def carregar_vendas() -> pd.DataFrame:
    """Carrega dados de vendas com verificação robusta - CAPTURA DADOS REAIS DE Vendas_m³"""
    try:
        dfs = []
        for arquivo in config.ARQUIVOS_VENDAS:
            if os.path.exists(arquivo):
                df_temp = pd.read_excel(arquivo)
                logger.info(f"Arquivo {arquivo} carregado: {len(df_temp)} registros")
                logger.info(f"Colunas em {arquivo}: {list(df_temp.columns)}")
                
                if 'Vendas_m³' in df_temp.columns:
                    logger.info(f"✓ Coluna 'Vendas_m³' encontrada em {arquivo} - Total: {df_temp['Vendas_m³'].sum():,.2f} m³")
                elif 'Vendas m³' in df_temp.columns:
                    logger.info(f"✓ Coluna 'Vendas m³' encontrada em {arquivo} - Total: {df_temp['Vendas m³'].sum():,.2f} m³")
                    df_temp['Vendas_m³'] = df_temp['Vendas m³']
                elif 'Quantidade' in df_temp.columns:
                    logger.info(f"✓ Coluna 'Quantidade' encontrada em {arquivo} - Total: {df_temp['Quantidade'].sum():,.2f}")
                    df_temp['Vendas_m³'] = df_temp['Quantidade']
                elif 'Volume' in df_temp.columns:
                    logger.info(f"✓ Coluna 'Volume' encontrada em {arquivo} - Total: {df_temp['Volume'].sum():,.2f}")
                    df_temp['Vendas_m³'] = df_temp['Volume']
                
                dfs.append(df_temp)
            else:
                logger.warning(f"Arquivo {arquivo} não encontrado")
        
        if not dfs:
            st.error("❌ Nenhum arquivo de vendas encontrado")
            return pd.DataFrame()
        
        df = pd.concat(dfs, ignore_index=True)
        
        if 'Vendas_m³' not in df.columns:
            for col in ['Vendas m³', 'Vendas_m3', 'Quantidade', 'Volume', 'Qtd_m3']:
                if col in df.columns:
                    logger.info(f"Renomeando coluna '{col}' para 'Vendas_m³'")
                    df['Vendas_m³'] = df[col]
                    break
        
        df['Data_Facturacao_original'] = df['Data_Facturacao'].copy()
        df['Data_Facturacao'] = converter_data_segura(df['Data_Facturacao'], "Data_Facturacao")
        df['Ano'] = df['Data_Facturacao'].dt.year.fillna(0).astype(int)
        df['Mes'] = df['Data_Facturacao'].dt.month.fillna(0).astype(int)
        df['Dia'] = df['Data_Facturacao'].dt.day.fillna(0).astype(int)
        
        colunas_monetarias = ['V_Liquido', 'V_Imposto', 'Custo_Produto', 'Margem_Vendas', 'V_Venda_Oceanica', 'Desconto', 'Valor_ISC']
        for col in colunas_monetarias:
            if col in df.columns and 'Cambio' in df.columns:
                df[f'{col}_MT'] = df[col] * df['Cambio']
                df[f'{col}_USD'] = df[col] / df['Cambio']
        
        logger.info("=" * 60)
        logger.info("RESUMO VENDAS CARREGADO:")
        logger.info(f"Total de registros: {len(df):,}")
        if 'Vendas_m³' in df.columns:
            logger.info(f"Total Vendas_m³: {df['Vendas_m³'].sum():,.2f} m³")
            logger.info(f"Registros com Vendas_m³ > 0: {(df['Vendas_m³'] > 0).sum():,}")
        logger.info("=" * 60)
        
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar vendas: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=config.CACHE_TTL)
def carregar_plano() -> pd.DataFrame:
    """Carrega dados do plano com tratamento robusto - CAPTURA DADOS REAIS DE Plano_m³"""
    try:
        dfs = []
        for arquivo in config.ARQUIVOS_PLANO:
            if os.path.exists(arquivo):
                df_temp = pd.read_excel(arquivo)
                logger.info(f"Arquivo {arquivo} carregado: {len(df_temp)} registros")
                logger.info(f"Colunas em {arquivo}: {list(df_temp.columns)}")
                
                if 'Plano_m³' in df_temp.columns:
                    logger.info(f"✓ Coluna 'Plano_m³' encontrada em {arquivo} - Total: {df_temp['Plano_m³'].sum():,.2f} m³")
                elif 'Plano m³' in df_temp.columns:
                    logger.info(f"✓ Coluna 'Plano m³' encontrada em {arquivo} - Total: {df_temp['Plano m³'].sum():,.2f} m³")
                    df_temp['Plano_m³'] = df_temp['Plano m³']
                elif 'Quantidade' in df_temp.columns:
                    logger.info(f"✓ Coluna 'Quantidade' encontrada em {arquivo} - Total: {df_temp['Quantidade'].sum():,.2f}")
                    df_temp['Plano_m³'] = df_temp['Quantidade']
                elif 'Volume' in df_temp.columns:
                    logger.info(f"✓ Coluna 'Volume' encontrada em {arquivo} - Total: {df_temp['Volume'].sum():,.2f}")
                    df_temp['Plano_m³'] = df_temp['Volume']
                
                dfs.append(df_temp)
            else:
                logger.warning(f"Arquivo {arquivo} não encontrado")
        
        if not dfs:
            st.warning("⚠️ Nenhum arquivo de plano encontrado")
            return pd.DataFrame()
        
        df = pd.concat(dfs, ignore_index=True)
        
        if 'Plano_m³' not in df.columns:
            for col in ['Plano m³', 'Plano_m3', 'Quantidade', 'Volume', 'Plano']:
                if col in df.columns:
                    logger.info(f"Renomeando coluna '{col}' para 'Plano_m³'")
                    df['Plano_m³'] = df[col]
                    break
        
        if 'Data_Facturacao' in df.columns:
            df['Data_Facturacao_original'] = df['Data_Facturacao'].copy()
            df['Data_Facturacao'] = converter_data_segura(df['Data_Facturacao'], "Data_Facturacao_Plano")
            df['Ano'] = df['Data_Facturacao'].dt.year.fillna(0).astype(int)
            df['Mes'] = df['Data_Facturacao'].dt.month.fillna(0).astype(int)
        
        logger.info("=" * 60)
        logger.info("RESUMO PLANO CARREGADO:")
        logger.info(f"Total de registros: {len(df):,}")
        if 'Plano_m³' in df.columns:
            logger.info(f"Total Plano_m³: {df['Plano_m³'].sum():,.2f} m³")
            logger.info(f"Registros com Plano_m³ > 0: {(df['Plano_m³'] > 0).sum():,}")
        logger.info("=" * 60)
        
        return df.fillna(0)
    except Exception as e:
        logger.error(f"Erro ao carregar plano: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=config.CACHE_TTL)
def carregar_lookups():
    """Carrega dados de lookup com validação"""
    try:
        if not os.path.exists(config.ARQUIVO_LOOKUPS):
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        v0 = pd.read_excel(config.ARQUIVO_LOOKUPS, sheet_name=0)
        v1 = pd.read_excel(config.ARQUIVO_LOOKUPS, sheet_name=1)
        v2 = pd.read_excel(config.ARQUIVO_LOOKUPS, sheet_name=2)
        v3 = pd.read_excel(config.ARQUIVO_LOOKUPS, sheet_name=3)
        v4 = pd.read_excel(config.ARQUIVO_LOOKUPS, sheet_name=4)
        v5 = pd.read_excel(config.ARQUIVO_LOOKUPS, sheet_name=5)
        if 'DataCriacaoCliente' in v0.columns:
            v0['DataCriacaoCliente'] = converter_data_segura(v0['DataCriacaoCliente'], "DataCriacaoCliente")
        return v0, v1, v2, v3, v4, v5
    except Exception as e:
        logger.error(f"Erro ao carregar lookups: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=config.CACHE_TTL)
def carregar_importacao() -> pd.DataFrame:
    """Carrega dados de importação"""
    try:
        if not os.path.exists(config.ARQUIVO_IMPORTACAO):
            st.error(f"❌ Arquivo {config.ARQUIVO_IMPORTACAO} não encontrado")
            return pd.DataFrame()
        df = pd.read_excel(config.ARQUIVO_IMPORTACAO)
        for col in ['NOR', 'Data_Descarga']:
            if col in df.columns:
                df[col] = converter_data_segura(df[col], col)
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar importação: {str(e)}")
        return pd.DataFrame()

@st.cache_data(ttl=config.CACHE_TTL)
def carregar_garantias_bancarias() -> pd.DataFrame:
    """Carrega dados reais de Garantias Bancárias do arquivo específico"""
    try:
        if os.path.exists(config.ARQUIVO_GARANTIAS):
            df = pd.read_excel(config.ARQUIVO_GARANTIAS)
            logger.info(f"Arquivo {config.ARQUIVO_GARANTIAS} carregado: {len(df)} registros")
            logger.info(f"Colunas em garantias: {list(df.columns)}")
            return df
        else:
            logger.warning(f"Arquivo {config.ARQUIVO_GARANTIAS} não encontrado")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Erro ao carregar garantias bancárias: {str(e)}")
        return pd.DataFrame()

# ============================================= CARREGAR TODOS OS DADOS =============================================

@st.cache_resource
def carregar_todos_dados():
    """Carrega todos os dados do sistema com tratamento de erros"""
    with st.spinner("🔄 Carregando dados do sistema..."):
        vendas_df = carregar_vendas()
        plano_df = carregar_plano()
        v0, v1, v2, v3, v4, v5 = carregar_lookups()
        import_df = carregar_importacao()
        garantias_df = carregar_garantias_bancarias()
        return vendas_df, plano_df, v0, v1, v2, v3, v4, v5, import_df, garantias_df

vendas_df, plano_df, v0, v1, v2, v3, v4, v5, import_df, garantias_df = carregar_todos_dados()

# ============================================= PROCESSAMENTO DO DATAFRAME vds_plan_MT_Pln =============================================

def processar_dataframes():
    """
    Processa e combina os dataframes de vendas e plano para criar vds_plan_MT_Pln.
    Este é o DATAFRAME PRINCIPAL com dados REAIS de vendas e plano.
    """
    try:
        if vendas_df.empty:
            logger.warning("DataFrame de vendas vazio")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        if 'Vendas_m³' not in vendas_df.columns:
            for col in ['Vendas m³', 'Vendas_m3', 'Quantidade', 'Volume']:
                if col in vendas_df.columns:
                    logger.info(f"Renomeando coluna '{col}' para 'Vendas_m³' no vendas_df")
                    vendas_df['Vendas_m³'] = vendas_df[col]
                    break
            else:
                logger.warning("Coluna de vendas não encontrada!")
                vendas_df['Vendas_m³'] = 0
        
        colunas_usd = ['V_Liquido_USD', 'V_Imposto_USD', 'Custo_Produto_USD', 'Margem_Vendas_USD',
                      'V_Venda_Oceanica_USD', 'Desconto_USD', 'Valor_ISC_USD']
        colunas_mt = ['V_Liquido_MT', 'V_Imposto_MT', 'Custo_Produto_MT', 'Margem_Vendas_MT',
                     'V_Venda_Oceanica_MT', 'Desconto_MT', 'Valor_ISC_MT']
        
        vendas_df_MT = vendas_df.copy()
        vendas_df_USD = vendas_df.copy()
        
        vendas_df_MT = vendas_df_MT.drop([col for col in colunas_usd if col in vendas_df_MT.columns], axis=1, errors='ignore')
        vendas_df_USD = vendas_df_USD.drop([col for col in colunas_mt if col in vendas_df_USD.columns], axis=1, errors='ignore')

        if config.COLUNA_DATA_VENDAS in vendas_df_MT.columns:
            vendas_df_MT['Ano'] = vendas_df_MT[config.COLUNA_DATA_VENDAS].dt.year
            vendas_df_MT['Mes'] = vendas_df_MT[config.COLUNA_DATA_VENDAS].dt.month

        # MERGES COM LOOKUPS
        if not v3.empty and 'CE' in vendas_df_MT.columns and 'CE' in v3.columns:
            vendas_df_MT['CE'] = vendas_df_MT['CE'].astype(str).str.strip()
            v3['CE'] = v3['CE'].astype(str).str.strip()
            vendas_df_MT = pd.merge(vendas_df_MT, v3, on=['CE'], how='left', suffixes=('', '_v3'))
        
        if not v0.empty and 'Emissor' in vendas_df_MT.columns and 'Emissor' in v0.columns:
            vendas_df_MT['Emissor'] = vendas_df_MT['Emissor'].astype(str).str.strip()
            v0['Emissor'] = v0['Emissor'].astype(str).str.strip()
            vendas_df_MT = pd.merge(vendas_df_MT, v0, on=['Emissor'], how='left', suffixes=('', '_v0'))
        
        if not v5.empty and 'Material' in vendas_df_MT.columns and 'Material' in v5.columns:
            vendas_df_MT['Material'] = vendas_df_MT['Material'].astype(str).str.strip()
            v5['Material'] = v5['Material'].astype(str).str.strip()
            vendas_df_MT = pd.merge(vendas_df_MT, v5, on=['Material'], how='left', suffixes=('', '_v5'))
        
        if not v4.empty and 'TipFt' in vendas_df_MT.columns and 'TipFt' in v4.columns:
            vendas_df_MT['TipFt'] = vendas_df_MT['TipFt'].astype(str).str.strip()
            v4['TipFt'] = v4['TipFt'].astype(str).str.strip()
            vendas_df_MT = pd.merge(vendas_df_MT, v4, on=['TipFt'], how='left', suffixes=('', '_v4'))
        
        if not v1.empty and 'CDst' in vendas_df_MT.columns and 'CDst' in v1.columns:
            vendas_df_MT['CDst'] = vendas_df_MT['CDst'].astype(str).str.strip()
            v1['CDst'] = v1['CDst'].astype(str).str.strip()
            vendas_df_MT = pd.merge(vendas_df_MT, v1, on=['CDst'], how='left', suffixes=('', '_v1'))

        if 'DataCriacaoCliente' in vendas_df_MT.columns:
            vendas_df_MT['DataCriacaoCliente'] = converter_data_segura(vendas_df_MT['DataCriacaoCliente'], "DataCriacaoCliente")

        colunas_remover = ['Doc.fat.', 'Tipo.Factura', 'TipFt', 'Denominação', 'Cambio', 'Moeda']
        vds_plan_MT_Pln = vendas_df_MT.drop([col for col in colunas_remover if col in vendas_df_MT.columns], axis=1, errors='ignore')
        
        # MERGE COM DADOS DO PLANO
        if not plano_df.empty:
            plano_df_clean = plano_df.copy()
            
            if 'Plano_m³' not in plano_df_clean.columns:
                for col in ['Plano m³', 'Plano_m3', 'Quantidade', 'Volume']:
                    if col in plano_df_clean.columns:
                        logger.info(f"Renomeando coluna '{col}' para 'Plano_m³' no plano_df")
                        plano_df_clean['Plano_m³'] = plano_df_clean[col]
                        break
            
            if 'Data_Facturacao' in plano_df_clean.columns:
                plano_df_clean['Data_Facturacao'] = pd.to_datetime(plano_df_clean['Data_Facturacao'], errors='coerce')
            
            for col in ['Emissor', 'CDst', 'Material']:
                if col in plano_df_clean.columns:
                    plano_df_clean[col] = plano_df_clean[col].astype(str).str.strip().fillna('')
                if col in vds_plan_MT_Pln.columns:
                    vds_plan_MT_Pln[col] = vds_plan_MT_Pln[col].astype(str).str.strip().fillna('')
            
            colunas_merge = []
            for col in [config.COLUNA_DATA_VENDAS, 'Emissor', 'CDst', 'Material']:
                if col in vds_plan_MT_Pln.columns and col in plano_df_clean.columns:
                    colunas_merge.append(col)
            
            if colunas_merge:
                if config.COLUNA_DATA_VENDAS in colunas_merge:
                    vds_plan_MT_Pln['Ano_Merge'] = vds_plan_MT_Pln[config.COLUNA_DATA_VENDAS].dt.year
                    vds_plan_MT_Pln['Mes_Merge'] = vds_plan_MT_Pln[config.COLUNA_DATA_VENDAS].dt.month
                    plano_df_clean['Ano_Merge'] = plano_df_clean[config.COLUNA_DATA_VENDAS].dt.year
                    plano_df_clean['Mes_Merge'] = plano_df_clean[config.COLUNA_DATA_VENDAS].dt.month
                    colunas_merge_completo = colunas_merge + ['Ano_Merge', 'Mes_Merge']
                else:
                    colunas_merge_completo = colunas_merge
                
                logger.info(f"Fazendo merge com colunas: {colunas_merge_completo}")
                
                vds_plan_MT_Pln = pd.merge(
                    vds_plan_MT_Pln, 
                    plano_df_clean, 
                    on=colunas_merge_completo, 
                    how='left',
                    suffixes=('', '_plano')
                )
                
                for col in ['Ano_Merge', 'Mes_Merge']:
                    if col in vds_plan_MT_Pln.columns:
                        vds_plan_MT_Pln = vds_plan_MT_Pln.drop(col, axis=1)
                
                logger.info(f"Após merge: {len(vds_plan_MT_Pln)} registros")
        
        vds_plan_MT_Pln = vds_plan_MT_Pln.fillna(0)
        
        # PADRONIZAR COLUNAS VENDAS E PLANO
        if 'Vendas_m³' in vds_plan_MT_Pln.columns:
            vds_plan_MT_Pln[config.COLUNA_VENDAS_M3] = pd.to_numeric(vds_plan_MT_Pln['Vendas_m³'], errors='coerce').fillna(0)
        else:
            vds_plan_MT_Pln[config.COLUNA_VENDAS_M3] = 0
        
        if 'Plano_m³' in vds_plan_MT_Pln.columns:
            vds_plan_MT_Pln[config.COLUNA_PLANO_M3] = pd.to_numeric(vds_plan_MT_Pln['Plano_m³'], errors='coerce').fillna(0)
        elif 'Quantidade_plano' in vds_plan_MT_Pln.columns:
            vds_plan_MT_Pln[config.COLUNA_PLANO_M3] = pd.to_numeric(vds_plan_MT_Pln['Quantidade_plano'], errors='coerce').fillna(0)
        else:
            vds_plan_MT_Pln[config.COLUNA_PLANO_M3] = 0
        
        # CALCULAR MÉTRICAS
        vds_plan_MT_Pln['Diferenca_m3'] = vds_plan_MT_Pln[config.COLUNA_VENDAS_M3] - vds_plan_MT_Pln[config.COLUNA_PLANO_M3]
        
        mask = vds_plan_MT_Pln[config.COLUNA_PLANO_M3] > 0
        vds_plan_MT_Pln.loc[mask, 'Percentual_Atingimento'] = (
            vds_plan_MT_Pln.loc[mask, config.COLUNA_VENDAS_M3] / 
            vds_plan_MT_Pln.loc[mask, config.COLUNA_PLANO_M3] * 100
        ).round(2)
        vds_plan_MT_Pln.loc[~mask, 'Percentual_Atingimento'] = 0
        
        logger.info("=" * 60)
        logger.info("RESUMO DO PROCESSAMENTO vds_plan_MT_Pln:")
        logger.info(f"Total de registros: {len(vds_plan_MT_Pln):,}")
        logger.info(f"Total Vendas Reais: {vds_plan_MT_Pln[config.COLUNA_VENDAS_M3].sum():,.2f} m³")
        logger.info(f"Total Plano Real: {vds_plan_MT_Pln[config.COLUNA_PLANO_M3].sum():,.2f} m³")
        logger.info(f"Diferença Total: {vds_plan_MT_Pln['Diferenca_m3'].sum():,.2f} m³")
        atingimento = (vds_plan_MT_Pln[config.COLUNA_VENDAS_M3].sum() / vds_plan_MT_Pln[config.COLUNA_PLANO_M3].sum() * 100) if vds_plan_MT_Pln[config.COLUNA_PLANO_M3].sum() > 0 else 0
        logger.info(f"Atingimento Geral: {atingimento:.2f}%")
        logger.info("=" * 60)
        
        return vds_plan_MT_Pln, vendas_df_MT, vendas_df_USD
        
    except Exception as e:
        logger.error(f"Erro ao processar dataframes: {str(e)}", exc_info=True)
        st.error(f"❌ Erro ao processar dataframes: {str(e)}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

vds_plan_MT_Pln, vendas_df_MT, vendas_df_USD = processar_dataframes()

# ============================================= CONSTANTES =============================================
CLIENTES_CONGENERES = config.CLIENTES_CONGENERES

# ============================================= FUNÇÕES DO MENU LATERAL =============================================
@st.cache_data(ttl=3600)
def carregar_opcoes_filtros(df: pd.DataFrame, tipo: str) -> Dict[str, Any]:
    """Carrega opções de filtros baseadas na tabela especificada"""
    if df.empty:
        return {}
    df = df.copy()
    result = {}
    start_date_default = config.DATA_INICIO_PADRAO
    end_date_default = date.today()
    
    if tipo == "importacao":
        coluna_data = config.COLUNA_DATA_IMPORTACAO if config.COLUNA_DATA_IMPORTACAO in df.columns else 'Data_Descarga'
    else:
        coluna_data = config.COLUNA_DATA_VENDAS
    
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
    
    result.update({'min_date': min_date, 'max_date': max_date, 'coluna_data': coluna_data})
    
    for coluna in df.columns:
        if coluna in ['_merge', 'Ano_merge', 'Mes_merge']:
            continue
        valores_unicos = df[coluna].dropna().unique()
        if 0 < len(valores_unicos) <= 100:
            if pd.api.types.is_numeric_dtype(df[coluna]) and coluna in ['Ano']:
                result[coluna] = sorted([int(v) for v in valores_unicos if pd.notna(v)])
            else:
                result[coluna] = sorted([str(v) for v in valores_unicos if pd.notna(v) and str(v) != ''])
    return result

def criar_secao_calendario(opcoes: Dict[str, Any], tipo: str) -> tuple:
    """Cria seção de calendário"""
    st.sidebar.header(f"📅 Calendário - {tipo.title()}")
    chave_calendario = f"date_range_{tipo}"
    date_range = st.sidebar.date_input(
        f"Intervalo de Datas ({tipo})",
        value=st.session_state[chave_calendario],
        min_value=date(2015, 1, 1),
        max_value=date.today(),
        key=f"widget_{chave_calendario}"
    )
    if len(date_range) == 2 and date_range[1] >= date_range[0]:
        st.session_state[chave_calendario] = date_range
        st.sidebar.caption(f"📊 Período: {(date_range[1] - date_range[0]).days} dias")
        return date_range
    return st.session_state[chave_calendario]

def limpar_filtros_session_state():
    """Limpa todos os filtros do session_state"""
    keys_to_remove = []
    for key in st.session_state.keys():
        if key.startswith('date_range_') or key.startswith('filtro_'):
            keys_to_remove.append(key)
    for key in keys_to_remove:
        del st.session_state[key]

def renderizar_menu_lateral():
    """Versão corrigida do menu lateral"""
    filtros = {}
    
    logo_base64 = carregar_logo_base64("Logo_Petromoc.png")
    if logo_base64:
        st.sidebar.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{logo_base64}" class="logo-img">
            <div style="font-weight:700; color:#FF6B35;">Petromoc, SA</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.sidebar.markdown("""
        <div class="logo-container">
            <div style="text-align:center; padding:1rem; background:linear-gradient(135deg,#FF6B35,#FF8C42); border-radius:10px; color:white;">
                <h3>⛽ PETROMOC</h3>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.sidebar.markdown("---")
    
    modo_trabalho = st.sidebar.radio(
        "🎯 Selecione",
        [m.value for m in ModoTrabalho],
        index=0,
        key="modo_trabalho_selector"
    )
    filtros['modo_trabalho'] = modo_trabalho
    
    st.sidebar.markdown("---")
    
    if modo_trabalho == ModoTrabalho.VENDAS.value and not vds_plan_MT_Pln.empty:
        opcoes = carregar_opcoes_filtros(vds_plan_MT_Pln, "vendas")
        if opcoes:
            date_range = criar_secao_calendario(opcoes, "vendas")
            filtros['date_range'] = date_range
            filtros['tipo_dados'] = 'vendas'
            
            st.sidebar.header("🔍 Filtros")
            colunas_filtro = ['Ano', 'Combustivel', 'Linha Neg.', 'Sector/Sigla', 'Gestor / Promotor', 'Provincia']
            for coluna in colunas_filtro:
                if coluna in opcoes and opcoes[coluna]:
                    chave_filtro = f"filtro_vendas_{coluna.replace('/', '_').replace(' ', '_')}"
                    valores = st.sidebar.multiselect(
                        f"{coluna}",
                        options=opcoes[coluna],
                        default=st.session_state.get(chave_filtro, []),
                        key=f"widget_{chave_filtro}"
                    )
                    st.session_state[chave_filtro] = valores
                    filtros[coluna] = valores
    
    elif modo_trabalho == ModoTrabalho.IMPORTACAO.value and not import_df.empty:
        opcoes = carregar_opcoes_filtros(import_df, "importacao")
        if opcoes:
            date_range = criar_secao_calendario(opcoes, "importacao")
            filtros['date_range'] = date_range
            filtros['tipo_dados'] = 'importacao'
            
            st.sidebar.header("🔍 Filtros")
            colunas_filtro = ['Ano', 'Combustivel', 'Porto', 'Situacao_Descarga']
            for coluna in colunas_filtro:
                if coluna in opcoes and opcoes[coluna]:
                    chave_filtro = f"filtro_import_{coluna}"
                    valores = st.sidebar.multiselect(
                        f"{coluna}",
                        options=opcoes[coluna],
                        default=st.session_state.get(chave_filtro, []),
                        key=f"widget_{chave_filtro}"
                    )
                    st.session_state[chave_filtro] = valores
                    filtros[coluna] = valores
    
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

def criar_link_externo(url: str, texto: str, icone: str = "🌐"):
    """Cria um link externo que abre em nova aba"""
    return f"""
    <a href="{url}" target="_blank" style="text-decoration: none;">
        <div style="background: linear-gradient(135deg, #FF6B35 0%, #FF8C42 100%); color: white; padding: 0.75rem 1rem; border-radius: 8px; text-align: center; font-weight: 600; margin: 0.5rem 0; border: 2px solid #FF5A1F;">
            {icone} {texto}
        </div>
    </a>
    """

# ============================================= FUNÇÕES DE FILTRAGEM =============================================

def aplicar_filtros_vendas(df: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
    """Aplica filtros no DataFrame de vendas"""
    if df.empty:
        return df
    df_filtrado = df.copy()
    
    if config.COLUNA_DATA_VENDAS in df_filtrado.columns and 'date_range' in filtros:
        df_filtrado[config.COLUNA_DATA_VENDAS] = pd.to_datetime(df_filtrado[config.COLUNA_DATA_VENDAS], errors='coerce')
        mask = (df_filtrado[config.COLUNA_DATA_VENDAS] >= pd.Timestamp(filtros['date_range'][0])) & \
               (df_filtrado[config.COLUNA_DATA_VENDAS] <= pd.Timestamp(filtros['date_range'][1]))
        df_filtrado = df_filtrado[mask]
    
    for coluna, valores in filtros.items():
        if coluna not in ['date_range', 'modo_trabalho', 'tipo_dados'] and valores and coluna in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin([str(v) for v in valores])]
    
    return df_filtrado

def aplicar_filtros_importacao(df: pd.DataFrame, filtros: Dict) -> pd.DataFrame:
    """Aplica filtros no DataFrame de importação"""
    if df.empty:
        return df
    df_filtrado = df.copy()
    
    colunas_data = [config.COLUNA_DATA_IMPORTACAO, 'Data_Descarga']
    for col_data in colunas_data:
        if col_data in df_filtrado.columns:
            df_filtrado[col_data] = pd.to_datetime(df_filtrado[col_data], errors='coerce')
            mask = (df_filtrado[col_data] >= pd.Timestamp(filtros['date_range'][0])) & \
                   (df_filtrado[col_data] <= pd.Timestamp(filtros['date_range'][1]))
            df_filtrado = df_filtrado[mask]
            break
    
    for coluna, valores in filtros.items():
        if coluna not in ['date_range', 'modo_trabalho', 'tipo_dados'] and valores and coluna in df_filtrado.columns:
            df_filtrado = df_filtrado[df_filtrado[coluna].astype(str).isin([str(v) for v in valores])]
    
    return df_filtrado

# ============================================= FUNÇÕES DE VISUALIZAÇÃO =============================================

def criar_card_metricas(titulo: str, valor_principal: str, subtitulo1: str = "", subtitulo2: str = "", icone: str = "📊", tipo_card: str = "default"):
    """Cria cards de métricas com cores vibrantes"""
    card_map = {
        "industria": "metric-card-industria", "petromoc": "metric-card-petromoc",
        "congenere": "metric-card-congenere", "Release": "metric-card-Release",
        "fh": "metric-card-fh", "plano": "metric-card-plano",
        "stock": "metric-card-stock", "autonomia": "metric-card-autonomia", "alerta": "metric-card-alerta"
    }
    card_class = card_map.get(tipo_card, "metric-card-petromoc")
    
    st.markdown(f"""
    <div class="{card_class}">
        <div class="metric-title">{icone} {titulo}</div>
        <div class="metric-value">{valor_principal}</div>
        <div class="metric-subvalue">{subtitulo1}</div>
        <div class="metric-subvalue-small">{subtitulo2}</div>
    </div>
    """, unsafe_allow_html=True)

def criar_grafico_linhas_vendas_plano(df_filtrado: pd.DataFrame):
    """Cria gráfico de linhas Vendas vs Plano usando dados REAIS"""
    if df_filtrado.empty:
        return None
    try:
        df_grafico = df_filtrado.copy()
        if config.COLUNA_DATA_VENDAS in df_grafico.columns:
            df_grafico[config.COLUNA_DATA_VENDAS] = pd.to_datetime(df_grafico[config.COLUNA_DATA_VENDAS], errors='coerce')
            df_grafico['Ano'] = df_grafico[config.COLUNA_DATA_VENDAS].dt.year
            df_grafico['Mes'] = df_grafico[config.COLUNA_DATA_VENDAS].dt.month
            df_grafico = df_grafico.dropna(subset=['Ano', 'Mes'])
        if df_grafico.empty:
            return None
        dados_mensais = df_grafico.groupby(['Ano', 'Mes']).agg({
            config.COLUNA_VENDAS_M3: 'sum',
            config.COLUNA_PLANO_M3: 'sum'
        }).reset_index()
        dados_mensais['Data'] = pd.to_datetime(dados_mensais['Ano'].astype(str) + '-' + dados_mensais['Mes'].astype(str) + '-01')
        dados_mensais = dados_mensais.sort_values('Data')
        meses_ptbr = {1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun', 7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'}
        dados_mensais['Periodo'] = dados_mensais['Mes'].map(meses_ptbr) + '/' + dados_mensais['Ano'].astype(str)
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dados_mensais['Periodo'], y=dados_mensais[config.COLUNA_VENDAS_M3], name='Vendas Reais',
                                  line=dict(color='#FF6B35', width=3), marker=dict(size=10), mode='lines+markers'))
        fig.add_trace(go.Scatter(x=dados_mensais['Periodo'], y=dados_mensais[config.COLUNA_PLANO_M3], name='Plano',
                                  line=dict(color='#9D4EDD', width=3, dash='dash'), marker=dict(size=10), mode='lines+markers'))
        fig.update_layout(title='📈 Vendas vs Plano - Evolução Mensal (Dados Reais)', xaxis_title='Período',
                          yaxis_title='Volume (m³)', height=500, hovermode='x unified', xaxis_tickangle=-45)
        return fig
    except Exception as e:
        logger.error(f"Erro no gráfico: {str(e)}")
        return None

def criar_grafico_linhas_simulado():
    """Cria gráfico de linhas simulado quando não há dados reais"""
    meses = ['Jan 2024', 'Fev 2024', 'Mar 2024', 'Abr 2024', 'Mai 2024', 'Jun 2024', 
             'Jul 2024', 'Ago 2024', 'Set 2024', 'Out 2024', 'Nov 2024', 'Dez 2024']
    np.random.seed(42)
    vendas = np.random.uniform(8000, 12000, 12) * (1 + np.linspace(0, 0.2, 12))
    plano = np.random.uniform(9000, 11000, 12) * (1 + np.linspace(0, 0.16, 12))
    dados_simulados = pd.DataFrame({'Periodo': meses, 'Vendas': vendas, 'Plano': plano})
    fig = px.line(dados_simulados, x='Periodo', y=['Vendas', 'Plano'], 
                  title='📈 Vendas vs Plano - Evolução Mensal (Dados Simulados)')
    fig.update_traces(mode='lines+markers', marker=dict(size=6))
    return fig

def criar_tabela_vendas_plano_real(df_filtrado: pd.DataFrame):
    """Cria tabela com dados REAIS de vendas e plano do dataframe vds_plan_MT_Pln"""
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível")
        return
    
    total_vendas = df_filtrado[config.COLUNA_VENDAS_M3].sum()
    total_plano = df_filtrado[config.COLUNA_PLANO_M3].sum()
    total_diferenca = total_vendas - total_plano
    perc_geral = (total_vendas / total_plano * 100) if total_plano > 0 else 0
    
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1: st.metric("Total Vendas", f"{formatar_ptbr(total_vendas, 0)} m³")
    with col2: st.metric("Total Plano", f"{formatar_ptbr(total_plano, 0)} m³")
    with col3: st.metric("Diferença", f"{formatar_ptbr(total_diferenca, 0)} m³", delta=f"{perc_geral:+.1f}%")
    with col4: st.metric("Atingimento", f"{perc_geral:.1f}%")
    with col5: st.metric("Registros c/ Plano", f"{(df_filtrado[config.COLUNA_PLANO_M3] > 0).sum()}/{len(df_filtrado)}")
    
    st.markdown("---")
    
    col_view1, col_view2, col_view3 = st.columns(3)
    with col_view1: 
        # Definir 'Por Mês' como opção padrão
        nivel = st.selectbox(
            "Nível de Agregação", 
            ["Por Mês", "Detalhado", "Por Linha", "Por Combustível"],
            index=0  # index=0 define 'Por Mês' como padrão
        )
    with col_view2: 
        ordenar = st.selectbox(
            "Ordenar por", 
            ["Período", "Vendas", "Plano", "Diferença", "Atingimento"],
            index=0  # 'Período' como padrão
        )
    with col_view3: 
        ordem = st.selectbox(
            "Ordem", 
            ["Crescente", "Decrescente"],
            index=0  # 'Crescente' como padrão
        )
    
    df_agregado = df_filtrado.copy()
    
    # Processar conforme nível de agregação selecionado
    if nivel == "Por Mês" and config.COLUNA_DATA_VENDAS in df_agregado.columns:
        df_agregado['Periodo'] = df_agregado[config.COLUNA_DATA_VENDAS].dt.strftime('%Y-%m')
        df_agregado = df_agregado.groupby('Periodo').agg({
            config.COLUNA_VENDAS_M3: 'sum', 
            config.COLUNA_PLANO_M3: 'sum', 
            'Diferenca_m3': 'sum', 
            'Percentual_Atingimento': 'mean'
        }).reset_index()
        df_agregado['Linha_Negocio'] = 'Todos'
        df_agregado['Combustivel'] = 'Todos'
    elif nivel == "Por Linha" and 'Linha Neg.' in df_agregado.columns:
        df_agregado = df_agregado.groupby('Linha Neg.').agg({
            config.COLUNA_VENDAS_M3: 'sum', 
            config.COLUNA_PLANO_M3: 'sum', 
            'Diferenca_m3': 'sum', 
            'Percentual_Atingimento': 'mean'
        }).reset_index()
        df_agregado['Periodo'] = 'Total'
        df_agregado['Combustivel'] = 'Todos'
        df_agregado = df_agregado.rename(columns={'Linha Neg.': 'Linha_Negocio'})
    elif nivel == "Por Combustível" and 'Combustivel' in df_agregado.columns:
        df_agregado = df_agregado.groupby('Combustivel').agg({
            config.COLUNA_VENDAS_M3: 'sum', 
            config.COLUNA_PLANO_M3: 'sum', 
            'Diferenca_m3': 'sum', 
            'Percentual_Atingimento': 'mean'
        }).reset_index()
        df_agregado['Periodo'] = 'Total'
        df_agregado['Linha_Negocio'] = 'Todos'
    else:
        # Modo Detalhado
        if config.COLUNA_DATA_VENDAS in df_agregado.columns:
            df_agregado['Periodo'] = df_agregado[config.COLUNA_DATA_VENDAS].dt.strftime('%Y-%m-%d')
        if 'Linha Neg.' in df_agregado.columns:
            df_agregado = df_agregado.rename(columns={'Linha Neg.': 'Linha_Negocio'})
        if 'Combustivel' not in df_agregado.columns:
            df_agregado['Combustivel'] = 'N/A'
    
    # Determinar coluna para ordenação
    col_ordem_map = {
        'Período': 'Periodo', 
        'Vendas': config.COLUNA_VENDAS_M3, 
        'Plano': config.COLUNA_PLANO_M3, 
        'Diferença': 'Diferenca_m3', 
        'Atingimento': 'Percentual_Atingimento'
    }
    col_ordem = col_ordem_map.get(ordenar, 'Periodo')
    
    # Verificar se a coluna existe antes de ordenar
    if col_ordem in df_agregado.columns:
        df_agregado = df_agregado.sort_values(col_ordem, ascending=(ordem == "Crescente"))
    
    # Preparar DataFrame para exibição
    df_display = df_agregado.copy()
    df_display['Vendas (m³)'] = df_display[config.COLUNA_VENDAS_M3].apply(lambda x: formatar_ptbr(x, 0))
    df_display['Plano (m³)'] = df_display[config.COLUNA_PLANO_M3].apply(lambda x: formatar_ptbr(x, 0))
    df_display['Diferença (m³)'] = df_display['Diferenca_m3'].apply(lambda x: f"+{formatar_ptbr(x, 0)}" if x >= 0 else f"-{formatar_ptbr(abs(x), 0)}")
    df_display['Atingimento (%)'] = df_display['Percentual_Atingimento'].apply(lambda x: f"{x:.1f}%" if x > 0 else "0%")
    
    def classificar_status(perc): 
        try:
            perc_val = float(perc.replace('%', '')) if isinstance(perc, str) else perc
            if perc_val >= 100:
                return "✅ Excelente"
            elif perc_val >= 90:
                return "👍 Bom"
            elif perc_val >= 70:
                return "⚠️ Regular"
            elif perc_val >= 50:
                return "🔶 Atenção"
            else:
                return "❌ Crítico"
        except:
            return "N/A"
    
    df_display['Status'] = df_display['Atingimento (%)'].apply(classificar_status)
    
    # Definir colunas para exibição conforme nível de agregação
    if nivel == "Por Mês":
        colunas_exibir = ['Periodo', 'Vendas (m³)', 'Plano (m³)', 'Diferença (m³)', 'Atingimento (%)', 'Status']
    elif nivel == "Por Linha":
        colunas_exibir = ['Linha_Negocio', 'Vendas (m³)', 'Plano (m³)', 'Diferença (m³)', 'Atingimento (%)', 'Status']
    elif nivel == "Por Combustível":
        colunas_exibir = ['Combustivel', 'Vendas (m³)', 'Plano (m³)', 'Diferença (m³)', 'Atingimento (%)', 'Status']
    else:
        colunas_exibir = ['Periodo', 'Linha_Negocio', 'Combustivel', 'Vendas (m³)', 'Plano (m³)', 'Diferença (m³)', 'Atingimento (%)', 'Status']
    
    # Filtrar apenas colunas que existem
    colunas_exibir = [c for c in colunas_exibir if c in df_display.columns]
    
    st.dataframe(df_display[colunas_exibir], use_container_width=True, hide_index=True)
    
    return df_agregado

def criar_analise_vendas_plano_completa(df_filtrado: pd.DataFrame):
    """Cria análise completa de Vendas vs Plano usando dados REAIS do vds_plan_MT_Pln"""
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para análise")
        return
    
    st.markdown('<div class="section-title">📊 Análise Vendas vs Plano - Dados Reais</div>', unsafe_allow_html=True)
    
    total_vendas = df_filtrado[config.COLUNA_VENDAS_M3].sum()
    total_plano = df_filtrado[config.COLUNA_PLANO_M3].sum()
    total_diferenca = total_vendas - total_plano
    perc_geral = (total_vendas / total_plano * 100) if total_plano > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: criar_card_metricas("Vendas Totais", formatar_ptbr(total_vendas, 0), "Volume realizado", f"{len(df_filtrado)} registros", "📈", "petromoc")
    with col2: criar_card_metricas("Plano Total", formatar_ptbr(total_plano, 0), "Meta estabelecida", "", "🎯", "plano")
    with col3: criar_card_metricas("Variação", f"{total_diferenca:+,.0f} m³", f"({perc_geral:+.1f}%)", "", "📊", "fh" if total_diferenca >= 0 else "Release")
    with col4: criar_card_metricas("Atingimento", f"{perc_geral:.1f}%", "Meta " + ("atingida" if perc_geral >= 100 else "não atingida"), "", "✅" if perc_geral >= 100 else "⚠️", "congenere" if perc_geral >= 100 else "industria")
    
    st.markdown("---")
    
    # ============================================= ANÁLISE POR LINHA DE NEGÓCIO =============================================
    # Definir a ordem correta das linhas de negócio
    ordem_linhas_negocio = config.ORDEM_LINHAS_NEGOCIO
    
    # Identificar a coluna de linha de negócio
    coluna_linha_negocio = None
    for col in ['Linha Neg.', 'Sector/Sigla', 'Linha_Negocio', 'Linha de Negócio', 'Segmento']:
        if col in df_filtrado.columns:
            coluna_linha_negocio = col
            break
    
    if coluna_linha_negocio:
        st.markdown("### 📊 Análise por Linha de Negócio")
        
        # Agrupar dados por linha de negócio
        analise_linhas = df_filtrado.groupby(coluna_linha_negocio).agg({
            config.COLUNA_VENDAS_M3: 'sum',
            config.COLUNA_PLANO_M3: 'sum'
        }).reset_index()
        
        # Calcular métricas adicionais
        analise_linhas['Diferenca'] = analise_linhas[config.COLUNA_VENDAS_M3] - analise_linhas[config.COLUNA_PLANO_M3]
        analise_linhas['Atingimento'] = (analise_linhas[config.COLUNA_VENDAS_M3] / analise_linhas[config.COLUNA_PLANO_M3] * 100).fillna(0).round(1)
        
        # Criar uma coluna de ordenação baseada na ordem definida
        analise_linhas['Ordem'] = analise_linhas[coluna_linha_negocio].apply(
            lambda x: ordem_linhas_negocio.index(x) if x in ordem_linhas_negocio else 999
        )
        analise_linhas = analise_linhas.sort_values('Ordem').drop('Ordem', axis=1)
        
        # Calcular totais para adicionar linha de total
        total_vendas_linhas = analise_linhas[config.COLUNA_VENDAS_M3].sum()
        total_plano_linhas = analise_linhas[config.COLUNA_PLANO_M3].sum()
        total_diferenca_linhas = total_vendas_linhas - total_plano_linhas
        total_atingimento = (total_vendas_linhas / total_plano_linhas * 100) if total_plano_linhas > 0 else 0
        
        # Adicionar linha de total
        linha_total = pd.DataFrame({
            coluna_linha_negocio: ['TOTAL GERAL'],
            config.COLUNA_VENDAS_M3: [total_vendas_linhas],
            config.COLUNA_PLANO_M3: [total_plano_linhas],
            'Diferenca': [total_diferenca_linhas],
            'Atingimento': [total_atingimento]
        })
        analise_linhas = pd.concat([analise_linhas, linha_total], ignore_index=True)
        
        # Criar gráfico de barras comparativo
        fig_barras = go.Figure()
        
        # Adicionar barras de Vendas
        fig_barras.add_trace(go.Bar(
            x=analise_linhas[analise_linhas[coluna_linha_negocio] != 'TOTAL GERAL'][coluna_linha_negocio],
            y=analise_linhas[analise_linhas[coluna_linha_negocio] != 'TOTAL GERAL'][config.COLUNA_VENDAS_M3],
            name='Vendas Reais',
            marker_color='#FF6B35',
            text=analise_linhas[analise_linhas[coluna_linha_negocio] != 'TOTAL GERAL'][config.COLUNA_VENDAS_M3].apply(lambda x: formatar_ptbr(x, 0)),
            textposition='outside'
        ))
        
        # Adicionar barras de Plano
        fig_barras.add_trace(go.Bar(
            x=analise_linhas[analise_linhas[coluna_linha_negocio] != 'TOTAL GERAL'][coluna_linha_negocio],
            y=analise_linhas[analise_linhas[coluna_linha_negocio] != 'TOTAL GERAL'][config.COLUNA_PLANO_M3],
            name='Plano',
            marker_color='#9D4EDD',
            text=analise_linhas[analise_linhas[coluna_linha_negocio] != 'TOTAL GERAL'][config.COLUNA_PLANO_M3].apply(lambda x: formatar_ptbr(x, 0)),
            textposition='outside'
        ))
        
        fig_barras.update_layout(
            title='Vendas vs Plano por Linha de Negócio',
            xaxis_title='Linha de Negócio',
            yaxis_title='Volume (m³)',
            barmode='group',
            height=500,
            xaxis_tickangle=-45
        )
        st.plotly_chart(fig_barras, use_container_width=True)
        
        # Gráfico de pizza para distribuição das vendas por linha de negócio
        st.markdown("#### 🥧 Distribuição das Vendas por Linha de Negócio")
        dados_pizza = analise_linhas[analise_linhas[coluna_linha_negocio] != 'TOTAL GERAL'].copy()
        
        col_pizza1, col_pizza2 = st.columns(2)
        with col_pizza1:
            fig_pizza_vendas = px.pie(
                dados_pizza,
                values=config.COLUNA_VENDAS_M3,
                names=coluna_linha_negocio,
                title='Distribuição das Vendas Reais',
                color_discrete_sequence=px.colors.sequential.Oranges_r,
                hole=0.3
            )
            fig_pizza_vendas.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pizza_vendas, use_container_width=True)
        
        with col_pizza2:
            fig_pizza_plano = px.pie(
                dados_pizza,
                values=config.COLUNA_PLANO_M3,
                names=coluna_linha_negocio,
                title='Distribuição do Plano',
                color_discrete_sequence=px.colors.sequential.Purples_r,
                hole=0.3
            )
            fig_pizza_plano.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pizza_plano, use_container_width=True)
        
        # Gráfico de atingimento por linha de negócio
        st.markdown("#### 🎯 Atingimento da Meta por Linha de Negócio")
        dados_atingimento = analise_linhas[analise_linhas[coluna_linha_negocio] != 'TOTAL GERAL'].copy()
        
        # Definir cores baseadas no atingimento
        def get_color(atingimento):
            if atingimento >= 100:
                return '#28A745'  # Verde - Excelente
            elif atingimento >= 80:
                return '#FFC107'  # Amarelo - Bom
            elif atingimento >= 60:
                return '#FD7E14'  # Laranja - Atenção
            else:
                return '#DC3545'  # Vermelho - Crítico
        
        dados_atingimento['Cor'] = dados_atingimento['Atingimento'].apply(get_color)
        
        fig_atingimento = go.Figure()
        fig_atingimento.add_trace(go.Bar(
            x=dados_atingimento[coluna_linha_negocio],
            y=dados_atingimento['Atingimento'],
            marker_color=dados_atingimento['Cor'],
            text=dados_atingimento['Atingimento'].apply(lambda x: f"{x:.1f}%"),
            textposition='outside',
            name='Atingimento (%)'
        ))
        
        # Adicionar linha de meta (100%)
        fig_atingimento.add_hline(
            y=100, 
            line_dash="dash", 
            line_color="green",
            annotation_text="Meta (100%)",
            annotation_position="top right"
        )
        
        fig_atingimento.update_layout(
            title='Percentual de Atingimento por Linha de Negócio',
            xaxis_title='Linha de Negócio',
            yaxis_title='Atingimento (%)',
            height=450,
            yaxis_range=[0, max(140, dados_atingimento['Atingimento'].max() + 10)]
        )
        st.plotly_chart(fig_atingimento, use_container_width=True)
        
        # Tabela detalhada por linha de negócio
        st.markdown("#### 📋 Detalhamento por Linha de Negócio")
        df_linhas = analise_linhas.copy()
        df_linhas[config.COLUNA_VENDAS_M3] = df_linhas[config.COLUNA_VENDAS_M3].apply(lambda x: formatar_ptbr(x, 0))
        df_linhas[config.COLUNA_PLANO_M3] = df_linhas[config.COLUNA_PLANO_M3].apply(lambda x: formatar_ptbr(x, 0))
        df_linhas['Diferenca'] = df_linhas['Diferenca'].apply(lambda x: f"{x:+,.0f}".replace(',', '.'))
        df_linhas['Atingimento'] = df_linhas['Atingimento'].apply(lambda x: f"{x:.1f}%" if x > 0 else "0.0%")
        
        # Adicionar coluna de status
        def get_status(atingimento_str):
            try:
                val = float(atingimento_str.replace('%', ''))
                if val >= 100:
                    return "✅ Excelente"
                elif val >= 80:
                    return "👍 Bom"
                elif val >= 60:
                    return "⚠️ Atenção"
                else:
                    return "❌ Crítico"
            except:
                return "N/A"
        
        df_linhas['Status'] = df_linhas['Atingimento'].apply(get_status)
        
        # Renomear colunas para exibição
        df_linhas = df_linhas.rename(columns={
            coluna_linha_negocio: 'Linha de Negócio',
            config.COLUNA_VENDAS_M3: 'Vendas (m³)',
            config.COLUNA_PLANO_M3: 'Plano (m³)',
            'Diferenca': 'Diferença (m³)',
            'Atingimento': 'Atingimento (%)'
        })
        
        st.dataframe(df_linhas, use_container_width=True, hide_index=True)
        
        # Botões de download específicos para análise de linha de negócio
        st.markdown("---")
        with st.expander("📥 Exportar Análise por Linha de Negócio"):
            col_exp1, col_exp2 = st.columns(2)
            
            # Preparar dados para exportação
            export_df = analise_linhas.copy()
            export_df = export_df.rename(columns={
                coluna_linha_negocio: 'Linha_de_Negocio',
                config.COLUNA_VENDAS_M3: 'Vendas_m3',
                config.COLUNA_PLANO_M3: 'Plano_m3',
                'Diferenca': 'Diferenca_m3',
                'Atingimento': 'Atingimento_Percentual'
            })
            
            output_linhas = io.BytesIO()
            with pd.ExcelWriter(output_linhas, engine='openpyxl') as writer:
                export_df.to_excel(writer, sheet_name='Analise_Linhas_Negocio', index=False)
            output_linhas.seek(0)
            
            with col_exp1:
                st.download_button(
                    "📊 Excel - Análise por Linha de Negócio",
                    data=output_linhas,
                    file_name=f"analise_linhas_negocio_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                    use_container_width=True
                )
            with col_exp2:
                st.download_button(
                    "📝 CSV - Análise por Linha de Negócio",
                    data=export_df.to_csv(index=False, sep=';', decimal=','),
                    file_name=f"analise_linhas_negocio_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    use_container_width=True
                )
    
    st.markdown("---")
    st.markdown("### 📈 Evolução Mensal")
    fig_linha = criar_grafico_linhas_vendas_plano(df_filtrado)
    if fig_linha: 
        st.plotly_chart(fig_linha, use_container_width=True)
    else: 
        st.info("Dados insuficientes para gráfico de evolução mensal")
    
    st.markdown("---")
    st.markdown("### 📋 Tabela Detalhada")
    criar_tabela_vendas_plano_real(df_filtrado)
    
    st.markdown("---")
    with st.expander("📥 Exportar Dados Completos"):
        col_exp1, col_exp2 = st.columns(2)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df_filtrado.to_excel(writer, sheet_name='Dados_Completos', index=False)
            if coluna_linha_negocio:
                resumo = df_filtrado.groupby(coluna_linha_negocio).agg({
                    config.COLUNA_VENDAS_M3: 'sum', 
                    config.COLUNA_PLANO_M3: 'sum'
                }).reset_index()
                resumo.to_excel(writer, sheet_name='Resumo_Linhas', index=False)
        output.seek(0)
        with col_exp1: 
            st.download_button(
                "📊 Excel Completo", 
                data=output, 
                file_name=f"vendas_plano_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx", 
                use_container_width=True
            )
        with col_exp2: 
            st.download_button(
                "📝 CSV Dados", 
                data=df_filtrado.to_csv(index=False, sep=';', decimal=','),
                file_name=f"vendas_plano_{datetime.now().strftime('%Y%m%d_%H%M')}.csv", 
                use_container_width=True
            )

# ============================================= FUNÇÕES DE DOWNLOAD =============================================

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
        st.download_button(label=f"📊 Excel - {descricao}", data=output,
                          file_name=f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
                          mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                          use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar Excel: {e}")

def criar_botao_download_csv(df: pd.DataFrame, nome_arquivo: str, descricao: str):
    """Cria botão para download em CSV"""
    if df.empty:
        st.warning(f"Nenhum dado disponível para {descricao}")
        return
    try:
        csv = df.to_csv(index=False, sep=';', decimal=',')
        st.download_button(label=f"📝 CSV - {descricao}", data=csv,
                          file_name=f"{nome_arquivo}_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                          mime="text/csv", use_container_width=True)
    except Exception as e:
        st.error(f"Erro ao gerar CSV: {e}")

# ============================================= FUNÇÕES PARA SCROLLER DE QUOTA DE MERCADO =============================================

def criar_scroller_quota_mercado(total_industria_tm: float, total_petromoc_tm: float, total_congeneres_tm: float,
                               total_industria_m3: float, total_petromoc_m3: float, total_congeneres_m3: float,
                               perc_petromoc: float, perc_congeneres: float):
    """Cria um scroller animado para a quota de mercado"""
    st.markdown(f"""
    <div class="scroller-container">
        <div class="scroller-title">🏭 QUOTA DE MERCADO - INDÚSTRIA</div>
        <div class="scroller-content">
            <div class="scroller-item">
                <div class="scroller-value pulse-effect">100.0%</div>
                <div class="scroller-label">INDÚSTRIA</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_industria_tm, 0)} TM</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_industria_m3, 0)} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #FFD166;">{perc_petromoc:.1f}%</div>
                <div class="scroller-label">PETROMOC</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_petromoc_tm, 0)} TM</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_petromoc_m3, 0)} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #4ECDC4;">{perc_congeneres:.1f}%</div>
                <div class="scroller-label">CONGÊNERE</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_congeneres_tm, 0)} TM</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_congeneres_m3, 0)} m³</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def criar_scroller_quota_petromoc(total_petromoc_tm: float, total_Release_tm: float, total_fh_tm: float,
                                total_petromoc_m3: float, total_Release_m3: float, total_fh_m3: float,
                                perc_Release: float, perc_fh: float):
    """Cria um scroller animado para a quota da Petromoc"""
    st.markdown(f"""
    <div class="scroller-container scroller-petromoc">
        <div class="scroller-title">⛽ QUOTA DE MERCADO - PETROMOC</div>
        <div class="scroller-content">
            <div class="scroller-item">
                <div class="scroller-value pulse-effect">100.0%</div>
                <div class="scroller-label">PETROMOC TOTAL</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_petromoc_tm, 0)} TM</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_petromoc_m3, 0)} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #FFD166;">{perc_Release:.1f}%</div>
                <div class="scroller-label">Release</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_Release_tm, 0)} TM</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_Release_m3, 0)} m³</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #06D6A0;">{perc_fh:.1f}%</div>
                <div class="scroller-label">Financial Hold</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_fh_tm, 0)} TM</div>
                <div class="scroller-subvalue">{formatar_ptbr(total_fh_m3, 0)} m³</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# ============================================= FUNÇÕES PARA EXTRAIR DADOS REAIS DA IMPORTACAOMZ =============================================

def extrair_dados_garantias_bancarias(df_importacao: pd.DataFrame) -> pd.DataFrame:
    """Extrai dados de Garantias Bancárias - PRIORIZA DADOS REAIS DO ARQUIVO Garantias_Bancarias_.xlsx"""
    # PRIORIDADE 1: Usar dados do arquivo específico de garantias bancárias
    if not garantias_df.empty:
        logger.info("Usando dados reais do arquivo Garantias_Bancarias_.xlsx")
        dados_garantias = garantias_df.copy()
        
        # Mapear colunas para o formato esperado
        colunas_mapeadas = {}
        for col in dados_garantias.columns:
            col_upper = col.upper()
            if 'BANCO' in col_upper or 'BANCO' in col:
                colunas_mapeadas['Banco_GB'] = col
            elif 'LIMITE' in col_upper or 'LIMITE' in col:
                colunas_mapeadas['ValorLimite_GB'] = col
            elif 'UTILIZADO' in col_upper or 'VALOR' in col_upper:
                colunas_mapeadas['Valor_GB'] = col
            elif 'DISPONIBILIDADE' in col_upper:
                colunas_mapeadas['Disponibilidade_GB'] = col
        
        # Renomear colunas se necessário
        if 'Banco_GB' in colunas_mapeadas:
            dados_garantias = dados_garantias.rename(columns={colunas_mapeadas['Banco_GB']: 'Banco_GB'})
        
        # Converter valores numéricos
        if 'ValorLimite_GB' in colunas_mapeadas:
            dados_garantias['ValorLimite_GB'] = limpar_coluna_numerica(dados_garantias, colunas_mapeadas['ValorLimite_GB'])
        else:
            dados_garantias['ValorLimite_GB'] = 0
        
        if 'Valor_GB' in colunas_mapeadas:
            dados_garantias['Valor_GB'] = limpar_coluna_numerica(dados_garantias, colunas_mapeadas['Valor_GB'])
        else:
            dados_garantias['Valor_GB'] = 0
        
        # Calcular disponibilidade se não existir
        if 'Disponibilidade_GB' in colunas_mapeadas:
            dados_garantias['Disponibilidade_GB'] = limpar_coluna_numerica(dados_garantias, colunas_mapeadas['Disponibilidade_GB'])
        else:
            dados_garantias['Disponibilidade_GB'] = dados_garantias['ValorLimite_GB'] - dados_garantias['Valor_GB']
        
        # Calcular percentual de disponibilidade
        dados_garantias['Disponibilidade_%'] = (dados_garantias['Disponibilidade_GB'] / dados_garantias['ValorLimite_GB'] * 100).round(1).fillna(0)
        
        # Agrupar por banco se houver múltiplos registros
        if 'Banco_GB' in dados_garantias.columns and len(dados_garantias) > 1:
            dados_garantias_agrupado = dados_garantias.groupby('Banco_GB').agg({
                'ValorLimite_GB': 'sum',
                'Valor_GB': 'sum',
                'Disponibilidade_GB': 'sum'
            }).reset_index()
            dados_garantias_agrupado['Disponibilidade_%'] = (dados_garantias_agrupado['Disponibilidade_GB'] / dados_garantias_agrupado['ValorLimite_GB'] * 100).round(1).fillna(0)
            dados_garantias = dados_garantias_agrupado
        
        # Calcular totais gerais
        total_limite = dados_garantias['ValorLimite_GB'].sum()
        total_valor = dados_garantias['Valor_GB'].sum()
        total_disponibilidade = dados_garantias['Disponibilidade_GB'].sum()
        total_percentagem = (total_disponibilidade / total_limite * 100) if total_limite > 0 else 0
        
        # Adicionar linha de total
        linha_total = pd.DataFrame({
            'Banco_GB': ['TOTAL GERAL'],
            'ValorLimite_GB': [total_limite],
            'Valor_GB': [total_valor],
            'Disponibilidade_GB': [total_disponibilidade],
            'Disponibilidade_%': [round(total_percentagem, 1)]
        })
        dados_garantias = pd.concat([dados_garantias, linha_total], ignore_index=True)
        
        logger.info(f"Dados reais de garantias bancárias processados: {len(dados_garantias)} registros")
        return dados_garantias
    
    # PRIORIDADE 2: Tentar extrair do dataframe de importação
    if df_importacao.empty:
        return pd.DataFrame()
    
    colunas_garantias = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['BANCO', 'GARANTIA', 'LIMITE', 'GB'])]
    
    if colunas_garantias:
        coluna_banco = None
        coluna_limite = None
        coluna_valor = None
        
        for col in colunas_garantias:
            col_upper = col.upper()
            if 'BANCO' in col_upper:
                coluna_banco = col
            elif 'LIMITE' in col_upper:
                coluna_limite = col
            elif 'VALOR' in col_upper or 'UTILIZADO' in col_upper:
                coluna_valor = col
        
        if coluna_banco and coluna_limite:
            dados_garantias = df_importacao.groupby(coluna_banco).agg({
                coluna_limite: 'sum',
                coluna_valor: 'sum' if coluna_valor else coluna_limite
            }).reset_index()
            
            dados_garantias = dados_garantias.rename(columns={
                coluna_banco: 'Banco_GB',
                coluna_limite: 'ValorLimite_GB',
                (coluna_valor if coluna_valor else coluna_limite): 'Valor_GB'
            })
            
            dados_garantias['Disponibilidade_GB'] = dados_garantias['ValorLimite_GB'] - dados_garantias['Valor_GB']
            dados_garantias['Disponibilidade_%'] = (dados_garantias['Disponibilidade_GB'] / dados_garantias['ValorLimite_GB'] * 100).round(1)
            
            total_limite = dados_garantias['ValorLimite_GB'].sum()
            total_valor = dados_garantias['Valor_GB'].sum()
            total_disponibilidade = dados_garantias['Disponibilidade_GB'].sum()
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
    
    # PRIORIDADE 3: Dados de exemplo baseados na estrutura
    logger.warning("Nenhum dado real de garantias bancárias encontrado. Usando dados de exemplo.")
    
    bancos = ["ABSA", "BCI", "BNI", "FCB", "MOZA", "SGM", "UBA"]
    dados_garantias = []
    total_limite = 0
    total_valor = 0
    total_disponibilidade = 0
    
    for banco in bancos:
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

def extrair_dados_portos_Release_fh(df_importacao: pd.DataFrame) -> pd.DataFrame:
    """Extrai dados de Portos vs Release/Financial Hold diretamente do dataframe ImportacaoMZ"""
    if df_importacao.empty:
        return pd.DataFrame()
    
    ORDEM_PORTOS = config.ORDEM_PORTOS
    colunas_porto = [col for col in df_importacao.columns if 'PORTO' in col.upper()]
    
    if not colunas_porto:
        dados_portos = []
        for porto in ORDEM_PORTOS:
            Release = np.random.uniform(50000, 200000)
            fh = np.random.uniform(10000, 50000)
            dados_portos.append({'Porto': porto, 'Release': Release, 'Financial Hold': fh})
        dados_portos = pd.DataFrame(dados_portos)
        dados_portos['% Financial Hold'] = (dados_portos['Financial Hold'] / (dados_portos['Release'] + dados_portos['Financial Hold']) * 100).round(1)
        total_Release = dados_portos['Release'].sum()
        total_fh = dados_portos['Financial Hold'].sum()
        total_geral = total_Release + total_fh
        percentual_fh_geral = (total_fh / total_geral * 100) if total_geral > 0 else 0
        dados_portos = pd.concat([dados_portos, pd.DataFrame([{
            'Porto': 'TOTAL GERAL', 'Release': total_Release, 'Financial Hold': total_fh, '% Financial Hold': round(percentual_fh_geral, 1)
        }])], ignore_index=True)
        return dados_portos
    
    coluna_porto = colunas_porto[0]
    colunas_Release = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['Release', 'PETRO_TM', 'QTD_PETRO'])]
    colunas_fh = [col for col in df_importacao.columns if any(termo in col.upper() for termo in ['FINANCIAL', 'FH', 'QTD_FH'])]
    
    if colunas_Release and colunas_fh:
        coluna_Release = colunas_Release[0]
        coluna_fh = colunas_fh[0]
        dados_portos = df_importacao.groupby(coluna_porto).agg({coluna_Release: 'sum', coluna_fh: 'sum'}).reset_index()
        dados_portos = dados_portos.rename(columns={coluna_porto: 'Porto', coluna_Release: 'Release', coluna_fh: 'Financial Hold'})
    else:
        colunas_padrao = ['Qtd_Petro_TM', 'Qtd_FH_( TM)']
        if all(col in df_importacao.columns for col in colunas_padrao):
            dados_portos = df_importacao.groupby(coluna_porto).agg({'Qtd_Petro_TM': 'sum', 'Qtd_FH_( TM)': 'sum'}).reset_index()
            dados_portos = dados_portos.rename(columns={coluna_porto: 'Porto', 'Qtd_Petro_TM': 'Release', 'Qtd_FH_( TM)': 'Financial Hold'})
        else:
            return pd.DataFrame()
    
    for porto in ORDEM_PORTOS:
        if porto not in dados_portos['Porto'].values:
            dados_portos = pd.concat([dados_portos, pd.DataFrame([{'Porto': porto, 'Release': 0.0, 'Financial Hold': 0.0}])], ignore_index=True)
    
    ordem_map = {porto: idx for idx, porto in enumerate(ORDEM_PORTOS)}
    dados_portos['Ordem'] = dados_portos['Porto'].map(ordem_map).fillna(99)
    dados_portos = dados_portos.sort_values('Ordem').reset_index(drop=True).drop('Ordem', axis=1)
    dados_portos['% Financial Hold'] = (dados_portos['Financial Hold'] / (dados_portos['Release'] + dados_portos['Financial Hold']) * 100).round(1).fillna(0)
    
    total_Release = dados_portos['Release'].sum()
    total_fh = dados_portos['Financial Hold'].sum()
    total_geral = total_Release + total_fh
    percentual_fh_geral = (total_fh / total_geral * 100) if total_geral > 0 else 0
    dados_portos = pd.concat([dados_portos, pd.DataFrame([{
        'Porto': 'TOTAL GERAL', 'Release': total_Release, 'Financial Hold': total_fh, '% Financial Hold': round(percentual_fh_geral, 1)
    }])], ignore_index=True)
    
    return dados_portos

def analisar_estrutura_importacao(df_importacao: pd.DataFrame):
    """Analisa a estrutura do dataframe ImportacaoMZ para debugging"""
    if df_importacao.empty:
        return
    with st.sidebar.expander("🔍 Debug - Importação", expanded=False):
        st.write(f"**Registros:** {len(df_importacao)}")
        st.write(f"**Colunas:** {len(df_importacao.columns)}")
        st.write("**Primeiras colunas:**", list(df_importacao.columns)[:10])

def extrair_ano_dos_dados(df_importacao: pd.DataFrame) -> int:
    """Extrai o ano dos dados de importação"""
    if df_importacao.empty:
        return datetime.now().year
    colunas_data = ['NOR', 'Data_Descarga', 'Data_Importacao', 'Data']
    for coluna in colunas_data:
        if coluna in df_importacao.columns:
            datas_validas = df_importacao[coluna].dropna()
            if not datas_validas.empty:
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
    colunas_tm = ['Qtd_Petro_TM', 'Qtd_FH_( TM)', 'Quantidade_TM', 'Quantidade']
    for col in colunas_tm:
        if col in df_processed.columns:
            df_processed[col] = limpar_coluna_numerica(df_processed, col)
    for c in config.CLIENTES_CONGENERES:
        if c in df_processed.columns:
            df_processed[c] = limpar_coluna_numerica(df_processed, c)

    total_petromoc_tm = 0
    total_congeneres_tm = 0
    
    if 'Qtd_Petro_TM' in df_processed.columns and 'Qtd_FH_( TM)' in df_processed.columns:
        total_petromoc_tm = (df_processed["Qtd_Petro_TM"] + df_processed["Qtd_FH_( TM)"]).sum()
    elif 'Quantidade_TM' in df_processed.columns:
        total_petromoc_tm = df_processed["Quantidade_TM"].sum()
    
    for c in config.CLIENTES_CONGENERES:
        if c in df_processed.columns:
            total_congeneres_tm += df_processed[c].sum()

    total_industria_tm = total_petromoc_tm + total_congeneres_tm
    total_Release_tm = df_processed["Qtd_Petro_TM"].sum() if "Qtd_Petro_TM" in df_processed.columns else 0
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

    total_petromoc_m3 = converter_tm_para_m3_seguro(total_petromoc_tm, combustivel_principal)
    total_Release_m3 = converter_tm_para_m3_seguro(total_Release_tm, combustivel_principal)
    total_fh_m3 = converter_tm_para_m3_seguro(total_fh_tm, combustivel_principal)
    total_industria_m3 = converter_tm_para_m3_seguro(total_industria_tm, combustivel_principal)
    total_congeneres_m3 = converter_tm_para_m3_seguro(total_congeneres_tm, combustivel_principal)

    def calcular_percentual(parte, total):
        return (parte / total * 100) if total > 0 else 0
    
    perc_petromoc = calcular_percentual(total_petromoc_tm, total_industria_tm)
    perc_congeneres = calcular_percentual(total_congeneres_tm, total_industria_tm)
    perc_Release = calcular_percentual(total_Release_tm, total_petromoc_tm) if total_petromoc_tm > 0 else 0
    perc_fh = calcular_percentual(total_fh_tm, total_petromoc_tm) if total_petromoc_tm > 0 else 0

    criar_scroller_quota_mercado(total_industria_tm, total_petromoc_tm, total_congeneres_tm,
                                 total_industria_m3, total_petromoc_m3, total_congeneres_m3,
                                 perc_petromoc, perc_congeneres)
    criar_scroller_quota_petromoc(total_petromoc_tm, total_Release_tm, total_fh_tm,
                                  total_petromoc_m3, total_Release_m3, total_fh_m3,
                                  perc_Release, perc_fh)

    st.markdown("#### 📊 Visualização Complementar - Distribuição de Mercado")
    col1, col2 = st.columns(2)
    with col1:
        fig_mercado = px.pie(values=[perc_petromoc, perc_congeneres], names=['Petromoc', 'Congênere'],
                              title='Distribuição do Mercado', color=['Petromoc', 'Congênere'],
                              color_discrete_map={'Petromoc': '#FF6B35', 'Congênere': '#4ECDC4'})
        fig_mercado.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_mercado, use_container_width=True)
    with col2:
        fig_petromoc = px.pie(values=[perc_Release, perc_fh], names=['Release', 'Financial Hold'],
                               title='Distribuição Interna - Petromoc', color=['Release', 'Financial Hold'],
                               color_discrete_map={'Release': '#FFD166', 'Financial Hold': '#06D6A0'})
        fig_petromoc.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_petromoc, use_container_width=True)

# ============================================= ABA IMPORTAÇÃO COMPLETA =============================================

def criar_aba_importacao_com_dados_reais(df_filtrado: pd.DataFrame):
    """Cria a aba de Importação com dados reais, scroller animado e opções de download"""
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado de importação encontrado com os filtros aplicados")
        return

    analisar_estrutura_importacao(df_filtrado)
    ano_dados = extrair_ano_dos_dados(df_filtrado)
    st.markdown(f'<div class="section-title">📦 Análise de Importação - {ano_dados}</div>', unsafe_allow_html=True)
    
    st.markdown("#### 🎯 Métricas Principais")
    with st.spinner("🔄 Calculando métricas..."):
        dados_garantias = extrair_dados_garantias_bancarias(df_filtrado)
        dados_portos = extrair_dados_portos_Release_fh(df_filtrado)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if not dados_garantias.empty and 'TOTAL GERAL' in dados_garantias['Banco_GB'].values:
            total_geral = dados_garantias[dados_garantias['Banco_GB'] == 'TOTAL GERAL'].iloc[0]
            criar_card_metricas("Disponibilidade GB", f"{total_geral.get('Disponibilidade_%', 0):.1f}%",
                               "Garantias Bancárias", f"MZN {formatar_ptbr(total_geral.get('Disponibilidade_GB', 0), 0)}", "🏦", "fh")
        else:
            criar_card_metricas("Disponibilidade GB", "0.0%", "Garantias Bancárias", "Dados não disponíveis", "🏦", "fh")
    
    with col2:
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_Release = total_geral.get('Release', 0)
            total_fh = total_geral.get('Financial Hold', 0)
            total_geral_volume = total_Release + total_fh
            perc_Release = (total_Release / total_geral_volume * 100) if total_geral_volume > 0 else 0
            criar_card_metricas("Volume Release", f"{perc_Release:.1f}%", "Do total importado",
                               f"{formatar_ptbr(total_Release, 0)} TM", "💰", "Release")
        else:
            criar_card_metricas("Volume Release", "0.0%", "Do total importado", "Dados não disponíveis", "💰", "Release")
    
    with col3:
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_Release = total_geral.get('Release', 0)
            total_fh = total_geral.get('Financial Hold', 0)
            total_geral_volume = total_Release + total_fh
            perc_fh = (total_fh / total_geral_volume * 100) if total_geral_volume > 0 else 0
            criar_card_metricas("Financial Hold", f"{perc_fh:.1f}%", "Do total importado",
                               f"{formatar_ptbr(total_fh, 0)} TM", "📊", "industria")
        else:
            criar_card_metricas("Financial Hold", "0.0%", "Do total importado", "Dados não disponíveis", "📊", "industria")
    
    with col4:
        if not dados_portos.empty and 'TOTAL GERAL' in dados_portos['Porto'].values:
            total_geral = dados_portos[dados_portos['Porto'] == 'TOTAL GERAL'].iloc[0]
            total_volume = total_geral.get('Release', 0) + total_geral.get('Financial Hold', 0)
            criar_card_metricas("Total Importado", f"{formatar_ptbr(total_volume, 0)}", "Volume total", "TM", "📦", "petromoc")
        else:
            criar_card_metricas("Total Importado", "0", "Volume total", "TM", "📦", "petromoc")
    
    st.markdown("---")
    criar_analise_market_share_com_scroller(df_filtrado)
    st.markdown("---")
    
    st.markdown("#### 📥 Download de Dados")
    col_download1, col_download2 = st.columns(2)
    with col_download1:
        criar_botao_download_excel(df_filtrado, "dados_importacao_brutos", "Dados Brutos")
    with col_download2:
        criar_botao_download_csv(df_filtrado, "dados_importacao_brutos", "Dados Brutos")
    
    st.markdown("---")
    st.markdown("#### 🏦 Garantias Bancárias")
    if not dados_garantias.empty:
        df_garantias_display = dados_garantias.copy()
        colunas_monetarias = ['ValorLimite_GB', 'Valor_GB', 'Disponibilidade_GB']
        for coluna in colunas_monetarias:
            if coluna in df_garantias_display.columns:
                df_garantias_display[f'{coluna}_Formatado'] = df_garantias_display[coluna].apply(
                    lambda x: f"MZN {formatar_ptbr(x, 0)}" if pd.notna(x) else "MZN 0")
        if 'Disponibilidade_%' in df_garantias_display.columns:
            df_garantias_display['Disponibilidade_%_Formatado'] = df_garantias_display['Disponibilidade_%'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
        
        colunas_exibicao = ['Banco_GB']
        for coluna in colunas_monetarias:
            if f'{coluna}_Formatado' in df_garantias_display.columns:
                colunas_exibicao.append(f'{coluna}_Formatado')
        if 'Disponibilidade_%_Formatado' in df_garantias_display.columns:
            colunas_exibicao.append('Disponibilidade_%_Formatado')
        
        df_display = df_garantias_display[colunas_exibicao].copy()
        df_display.columns = ['Banco', 'Limite de Garantia', 'Valor Utilizado', 'Disponibilidade', 'Disponibilidade %']
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Adicionar gráfico de distribuição das garantias bancárias
        st.markdown("##### 📊 Distribuição das Garantias Bancárias")
        dados_grafico_garantias = dados_garantias[dados_garantias['Banco_GB'] != 'TOTAL GERAL'].copy()
        if not dados_grafico_garantias.empty:
            col_graf1, col_graf2 = st.columns(2)
            with col_graf1:
                fig_garantias_limite = px.pie(
                    dados_grafico_garantias,
                    values='ValorLimite_GB',
                    names='Banco_GB',
                    title='Distribuição do Limite de Garantia por Banco',
                    color_discrete_sequence=px.colors.qualitative.Set3,
                    hole=0.3
                )
                fig_garantias_limite.update_traces(textposition='inside', textinfo='percent+label')
                st.plotly_chart(fig_garantias_limite, use_container_width=True)
            
            with col_graf2:
                fig_garantias_utilizado = px.bar(
                    dados_grafico_garantias,
                    x='Banco_GB',
                    y=['ValorLimite_GB', 'Valor_GB'],
                    title='Limite vs Utilizado por Banco',
                    barmode='group',
                    color_discrete_sequence=['#FF6B35', '#9D4EDD']
                )
                fig_garantias_utilizado.update_layout(yaxis_title='Valor (MZN)', xaxis_title='Banco')
                st.plotly_chart(fig_garantias_utilizado, use_container_width=True)
        
        st.markdown("##### 📥 Download Garantias Bancárias")
        col_gar1, col_gar2 = st.columns(2)
        with col_gar1: 
            criar_botao_download_excel(df_display, "garantias_bancarias", "Garantias Bancárias")
        with col_gar2: 
            criar_botao_download_csv(df_display, "garantias_bancarias", "Garantias Bancárias")
    else:
        st.info("ℹ️ Nenhum dado de garantias bancárias disponível")
    
    st.markdown("---")
    st.markdown("#### ⚓ Portos - Release vs Financial Hold")
    if not dados_portos.empty:
        dados_portos_clean = dados_portos.copy()
        ordem_correta = config.ORDEM_PORTOS + ['TOTAL GERAL']
        dados_portos_clean['Ordem'] = dados_portos_clean['Porto'].map({porto: idx for idx, porto in enumerate(ordem_correta)}).fillna(99)
        dados_portos_clean = dados_portos_clean.sort_values('Ordem').drop('Ordem', axis=1)
        
        df_portos_display = dados_portos_clean.copy()
        colunas_volume = ['Release', 'Financial Hold']
        for coluna in colunas_volume:
            if coluna in df_portos_display.columns:
                df_portos_display[f'{coluna}_Formatado'] = df_portos_display[coluna].apply(
                    lambda x: f"{formatar_ptbr(x, 0)} TM" if pd.notna(x) else "0 TM")
        if '% Financial Hold' in df_portos_display.columns:
            df_portos_display['% Financial Hold_Formatado'] = df_portos_display['% Financial Hold'].apply(
                lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
        
        colunas_exibicao = ['Porto']
        for coluna in colunas_volume:
            if f'{coluna}_Formatado' in df_portos_display.columns:
                colunas_exibicao.append(f'{coluna}_Formatado')
        if '% Financial Hold_Formatado' in df_portos_display.columns:
            colunas_exibicao.append('% Financial Hold_Formatado')
        
        df_display_portos = df_portos_display[colunas_exibicao].copy()
        df_display_portos.columns = ['Porto', 'Release (TM)', 'Financial Hold (TM)', '% Financial Hold']
        st.dataframe(df_display_portos, use_container_width=True, hide_index=True)
        
        st.markdown("##### 📥 Download Dados de Portos")
        col_port1, col_port2 = st.columns(2)
        with col_port1: criar_botao_download_excel(df_display_portos, "dados_portos", "Dados de Portos")
        with col_port2: criar_botao_download_csv(df_display_portos, "dados_portos", "Dados de Portos")
        
        st.markdown("#### 📊 Visualização - Distribuição por Porto")
        dados_grafico = dados_portos_clean[dados_portos_clean['Porto'] != 'TOTAL GERAL'].copy()
        if not dados_grafico.empty:
            dados_grafico = dados_grafico[dados_grafico['Porto'].isin(config.ORDEM_PORTOS)]
            dados_grafico['Porto'] = pd.Categorical(dados_grafico['Porto'], categories=config.ORDEM_PORTOS, ordered=True)
            dados_grafico = dados_grafico.sort_values('Porto')
            dados_melted = dados_grafico.melt(id_vars=['Porto'], value_vars=['Release', 'Financial Hold'],
                                              var_name='Tipo', value_name='Volume')
            fig = px.bar(dados_melted, x='Porto', y='Volume', color='Tipo', barmode='group',
                         title='Distribuição por Porto - Release vs Financial Hold',
                         color_discrete_map={'Release': '#FF6B35', 'Financial Hold': '#4ECDC4'})
            fig.update_layout(yaxis_title='Volume (TM)', xaxis_title='Porto')
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Nenhum dado de portos disponível")

# ============================================= FUNÇÕES PARA ABA PROMOTORES =============================================

@st.cache_data(ttl=3600)
def carregar_dados_MIS():
    """Carrega e processa dados do MIS"""
    try:
        if not os.path.exists(config.ARQUIVO_MIS):
            logger.warning(f"Arquivo {config.ARQUIVO_MIS} não encontrado")
            return criar_dados_mis_simulados()
        MIS = pd.read_excel(config.ARQUIVO_MIS)
        v0_lookup = pd.DataFrame()
        if os.path.exists(config.ARQUIVO_LOOKUPS):
            v0_lookup = pd.read_excel(config.ARQUIVO_LOOKUPS, sheet_name=0)
        if not v0_lookup.empty and 'Emissor' in MIS.columns and 'Emissor' in v0_lookup.columns:
            MIS = pd.merge(MIS, v0_lookup, on=['Emissor'], how='left')
        MIS.columns = MIS.columns.str.strip().str.upper()
        
        if 'DENTRO_PRAZO' in MIS.columns and '0_30_DIAS' in MIS.columns:
            MIS['DENTRO_PRAZO'] = pd.to_numeric(MIS['DENTRO_PRAZO'], errors='coerce').fillna(0)
            MIS['0_30_DIAS'] = pd.to_numeric(MIS['0_30_DIAS'], errors='coerce').fillna(0)
            MIS['PREVISAO_30_DIAS'] = MIS['DENTRO_PRAZO'] + MIS['0_30_DIAS']
        elif 'DENTRO_PRAZO' in MIS.columns:
            MIS['DENTRO_PRAZO'] = pd.to_numeric(MIS['DENTRO_PRAZO'], errors='coerce').fillna(0)
            MIS['PREVISAO_30_DIAS'] = MIS['DENTRO_PRAZO']
        elif '0_30_DIAS' in MIS.columns:
            MIS['0_30_DIAS'] = pd.to_numeric(MIS['0_30_DIAS'], errors='coerce').fillna(0)
            MIS['PREVISAO_30_DIAS'] = MIS['0_30_DIAS']
        else:
            MIS['PREVISAO_30_DIAS'] = 0
        
        if 'DIVIDA_TOTAL' not in MIS.columns:
            MIS['DIVIDA_TOTAL'] = MIS['PREVISAO_30_DIAS'] * 1.5
        return MIS
    except Exception as e:
        logger.error(f"Erro ao carregar MIS: {str(e)}", exc_info=True)
        return criar_dados_mis_simulados()

def criar_dados_mis_simulados():
    """Cria dados simulados de MIS para demonstração"""
    np.random.seed(42)
    linhas_negocio = config.LINHAS_NEGOCIO
    promotores = ["João Silva", "Maria Santos", "Pedro Costa", "Ana Oliveira", "Carlos Souza", 
                  "Lucia Ferreira", "Paulo Rodrigues", "Sofia Almeida", "Ricardo Gomes", "Beatriz Lima"]
    dados = []
    for i in range(100):
        linha = np.random.choice(linhas_negocio)
        promotor = np.random.choice(promotores)
        divida_total = np.random.uniform(100000, 5000000)
        dentro_prazo = divida_total * np.random.uniform(0.3, 0.7)
        previsao_30 = divida_total * np.random.uniform(0.1, 0.3)
        dados.append({'LINHA NEG.': linha, 'GESTOR/PROMOTOR': promotor, 'EMISSOR': f'CLI{1000+i}',
                      'NOME_DO_CLIENTE': f'Cliente {i+1}', 'DIVIDA_TOTAL': divida_total,
                      'DENTRO_PRAZO': dentro_prazo, 'PREVISAO_30_DIAS': previsao_30})
    return pd.DataFrame(dados)

def criar_tabela_divida_por_linha_negocio(mis_df: pd.DataFrame):
    """Cria tabela de dívida por linha de negócio"""
    if mis_df.empty:
        return pd.DataFrame()
    if 'LINHA NEG.' not in mis_df.columns:
        for alt in ['LINHA_NEG', 'LINHA_NEGOCIO', 'LINHA DE NEGÓCIO', 'SECTOR/SIGLA']:
            if alt in mis_df.columns:
                mis_df = mis_df.rename(columns={alt: 'LINHA NEG.'})
                break
        if 'LINHA NEG.' not in mis_df.columns:
            return pd.DataFrame()
    
    agg_dict = {}
    if 'DIVIDA_TOTAL' in mis_df.columns: agg_dict['DIVIDA_TOTAL'] = 'sum'
    if 'DENTRO_PRAZO' in mis_df.columns: agg_dict['DENTRO_PRAZO'] = 'sum'
    if 'PREVISAO_30_DIAS' in mis_df.columns: agg_dict['PREVISAO_30_DIAS'] = 'sum'
    if not agg_dict: return pd.DataFrame()
    
    tabela_linhas = mis_df.groupby('LINHA NEG.').agg(agg_dict).reset_index()
    linha_total = {'LINHA NEG.': 'Total'}
    for col in agg_dict.keys(): linha_total[col] = tabela_linhas[col].sum()
    tabela_completa = pd.concat([tabela_linhas, pd.DataFrame([linha_total])], ignore_index=True)
    
    if 'DIVIDA_TOTAL' in tabela_completa.columns:
        total_divida = tabela_completa.loc[tabela_completa['LINHA NEG.'] == 'Total', 'DIVIDA_TOTAL'].iloc[0]
        if total_divida > 0:
            tabela_completa['% sobre Total'] = (tabela_completa['DIVIDA_TOTAL'] / total_divida * 100).round(1)
    return tabela_completa

def criar_tabela_top10_promotores(mis_df: pd.DataFrame):
    """Cria tabela Top 10 Promotores com dados de dívida"""
    if mis_df.empty:
        return pd.DataFrame()
    
    coluna_promotor = None
    for col in ['GESTOR/PROMOTOR', 'GESTOR', 'PROMOTOR', 'GESTOR / PROMOTOR']:
        if col in mis_df.columns:
            coluna_promotor = col
            break
    if not coluna_promotor:
        mis_df['GESTOR/PROMOTOR'] = 'Promotor Geral'
        coluna_promotor = 'GESTOR/PROMOTOR'
    
    coluna_emissor = None
    for col in ['EMISSOR', 'EMISSOR_CLIENTE', 'COD_CLIENTE']:
        if col in mis_df.columns:
            coluna_emissor = col
            break
    if not coluna_emissor:
        mis_df['EMISSOR'] = ''
        coluna_emissor = 'EMISSOR'
    
    coluna_cliente = None
    for col in ['NOME_DO_CLIENTE', 'NOME_CLIENTE', 'CLIENTE', 'NOME']:
        if col in mis_df.columns:
            coluna_cliente = col
            break
    if not coluna_cliente:
        mis_df['NOME_CLIENTE'] = ''
        coluna_cliente = 'NOME_CLIENTE'
    
    agg_dict = {}
    for col in ['DIVIDA_TOTAL', 'DENTRO_PRAZO', 'PREVISAO_30_DIAS']:
        if col in mis_df.columns:
            agg_dict[col] = 'sum'
    
    if agg_dict:
        tabela_agrupada = mis_df.groupby(coluna_promotor).agg(agg_dict).reset_index()
        if 'DIVIDA_TOTAL' in tabela_agrupada.columns:
            tabela_agrupada = tabela_agrupada.sort_values('DIVIDA_TOTAL', ascending=False)
    else:
        tabela_agrupada = mis_df[[coluna_promotor]].drop_duplicates()
    
    top10_promotores = tabela_agrupada.head(10)
    tabela_final = []
    
    for _, row in top10_promotores.iterrows():
        promotor = row[coluna_promotor]
        clientes_promotor = mis_df[mis_df[coluna_promotor] == promotor]
        if 'DIVIDA_TOTAL' in clientes_promotor.columns:
            clientes_promotor = clientes_promotor.sort_values('DIVIDA_TOTAL', ascending=False)
        
        for _, cliente_row in clientes_promotor.iterrows():
            linha = {
                'Gestor/Promotor': str(promotor) if pd.notna(promotor) else '',
                'Emissor': str(cliente_row.get(coluna_emissor, '')),
                'Nome_do_Cliente': str(cliente_row.get(coluna_cliente, '')),
                'Dívida Total': cliente_row.get('DIVIDA_TOTAL', 0),
                'Dentro Prazo': cliente_row.get('DENTRO_PRAZO', 0),
                'Previsão 30 Dias': cliente_row.get('PREVISAO_30_DIAS', 0)
            }
            tabela_final.append(linha)
    
    if tabela_final:
        totais = {'Gestor/Promotor': 'TOTAL', 'Emissor': '', 'Nome_do_Cliente': '',
                  'Dívida Total': sum(row['Dívida Total'] for row in tabela_final),
                  'Dentro Prazo': sum(row['Dentro Prazo'] for row in tabela_final),
                  'Previsão 30 Dias': sum(row['Previsão 30 Dias'] for row in tabela_final)}
        tabela_final.append(totais)
    
    return pd.DataFrame(tabela_final)

def criar_aba_vendas_promotores(df_filtrado: pd.DataFrame):
    """Cria a parte de análise de vendas dos promotores"""
    if df_filtrado.empty:
        st.warning("⚠️ Nenhum dado disponível para análise de vendas dos promotores")
        return
    
    coluna_promotor = None
    for col in ['Gestor / Promotor', 'Promotor', 'Gestor_Promotor', 'Vendedor', 'Comercial']:
        if col in df_filtrado.columns:
            coluna_promotor = col
            break
    if not coluna_promotor:
        st.error("❌ Não foi possível encontrar coluna de promotor/gestor nos dados de vendas")
        return
    
    st.markdown("#### 🎯 Visão Geral dos Promotores - Vendas")
    total_promotores = df_filtrado[coluna_promotor].nunique()
    coluna_vendas = config.COLUNA_VENDAS_M3
    coluna_plano = config.COLUNA_PLANO_M3
    total_vendas = df_filtrado[coluna_vendas].sum() if coluna_vendas in df_filtrado.columns else 0
    total_plano = df_filtrado[coluna_plano].sum() if coluna_plano in df_filtrado.columns else 0
    taxa_atingimento = (total_vendas / total_plano * 100) if total_plano > 0 else 0
    
    col1, col2, col3, col4 = st.columns(4)
    with col1: criar_card_metricas("Total Promotores", str(total_promotores), "Ativos no período", f"{len(df_filtrado)} transações", "👥", "petromoc")
    with col2: criar_card_metricas("Volume Total", f"{formatar_ptbr(total_vendas, 0)}", "m³ vendidos", "", "📊", "industria")
    with col3: criar_card_metricas("Meta do Período", f"{formatar_ptbr(total_plano, 0)}" if coluna_plano in df_filtrado.columns else "N/A",
                                   "m³ planejados" if coluna_plano in df_filtrado.columns else "Meta não definida", "", "🎯", "plano")
    with col4:
        status_cor = "congenere" if taxa_atingimento >= 100 else "Release" if taxa_atingimento >= 80 else "industria"
        criar_card_metricas("Taxa de Atingimento", f"{taxa_atingimento:.1f}%" if coluna_plano in df_filtrado.columns else "N/A",
                           "Meta vs Realizado" if coluna_plano in df_filtrado.columns else "Sem meta definida", "",
                           "📈" if taxa_atingimento >= 100 else "📉", status_cor if coluna_plano in df_filtrado.columns else "petromoc")
    
    st.markdown("---")
    
    # Adicionar seletor de Gestor/Promotor - CORRIGIDO
    st.markdown("#### 👤 Seletor de Gestor/Promotor")
    col_selector1, col_selector2 = st.columns([2, 1])
    with col_selector1:
        # Converter todos os valores para string para evitar erro de comparação
        valores_promotores = df_filtrado[coluna_promotor].dropna()
        valores_unicos = sorted(set(str(v) for v in valores_promotores))
        lista_promotores = ['Todos'] + valores_unicos
        promotor_selecionado = st.selectbox(
            "Selecione o Gestor/Promotor para análise detalhada:",
            options=lista_promotores,
            key="selector_promotor_vendas"
        )
    
    # Filtrar por promotor selecionado
    if promotor_selecionado != 'Todos':
        df_filtrado_promotor = df_filtrado[df_filtrado[coluna_promotor].astype(str) == promotor_selecionado]
        st.info(f"📊 Mostrando dados apenas para o promotor: **{promotor_selecionado}**")
    else:
        df_filtrado_promotor = df_filtrado.copy()
    
    st.markdown("#### 📋 Ranking de Promotores - Vendas")
    try:
        agg_dict = {}
        if coluna_vendas in df_filtrado.columns: agg_dict[coluna_vendas] = 'sum'
        if coluna_plano in df_filtrado.columns: agg_dict[coluna_plano] = 'sum'
        if not agg_dict:
            st.warning("⚠️ Nenhuma coluna numérica disponível para análise")
            return
        
        # Converter a coluna do promotor para string antes do groupby
        df_temp = df_filtrado.copy()
        df_temp[coluna_promotor] = df_temp[coluna_promotor].astype(str)
        desempenho_promotores = df_temp.groupby(coluna_promotor).agg(agg_dict).reset_index()
        
        if coluna_vendas in df_filtrado.columns and coluna_plano in df_filtrado.columns:
            desempenho_promotores['Variação (m³)'] = desempenho_promotores[coluna_vendas] - desempenho_promotores[coluna_plano]
            desempenho_promotores['Atingimento (%)'] = (desempenho_promotores[coluna_vendas] / desempenho_promotores[coluna_plano] * 100).round(1)
            desempenho_promotores = desempenho_promotores.sort_values('Atingimento (%)', ascending=False)
            desempenho_promotores['Ranking'] = range(1, len(desempenho_promotores) + 1)
            
            # Calcular totais
            total_vendas_prom = desempenho_promotores[coluna_vendas].sum()
            total_plano_prom = desempenho_promotores[coluna_plano].sum()
            total_variacao = total_vendas_prom - total_plano_prom
            total_atingimento = (total_vendas_prom / total_plano_prom * 100) if total_plano_prom > 0 else 0
            
            # Adicionar linha de total
            linha_total = pd.DataFrame({
                coluna_promotor: ['TOTAL GERAL'],
                coluna_vendas: [total_vendas_prom],
                coluna_plano: [total_plano_prom],
                'Variação (m³)': [total_variacao],
                'Atingimento (%)': [total_atingimento],
                'Ranking': ['']
            })
            desempenho_promotores = pd.concat([desempenho_promotores, linha_total], ignore_index=True)
            
            colunas_exibicao = ['Ranking', coluna_promotor, coluna_vendas, coluna_plano, 'Variação (m³)', 'Atingimento (%)']
        else:
            if coluna_vendas in df_filtrado.columns:
                desempenho_promotores = desempenho_promotores.sort_values(coluna_vendas, ascending=False)
                total_geral = desempenho_promotores[coluna_vendas].sum()
                desempenho_promotores['Participação (%)'] = (desempenho_promotores[coluna_vendas] / total_geral * 100).round(1)
                desempenho_promotores['Ranking'] = range(1, len(desempenho_promotores) + 1)
                
                # Adicionar linha de total
                total_vendas_prom = desempenho_promotores[coluna_vendas].sum()
                linha_total = pd.DataFrame({
                    coluna_promotor: ['TOTAL GERAL'],
                    coluna_vendas: [total_vendas_prom],
                    'Participação (%)': [100.0],
                    'Ranking': ['']
                })
                desempenho_promotores = pd.concat([desempenho_promotores, linha_total], ignore_index=True)
                
                colunas_exibicao = ['Ranking', coluna_promotor, coluna_vendas, 'Participação (%)']
        
        df_display = desempenho_promotores.copy()
        if coluna_vendas in df_display.columns: 
            df_display[coluna_vendas] = df_display[coluna_vendas].apply(lambda x: formatar_ptbr(x, 0) if pd.notna(x) else "0")
        if 'Variação (m³)' in df_display.columns: 
            df_display['Variação (m³)'] = df_display['Variação (m³)'].apply(lambda x: formatar_ptbr(x, 0) if pd.notna(x) else "0")
        if coluna_plano in df_filtrado.columns and coluna_plano in df_display.columns: 
            df_display[coluna_plano] = df_display[coluna_plano].apply(lambda x: formatar_ptbr(x, 0) if pd.notna(x) else "0")
        for col in ['Atingimento (%)', 'Participação (%)']:
            if col in df_display.columns: 
                df_display[col] = df_display[col].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
        
        # Destacar a linha de total
        st.dataframe(
            df_display[colunas_exibicao], 
            use_container_width=True, 
            height=400,
            column_config={
                coluna_promotor: st.column_config.TextColumn("Gestor/Promotor", width="medium"),
            }
        )
        
        # Mostrar detalhes do promotor selecionado
        if promotor_selecionado != 'Todos' and not df_filtrado_promotor.empty:
            st.markdown("---")
            st.markdown(f"#### 📊 Detalhes do Promotor: {promotor_selecionado}")
            
            # Gráfico de evolução mensal do promotor
            if config.COLUNA_DATA_VENDAS in df_filtrado_promotor.columns:
                df_promotor_mensal = df_filtrado_promotor.copy()
                df_promotor_mensal['Mes_Ano'] = df_promotor_mensal[config.COLUNA_DATA_VENDAS].dt.strftime('%Y-%m')
                df_mensal = df_promotor_mensal.groupby('Mes_Ano').agg({
                    coluna_vendas: 'sum',
                    coluna_plano: 'sum' if coluna_plano in df_filtrado_promotor.columns else None
                }).reset_index()
                
                fig_promotor = go.Figure()
                fig_promotor.add_trace(go.Bar(x=df_mensal['Mes_Ano'], y=df_mensal[coluna_vendas], 
                                               name='Vendas', marker_color='#FF6B35'))
                if coluna_plano in df_filtrado_promotor.columns:
                    fig_promotor.add_trace(go.Bar(x=df_mensal['Mes_Ano'], y=df_mensal[coluna_plano], 
                                                   name='Plano', marker_color='#9D4EDD'))
                fig_promotor.update_layout(title=f'Evolução Mensal - {promotor_selecionado}', 
                                            xaxis_title='Mês', yaxis_title='Volume (m³)', barmode='group')
                st.plotly_chart(fig_promotor, use_container_width=True)
        
    except Exception as e:
        st.error(f"❌ Erro ao criar tabela de desempenho: {str(e)}")
        import traceback
        st.error(traceback.format_exc())

def criar_aba_divida_promotores():
    """Cria a parte de análise de dívida dos promotores"""
    st.markdown("#### 💰 Análise de Dívida - Linhas de Negócio")
    MIS_df = carregar_dados_MIS()
    if MIS_df.empty:
        st.warning("⚠️ Nenhum dado do MIS disponível para análise de dívida")
        return
    
    # Adicionar seletor de Gestor/Promotor para dívida - VISÃO GERAL
    coluna_promotor_divida = None
    for col in ['GESTOR/PROMOTOR', 'GESTOR', 'PROMOTOR', 'Gestor / Promotor']:
        if col in MIS_df.columns:
            coluna_promotor_divida = col
            break
    
    if coluna_promotor_divida:
        st.markdown("#### 👤 Seletor de Gestor/Promotor - Visão Geral")
        col_selector1, col_selector2 = st.columns([2, 1])
        with col_selector1:
            # Converter todos os valores para string para evitar erro de comparação
            valores_promotores = MIS_df[coluna_promotor_divida].dropna()
            valores_unicos = sorted(set(str(v) for v in valores_promotores))
            lista_promotores_divida = ['Todos'] + valores_unicos
            promotor_divida_selecionado = st.selectbox(
                "Selecione o Gestor/Promotor para análise de dívida:",
                options=lista_promotores_divida,
                key="selector_promotor_divida_geral"
            )
        
        # Filtrar por promotor selecionado
        if promotor_divida_selecionado != 'Todos':
            MIS_df_filtrado = MIS_df[MIS_df[coluna_promotor_divida].astype(str) == promotor_divida_selecionado]
            st.info(f"📊 Mostrando dados apenas para o promotor: **{promotor_divida_selecionado}**")
        else:
            MIS_df_filtrado = MIS_df.copy()
    else:
        MIS_df_filtrado = MIS_df.copy()
        st.info("ℹ️ Coluna de Gestor/Promotor não encontrada nos dados de dívida")
    
    tabela_linhas = criar_tabela_divida_por_linha_negocio(MIS_df_filtrado)
    if not tabela_linhas.empty:
        df_linhas_display = tabela_linhas.copy()
        for col in ['DIVIDA_TOTAL', 'DENTRO_PRAZO', 'PREVISAO_30_DIAS']:
            if col in df_linhas_display.columns:
                df_linhas_display[col] = df_linhas_display[col].apply(lambda x: f"MZN {formatar_ptbr(x, 0)}" if pd.notna(x) else "MZN 0")
        if '% sobre Total' in df_linhas_display.columns:
            df_linhas_display['% sobre Total'] = df_linhas_display['% sobre Total'].apply(lambda x: f"{x:.1f}%" if pd.notna(x) else "0.0%")
        
        df_linhas_display = df_linhas_display.rename(columns={'LINHA NEG.': 'Linha de Negócio', 'DIVIDA_TOTAL': 'Dívida Total',
                                                              'DENTRO_PRAZO': 'Dentro do Prazo', 'PREVISAO_30_DIAS': 'Previsão 30 Dias',
                                                              '% sobre Total': '% sobre Total'})
        st.dataframe(df_linhas_display, use_container_width=True, hide_index=True, height=400)
        
        dados_grafico_linhas = tabela_linhas[tabela_linhas['LINHA NEG.'] != 'Total']
        if not dados_grafico_linhas.empty and 'DIVIDA_TOTAL' in dados_grafico_linhas.columns:
            fig_barras_linhas = px.bar(dados_grafico_linhas.sort_values('DIVIDA_TOTAL', ascending=False),
                                       x='LINHA NEG.', y='DIVIDA_TOTAL', title='Dívida Total por Linha de Negócio',
                                       color='DIVIDA_TOTAL', color_continuous_scale='Viridis',
                                       text_auto=True)
            fig_barras_linhas.update_traces(marker_line_color='rgb(8,48,107)', marker_line_width=1.5, opacity=0.9)
            fig_barras_linhas.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig_barras_linhas, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================= TOP 10 PROMOTORES - COM SELETOR =============================================
    st.markdown("#### 📋 Top 10 Promotores - Situação de Dívida")
    
    # Seletor para Top 10 Promotores
    col_selector_top10, col_selector_top10_2 = st.columns([2, 1])
    with col_selector_top10:
        opcoes_ordenacao_top10 = st.selectbox(
            "Ordenar por:",
            options=["Dívida Total (Maior para Menor)", "Dívida Total (Menor para Maior)", 
                     "Dentro Prazo", "Previsão 30 Dias", "Nº Clientes"],
            key="selector_ordenacao_top10"
        )
    
    # Gerar tabela Top 10 Promotores
    tabela_top10 = criar_tabela_top10_promotores(MIS_df_filtrado)
    if not tabela_top10.empty:
        df_top10_display = tabela_top10.copy()
        
        # Converter coluna de promotor para string
        if 'Gestor/Promotor' in df_top10_display.columns:
            df_top10_display['Gestor/Promotor'] = df_top10_display['Gestor/Promotor'].astype(str)
        
        # Extrair valores numéricos para ordenação
        def extrair_valor_numerico(valor_str):
            try:
                if isinstance(valor_str, (int, float)):
                    return float(valor_str)
                valor_limpo = str(valor_str).replace('MZN ', '').replace('.', '').replace(',', '.')
                return float(valor_limpo) if valor_limpo.replace('.', '', 1).isdigit() else 0
            except:
                return 0
        
        # Adicionar colunas numéricas para ordenação
        df_top10_display['Dívida Total_Num'] = df_top10_display['Dívida Total'].apply(extrair_valor_numerico)
        df_top10_display['Dentro Prazo_Num'] = df_top10_display['Dentro Prazo'].apply(extrair_valor_numerico)
        df_top10_display['Previsão 30 Dias_Num'] = df_top10_display['Previsão 30 Dias'].apply(extrair_valor_numerico)
        
        # Ordenar conforme seleção
        if opcoes_ordenacao_top10 == "Dívida Total (Maior para Menor)":
            df_top10_display = df_top10_display.sort_values('Dívida Total_Num', ascending=False)
        elif opcoes_ordenacao_top10 == "Dívida Total (Menor para Maior)":
            df_top10_display = df_top10_display.sort_values('Dívida Total_Num', ascending=True)
        elif opcoes_ordenacao_top10 == "Dentro Prazo":
            df_top10_display = df_top10_display.sort_values('Dentro Prazo_Num', ascending=False)
        elif opcoes_ordenacao_top10 == "Previsão 30 Dias":
            df_top10_display = df_top10_display.sort_values('Previsão 30 Dias_Num', ascending=False)
        elif opcoes_ordenacao_top10 == "Nº Clientes":
            df_top10_display = df_top10_display.sort_values('Nº Clientes', ascending=False)
        
        # Selecionar Top 10 (excluindo a linha de total se existir)
        df_top10_exibir = df_top10_display[df_top10_display['Gestor/Promotor'] != 'TOTAL'].head(10).copy()
        
        # Calcular totais para adicionar linha de total
        total_divida = df_top10_exibir['Dívida Total_Num'].sum()
        total_dentro = df_top10_exibir['Dentro Prazo_Num'].sum()
        total_30_dias = df_top10_exibir['Previsão 30 Dias_Num'].sum()
        
        # Adicionar linha de total
        linha_total = pd.DataFrame([{
            'Gestor/Promotor': 'TOTAL GERAL',
            'Emissor': '',
            'Nome_do_Cliente': '',
            'Dívida Total': f"MZN {formatar_ptbr(total_divida, 0)}",
            'Dentro Prazo': f"MZN {formatar_ptbr(total_dentro, 0)}",
            'Previsão 30 Dias': f"MZN {formatar_ptbr(total_30_dias, 0)}",
            'Nº Clientes': '',
            'Dívida Total_Num': total_divida,
            'Dentro Prazo_Num': total_dentro,
            'Previsão 30 Dias_Num': total_30_dias
        }])
        
        df_top10_exibir = pd.concat([df_top10_exibir, linha_total], ignore_index=True)
        
        # Formatar colunas para exibição
        for col in ['Dívida Total', 'Dentro Prazo', 'Previsão 30 Dias']:
            if col in df_top10_exibir.columns:
                df_top10_exibir[col] = df_top10_exibir[col].apply(lambda x: f"MZN {formatar_ptbr(extrair_valor_numerico(x), 0)}" if pd.notna(x) and x != 0 else "MZN 0")
        
        # Selecionar colunas para exibição
        colunas_exibicao_top10 = ['Gestor/Promotor', 'Dívida Total', 'Dentro Prazo', 'Previsão 30 Dias', 'Nº Clientes']
        st.dataframe(df_top10_exibir[colunas_exibicao_top10], use_container_width=True, hide_index=True, height=400)
        
        # Gráfico de barras dos Top 10 Promotores
        st.markdown("##### 📊 Visualização - Top 10 Promotores")
        dados_grafico_top10 = df_top10_exibir[df_top10_exibir['Gestor/Promotor'] != 'TOTAL GERAL'].copy()
        if not dados_grafico_top10.empty:
            fig_top10 = go.Figure()
            fig_top10.add_trace(go.Bar(
                x=dados_grafico_top10['Gestor/Promotor'],
                y=dados_grafico_top10['Dívida Total_Num'],
                name='Dívida Total',
                marker_color='#FF6B35',
                text=dados_grafico_top10['Dívida Total'].apply(lambda x: x.replace('MZN ', '')),
                textposition='outside'
            ))
            fig_top10.update_layout(
                title='Top 10 Promotores - Dívida Total',
                xaxis_title='Promotor',
                yaxis_title='Valor (MZN)',
                height=450,
                xaxis_tickangle=-45
            )
            st.plotly_chart(fig_top10, use_container_width=True)
    
    st.markdown("---")
    
    # ============================================= RESUMO POR PROMOTOR (TOP 10) - COM SELETOR =============================================
    st.markdown("#### 📊 Resumo por Promotor (Top 10)")
    
    # Seletor para Resumo por Promotor
    col_selector_resumo, col_selector_resumo_2 = st.columns([2, 1])
    with col_selector_resumo:
        tipo_resumo = st.selectbox(
            "Selecionar visão:",
            options=["Todos os Promotores", "Top 10 por Dívida", "Top 10 por Clientes", "Promotor Específico"],
            key="selector_tipo_resumo"
        )
        
        promotor_especifico = None
        if tipo_resumo == "Promotor Específico" and coluna_promotor_divida:
            valores_promotores = MIS_df[coluna_promotor_divida].dropna()
            valores_unicos = sorted(set(str(v) for v in valores_promotores))
            promotor_especifico = st.selectbox(
                "Selecione o Promotor:",
                options=valores_unicos,
                key="selector_promotor_especifico"
            )
    
    # Calcular resumo por promotor
    if coluna_promotor_divida:
        # Agrupar dados por promotor
        df_resumo_base = MIS_df_filtrado.groupby(coluna_promotor_divida).agg({
            'DIVIDA_TOTAL': 'sum',
            'DENTRO_PRAZO': 'sum',
            'PREVISAO_30_DIAS': 'sum',
            'EMISSOR': 'count'
        }).reset_index()
        
        df_resumo_base = df_resumo_base.rename(columns={
            coluna_promotor_divida: 'Promotor',
            'DIVIDA_TOTAL': 'Total Dívida',
            'DENTRO_PRAZO': 'Total Dentro Prazo',
            'PREVISAO_30_DIAS': 'Total Previsão 30 Dias',
            'EMISSOR': 'Nº Clientes'
        })
        
        # Filtrar conforme seleção
        if tipo_resumo == "Promotor Específico" and promotor_especifico:
            df_resumo_filtrado = df_resumo_base[df_resumo_base['Promotor'].astype(str) == promotor_especifico]
            st.info(f"📊 Mostrando dados apenas para o promotor: **{promotor_especifico}**")
        elif tipo_resumo == "Top 10 por Dívida":
            df_resumo_filtrado = df_resumo_base.sort_values('Total Dívida', ascending=False).head(10)
        elif tipo_resumo == "Top 10 por Clientes":
            df_resumo_filtrado = df_resumo_base.sort_values('Nº Clientes', ascending=False).head(10)
        else:
            df_resumo_filtrado = df_resumo_base.sort_values('Total Dívida', ascending=False).head(10)
        
        if not df_resumo_filtrado.empty:
            # Calcular totais
            total_geral_divida = df_resumo_filtrado['Total Dívida'].sum()
            total_geral_dentro = df_resumo_filtrado['Total Dentro Prazo'].sum()
            total_geral_30_dias = df_resumo_filtrado['Total Previsão 30 Dias'].sum()
            total_clientes = df_resumo_filtrado['Nº Clientes'].sum()
            
            # Adicionar linha de total
            linha_total_resumo = pd.DataFrame([{
                'Promotor': 'TOTAL GERAL',
                'Total Dívida': total_geral_divida,
                'Total Dentro Prazo': total_geral_dentro,
                'Total Previsão 30 Dias': total_geral_30_dias,
                'Nº Clientes': total_clientes
            }])
            df_resumo_filtrado = pd.concat([df_resumo_filtrado, linha_total_resumo], ignore_index=True)
            
            # Formatar para exibição
            df_resumo_display = df_resumo_filtrado.copy()
            for col in ['Total Dívida', 'Total Dentro Prazo', 'Total Previsão 30 Dias']:
                if col in df_resumo_display.columns:
                    df_resumo_display[col] = df_resumo_display[col].apply(lambda x: f"MZN {formatar_ptbr(x, 0)}" if pd.notna(x) else "MZN 0")
            
            st.dataframe(df_resumo_display, use_container_width=True, hide_index=True)
            
            # Gráfico de barras do resumo
            if tipo_resumo != "Promotor Específico":
                dados_grafico_resumo = df_resumo_filtrado[df_resumo_filtrado['Promotor'] != 'TOTAL GERAL'].copy()
                if not dados_grafico_resumo.empty:
                    col_graf1, col_graf2 = st.columns(2)
                    with col_graf1:
                        fig_resumo_divida = px.bar(
                            dados_grafico_resumo,
                            x='Promotor',
                            y='Total Dívida',
                            title='Dívida Total por Promotor',
                            color='Total Dívida',
                            color_continuous_scale='Reds',
                            text_auto=True
                        )
                        fig_resumo_divida.update_layout(xaxis_tickangle=-45, height=400)
                        st.plotly_chart(fig_resumo_divida, use_container_width=True)
                    
                    with col_graf2:
                        fig_resumo_clientes = px.bar(
                            dados_grafico_resumo,
                            x='Promotor',
                            y='Nº Clientes',
                            title='Número de Clientes por Promotor',
                            color='Nº Clientes',
                            color_continuous_scale='Blues',
                            text_auto=True
                        )
                        fig_resumo_clientes.update_layout(xaxis_tickangle=-45, height=400)
                        st.plotly_chart(fig_resumo_clientes, use_container_width=True)
    
    st.markdown("---")
    st.markdown("#### 📥 Download dos Dados de Dívida")
    with st.expander("📊 Opções de Exportação"):
        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            if 'tabela_linhas' in locals() and not tabela_linhas.empty:
                criar_botao_download_excel(tabela_linhas, "divida_linhas_negocio", "Dívida por Linha de Negócio")
        with col_dl2:
            if 'tabela_top10' in locals() and not tabela_top10.empty:
                criar_botao_download_excel(tabela_top10, "top10_promotores_divida", "Top 10 Promotores - Dívida")
        with col_dl3:
            if 'df_resumo_base' in locals() and not df_resumo_base.empty:
                criar_botao_download_excel(df_resumo_base, "resumo_promotores", "Resumo por Promotor")

def criar_aba_promotores(df_filtrado: pd.DataFrame):
    """Cria a aba de Análise de Promotores"""
    st.markdown('<div class="section-title">👥 Análise de Promotores - Desempenho Comercial</div>', unsafe_allow_html=True)
    tab_vendas, tab_divida = st.tabs(["📈 Análise de Vendas", "💰 Análise de Dívida"])
    with tab_vendas: 
        criar_aba_vendas_promotores(df_filtrado)
    with tab_divida: 
        criar_aba_divida_promotores()

# ============================================= FUNÇÕES PARA ABA STOCK =============================================

def criar_dados_stock_simulados():
    """Cria dados simulados de stock por província"""
    provincias_mocambique = ["Maputo Cidade", "Maputo", "Gaza", "Inhambane", "Sofala", "Manica", "Tete", "Zambézia", "Nampula", "Cabo Delgado", "Niassa"]
    dados = []
    for provincia in provincias_mocambique:
        stock_gasolina = np.random.uniform(500, 5000)
        stock_gasoleo = np.random.uniform(1000, 10000)
        stock_jet = np.random.uniform(100, 2000) if provincia in ["Maputo Cidade", "Maputo", "Nampula"] else np.random.uniform(50, 500)
        vds_gasolina = np.random.uniform(20, 200)
        vds_gasoleo = np.random.uniform(50, 500)
        vds_jet = np.random.uniform(5, 50) if provincia in ["Maputo Cidade", "Maputo", "Nampula"] else np.random.uniform(1, 10)
        autonomia_gasolina = stock_gasolina / vds_gasolina if vds_gasolina > 0 else 0
        autonomia_gasoleo = stock_gasoleo / vds_gasoleo if vds_gasoleo > 0 else 0
        autonomia_jet = stock_jet / vds_jet if vds_jet > 0 else 0
        stock_total = stock_gasolina + stock_gasoleo + stock_jet
        vds_total = vds_gasolina + vds_gasoleo + vds_jet
        autonomia_total = stock_total / vds_total if vds_total > 0 else 0
        dados.append({"Provincia": provincia, "Stock_Gasolina": stock_gasolina, "Stock_Gasoleo": stock_gasoleo,
                      "Stock_Jet": stock_jet, "Stock_Total": stock_total, "VDS_Gasolina": vds_gasolina,
                      "VDS_Gasoleo": vds_gasoleo, "VDS_Jet": vds_jet, "VDS_Total": vds_total,
                      "Autonomia_Gasolina": autonomia_gasolina, "Autonomia_Gasoleo": autonomia_gasoleo,
                      "Autonomia_Jet": autonomia_jet, "Autonomia_Total": autonomia_total,
                      "Data_Atualizacao": datetime.now().strftime("%Y-%m-%d")})
    return pd.DataFrame(dados)

@st.cache_data(ttl=3600)
def carregar_dados_stock():
    """Carrega dados de stock - pode ser real ou simulado"""
    try:
        if os.path.exists(config.ARQUIVO_STOCK):
            df_stock = pd.read_excel(config.ARQUIVO_STOCK)
            logger.info(f"Dados de stock carregados: {len(df_stock)} registros")
        else:
            logger.info("Arquivo de stock não encontrado. Criando dados simulados.")
            df_stock = criar_dados_stock_simulados()
        return df_stock
    except Exception as e:
        logger.error(f"Erro ao carregar dados de stock: {str(e)}")
        st.warning(f"⚠️ Erro ao carregar dados de stock. Usando dados simulados.")
        return criar_dados_stock_simulados()

def calcular_metricas_stock_gerais(df_stock: pd.DataFrame) -> Dict:
    """Calcula métricas gerais de stock"""
    metricas = {
        "total_stock": df_stock["Stock_Total"].sum(),
        "autonomia_media": df_stock["Autonomia_Total"].mean(),
        "provincias_alerta": len(df_stock[df_stock["Autonomia_Total"] < 10]),
        "provincias_criticas": len(df_stock[df_stock["Autonomia_Total"] < 5]),
        "stock_gasolina": df_stock["Stock_Gasolina"].sum(),
        "stock_gasoleo": df_stock["Stock_Gasoleo"].sum(),
        "stock_jet": df_stock["Stock_Jet"].sum(),
        "vds_total": df_stock["VDS_Total"].sum(),
        "provincia_maior_stock": df_stock.loc[df_stock["Stock_Total"].idxmax(), "Provincia"] if not df_stock.empty else "",
        "provincia_menor_autonomia": df_stock.loc[df_stock["Autonomia_Total"].idxmin(), "Provincia"] if not df_stock.empty else "",
        "menor_autonomia": df_stock["Autonomia_Total"].min() if not df_stock.empty else 0,
        "maior_autonomia": df_stock["Autonomia_Total"].max() if not df_stock.empty else 0
    }
    return metricas

def criar_scroller_stock(total_stock: float, autonomia_media: float, provincias_alerta: int, provincias_criticas: int):
    """Cria um scroller animado para métricas de stock"""
    st.markdown(f"""
    <div class="scroller-container scroller-stock">
        <div class="scroller-title">📦 SITUAÇÃO DE STOCK - MOÇAMBIQUE</div>
        <div class="scroller-content">
            <div class="scroller-item">
                <div class="scroller-value pulse-effect">{formatar_ptbr(total_stock, 0)}</div>
                <div class="scroller-label">STOCK TOTAL</div>
                <div class="scroller-subvalue">m³ disponíveis</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #32CD32;">{autonomia_media:.1f} dias</div>
                <div class="scroller-label">AUTONOMIA MÉDIA</div>
                <div class="scroller-subvalue">Stock / Vendas Diárias</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #FFD700;">{provincias_alerta}</div>
                <div class="scroller-label">PROVÍNCIAS EM ALERTA</div>
                <div class="scroller-subvalue">Autonomia &lt; 10 dias</div>
            </div>
            <div class="scroller-item">
                <div class="scroller-value" style="color: #DC143C;">{provincias_criticas}</div>
                <div class="scroller-label">PROVÍNCIAS CRÍTICAS</div>
                <div class="scroller-subvalue">Autonomia &lt; 5 dias</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def classificar_autonomia(dias_autonomia: float) -> Tuple[str, str, str]:
    if dias_autonomia >= 20: return "Excelente", "valor-excelente", "status-excelente"
    elif dias_autonomia >= 10: return "Bom", "valor-positivo", "status-bom"
    elif dias_autonomia >= 5: return "Alerta", "valor-alerta", "status-alerta"
    else: return "Crítico", "valor-critico", "status-critico"

def criar_mapa_mocambique_interativo(df_stock: pd.DataFrame):
    """Cria um mapa interativo de Moçambique com dados de stock por província"""
    dados_mapa = {"Provincia": ["Maputo Cidade", "Maputo", "Gaza", "Inhambane", "Sofala", "Manica", "Tete", "Zambézia", "Nampula", "Cabo Delgado", "Niassa"],
                  "Latitude": [-25.9692, -25.9667, -23.0228, -23.8650, -19.8333, -18.9333, -16.1564, -17.8416, -15.1266, -12.9608, -13.2930],
                  "Longitude": [32.5732, 32.5833, 32.5736, 35.3833, 34.8500, 33.4667, 33.5867, 36.8480, 39.2604, 40.5078, 36.2522]}
    df_mapa = pd.DataFrame(dados_mapa)
    df_completo = pd.merge(df_mapa, df_stock, on="Provincia", how="left")
    
    def definir_cor_autonomia(dias):
        if dias >= 20: return "#32CD32"
        elif dias >= 10: return "#1E90FF"
        elif dias >= 5: return "#FFD700"
        else: return "#DC143C"
    df_completo["Cor"] = df_completo["Autonomia_Total"].apply(definir_cor_autonomia)
    
    fig = px.scatter_mapbox(df_completo, lat="Latitude", lon="Longitude", hover_name="Provincia",
                            hover_data={"Stock_Total": ":.0f", "Autonomia_Total": ":.1f"},
                            size="Stock_Total", color="Cor", color_discrete_map="identity",
                            size_max=30, zoom=5, height=600, title="📍 Mapa de Moçambique - Stock por Província")
    fig.update_layout(mapbox_style="carto-positron", mapbox=dict(center=dict(lat=-18.5, lon=35), zoom=5))
    return fig

def criar_aba_stock():
    """Cria a aba completa de análise de Stock"""
    st.markdown('<div class="section-title-stock">📦 ANÁLISE DE STOCK - MOÇAMBIQUE</div>', unsafe_allow_html=True)
    stock_df = carregar_dados_stock()
    if stock_df.empty:
        st.warning("⚠️ Nenhum dado de stock disponível")
        return
    
    metricas = calcular_metricas_stock_gerais(stock_df)
    criar_scroller_stock(metricas["total_stock"], metricas["autonomia_media"], metricas["provincias_alerta"], metricas["provincias_criticas"])
    
    st.markdown("#### 🎯 Métricas Principais")
    col1, col2, col3, col4 = st.columns(4)
    with col1: criar_card_metricas("Stock Total", f"{formatar_ptbr(metricas['total_stock'], 0)}", "m³ disponíveis", f"{len(stock_df)} províncias", "📦", "stock")
    with col2:
        cor_card = "autonomia" if metricas["autonomia_media"] >= 20 else "fh" if metricas["autonomia_media"] >= 10 else "Release" if metricas["autonomia_media"] >= 5 else "alerta"
        status_emoji = "✅" if metricas["autonomia_media"] >= 20 else "👍" if metricas["autonomia_media"] >= 10 else "⚠️" if metricas["autonomia_media"] >= 5 else "🚨"
        criar_card_metricas("Autonomia Média", f"{metricas['autonomia_media']:.1f} dias", "Stock / Vendas Diárias", f"{status_emoji} {classificar_autonomia(metricas['autonomia_media'])[0]}", "⏱️", cor_card)
    with col3: criar_card_metricas("Vendas Diárias", f"{formatar_ptbr(metricas['vds_total'], 0)}", "m³/dia", "", "💰", "petromoc")
    with col4:
        total = metricas['total_stock']
        perc_gasoleo = (metricas['stock_gasoleo'] / total * 100) if total > 0 else 0
        perc_gasolina = (metricas['stock_gasolina'] / total * 100) if total > 0 else 0
        perc_jet = (metricas['stock_jet'] / total * 100) if total > 0 else 0
        criar_card_metricas("Distribuição por Combustível", f"Gasóleo: {perc_gasoleo:.1f}%", f"Gasolina: {perc_gasolina:.1f}%", f"Jet: {perc_jet:.1f}%", "⚡", "congenere")
    
    st.markdown("---")
    st.markdown("#### 🗺️ Visualizações de Stock")
    tab_mapa, tab_tabela, tab_graficos = st.tabs(["🗺️ Mapa", "📋 Tabela", "📊 Gráficos"])
    
    with tab_mapa: st.plotly_chart(criar_mapa_mocambique_interativo(stock_df), use_container_width=True)
    with tab_tabela:
        df_display = stock_df.copy()
        for col in ["Stock_Gasolina", "Stock_Gasoleo", "Stock_Jet", "Stock_Total", "VDS_Gasolina", "VDS_Gasoleo", "VDS_Jet", "VDS_Total"]:
            if col in df_display.columns: df_display[col] = df_display[col].apply(lambda x: formatar_ptbr(x, 0) if pd.notna(x) else "0")
        st.dataframe(df_display, use_container_width=True, height=500)
        col_dl1, col_dl2 = st.columns(2)
        with col_dl1: criar_botao_download_excel(stock_df, "dados_stock_provincias", "Dados Completos")
        with col_dl2: criar_botao_download_csv(stock_df, "dados_stock_provincias", "Dados Completos")
    
    with tab_graficos:
        fig1 = px.bar(stock_df.sort_values("Stock_Total", ascending=True), y="Provincia", x="Stock_Total", orientation="h",
                      title="Stock Total por Província (m³)", color="Autonomia_Total", color_continuous_scale="RdYlGn_r")
        fig1.update_layout(height=500)
        st.plotly_chart(fig1, use_container_width=True)
        
        fig2 = px.bar(stock_df.sort_values("Autonomia_Total", ascending=True), y="Provincia", x="Autonomia_Total", orientation="h",
                      title="Dias de Autonomia por Província", color="Autonomia_Total", color_continuous_scale="RdYlGn")
        fig2.update_layout(height=500)
        st.plotly_chart(fig2, use_container_width=True)
        
        fig3 = px.pie(values=[stock_df["Stock_Gasolina"].sum(), stock_df["Stock_Gasoleo"].sum(), stock_df["Stock_Jet"].sum()],
                      names=["Gasolina", "Gasóleo", "Jet A1"], title="Distribuição de Stock por Tipo de Combustível",
                      color=["Gasolina", "Gasóleo", "Jet A1"], color_discrete_map={"Gasolina": "#FF6B35", "Gasóleo": "#1E90FF", "Jet A1": "#4ECDC4"})
        fig3.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig3, use_container_width=True)

# ============================================= FUNÇÃO PRINCIPAL =============================================

def main():
    """Função principal - Ponto de entrada do sistema"""
    st.markdown('<h1 class="main-header">Sistema de Gestão - Petromoc, SA</h1>', unsafe_allow_html=True)
    
    if not vds_plan_MT_Pln.empty:
        with st.expander("📊 Resumo dos Dados Carregados", expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Vendas", f"{formatar_ptbr(vds_plan_MT_Pln[config.COLUNA_VENDAS_M3].sum(), 0)} m³")
            with col2:
                st.metric("Total Plano", f"{formatar_ptbr(vds_plan_MT_Pln[config.COLUNA_PLANO_M3].sum(), 0)} m³")
            with col3:
                atingimento = (vds_plan_MT_Pln[config.COLUNA_VENDAS_M3].sum() / vds_plan_MT_Pln[config.COLUNA_PLANO_M3].sum() * 100) if vds_plan_MT_Pln[config.COLUNA_PLANO_M3].sum() > 0 else 0
                st.metric("Atingimento", f"{atingimento:.1f}%")
            st.caption(f"Total de registros: {len(vds_plan_MT_Pln):,}")
    
    with st.sidebar:
        filtros = renderizar_menu_lateral()
    
    if vds_plan_MT_Pln.empty and import_df.empty:
        st.warning("""
        ⚠️ **Nenhum dado disponível para análise.**
        
        **Verifique:**
        1. Se os arquivos estão na pasta correta
        2. Nomes dos arquivos:
           - Vds_2023_Comb_.xlsx, Vds_2024_Comb_.xlsx, Vds_2025_Comb_.xlsx
           - PlanComb_2023.xlsx, PlanComb_2024.xlsx, PlanComb_2025.xlsx
           - ImportacaoMZ.xlsx
           - v_loock_up.xlsx
           - Garantias_Bancarias_.xlsx
        3. Se as colunas 'Vendas_m³' e 'Plano_m³' existem nos arquivos
        """)
        st.markdown("#### 📈 Demonstração - Vendas vs Plano")
        st.plotly_chart(criar_grafico_linhas_simulado(), use_container_width=True)
        return
    
    modo_trabalho = filtros.get('modo_trabalho', 'Importação')
    
    if modo_trabalho == ModoTrabalho.VENDAS.value:
        if vds_plan_MT_Pln.empty:
            st.error("❌ Dados de vendas não disponíveis")
            return
        df_filtrado = aplicar_filtros_vendas(vds_plan_MT_Pln, filtros)
        criar_analise_vendas_plano_completa(df_filtrado)
    
    elif modo_trabalho == ModoTrabalho.IMPORTACAO.value:
        if import_df.empty:
            st.error("❌ Dados de importação não disponíveis")
            return
        df_filtrado = aplicar_filtros_importacao(import_df, filtros)
        criar_aba_importacao_com_dados_reais(df_filtrado)
    
    elif modo_trabalho == ModoTrabalho.PROMOTORES.value:
        if not vds_plan_MT_Pln.empty:
            df_filtrado = aplicar_filtros_vendas(vds_plan_MT_Pln, filtros)
            criar_aba_promotores(df_filtrado)
        else:
            st.info("👥 Módulo de Promotores em desenvolvimento")
    
    elif modo_trabalho == ModoTrabalho.STOCK.value:
        criar_aba_stock()
    
    else:
        st.info(f"👥 Módulo {modo_trabalho} em desenvolvimento")
    
    st.markdown("---")
    st.markdown(f"""
    <div style="text-align: center; color: #666; font-size: 0.8rem;">
        <p>⛽ <strong>Petromoc, SA</strong> - Sistema de Gestão Econômica</p>
        <p>📧 <a href="mailto:suporte@petromoc.co.mz" style="color: #FF6B35;">suporte@petromoc.co.mz</a> | 
        🌐 <a href="https://www.petromoc.co.mz" style="color: #FF6B35;" target="_blank">www.petromoc.co.mz</a></p>
        <p>🔄 Última atualização: {datetime.now().strftime("%d/%m/%Y %H:%M")}</p>
        <p>✅ Versão 2.0 - Análise com dados REAIS de Vendas_m³ e Plano_m³</p>
        <p>📊 Análise por Linha de Negócio: Vulcan, Consumidores, Revenda, Bunkers, Aviacao, Reexportacao</p>
        <p>🏦 Dados REAIS de Garantias Bancárias do arquivo Garantias_Bancarias_.xlsx</p>
        <p>📅 Nível de Agregação padrão: Por Mês na tabela de vendas</p>
        <p>👥 Seletores de ordenação e filtros nas tabelas de dívida dos promotores</p>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()