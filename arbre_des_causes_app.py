import streamlit as st
import graphviz

# Initialisation des états de session
if "nodes" not in st.session_state:
    st.session_state.nodes = {"root": {"label": "Racine"}}
if "edges" not in st.session_state:
    st.session_state.edges = []

st.title("Arbre des Causes Interactif")

# Section pour ajouter un nœud
st.header("Ajouter un nœud")
new_node_label = st.text_input("Nom du nouveau nœud")
parent_id = st.selectbox(
    "Sélectionner le nœud parent",
    options=list(st.session_state.nodes.keys()),
    format_func=lambda x: st.session_state.nodes[x]["label"]
)

if st.button("Ajouter"):
    if new_node_label.strip():
        new_node_id = f"node_{len(st.session_state.nodes)}"
        st.session_state.nodes[new_node_id] = {"label": new_node_label}
        st.session_state.edges.append((parent_id, new_node_id))
        st.success(f"Nœud '{new_node_label}' ajouté sous '{st.session_state.nodes[parent_id]['label']}'")
    else:
        st.warning("Veuillez entrer un nom de nœud valide.")

# Section pour supprimer un nœud
st.header("Supprimer un nœud")
if len(st.session_state.nodes) > 1:
    node_to_delete = st.selectbox(
        "Sélectionner le nœud à supprimer",
        options=[nid for nid in st.session_state.nodes if nid != "root"],
        format_func=lambda x: st.session_state.nodes[x]["label"]
    )
    if st.button("Supprimer"):
        # Supprimer les arêtes associées
        st.session_state.edges = [
            (src, tgt) for src, tgt in st.session_state.edges
            if tgt != node_to_delete and src != node_to_delete
        ]
        # Supprimer le nœud
        deleted_label = st.session_state.nodes[node_to_delete]["label"]
        del st.session_state.nodes[node_to_delete]
        st.success(f"Nœud '{deleted_label}' supprimé")

# Affichage de l'arbre des causes
st.header("Visualisation de l'arbre")
dot = graphviz.Digraph("Arbre des Causes", format="png")
dot.attr(rankdir="RL")  # Right-to-Left (la racine à droite, causes vers la gauche)

# Ajouter les nœuds
for node_id, data in st.session_state.nodes.items():
    dot.node(node_id, data["label"])

# Ajouter les arêtes en inversant le sens (enfant -> parent)
for src, tgt in st.session_state.edges:
    dot.edge(tgt, src)  # Inversion du sens des flèches

st.graphviz_chart(dot)
