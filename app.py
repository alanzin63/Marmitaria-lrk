import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd
import os

# ==========================================
# CONFIGURAÇÕES VISUAIS
# ==========================================
st.set_page_config(page_title="Marmitaria Lrk", page_icon="🍱", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    h1, h2, h3 { color: #EA1D2C !important; }
    .stButton>button {
        background-color: #EA1D2C;
        color: white;
        border-radius: 10px;
        width: 100%;
        font-weight: bold;
    }
    .marmita-container {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0px 4px 10px rgba(0,0,0,0.05);
    }
    .pix-box {
        background-color: #f0f7ff;
        padding: 20px;
        border-radius: 15px;
        border: 2px solid #007bff;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)
# ==========================================
# BANCO DE DADOS
# ==========================================
def init_db():
    conn = sqlite3.connect('marmitaria_lrk.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, cliente TEXT, bloco TEXT, apartamento TEXT, 
                  tamanho TEXT, proteinas TEXT, acompanhamentos TEXT, total REAL, data_hora TEXT)''')
    c.execute('CREATE TABLE IF NOT EXISTS proteinas (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)')
    c.execute('CREATE TABLE IF NOT EXISTS acompanhamentos (id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT)')
    conn.commit()
    conn.close()

def get_items(tabela):
    conn = sqlite3.connect('marmitaria_lrk.db')
    df = pd.read_sql_query(f"SELECT nome FROM {tabela}", conn)
    conn.close()
    return df['nome'].tolist()

init_db()

# ==========================================
# INTERFACE PRINCIPAL
# ==========================================
st.title("🍱 Marmitaria Lrk")

aba_cliente, aba_admin = st.tabs(["🛒 Fazer Pedido", "🔐 Administração"])

with aba_cliente:
    st.markdown('<div class="marmita-container">', unsafe_allow_html=True)
    
    st.subheader("📍 Onde Entregar?")
    nome = st.text_input("Seu Nome:")
    col_bloco, col_ap = st.columns(2)
    with col_bloco:
        bloco = st.text_input("Bloco:")
    with col_ap:
        apartamento = st.text_input("Apartamento:")

    st.divider()
    st.subheader("🍽️ Monte sua Marmita")
    tamanho = st.radio("Tamanho:", ["Pequena (R$ 12,00)", "Grande (R$ 17,00)"], horizontal=True)
    
    limite_carne = 1 if "Pequena" in tamanho else 2
    preco_base = 12.00 if "Pequena" in tamanho else 17.00
    
    opcoes_p = get_items('proteinas')
    opcoes_a = get_items('acompanhamentos')

    if not opcoes_p:
        st.info("O cardápio está sendo atualizado. Volte em instantes!")
    
    sel_proteinas = st.multiselect(f"Proteínas (Até {limite_carne}):", opcoes_p, max_selections=limite_carne)
    sel_acompanhamentos = st.multiselect("Acompanhamentos (Livre):", opcoes_a)
    
    col1, col2 = st.columns(2)
    with col1:
        salada = st.checkbox("Salada e Tomate (Grátis)")
    with col2:
        ovo = st.checkbox("Ovo Frito (+ R$ 3,00)")
    
    total = preco_base + (3.00 if ovo else 0)
    st.markdown(f"### Total: R$ {total:.2f}")

    if st.button("FINALIZAR PEDIDO"):
        if not nome or not bloco or not apartamento or not sel_proteinas:
            st.warning("⚠️ Preencha seu nome, bloco, apartamento e escolha a proteína!")
        else:
            conn = sqlite3.connect('marmitaria_lrk.db')
            c = conn.cursor()
            agora = datetime.now().strftime("%d/%m/%Y %H:%M")
            c.execute("INSERT INTO pedidos (cliente, bloco, apartamento, tamanho, proteinas, acompanhamentos, total, data_hora) VALUES (?,?,?,?,?,?,?,?)",
                      (nome, bloco, apartamento, tamanho, str(sel_proteinas), str(sel_acompanhamentos), total, agora))
            conn.commit()
            conn.close()
            st.success("🎉 Pedido Confirmado!")
            
            st.markdown('<div class="pix-box">', unsafe_allow_html=True)
            if os.path.exists("qrcode.png"):
                st.image("qrcode.png", width=250)
            st.write("✅ **Nome:** Laura Jessica")
            st.markdown('</div>', unsafe_allow_html=True)
            st.balloons()
    st.markdown('</div>', unsafe_allow_html=True)

# ==========================================
# PAINEL ADMIN
# ==========================================
with aba_admin:
    senha = st.text_input("Senha Admin:", type="password")
    if senha == "lrk0102":
        st.subheader("📝 Pedidos Recebidos")
        conn = sqlite3.connect('marmitaria_lrk.db')
        df_p = pd.read_sql_query("SELECT * FROM pedidos ORDER BY id DESC", conn)
        st.dataframe(df_p, use_container_width=True)
        
        if st.button("Limpar Todos os Pedidos"):
            c = conn.cursor()
            c.execute("DELETE FROM pedidos")
            conn.commit()
            st.rerun()

        st.divider()
        st.subheader("⚙️ Editar Cardápio")
        
        col_ed_p, col_ed_a = st.columns(2)
        
        with col_ed_p:
            st.write("### Proteínas")
            nova_p = st.text_input("Nome da Carne:")
            if st.button("Adicionar Proteína"):
                if nova_p:
                    c = conn.cursor()
                    c.execute("INSERT INTO proteinas (nome) VALUES (?)", (nova_p,))
                    conn.commit()
                    st.rerun()
            
            p_lista = get_items('proteinas')
            item_p_del = st.selectbox("Remover Proteína:", ["-- Selecione --"] + p_lista)
            if st.button("Excluir Carne"):
                c = conn.cursor()
                c.execute("DELETE FROM proteinas WHERE nome = ?", (item_p_del,))
                conn.commit()
                st.rerun()

        with col_ed_a:
            st.write("### Acompanhamentos")
            nova_a = st.text_input("Nome do Acompanhamento:")
            if st.button("Adicionar Acompanhamento"):
                if nova_a:
                    c = conn.cursor()
                    c.execute("INSERT INTO acompanhamentos (nome) VALUES (?)", (nova_a,))
                    conn.commit()
                    st.rerun()
            
            a_lista = get_items('acompanhamentos')
            item_a_del = st.selectbox("Remover Acompanhamento:", ["-- Selecione --"] + a_lista)
            if st.button("Excluir Acompanhamento"):
                c = conn.cursor()
                c.execute("DELETE FROM acompanhamentos WHERE nome = ?", (item_a_del,))
                conn.commit()
                st.rerun()
        conn.close()
        # FORÇAR MODO CLARO PARA NÃO FICAR ESCURO NO CELULAR
st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: white; }
    [data-testid="stHeader"] { background-color: rgba(0,0,0,0); }
    .stMarkdown p, label, .stRadio label { color: black !important; }
    h1, h2, h3 { color: #EA1D2C !important; }
    input { background-color: #f0f2f6 !important; color: black !important; }
    </style>
    """, unsafe_allow_html=True)
st.markdown("""
    <style>
    /* 1. Fundo da página sempre branco */
    .stApp { background-color: white !important; }

    /* 2. Forçar cor PRETA em todos os textos de seleção e rádio */
    /* Isso resolve o Tamanho, Salada e Ovo */
    .stMarkdown p, 
    label, 
    .stSelectbox label, 
    .stMultiSelect label, 
    .stCheckbox label, 
    .stRadio label,
    div[data-testid="stMarkdownContainer"] p {
        color: #000000 !important;
        font-weight: 800 !important; /* Deixa a letra mais grossa */
        font-size: 1.1rem !important;
    }

    /* 3. Ajuste específico para as bolinhas do rádio e quadrados do check */
    div[data-testid="stRadio"] label p, 
    div[data-testid="stCheckbox"] label p {
        color: #000000 !important;
    }

    /* 4. Caixas de seleção (Proteínas e Acompanhamentos) */
    div[data-baseweb="select"] > div {
        background-color: #f0f2f6 !important;
        border: 2px solid #000000 !important; /* Borda preta para destacar */
    }
    
    /* Texto dentro da caixa de seleção */
    div[data-baseweb="select"] div {
        color: #000000 !important;
    }

    /* 5. Títulos em Vermelho Destaque */
    h1, h2, h3 { 
        color: #EA1D2C !important; 
        font-weight: bold !important;
    }

    /* 6. Botão Finalizar */
    .stButton>button {
        background-color: #EA1D2C !important;
        color: white !important;
        width: 100%;
        font-weight: bold;
        border-radius: 10px;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)
