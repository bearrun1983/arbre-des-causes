import streamlit as st
import graphviz

# --- Constantes ---
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#CFE8FF", "desc": "Bleu clair"},
    "HUMAINE": {"color": "#FFE5CC", "desc": "Orange clair"},
    "TECHNIQUE": {"color": "#E6E6E6", "desc": "Gris clair"},
}

# --- États de session ---
if "nodes" not in st.session_state:
    # Chaque nœud: {label: str, category: Optional[str]}
    st.session_state.nodes = {
        "root": {"label": "Racine", "category": None}
    }
if "edges" not in st.session_state:
    st.session_state.edges = []

st.title("Arbre des Causes Interactif")

# --- Ajout d'un nœud ---
st.header("Ajouter un nœud")
new_node_label = st.text_input("Nom du nouveau nœud")
parent_id = st.selectbox(
    "Sélectionner le nœud parent",
    options=list(st.session_state.nodes.keys()),
    format_func=lambda x: st.session_state.nodes[x]["label"]
)
new_node_category = st.selectbox(
    "Catégorie (détermine la couleur de la bulle)",
    options=list(CATEGORIES.keys()),
    index=0,
    help="ORGANISATIONNELLE = bleu clair, HUMAINE = orange clair, TECHNIQUE = gris clair"
)

if st.button("Ajouter"):
    if new_node_label.strip():
        new_node_id = f"node_{len(st.session_state.nodes)}"
        st.session_state.nodes[new_node_id] = {
            "label": new_node_label.strip(),
            "category": new_node_category,
        }
        # On enregistre la relation parent -> enfant (structure logique)
        st.session_state.edges.append((parent_id, new_node_id))
        st.success(
            f"Nœud '{new_node_label}' ajouté sous "
            f"'{st.session_state.nodes[parent_id]['label']}' "
            f"avec catégorie {new_node_category}."
        )
    else:
        st.warning("Veuillez entrer un nom de nœud valide.")

# --- Suppression d'un nœud ---
st.header("Supprimer un nœud")
if len(st.session_state.nodes) > 1:
    node_to_delete = st.selectbox(
        "Sélectionner le nœud à supprimer",
        options=[nid for nid in st.session_state.nodes if nid != "root"],
        format_func=lambda x: st.session_state.nodes[x]["label"]
    )
    if st.button("Supprimer"):
        st.session_state.edges = [
            (src, tgt) for src, tgt in st.session_state.edges
            if tgt != node_to_delete and src != node_to_delete
        ]
        deleted_label = st.session_state.nodes[node_to_delete]["label"]
        del st.session_state.nodes[node_to_delete]
        st.success(f"Nœud '{deleted_label}' supprimé")

# --- Visualisation ---
st.header("Visualisation de l'arbre")
dot = graphviz.Digraph("Arbre des Causes", format="png")
# Right-to-Left: la racine est à droite, les causes se développent vers la gauche
dot.attr(rankdir="RL")

# Nœuds colorés selon la catégorie
for node_id, data in st.session_state.nodes.items():
    label = data.get("label", node_id)
    cat = data.get("category")
    if cat in CATEGORIES:
        dot.node(node_id, label, style="filled", fillcolor=CATEGORIES[cat]["color"])
    else:
        dot.node(node_id, label)  # pas de catégorie -> style par défaut

# Arêtes affichées de droite vers gauche (enfant -> parent visuellement)
for src, tgt in st.session_state.edges:
    dot.edge(tgt, src)

st.graphviz_chart(dot)

# Légende
st.caption(
    "Couleurs — ORGANISATIONNELLE: bleu clair • HUMAINE: orange clair • TECHNIQUE: gris clair"
)
