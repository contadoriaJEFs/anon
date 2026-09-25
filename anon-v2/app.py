import io
import re
import streamlit as st
import fitz  # PyMuPDF
import pandas as pd

st.set_page_config(
    page_title="Anonimizador de PDF",
    page_icon="🔒",
    layout="wide",
)

# ---------------- Session state ----------------
if "rules" not in st.session_state:
    st.session_state.rules = [{"find": "", "replace": ""}]
if "output_bytes" not in st.session_state:
    st.session_state.output_bytes = None
if "total_subs" not in st.session_state:
    st.session_state.total_subs = 0
if "scan_results" not in st.session_state:
    st.session_state.scan_results = None
if "scan_done" not in st.session_state:
    st.session_state.scan_done = False

# ---------------- Padrões de dados sensíveis ----------------
SENSITIVE_PATTERNS = {
    "CPF": (r"\d{3}\.\d{3}\.\d{3}-\d{2}", "000.000.000-00"),
    "CNPJ": (r"\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}", "00.000.000/0000-00"),
    "CEP": (r"\b\d{5}-\d{3}\b", "00000-000"),
    "E-mail": (r"[\w\.-]+@[\w\.-]+\.\w+", "anonimo@email.com"),
    "Telefone": (r"\(\d{2}\)\s?\d{4,5}[-\s]?\d{4}", "(00) 00000-0000"),
    "Cartão de crédito": (r"\b(?:\d{4}[\s-]?){3}\d{4}\b", "0000 0000 0000 0000"),
    "Data": (r"\b\d{2}/\d{2}/\d{4}\b", "00/00/0000"),
    "Valor R$": (r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?", "R$ 0,00"),
    "Placa de veículo": (r"\b[A-Z]{3}[-\s]?\d[A-Z0-9]\d{2}\b", "AAA-0000"),
    "Chave PIX aleatória": (
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        "00000000-0000-0000-0000-000000000000",
    ),
}

# ---------------- Funções ----------------
def scan_sensitive(pdf_bytes):
    """Escaneia o PDF em busca de padrões sensíveis. Retorna dict {(tipo, valor): set(páginas)}."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    found = {}
    n_pages = len(doc)
    for pno in range(n_pages):
        try:
            text = doc[pno].get_text()
        except Exception:
            text = ""
        for tipo, (pattern, _) in SENSITIVE_PATTERNS.items():
            try:
                for m in re.finditer(pattern, text):
                    val = m.group()
                    if not val:
                        continue
                    found.setdefault((tipo, val), set()).add(pno + 1)
            except re.error:
                continue
    doc.close()
    return found


def process_pdf(pdf_bytes, rules, mode, use_regex, case_sensitive,
                auto_font, manual_font_size, expand_box, progress_cb=None):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total = 0
    n_pages = len(doc)

    for pno in range(n_pages):
        page = doc[pno]
        insertions = []

        for rule in rules:
            find_text = rule["find"]
            replace_text = rule["replace"] if mode == "Substituir texto" else ""

            terms = set()

            if use_regex:
                flags = 0 if case_sensitive else re.IGNORECASE
                try:
                    pattern = re.compile(find_text, flags)
                except re.error:
                    continue
                try:
                    page_text = page.get_text()
                except Exception:
                    page_text = ""
                for m in pattern.finditer(page_text):
                    if m.group():
                        terms.add(m.group())
            else:
                terms.add(find_text)

            for term in terms:
                if not term:
                    continue
                try:
                    rects = page.search_for(term)
                except Exception:
                    rects = []
                for rect in rects:
                    if mode == "Tarjar (tarja preta)":
                        page.add_redact_annot(rect, fill=(0, 0, 0))
                    else:
                        page.add_redact_annot(rect, fill=None)
                    insertions.append((rect, replace_text))
                    total += 1

        try:
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        except TypeError:
            page.apply_redactions()
        except Exception:
            pass

        if mode == "Substituir texto":
            for rect, text in insertions:
                if not text:
                    continue

                fs = max(5.0, min(rect.height * 0.95, 20.0)) if auto_font else float(manual_font_size)

                if expand_box:
                    box = fitz.Rect(
                        rect.x0,
                        rect.y0 - 1,
                        min(page.rect.x1 - 5,
                            rect.x0 + max(rect.width * 2, len(text) * fs * 0.6) + 10),
                        rect.y1 + 2,
                    )
                else:
                    box = fitz.Rect(rect.x0, rect.y0 - 1, rect.x1, rect.y1 + 2)

                inserted = False
                for _ in range(8):
                    try:
                        rc = page.insert_textbox(
                            box, text,
                            fontsize=fs,
                            fontname="helv",
                            color=(0, 0, 0),
                            align=0,
                        )
                        if rc >= 0:
                            inserted = True
                            break
                        fs *= 0.85
                    except Exception:
                        fs *= 0.85
                    if fs < 4:
                        break

                if not inserted:
                    try:
                        page.insert_text(
                            (rect.x0, rect.y1 - 1), text,
                            fontsize=max(5.0, fs),
                            fontname="helv",
                            color=(0, 0, 0),
                        )
                    except Exception:
                        pass

        if progress_cb:
            progress_cb(pno + 1, n_pages)

    out = io.BytesIO()
    doc.save(out, garbage=4, deflate=True)
    doc.close()
    return out.getvalue(), total


# ---------------- Sidebar (global) ----------------
with st.sidebar:
    st.header("⚙️ Configurações")

    mode = st.radio(
        "Modo de anonimização",
        ["Substituir texto", "Tarjar (tarja preta)"],
        help="Substituir troca o valor pelo que você digitar. "
             "Tarjar apenas cobre com preto (não substitui o texto).",
    )

    use_regex = st.checkbox(
        "Usar expressões regulares (Regex)",
        value=False,
        help=r"Use Regex para encontrar padrões. Ex: CPF → \d{3}\.\d{3}\.\d{3}-\d{2}",
    )

    case_sensitive = st.checkbox(
        "Diferenciar maiúsculas/minúsculas (apenas Regex)",
        value=False,
    )

    st.divider()

    auto_font = st.checkbox(
        "Ajustar tamanho da fonte automaticamente",
        value=True,
        help="Usa o tamanho original do texto como referência.",
    )
    manual_font_size = st.slider(
        "Tamanho da fonte manual",
        min_value=6, max_value=24, value=10,
        disabled=auto_font,
    )
    expand_box = st.checkbox(
        "Expandir caixa de texto ao substituir",
        value=True,
        help="Permite que textos maiores caibam. Pode sobrepor levemente textos vizinhos.",
    )

    st.divider()
    st.markdown("**Exemplos de Regex úteis:**")
    st.code(
        r"CPF: \d{3}\.\d{3}\.\d{3}-\d{2}" + "\n"
        r"E-mail: [\w\.-]+@[\w\.-]+\.\w+" + "\n"
        r"Telefone: \(\d{2}\)\s?\d{4,5}-\d{4}",
        language="text",
    )

# ---------------- Tabs ----------------
tab_app, tab_manual = st.tabs(["🔒 Anonimizador", "📖 Manual"])

# ==================================================================
# TAB 1 — ANONIMIZADOR
# ==================================================================
with tab_app:
    st.title("🔒 Anonimizador de PDF")
    st.caption(
        "Carregue um PDF, defina as palavras/valores a substituir (ou tarjar) "
        "e baixe o arquivo alterado. Ideal para anonimizar CPFs, nomes, e-mails "
        "e outros dados sensíveis em massa."
    )

    # --------- Upload ---------
    uploaded = st.file_uploader("📄 Carregue o PDF", type=["pdf"])

    # --------- Scanner ---------
    st.subheader("🔍 Scanner de dados sensíveis (opcional)")
    st.caption(
        "Não sabe quais dados sensíveis existem no PDF? Clique em escanear — "
        "o app procura automaticamente por CPF, CNPJ, e-mail, telefone, "
        "cartão de crédito, CEP, PIX, placas e mais. Depois você escolhe "
        "quais quer anonimizar."
    )

    col_scan, col_clear = st.columns([3, 1])
    with col_scan:
        scan_btn = st.button(
            "🔍 Escanear PDF em busca de dados sensíveis",
            use_container_width=True,
            disabled=not uploaded,
        )
    with col_clear:
        if st.button("🗑️ Limpar escaneamento", use_container_width=True,
                     disabled=not st.session_state.scan_done):
            st.session_state.scan_results = None
            st.session_state.scan_done = False
            st.rerun()

    if scan_btn and uploaded:
        with st.spinner("Escaneando o PDF..."):
            try:
                found = scan_sensitive(uploaded.getvalue())
                st.session_state.scan_results = found
                st.session_state.scan_done = True
                st.rerun()
            except Exception as e:
                st.exception(e)

    if st.session_state.scan_done and st.session_state.scan_results is not None:
        found = st.session_state.scan_results

        if not found:
            st.info(
                "✅ Nenhum dado sensível foi detectado pelos padrões automáticos. "
                "Você ainda pode adicionar regras manuais abaixo."
            )
        else:
            rows = []
            for (tipo, valor), pages in sorted(found.items(), key=lambda x: (x[0][0], x[0][1])):
                rows.append({
                    "Anonimizar": False,
                    "Tipo": tipo,
                    "Valor": valor,
                    "Páginas": ", ".join(str(p) for p in sorted(pages)),
                    "Ocorrências": len(pages),
                    "Substituir por": SENSITIVE_PATTERNS[tipo][1],
                })

            df = pd.DataFrame(rows)

            total_itens = len(df)
            total_ocorr = int(df["Ocorrências"].sum())
            st.success(
                f"🔎 Encontrados **{total_itens}** valores únicos em "
                f"**{total_ocorr}** ocorrência(s). Marque os que deseja anonimizar:"
            )

            c1, c2, c3 = st.columns([1, 1, 2])
            with c1:
                if st.button("✅ Marcar todos", use_container_width=True):
                    st.session_state["scan_editor"] = df.assign(Anonimizar=True)
                    st.rerun()
            with c2:
                if st.button("⬜ Desmarcar todos", use_container_width=True):
                    st.session_state["scan_editor"] = df.assign(Anonimizar=False)
                    st.rerun()

            edited_df = st.data_editor(
                df,
                column_config={
                    "Anonimizar": st.column_config.CheckboxColumn(
                        "Anonimizar", default=False, width="small"
                    ),
                    "Tipo": st.column_config.TextColumn("Tipo", disabled=True, width="medium"),
                    "Valor": st.column_config.TextColumn("Valor encontrado", disabled=True, width="large"),
                    "Páginas": st.column_config.TextColumn("Páginas", disabled=True, width="medium"),
                    "Ocorrências": st.column_config.NumberColumn("Ocorr.", disabled=True, width="small"),
                    "Substituir por": st.column_config.TextColumn(
                        "Substituir por (editável)", width="large"
                    ),
                },
                hide_index=True,
                use_container_width=True,
                key="scan_editor",
            )

            if st.button("➕ Adicionar selecionados como regras", type="primary",
                         use_container_width=True):
                selecionados = edited_df[edited_df["Anonimizar"] == True]
                if selecionados.empty:
                    st.warning("⚠️ Nenhum item marcado.")
                else:
                    adicionados = 0
                    for _, row in selecionados.iterrows():
                        find_val = str(row["Valor"])
                        repl_val = str(row["Substituir por"]) if str(row["Substituir por"]).strip() \
                            else SENSITIVE_PATTERNS[row["Tipo"]][1]
                        ja_existe = any(r["find"] == find_val for r in st.session_state.rules)
                        if not ja_existe:
                            st.session_state.rules.append({"find": find_val, "replace": repl_val})
                            adicionados += 1

                    # Remove regras vazias deixadas no início
                    st.session_state.rules = [
                        r for r in st.session_state.rules
                        if r["find"].strip() or r["replace"].strip()
                    ] or [{"find": "", "replace": ""}]

                    st.success(
                        f"✅ {adicionados} regra(s) adicionada(s) à lista. "
                        "Use com **Regex DESATIVADO** para máxima precisão."
                    )
                    st.rerun()

    # --------- Regras ---------
    st.divider()
    st.subheader("📝 Regras de substituição")
    h1, h2 = st.columns([1, 1])
    h1.markdown("**Localizar**")
    h2.markdown("**Substituir por**")

    remove_idx = None
    for i, rule in enumerate(st.session_state.rules):
        cA, cB, cC = st.columns([4, 4, 0.7])
        with cA:
            rule["find"] = st.text_input(
                f"find_{i}",
                value=rule["find"],
                key=f"find_{i}",
                label_visibility="collapsed",
                placeholder=r"Ex: 111.111.111-11 | JOSE MARIA | \d{3}\.\d{3}\.\d{3}-\d{2}",
            )
        with cB:
            rule["replace"] = st.text_input(
                f"replace_{i}",
                value=rule["replace"],
                key=f"replace_{i}",
                label_visibility="collapsed",
                placeholder="Ex: 000.000.000-00 | CARLOS PATRICK",
                disabled=(mode == "Tarjar (tarja preta)"),
            )
        with cC:
            if st.button("🗑️", key=f"del_{i}", help="Remover esta regra"):
                remove_idx = i

    if remove_idx is not None:
        st.session_state.rules.pop(remove_idx)
        st.rerun()

    if st.button("➕ Adicionar regra"):
        st.session_state.rules.append({"find": "", "replace": ""})
        st.rerun()

    # --------- Processamento ---------
    st.divider()
    process_btn = st.button("🚀 Anonimizar PDF", type="primary", use_container_width=True)

    if process_btn:
        if not uploaded:
            st.error("⚠️ Carregue um PDF primeiro.")
        else:
            active_rules = [r for r in st.session_state.rules if r["find"].strip()]
            if not active_rules:
                st.error("⚠️ Adicione pelo menos uma regra de busca.")
            else:
                st.session_state.output_bytes = None
                progress = st.progress(0.0, text="Processando PDF...")

                def cb(done, tot):
                    progress.progress(done / tot, text=f"Processando página {done}/{tot}...")

                try:
                    result_bytes, total = process_pdf(
                        pdf_bytes=uploaded.getvalue(),
                        rules=active_rules,
                        mode=mode,
                        use_regex=use_regex,
                        case_sensitive=case_sensitive,
                        auto_font=auto_font,
                        manual_font_size=manual_font_size,
                        expand_box=expand_box,
                        progress_cb=cb,
                    )
                    st.session_state.output_bytes = result_bytes
                    st.session_state.total_subs = total
                    progress.empty()
                    st.success(f"✅ Concluído! **{total}** ocorrência(s) processada(s).")
                except Exception as e:
                    progress.empty()
                    st.exception(e)

    if st.session_state.output_bytes:
        st.download_button(
            "⬇️ Baixar PDF anonimizado",
            data=st.session_state.output_bytes,
            file_name="anonimizado.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )


# ==================================================================
# TAB 2 — MANUAL
# ==================================================================
MANUAL_MD = r"""
# 📖 Manual de Uso — Anonimizador de PDF

Guia completo, do zero até o PDF anonimizado, com todos os recursos explicados.

---

## 1. O que é o app

O **Anonimizador de PDF** é uma ferramenta web que:

- ✅ Carrega um PDF (qualquer quantidade de páginas)
- ✅ Substitui **em massa** palavras, nomes, CPFs, e-mails, telefones, etc.
- ✅ Ou cobre esses dados com **tarja preta** (redaction real)
- ✅ **Detecta automaticamente** dados sensíveis no PDF (novo!)
- ✅ Devolve o arquivo alterado para download

Tudo roda **no navegador**, sem login, sem banco de dados e sem enviar seus arquivos para servidores de terceiros.

---

## 2. Tela principal (visão geral)

A tela é dividida em:

- **Menu lateral (⚙️ Configurações):** modo, regex, fonte
- **Aba 🔒 Anonimizador:** upload, scanner, regras, processar
- **Aba 📖 Manual:** este manual

---

## 3. Passo a passo básico

### 🔹 Passo 1 — Carregar o PDF

Na área **📄 Carregue o PDF**, clique em **Browse files** e selecione um arquivo `.pdf`.

> ⚠️ Só aceita arquivos com extensão `.pdf`

### 🔹 Passo 2 — (Opcional) Escanear dados sensíveis

Na seção **🔍 Scanner de dados sensíveis**, clique em:

> **🔍 Escanear PDF em busca de dados sensíveis**

O app varre **todas as páginas** do PDF procurando por:

| Tipo | Exemplo |
|---|---|
| CPF | `111.111.111-00` |
| CNPJ | `11.111.111/0001-11` |
| CEP | `01310-100` |
| E-mail | `jose@email.com` |
| Telefone | `(11) 98765-4321` |
| Cartão de crédito | `4111 1111 1111 1111` |
| Data | `01/01/2024` |
| Valor R$ | `R$ 1.234,56` |
| Placa de veículo | `ABC-1234` |
| Chave PIX aleatória | `12345678-1234-1234-1234-123456789012` |

Os resultados aparecem em uma **tabela interativa** com checkboxes. Marque o que deseja anonimizar (pode marcar todos com **✅ Marcar todos**), edite a coluna **Substituir por** se quiser, e clique em:

> **➕ Adicionar selecionados como regras**

Os valores selecionados viram **regras normais** — você pode editá-las ou removê-las antes de processar.

> 💡 **Dica importante:** use as regras vindas do scanner com **Regex DESATIVADO** para máxima precisão.

### 🔹 Passo 3 — Adicionar regras manualmente

Na seção **📝 Regras de substituição**:

- **Localizar** → o que deve ser encontrado
- **Substituir por** → o que vai no lugar

Clique em **➕ Adicionar regra** para incluir mais, e **🗑️** para remover.

### 🔹 Passo 4 — Processar

Clique em **🚀 Anonimizar PDF**. Uma barra de progresso mostra o andamento página a página.

### 🔹 Passo 5 — Baixar

Clique em **⬇️ Baixar PDF anonimizado**. O arquivo é salvo como `anonimizado.pdf`.

---

## 4. As duas formas de anonimizar

No menu lateral, em **Modo de anonimização**:

### 🅰️ Substituir texto

Troca o texto antigo por um novo no mesmo lugar.

| Antes | Depois |
|---|---|
| `JOSE MARIA SILVA` | `CARLOS PATRICK` |
| `111.111.111-11` | `000.000.000-00` |

**Quando usar:** quando você quer manter o documento legível, apenas trocando informações.

### 🅱️ Tarjar (tarja preta)

Cobre o texto com um retângulo preto. O texto original é **removido** do conteúdo do PDF.

| Antes | Depois |
|---|---|
| `JOSE MARIA SILVA` | ████████████████ |

**Quando usar:** quando você quer **ocultar completamente** o dado, sem chance de recuperá-lo.

> 💡 O app faz redaction **de verdade** — usa `apply_redactions()` do PyMuPDF, que destrói o texto original do fluxo de conteúdo.

---

## 5. Scanner automático de dados sensíveis

Esta é a **funcionalidade mais poderosa** do app. Use quando você **não sabe** quais dados sensíveis existem no PDF.

### Como funciona

1. Carregue o PDF
2. Clique em **🔍 Escanear PDF em busca de dados sensíveis**
3. O app percorre **todas as páginas** aplicando 10 padrões Regex prontos
4. Aparece uma tabela com **tudo que encontrou**, agrupado por tipo + valor
5. Você marca com checkbox só o que quer anonimizar
6. Clica em **➕ Adicionar selecionados como regras**
7. Revisa as regras (pode editar/remover)
8. Clica em **🚀 Anonimizar PDF**

### Vantagens

- Você **não precisa saber** de antemão o CPF `222.222.222-00` que está na página 47
- Você **não precisa lembrar** dos formatos de e-mail, telefone, etc.
- Você escolhe **caso a caso** o que anonimizar

### Limitações honestas

- Regex pega o que **tem formato fixo** (CPF, e-mail, etc.)
- **Não pega** nomes de pessoas, endereços por extenso, nomes de empresas
- Pode haver **falsos positivos** — por isso a tabela tem checkboxes, para você revisar
- Para nomes específicos, use regras manuais (ex: `JOSE MARIA` → `CARLOS PATRICK`)

---

## 6. Regex úteis (para colar nas regras)

| O que buscar | Padrão Regex |
|---|---|
| **CPF** | `\d{3}\.\d{3}\.\d{3}-\d{2}` |
| **CNPJ** | `\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}` |
| **E-mail** | `[\w\.-]+@[\w\.-]+\.\w+` |
| **Telefone (fixo/celular)** | `\(\d{2}\)\s?\d{4,5}-\d{4}` |
| **CEP** | `\d{5}-\d{3}` |
| **Data (dd/mm/aaaa)** | `\d{2}/\d{2}/\d{4}` |
| **Nomes completos (aprox.)** | `[A-Z][a-z]+(\s[A-Z][a-z]+)+` |

---

## 7. Configurações avançadas (menu lateral)

### 🎛️ Modo de anonimização
- **Substituir texto** (padrão)
- **Tarjar (tarja preta)**

### 🔣 Usar expressões regulares (Regex)
Ativa o modo Regex. Necessário para padrões como `\d{3}\.\d{3}\.\d{3}-\d{2}`.

### 🔡 Diferenciar maiúsculas/minúsculas
- **Desmarcado** (padrão): `jose` acha `JOSE`, `Jose`, `jose`
- **Marcado:** busca exata

### 🔠 Ajustar tamanho da fonte automaticamente
- **Marcado** (recomendado): mantém o tamanho original

### 📏 Tamanho da fonte manual
Slider de 6 a 24 — só ativa se desmarcar o auto-ajuste.

### ↔️ Expandir caixa de texto
- **Marcado** (recomendado): permite substituições maiores
- **Desmarcado:** mantém a largura original

---

## 8. Exemplos práticos

### 🔸 Exemplo 1 — Anonimizar um contrato

| Localizar | Substituir por |
|---|---|
| `111.111.111-11` | `000.000.000-00` |
| `JOSE MARIA SILVA` | `CARLOS PATRICK SOUZA` |
| `jose.silva@email.com` | `anonimo@email.com` |

**Modo:** Substituir texto. **Regex:** desmarcado.

### 🔸 Exemplo 2 — Tarjar TODOS os CPFs de um lote (sem saber quais são)

| Localizar | Substituir por |
|---|---|
| `\d{3}\.\d{3}\.\d{3}-\d{2}` | *(deixe em branco)* |

**Modo:** Tarjar (tarja preta). **Regex:** marcado.

### 🔸 Exemplo 3 — Fluxo com scanner (recomendado)

1. Carregue o PDF
2. Clique em **🔍 Escanear PDF em busca de dados sensíveis**
3. Clique em **✅ Marcar todos**
4. Clique em **➕ Adicionar selecionados como regras**
5. Confirme que **Regex está DESATIVADO** no menu lateral
6. Clique em **🚀 Anonimizar PDF**
7. Baixe o resultado

---

## 9. Perguntas frequentes

### ❓ O texto antigo é realmente apagado?
✅ **Sim.** O app usa `apply_redactions()` do PyMuPDF, que remove o texto do fluxo de conteúdo do PDF.

### ❓ Meus arquivos ficam salvos em algum servidor?
❌ **Não.** Todo processamento ocorre em memória. Nada é armazenado.

### ❓ Funciona em PDF digitalizado (só imagem)?
❌ **Não diretamente.** Precisa de OCR antes.

### ❓ Quantas páginas suporta?
✅ Testado com **100+ páginas** sem problema.

### ❓ O app guarda histórico das buscas?
❌ **Não.** Ao recarregar, tudo é zerado.

### ❓ Preciso criar conta?
❌ **Não.** Sem login, sem cadastro.

### ❓ Por que o scanner não achou nomes de pessoas?
Nomes não têm formato fixo — não dá para pegar por Regex sem muitos falsos positivos. Adicione manualmente.

---

## 10. Solução de problemas

| Problema | Solução |
|---|---|
| **Não encontrou a palavra** | Use Regex com case-insensitive |
| **Texto saiu cortado** | Marque "Expandir caixa de texto" |
| **Fonte grande/pequena demais** | Desmarque auto, use slider |
| **Acentos saem errados** | Me avise — precisa registrar fonte custom |
| **Erro `ModuleNotFoundError: fitz`** | Confirme que `requirements.txt` (com "i") existe e reinicie |
| **App "dormiu"** | Reabra a URL, acorda em ~30s |
| **Lento em PDF gigante** | Divida o PDF e processe em partes |
| **Scanner não achou nada** | O PDF pode ser imagem. Precisa OCR |
| **Scanner achou coisa demais** | Desmarque manualmente os falsos positivos |

---

## 11. Boas práticas

1. **Sempre teste em um PDF pequeno** (2-3 páginas) antes de um lote grande
2. **Guarde o PDF original** — sempre tenha backup
3. **Confira o resultado** abrindo o PDF e usando Ctrl+F para buscar o dado sensível
4. **Para dados realmente sensíveis**, use o modo **Tarjar**
5. **Use o Scanner** primeiro, depois complemente com regras manuais para nomes
6. **Use Regex** quando os dados têm padrão fixo

---

## 🎓 Fluxo resumido (cola rápida)
