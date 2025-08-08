import streamlit as st
import graphviz
from collections import defaultdict, deque

# --- Constantes ---
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#CFE8FF", "desc": "Bleu clair"},
    "HUMAINE": {"color": "#FFE5CC", "desc": "Orange clair"},
    "TECHNIQUE": {"color": "#E6E6E6", "desc": "Gris clair"},
}

DEFAULT_RANKDIR = "RL"  # racine à droite -> causes à gauche
ARROW_MODE = "PARENT_TO_CHILD"  # flèches Parent -> Enfant

# --- États de session ---
if "nodes" not in st.session_state:
    # Chaque nœud: {label: str, category: Optional[str]}
    st.session_state.nodes = {"root": {"label": "Racine", "category": None}}
if "edges" not in st.session_state:
    st.session_state.edges = []

st.title("Arbre des Causes Interactif")

# =========================
# Helpers
# =========================
def get_parent(node_id: str):
    for src, tgt in st.session_state.edges:
        if tgt == node_id:
            return src
    return None

def build_children_map(edges):
    children = defaultdict(list)
    for src, tgt in edges:
        children[src].append(tgt)
    return children

def is_descendant(root_id: str, query_id: str) -> bool:
    """Retourne True si query_id est dans le sous-arbre de root_id (en suivant Parent->Enfant)."""
    children = build_children_map(st.session_state.edges)
    q = deque([root_id])
    while q:
        n = q.popleft()
        if n == query_id:
            return True
        q.extend(children.get(n, []))
    return False

# =========================
# Ajout d'un nœud
# =========================
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
        # Parent -> Enfant (structure logique)
        st.session_state.edges.append((parent_id, new_node_id))
        st.success(
            f"Nœud '{new_node_label}' ajouté sous "
            f"'{st.session_state.nodes[parent_id]['label']}' "
            f"avec catégorie {new_node_category}."
        )
    else:
        st.warning("Veuillez entrer un nom de nœud valide.")

# =========================
# Édition d'un nœud existant
# =========================
st.header("Modifier un nœud existant")
if len(st.session_state.nodes) > 0:
    node_to_edit = st.selectbox(
        "Choisir le nœud à modifier",
        options=list(st.session_state.nodes.keys()),
        format_func=lambda x: st.session_state.nodes[x]["label"],
        key="edit_node_select"
    )

    cur_label = st.session_state.nodes[node_to_edit]["label"]
    cur_cat = st.session_state.nodes[node_to_edit].get("category")
    cur_parent = get_parent(node_to_edit)

    edit_label = st.text_input("Nouveau libellé", value=cur_label, key="edit_label")
    # Catégorie (None possible pour la racine si souhaité)
    all_cats = list(CATEGORIES.keys())
    if cur_cat in all_cats:
        default_idx = all_cats.index(cur_cat)
    else:
        default_idx = 0
    edit_cat = st.selectbox(
        "Nouvelle catégorie",
        options=all_cats,
        index=default_idx,
        key="edit_category"
    )

    # Re-attacher sous un nouveau parent (sauf pour la racine qui n'a pas de parent)
    parents_candidates = [nid for nid in st.session_state.nodes.keys() if nid != node_to_edit]
    # Filtrer pour éviter les cycles : on n'autorise pas de rattacher sous un descendant du nœud
    parents_candidates = [nid for nid in parents_candidates if not is_descendant(node_to_edit, nid)]

    if node_to_edit == "root":
        st.info("La racine ne peut pas être rattachée à un parent.")
        edit_parent = None
    else:
        # Déterminer l'index par défaut basé sur le parent actuel
        if cur_parent in parents_candidates:
            default_parent_idx = parents_candidates.index(cur_parent)
        elif parents_candidates:
            default_parent_idx = 0
        else:
            default_parent_idx = 0
        edit_parent = st.selectbox(
            "Nouveau parent",
            options=parents_candidates,
            index=default_parent_idx if parents_candidates else 0,
            format_func=lambda x: st.session_state.nodes[x]["label"],
            key="edit_parent_select"
        ) if parents_candidates else None

    if st.button("Mettre à jour"):
        # Mettre à jour libellé et catégorie
        st.session_state.nodes[node_to_edit]["label"] = edit_label.strip() or cur_label
        st.session_state.nodes[node_to_edit]["category"] = edit_cat

        # Mettre à jour le parent si applicable
        if node_to_edit != "root" and edit_parent is not None and edit_parent != cur_parent:
            # Supprimer l'arête actuelle (cur_parent -> node_to_edit)
            st.session_state.edges = [
                (src, tgt) for src, tgt in st.session_state.edges
                if not (src == cur_parent and tgt == node_to_edit)
            ]
            # Ajouter la nouvelle arête
            st.session_state.edges.append((edit_parent, node_to_edit))

        st.success("Nœud mis à jour.")

# =========================
# Visualisation
# =========================
st.header("Visualisation de l'arbre")
dot = graphviz.Digraph("Arbre des Causes", format="png")
dot.attr(rankdir=DEFAULT_RANKDIR)  # RL: racine à droite

# Nœuds colorés selon la catégorie
for node_id, data in st.session_state.nodes.items():
    label = data.get("label", node_id)
    cat = data.get("category")
    if cat in CATEGORIES:
        dot.node(node_id, label, style="filled", fillcolor=CATEGORIES[cat]["color"])
    else:
        dot.node(node_id, label)

# Arêtes
for src, tgt in st.session_state.edges:
    if ARROW_MODE == "PARENT_TO_CHILD":
        dot.edge(src, tgt)
    else:
        dot.edge(tgt, src)

st.graphviz_chart(dot)

# Légende
st.caption(
    "Couleurs — ORGANISATIONNELLE: bleu clair • HUMAINE: orange clair • TECHNIQUE: gris clair"
)
