import io
import re
import streamlit as st
import fitz  # PyMuPDF

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

# ---------------- Header ----------------
st.title("🔒 Anonimizador de PDF")
st.caption(
    "Carregue um PDF, defina as palavras/valores a substituir (ou tarjar) "
    "e baixe o arquivo alterado. Ideal para anonimizar CPFs, nomes, e-mails "
    "e outros dados sensíveis em massa."
)

# ---------------- Sidebar ----------------
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

# ---------------- Upload ----------------
uploaded = st.file_uploader("📄 Carregue o PDF", type=["pdf"])

# ---------------- Regras ----------------
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

# ---------------- Processamento ----------------
st.divider()
process_btn = st.button("🚀 Anonimizar PDF", type="primary", use_container_width=True)


def process_pdf(pdf_bytes, rules, mode, use_regex, case_sensitive,
                auto_font, manual_font_size, expand_box, progress_cb=None):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    total = 0
    n_pages = len(doc)

    for pno in range(n_pages):
        page = doc[pno]
        insertions = []  # lista de (rect, texto_substituto)

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
                        # fill=None remove o texto original sem pintar nada
                        page.add_redact_annot(rect, fill=None)
                    insertions.append((rect, replace_text))
                    total += 1

        # Aplica as redações (isso REMOVE o texto original de verdade)
        try:
            page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
        except TypeError:
            page.apply_redactions()
        except Exception:
            pass

        # Insere os textos substitutos
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

# ---------------- Download ----------------
if st.session_state.output_bytes:
    st.download_button(
        "⬇️ Baixar PDF anonimizado",
        data=st.session_state.output_bytes,
        file_name="anonimizado.pdf",
        mime="application/pdf",
        type="primary",
        use_container_width=True,
    )