import streamlit as st
import graphviz
from collections import defaultdict, deque
from io import BytesIO
from docx import Document
import os
import re

# =========================
# Constantes
# =========================
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#5B9BD5", "desc": "Bleu soutenu"},
    "HUMAINE": {"color": "#ED7D31", "desc": "Orange soutenu"},
    "TECHNIQUE": {"color": "#A6A6A6", "desc": "Gris soutenu"},
}

DEFAULT_RANKDIR = "RL"  # racine à droite
ARROW_MODE = "PARENT_TO_CHILD"

# =========================
# Initialisation de l'état
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Assistant IA (Recueil d’effets)"

if "nodes" not in st.session_state:
    st.session_state.nodes = {"root": {"label": "Racine", "category": None}}
if "edges" not in st.session_state:
    st.session_state.edges = []
if "root_label" not in st.session_state:
    st.session_state.root_label = "Racine"

if "why" not in st.session_state:
    st.session_state.why = []

# =========================
# Fonctions utilitaires
# =========================
def export_docx(title, nodes, edges):
    doc = Document()
    doc.add_heading(title, 0)
    doc.add_heading("Catégories :", level=1)
    for cat, info in CATEGORIES.items():
        doc.add_paragraph(f"{cat} : {info['desc']}")
    doc.add_heading("Nœuds :", level=1)
    for nid, data in nodes.items():
        label = data.get("label", "")
        cat = data.get("category", "Non défini")
        doc.add_paragraph(f"- {label} ({cat})")
    doc.add_heading("Liens Parent → Enfant :", level=1)
    for src, tgt in edges:
        doc.add_paragraph(f"{nodes[src]['label']} → {nodes[tgt]['label']}")
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def export_why_docx(problem, answers):
    doc = Document()
    doc.add_heading("Analyse 5 Pourquoi", 0)
    doc.add_paragraph(f"Problème observé : {problem}")
    for i, ans in enumerate(answers, 1):
        doc.add_paragraph(f"{i}. Pourquoi ? — {ans}")
    buffer = BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer

def read_docx_text(file) -> str:
    doc = Document(file)
    parts = []
    # Paragraphs
    for p in doc.paragraphs:
        txt = p.text.strip()
        if txt:
            parts.append(txt)
    # Tables
    for tbl in doc.tables:
        for row in tbl.rows:
            cells = [c.text.strip() for c in row.cells]
            line = " | ".join([c for c in cells if c])
            if line:
                parts.append(line)
    return "\n".join(parts)

def heuristic_questions_and_facts(text: str):
    """
    Mode sans IA : tenter d'extraire des questions/faits de manière simple.
    - Questions : lignes/sentences avec '?', ou commençant par Qui/Quoi/Où/Quand/Pourquoi/Comment
    - Faits : puces (-, •, *) ou lignes courtes déclaratives
    """
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    questions = []
    facts = []

    q_starts = re.compile(r'^(qui|quoi|où|quand|pourquoi|comment)\b', re.IGNORECASE)
    # Collect questions
    for l in lines:
        if l.endswith('?') or q_starts.search(l):
            questions.append(l)

    # Collect facts: bullet-like or short statements
    for l in lines:
        if l.startswith(('-', '•', '*')):
            facts.append(l.lstrip('-•* ').strip())
        else:
            # Short declarative lines (no '?', < 120 chars, with at least 3 words)
            if '?' not in l and len(l) <= 120 and len(l.split()) >= 3:
                facts.append(l)

    # Deduplicate while preserving order
    def dedup(seq):
        seen = set()
        out = []
        for s in seq:
            if s not in seen:
                seen.add(s)
                out.append(s)
        return out

    return dedup(questions)[:15], dedup(facts)[:40]

# =========================
# Sidebar navigation
# =========================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Aller vers :",
    ["Arbre des causes", "5 Pourquoi", "Assistant IA (Recueil d’effets)"],
    index=["Arbre des causes", "5 Pourquoi", "Assistant IA (Recueil d’effets)"].index(st.session_state.page)
)
st.session_state.page = page

# =========================
# Pages (on ne montre ici que l'Assistant IA pour concision de l'exemple)
# =========================
if page == "Assistant IA (Recueil d’effets)":
    st.title("Assistant IA (Recueil d’effets)")
    st.markdown("Uploadez votre **fichier Word (.docx)** contenant le recueil d'effets. L’IA analysera le contenu pour proposer des **questions à poser** et des **faits objectifs**.")

    uploaded = st.file_uploader("Importer un fichier Word (.docx)", type=["docx"])

    extracted_text = ""
    if uploaded is not None:
        try:
            extracted_text = read_docx_text(uploaded)
            with st.expander("Texte extrait (aperçu)"):
                st.text_area("Aperçu", value=extracted_text, height=200)
        except Exception as e:
            st.error(f"Impossible de lire le .docx : {e}")

    if st.button("Analyser avec IA", disabled=uploaded is None):
        if not extracted_text:
            st.warning("Le document ne contient pas de texte exploitable.")
        else:
            # Tente avec OpenAI si une clé est dispo, sinon heuristique
            api_key = st.secrets.get("OPENAI_API_KEY", None) or os.environ.get("OPENAI_API_KEY")
            if api_key:
                try:
                    from openai import OpenAI
                    client = OpenAI(api_key=api_key)
                    prompt = f"""Analyse le texte suivant comme recueil d'effets d'un accident du travail.
                    Écris deux sections en Markdown :
                    ### Questions à poser
                    - puces, une question par ligne

                    ### Faits objectifs
                    - puces, formulations courtes, neutres, exploitables

                    Texte:
                    {extracted_text}
                    """
                    resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                    )
                    st.session_state.ai_output = resp.choices[0].message.content
                except Exception as e:
                    st.error(f"Erreur IA : {e}")
                    st.info("⚠️ Vérifie OPENAI_API_KEY dans les *Secrets* Streamlit.")
            else:
                # Mode dégradé : heuristique locale
                qs, fs = heuristic_questions_and_facts(extracted_text)
                md = ["### Questions à poser"] + [f"- {q}" for q in qs]
                md += ["", "### Faits objectifs"] + [f"- {f}" for f in fs]
                st.session_state.ai_output = "\n".join(md)

    if "ai_output" in st.session_state:
        st.subheader("Résultat")
        st.markdown(st.session_state.ai_output)

    st.divider()
    st.caption("Astuce : dans Streamlit Cloud, ajoutez **OPENAI_API_KEY** dans *Settings → Secrets* pour activer l'IA complète.")
