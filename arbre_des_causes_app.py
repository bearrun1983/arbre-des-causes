
import streamlit as st
import graphviz
import uuid

st.set_page_config(page_title="Arbre des Causes Interactif", layout="wide")
st.title("🌳 Arbre des Causes Interactif")

# Initialisation de l'état de session
if "nodes" not in st.session_state:
    st.session_state.nodes = {}
if "edges" not in st.session_state:
    st.session_state.edges = []

# Fonction pour ajouter un nœud
def add_node(label, parent_id=None):
    node_id = str(uuid.uuid4())
    st.session_state.nodes[node_id] = {"label": label}
    if parent_id:
        st.session_state.edges.append((parent_id, node_id))

# Fonction pour supprimer un nœud
def delete_node(node_id):
    if node_id in st.session_state.nodes:
        del st.session_state.nodes[node_id]
        st.session_state.edges = [(src, tgt) for src, tgt in st.session_state.edges if src != node_id and tgt != node_id]

# Interface utilisateur pour ajouter un nœud
with st.form("add_node_form"):
    new_label = st.text_input("Nom du nœud à ajouter")
    parent_options = {"Aucun (racine)": None}
    parent_options.update({v["label"]: k for k, v in st.session_state.nodes.items()})
    selected_parent_label = st.selectbox("Sélectionner le nœud parent", list(parent_options.keys()))
    submitted = st.form_submit_button("Ajouter")
    if submitted and new_label:
        add_node(new_label, parent_options[selected_parent_label])

# Interface utilisateur pour supprimer un nœud
with st.form("delete_node_form"):
    if st.session_state.nodes:
        delete_options = {v["label"]: k for k, v in st.session_state.nodes.items()}
        selected_delete_label = st.selectbox("Sélectionner un nœud à supprimer", list(delete_options.keys()))
        delete_submitted = st.form_submit_button("Supprimer")
        if delete_submitted:
            delete_node(delete_options[selected_delete_label])

# Affichage de l'arbre avec Graphviz
if st.session_state.nodes:
    dot = graphviz.Digraph()
    dot.attr(rankdir="RL")  # Affichage de droite à gauche
    for node_id, data in st.session_state.nodes.items():
        dot.node(node_id, data["label"])
    for src, tgt in st.session_state.edges:
        dot.edge(src, tgt)
    st.graphviz_chart(dot)
else:
    st.info("Ajoutez un nœud pour commencer à construire l'arbre des causes.")

# Instructions pour mise à jour GitHub
with st.expander("📦 Instructions pour mettre à jour sur GitHub et Streamlit Cloud"):
    st.markdown("""
    1. Sur GitHub, allez dans votre dépôt `arbre-des-causes`.
    2. Supprimez l'ancien fichier `arbre_des_causes_app.py`.
    3. Cliquez sur **Add file > Upload files** et ajoutez ce nouveau fichier.
    4. Cliquez sur **Commit changes**.
    5. Sur [Streamlit Cloud](https://streamlit.io/cloud), allez dans **Manage app** et cliquez sur **Rerun** ou **Restart**.
    """)
