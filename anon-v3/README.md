# 🔒 Anonimizador de PDF

Ferramenta web simples para **anonimizar PDFs em massa**, substituindo
ou tarjando palavras, CPFs, nomes, e-mails, etc. Roda 100% via Streamlit,
sem login, sem banco de dados.

## ✨ Funcionalidades

- Upload de PDF (qualquer tamanho, testado com 100+ páginas)
- Regras ilimitadas de "localizar → substituir"
- Dois modos: **substituir texto** ou **tarjar (tarja preta)**
- Suporte a **Regex** (ex: encontrar todos os CPFs)
- Ajuste automático do tamanho da fonte
- Download do PDF já anonimizado

## 🚀 Rodar localmente

```bash
python -m venv .venv
source .venv/bin/activate      # Linux/Mac
# .venv\Scripts\activate       # Windows

pip install -r requirements.txt
streamlit run app.py