import streamlit as st
import graphviz
from collections import defaultdict, deque
from io import BytesIO
from docx import Document
import os

# =========================
# Constantes
# =========================
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#5B9BD5", "desc": "Bleu soutenu"},
    "HUMAINE": {"color": "#ED7D31", "desc": "Orange soutenu"},
    "TECHNIQUE": {"color": "#A6A6A6", "desc": "Gris soutenu"},
}

# =========================
# Initialisation de l'état
# =========================
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

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
def get_parent(node_id):
    for src, tgt in st.session_state.edges:
        if tgt == node_id:
            return src
    return None

def build_children_map(edges):
    children = defaultdict(list)
    for src, tgt in edges:
        children[src].append(tgt)
    return children

def is_descendant(root_id, query_id):
    children = build_children_map(st.session_state.edges)
    q = deque([root_id])
    while q:
        n = q.popleft()
        if n == query_id:
            return True
        q.extend(children.get(n, []))
    return False

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
        doc.add_paragraph(
            f"{nodes[src]['label']} → {nodes[tgt]['label']}"
        )

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

# =========================
# Sidebar navigation
# =========================
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Aller vers :",
    ["Accueil", "Arbre des causes", "5 Pourquoi", "Assistant IA (Recueil d’effets)"],
)
st.session_state.page = page

# =========================
# Page Accueil
# =========================
if page == "Accueil":
    st.title("Bienvenue 👋")
    st.markdown("""
    Choisissez une méthode d'analyse :

    - **Arbre des causes** : pour cartographier les causes multiples d'un accident de travail.
    - **5 Pourquoi** : pour remonter linéairement à la cause racine.
    - **Assistant IA (Recueil d’effets)** : collez vos constats, l’IA propose des questions et faits.
    """)

# =========================
# Page Arbre des causes
# =========================
elif page == "Arbre des causes":
    st.title("Analyse par Arbre des causes")

    # Nom racine
    st.subheader("Nom de la racine")
    st.session_state.root_label = st.text_input(
        "Nom de la racine",
        value=st.session_state.root_label
    )
    st.session_state.nodes["root"]["label"] = st.session_state.root_label

    # Ajout
    st.subheader("Ajouter un nœud")
    new_node_label = st.text_input("Nom du nouveau nœud")
    parent_id = st.selectbox(
        "Sélectionner le nœud parent",
        options=list(st.session_state.nodes.keys()),
        format_func=lambda x: st.session_state.nodes[x]["label"]
    )
    new_node_category = st.selectbox(
        "Catégorie",
        options=list(CATEGORIES.keys()),
        index=0,
    )
    if st.button("Ajouter"):
        if new_node_label.strip():
            new_node_id = f"node_{len(st.session_state.nodes)}"
            st.session_state.nodes[new_node_id] = {
                "label": new_node_label.strip(),
                "category": new_node_category,
            }
            st.session_state.edges.append((parent_id, new_node_id))
            st.success(f"Nœud ajouté : {new_node_label}")
        else:
            st.warning("Veuillez entrer un nom de nœud valide.")

    # Visualisation
    st.subheader("Visualisation")
    dot = graphviz.Digraph("Arbre des Causes", format="png")
    dot.attr(rankdir="RL")
    for node_id, data in st.session_state.nodes.items():
        label = data.get("label", node_id)
        cat = data.get("category")
        if cat in CATEGORIES:
            dot.node(node_id, label, style="filled", fillcolor=CATEGORIES[cat]["color"])
        else:
            dot.node(node_id, label)
    for src, tgt in st.session_state.edges:
        dot.edge(src, tgt)
    st.graphviz_chart(dot)

    # Export
    st.subheader("Exporter")
    if st.button("Exporter en Word (.docx)"):
        buffer = export_docx(
            st.session_state.root_label, st.session_state.nodes, st.session_state.edges
        )
        st.download_button(
            "Télécharger le fichier Word",
            buffer,
            file_name="arbre_des_causes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

# =========================
# Page 5 Pourquoi
# =========================
elif page == "5 Pourquoi":
    st.title("Analyse par la méthode des 5 Pourquoi")
    st.markdown("**Conseils : viser 5 pourquoi.**")

    problem = st.text_area("1) Décrire le problème")
    st.subheader("2) Poser successivement 'Pourquoi ?'")

    if st.button("Ajouter un 'Pourquoi'"):
        st.session_state.why.append("")

    for i in range(len(st.session_state.why)):
        st.session_state.why[i] = st.text_input(
            f"Réponse au Pourquoi n°{i+1}", value=st.session_state.why[i], key=f"why_{i}"
        )

    # Récapitulatif
    st.subheader("Récapitulatif")
    st.write(f"**Problème observé :** {problem}")
    for i, ans in enumerate(st.session_state.why, 1):
        st.write(f"{i}. Pourquoi ? — {ans}")

    # Export
    st.subheader("Exporter")
    if st.button("Exporter en Word (.docx)", key="exp_why"):
        buffer = export_why_docx(problem, st.session_state.why)
        st.download_button(
            "Télécharger le fichier Word",
            buffer,
            file_name="analyse_5_pourquoi.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

# =========================
# Page Assistant IA
# =========================
elif page == "Assistant IA (Recueil d’effets)":
    st.title("Assistant IA (Recueil d’effets)")
    st.markdown("Collez vos constats, l’IA propose des **questions** et des **faits** à intégrer.")

    recueil = st.text_area("Recueil d'effets")

    if st.button("Analyser avec IA"):
        try:
            from openai import OpenAI
            client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
            prompt = f"""Analyse le texte suivant comme recueil d'effets d'un accident du travail.
            Propose :
            - une liste de questions complémentaires à poser
            - une liste de faits objectifs, courts et neutres.

            Texte :
            {recueil}
            """
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
            )
            st.session_state.ai_output = response.choices[0].message.content
        except Exception as e:
            st.error(f"Erreur IA : {e}")
            st.info("⚠️ Vérifie que tu as défini OPENAI_API_KEY dans les secrets Streamlit.")

    if "ai_output" in st.session_state:
        st.subheader("Résultat IA")
        st.markdown(st.session_state.ai_output)
