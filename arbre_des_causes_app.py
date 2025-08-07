import streamlit as st
import graphviz

# Initialisation de l'état de session
if "nodes" not in st.session_state:
    st.session_state.nodes = {"racine": "Racine"}
if "edges" not in st.session_state:
    st.session_state.edges = []

st.title("🌳 Arbre des Causes Interactif")

# Section pour ajouter un nœud
st.subheader("➕ Ajouter un nœud")
new_node_label = st.text_input("Nom du nouveau nœud")
parent_options = list(st.session_state.nodes.keys())
selected_parent = st.selectbox("Sélectionner le nœud parent", parent_options)

if st.button("Ajouter"):
    if new_node_label:
        new_node_id = f"node_{len(st.session_state.nodes)}"
        st.session_state.nodes[new_node_id] = new_node_label
        st.session_state.edges.append((selected_parent, new_node_id))
        st.success(f"Nœud '{new_node_label}' ajouté sous '{st.session_state.nodes[selected_parent]}'")

# Section pour supprimer un nœud
st.subheader("🗑️ Supprimer un nœud")
removable_nodes = {k: v for k, v in st.session_state.nodes.items() if k != "racine"}
if removable_nodes:
    node_to_remove = st.selectbox("Sélectionner un nœud à supprimer", list(removable_nodes.keys()))
    if st.button("Supprimer"):
        # Supprimer les liens associés
        st.session_state.edges = [edge for edge in st.session_state.edges if node_to_remove not in edge]
        # Supprimer le nœud
        del st.session_state.nodes[node_to_remove]
        st.success(f"Nœud supprimé : {removable_nodes[node_to_remove]}")

# Affichage de l'arbre avec Graphviz
st.subheader("📌 Arbre des causes")
dot = graphviz.Digraph("Arbre des Causes", format="png")
dot.attr(rankdir="RL")  # Affichage de droite à gauche

# Ajouter les nœuds
for node_id, label in st.session_state.nodes.items():
    dot.node(node_id, label)

# Ajouter les flèches
for parent, child in st.session_state.edges:
    dot.edge(parent, child)

st.graphviz_chart(dot)

# Instructions pour mise à jour
with st.expander("📦 Instructions pour mettre à jour sur GitHub et Streamlit Cloud"):
    st.markdown("""
    1. Supprime l'ancien fichier `arbre_des_causes_app.py` sur GitHub.
    2. Upload ce nouveau fichier corrigé.
    3. Clique sur "Commit changes".
    4. Sur Streamlit Cloud, clique sur "Manage app" > "Rerun" pour relancer l'application.
    """)
