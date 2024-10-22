import streamlit as st
from database import carregar_dados_do_postgres, carregar_planilha, executar_query, listar_tabelas
from agent import criar_agente, fazer_pergunta
from utils import formatar_resposta
import os
from dotenv import load_dotenv
from PIL import Image

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da página
st.set_page_config(layout="wide", page_title="Agent AI - AI2SQL")

# Carregar CSS externo
def load_css(file_name):
    with open(file_name) as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

load_css('style.css')

# Função para exibir mensagens no chat
def exibir_mensagem(role, content, sql_usado=None):
    if role == "Usuário":
        st.markdown(f"<div class='user-message'><strong>Usuário:</strong> {content}</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='assistant-message'><strong>Assistente:</strong> {content}</div>", unsafe_allow_html=True)
        if sql_usado:
            st.markdown(f"<div class='sql-used'><strong>SQL usado:</strong><br>{sql_usado}</div>", unsafe_allow_html=True)

# Inicialização do histórico de chat
if 'mensagens' not in st.session_state:
    st.session_state.mensagens = []

# Área principal
col1, col2 = st.columns([1, 5])

with col1:
    # Carregar e exibir a logo
    logo = Image.open("fig.png")
    st.image(logo, width=100)  # Ajuste o width conforme necessário

with col2:
    st.markdown("<h1 class='main-title'>Agent AI - <span class='gradient-text'>Text to SQL</span></h1>", unsafe_allow_html=True)
    st.markdown("<p class='subtitle'>Transforme suas perguntas em consultas SQL poderosas</p>", unsafe_allow_html=True)

# Barra lateral
st.sidebar.title("Configurações")

# Opção para escolher entre banco de dados ou planilha
opcao = st.sidebar.radio("Escolha a fonte de dados:", ("Banco de Dados PostgreSQL", "Carregar Planilha"))

if opcao == "Banco de Dados PostgreSQL":
    connection_string = st.sidebar.text_input("String de conexão PostgreSQL:")
    if st.sidebar.button("Conectar"):
        try:
            engine = carregar_dados_do_postgres(connection_string)
            st.session_state.engine = engine
            st.session_state.agente = criar_agente(engine)
            tabelas = listar_tabelas(engine)
            st.sidebar.write("Tabelas disponíveis:", tabelas)
            st.sidebar.success("Conectado com sucesso!")
        except Exception as e:
            st.sidebar.error(f"Erro ao conectar: {str(e)}")
else:
    arquivo = st.sidebar.file_uploader("Carregue sua planilha (CSV, XLS, XLSX)")
    if arquivo is not None:
        try:
            engine = carregar_planilha(arquivo)
            st.session_state.engine = engine
            st.session_state.agente = criar_agente(engine)
            tabelas = listar_tabelas(engine)
            st.sidebar.write("Tabelas disponíveis:", tabelas)
            st.sidebar.success("Planilha carregada com sucesso!")
        except Exception as e:
            st.sidebar.error(f"Erro ao carregar planilha: {str(e)}")

# Botão para limpar o histórico de chat
if st.sidebar.button("Limpar Histórico"):
    st.session_state.mensagens = []
    st.experimental_rerun()

# Área de chat
st.subheader("Chat com IA")

# Exibir mensagens do chat
for mensagem in st.session_state.mensagens:
    exibir_mensagem(mensagem['role'], mensagem['content'], mensagem.get('sql_usado'))

# Área de entrada de pergunta
pergunta = st.text_input("Faça uma pergunta sobre os dados:")

if st.button("Enviar"):
    if pergunta:
        if 'agente' in st.session_state and 'engine' in st.session_state:
            try:
                resposta, sql_usado = fazer_pergunta(st.session_state.agente, st.session_state.engine, pergunta)
                st.session_state.mensagens.append({"role": "Usuário", "content": pergunta})
                st.session_state.mensagens.append({"role": "Assistente", "content": resposta, "sql_usado": sql_usado})
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Erro ao processar pergunta: {str(e)}")
                st.error(f"Detalhes do erro: {type(e).__name__}, {str(e)}")
        else:
            st.error("Por favor, conecte-se ao banco de dados ou carregue uma planilha primeiro.")

# Exibir versão do Streamlit
st.sidebar.text(f"Versão do Streamlit: {st.__version__}")