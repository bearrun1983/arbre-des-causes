
import streamlit as st
import graphviz
import uuid

# Initialiser les états de session
if "nodes" not in st.session_state:
    st.session_state.nodes = {}
    st.session_state.edges = []

# Fonction pour ajouter un nœud
def add_node(label, parent_id=None):
    node_id = str(uuid.uuid4())
    st.session_state.nodes[node_id] = {"label": label}
    if parent_id:
        st.session_state.edges.append((parent_id, node_id))

# Fonction pour supprimer un nœud
def delete_node(node_id):
    st.session_state.nodes.pop(node_id, None)
    st.session_state.edges = [edge for edge in st.session_state.edges if edge[0] != node_id and edge[1] != node_id]

# Interface utilisateur
st.title("🌳 Arbre des Causes Interactif")

# Ajouter un nouveau nœud
with st.form("add_node_form"):
    label = st.text_input("Nom du nœud à ajouter")
    parent_options = list(st.session_state.nodes.items())
    parent_id = st.selectbox("Sélectionner le nœud parent", options=[None] + [node_id for node_id, data in parent_options],
                             format_func=lambda x: "Aucun (racine)" if x is None else st.session_state.nodes[x]["label"])
    submitted = st.form_submit_button("Ajouter")
    if submitted and label:
        add_node(label, parent_id)

# Supprimer un nœud
with st.form("delete_node_form"):
    delete_id = st.selectbox("Sélectionner un nœud à supprimer", options=[None] + list(st.session_state.nodes.keys()),
                             format_func=lambda x: "" if x is None else st.session_state.nodes[x]["label"])
    delete_submit = st.form_submit_button("Supprimer")
    if delete_submit and delete_id:
        delete_node(delete_id)

# Affichage de l'arbre avec orientation droite à gauche
if st.session_state.nodes:
    dot = graphviz.Digraph()
    dot.attr(rankdir="RL")  # Right to Left
    for node_id, data in st.session_state.nodes.items():
        dot.node(node_id, data["label"])
    for parent, child in st.session_state.edges:
        dot.edge(parent, child)
    st.graphviz_chart(dot)

# Instructions pour mise à jour GitHub et Streamlit Cloud
with st.expander("📦 Instructions pour mettre à jour sur GitHub et relancer Streamlit Cloud"):
    st.markdown("""
**Étapes pour mettre à jour ton application :**

1. Va sur ton dépôt GitHub `arbre-des-causes`.
2. Clique sur **"Add file" > "Upload files"**.
3. Glisse ce fichier mis à jour `arbre_des_causes_app.py`.
4. Clique sur **"Commit changes"**.

**Sur Streamlit Cloud :**

1. Va sur [https://streamlit.io/cloud](https://streamlit.io/cloud).
2. Clique sur **"Manage app"**.
3. Clique sur **"Rerun"** ou **"Restart"** pour relancer l’application avec les modifications.

Ton application sera mise à jour automatiquement 🎉
""")
