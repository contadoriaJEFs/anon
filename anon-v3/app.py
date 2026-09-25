import io
import os
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
    "Cartao de credito": (r"\b(?:\d{4}[\s-]?){3}\d{4}\b", "0000 0000 0000 0000"),
    "Data": (r"\b\d{2}/\d{2}/\d{4}\b", "00/00/0000"),
    "Valor R$": (r"R\$\s?\d{1,3}(?:\.\d{3})*(?:,\d{2})?", "R$ 0,00"),
    "Placa de veiculo": (r"\b[A-Z]{3}[-\s]?\d[A-Z0-9]\d{2}\b", "AAA-0000"),
    "Chave PIX aleatoria": (
        r"\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b",
        "00000000-0000-0000-0000-000000000000",
    ),
}


# ---------------- Funcoes ----------------
def scan_sensitive(pdf_bytes):
    """Escaneia o PDF em busca de padroes sensiveis."""
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
    st.header("Configuracoes")

    mode = st.radio(
        "Modo de anonimizacao",
        ["Substituir texto", "Tarjar (tarja preta)"],
        help="Substituir troca o valor pelo que voce digitar. "
             "Tarjar apenas cobre com preto.",
    )

    use_regex = st.checkbox(
        "Usar expressoes regulares (Regex)",
        value=False,
        help=r"Ex: CPF -> \d{3}\.\d{3}\.\d{3}-\d{2}",
    )

    case_sensitive = st.checkbox(
        "Diferenciar maiusculas/minusculas (apenas Regex)",
        value=False,
    )

    st.divider()

    auto_font = st.checkbox(
        "Ajustar tamanho da fonte automaticamente",
        value=True,
    )
    manual_font_size = st.slider(
        "Tamanho da fonte manual",
        min_value=6, max_value=24, value=10,
        disabled=auto_font,
    )
    expand_box = st.checkbox(
        "Expandir caixa de texto ao substituir",
        value=True,
    )

    st.divider()
    st.markdown("**Exemplos de Regex uteis:**")
    st.code(
        r"CPF: \d{3}\.\d{3}\.\d{3}-\d{2}" + "\n"
        r"E-mail: [\w\.-]+@[\w\.-]+\.\w+" + "\n"
        r"Telefone: \(\d{2}\)\s?\d{4,5}-\d{4}",
        language="text",
    )

# ---------------- Tabs ----------------
tab_app, tab_manual = st.tabs(["Anonimizador", "Manual"])

# ==================================================================
# TAB 1 — ANONIMIZADOR
# ==================================================================
with tab_app:
    st.title("Anonimizador de PDF")
    st.caption(
        "Carregue um PDF, defina as palavras/valores a substituir (ou tarjar) "
        "e baixe o arquivo alterado."
    )

    uploaded = st.file_uploader("Carregue o PDF", type=["pdf"])

    # --------- Scanner ---------
    st.subheader("Scanner de dados sensiveis (opcional)")
    st.caption(
        "Nao sabe quais dados sensiveis existem no PDF? Clique em escanear — "
        "o app procura por CPF, CNPJ, e-mail, telefone, cartao, CEP, PIX, placas e mais."
    )

    col_scan, col_clear = st.columns([3, 1])
    with col_scan:
        scan_btn = st.button(
            "Escanear PDF em busca de dados sensiveis",
            use_container_width=True,
            disabled=not uploaded,
        )
    with col_clear:
        if st.button("Limpar escaneamento", use_container_width=True,
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
                "Nenhum dado sensivel foi detectado pelos padroes automaticos. "
                "Voce ainda pode adicionar regras manuais abaixo."
            )
        else:
            rows = []
            for (tipo, valor), pages in sorted(found.items(), key=lambda x: (x[0][0], x[0][1])):
                rows.append({
                    "Anonimizar": False,
                    "Tipo": tipo,
                    "Valor": valor,
                    "Paginas": ", ".join(str(p) for p in sorted(pages)),
                    "Ocorrencias": len(pages),
                    "Substituir por": SENSITIVE_PATTERNS[tipo][1],
                })

            df = pd.DataFrame(rows)
            total_itens = len(df)
            total_ocorr = int(df["Ocorrencias"].sum())
            st.success(
                f"Encontrados **{total_itens}** valores unicos em "
                f"**{total_ocorr}** ocorrencia(s). Marque os que deseja anonimizar:"
            )

            c1, c2 = st.columns([1, 1])
            with c1:
                if st.button("Marcar todos", use_container_width=True):
                    st.session_state["scan_editor"] = df.assign(Anonimizar=True)
                    st.rerun()
            with c2:
                if st.button("Desmarcar todos", use_container_width=True):
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
                    "Paginas": st.column_config.TextColumn("Paginas", disabled=True, width="medium"),
                    "Ocorrencias": st.column_config.NumberColumn("Ocorr.", disabled=True, width="small"),
                    "Substituir por": st.column_config.TextColumn(
                        "Substituir por (editavel)", width="large"
                    ),
                },
                hide_index=True,
                use_container_width=True,
                key="scan_editor",
            )

            if st.button("Adicionar selecionados como regras", type="primary",
                         use_container_width=True):
                selecionados = edited_df[edited_df["Anonimizar"] == True]
                if selecionados.empty:
                    st.warning("Nenhum item marcado.")
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

                    st.session_state.rules = [
                        r for r in st.session_state.rules
                        if r["find"].strip() or r["replace"].strip()
                    ] or [{"find": "", "replace": ""}]

                    st.success(
                        f"{adicionados} regra(s) adicionada(s) a lista. "
                        "Use com Regex DESATIVADO para maxima precisao."
                    )
                    st.rerun()

    # --------- Regras ---------
    st.divider()
    st.subheader("Regras de substituicao")
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
            if st.button("X", key=f"del_{i}", help="Remover esta regra"):
                remove_idx = i

    if remove_idx is not None:
        st.session_state.rules.pop(remove_idx)
        st.rerun()

    if st.button("Adicionar regra"):
        st.session_state.rules.append({"find": "", "replace": ""})
        st.rerun()

    # --------- Processamento ---------
    st.divider()
    process_btn = st.button("Anonimizar PDF", type="primary", use_container_width=True)

    if process_btn:
        if not uploaded:
            st.error("Carregue um PDF primeiro.")
        else:
            active_rules = [r for r in st.session_state.rules if r["find"].strip()]
            if not active_rules:
                st.error("Adicione pelo menos uma regra de busca.")
            else:
                st.session_state.output_bytes = None
                progress = st.progress(0.0, text="Processando PDF...")

                def cb(done, tot):
                    progress.progress(done / tot, text=f"Processando pagina {done}/{tot}...")

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
                    st.success(f"Concluido! **{total}** ocorrencia(s) processada(s).")
                except Exception as e:
                    progress.empty()
                    st.exception(e)

    if st.session_state.output_bytes:
        st.download_button(
            "Baixar PDF anonimizado",
            data=st.session_state.output_bytes,
            file_name="anonimizado.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True,
        )


# ==================================================================
# TAB 2 — MANUAL (le do arquivo manual.md)
# ==================================================================
with tab_manual:
    st.title("Manual de Uso")
    manual_path = os.path.join(os.path.dirname(__file__), "manual.md")
    try:
        with open(manual_path, "r", encoding="utf-8") as f:
            manual_content = f.read()
        st.markdown(manual_content)
    except FileNotFoundError:
        st.error(
            "Arquivo `manual.md` nao encontrado. "
            "Certifique-se de que ele esta na raiz do repositorio, ao lado do `app.py`."
        )
    except Exception as e:
        st.exception(e)
