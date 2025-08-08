import streamlit as st
import graphviz
from collections import defaultdict, deque
from io import BytesIO

# === Couleurs (plus foncées) ===
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#5B9BD5", "desc": "Bleu soutenu"},
    "HUMAINE": {"color": "#ED7D31", "desc": "Orange soutenu"},
    "TECHNIQUE": {"color": "#A6A6A6", "desc": "Gris soutenu"},
}

DEFAULT_RANKDIR = "RL"  # racine à droite -> causes à gauche
ARROW_MODE = "PARENT_TO_CHILD"  # flèches Parent -> Enfant

# === États de session ===
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
# Paramètres racine (modifiable)
# =========================
st.header("Paramètres de la racine")
root_label_current = st.session_state.nodes["root"]["label"]
root_label_new = st.text_input("Nom de la racine", value=root_label_current)
if root_label_new.strip() and root_label_new != root_label_current:
    st.session_state.nodes["root"]["label"] = root_label_new.strip()
    st.success("Nom de la racine mis à jour.")

# =========================
# Ajout d'un nœud
# =========================
st.header("Ajouter un nœud")
col1, col2 = st.columns(2)
with col1:
    new_node_label = st.text_input("Nom du nouveau nœud", key="new_node_label")
with col2:
    new_node_category = st.selectbox(
        "Catégorie",
        options=list(CATEGORIES.keys()),
        index=0,
        help="ORGANISATIONNELLE = bleu • HUMAINE = orange • TECHNIQUE = gris",
        key="new_node_category"
    )

parent_id = st.selectbox(
    "Sélectionner le nœud parent",
    options=list(st.session_state.nodes.keys()),
    format_func=lambda x: st.session_state.nodes[x]["label"]
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

    col1, col2 = st.columns(2)
    with col1:
        edit_label = st.text_input("Nouveau libellé", value=cur_label, key="edit_label")
    with col2:
        all_cats = list(CATEGORIES.keys())
        default_idx = all_cats.index(cur_cat) if cur_cat in all_cats else 0
        edit_cat = st.selectbox(
            "Nouvelle catégorie",
            options=all_cats,
            index=default_idx,
            key="edit_category"
        )

    parents_candidates = [nid for nid in st.session_state.nodes.keys() if nid != node_to_edit]
    parents_candidates = [nid for nid in parents_candidates if not is_descendant(node_to_edit, nid)]

    if node_to_edit == "root":
        st.info("La racine ne peut pas être rattachée à un parent.")
        edit_parent = None
    else:
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
        st.session_state.nodes[node_to_edit]["label"] = edit_label.strip() or cur_label
        st.session_state.nodes[node_to_edit]["category"] = edit_cat
        if node_to_edit != "root" and edit_parent is not None and edit_parent != cur_parent:
            st.session_state.edges = [
                (src, tgt) for src, tgt in st.session_state.edges
                if not (src == cur_parent and tgt == node_to_edit)
            ]
            st.session_state.edges.append((edit_parent, node_to_edit))
        st.success("Nœud mis à jour.")

# =========================
# Visualisation
# =========================
st.header("Visualisation de l'arbre")
dot = graphviz.Digraph("Arbre des Causes", format="png")
dot.attr(rankdir=DEFAULT_RANKDIR)  # RL: racine à droite

for node_id, data in st.session_state.nodes.items():
    label = data.get("label", node_id)
    cat = data.get("category")
    if cat in CATEGORIES:
        dot.node(node_id, label, style="filled", fillcolor=CATEGORIES[cat]["color"])
    else:
        dot.node(node_id, label)

for src, tgt in st.session_state.edges:
    if ARROW_MODE == "PARENT_TO_CHILD":
        dot.edge(src, tgt)
    else:
        dot.edge(tgt, src)

st.graphviz_chart(dot)

# =========================
# Export Word (.docx) — texte uniquement
# =========================
st.header("Exporter")
def generate_docx_bytes():
    try:
        from docx import Document
    except Exception as e:
        st.error("Le module python-docx n'est pas disponible dans cet environnement.")
        return None

    doc = Document()
    doc.add_heading(f"Arbre des causes — {st.session_state.nodes['root']['label']}", 0)

    doc.add_heading("Légende des catégories", level=1)
    p = doc.add_paragraph()
    for cat, meta in CATEGORIES.items():
        p.add_run(f"• {cat} : {meta['desc']} (couleur {meta['color']})\n")

    doc.add_heading("Nœuds", level=1)
    for node_id, data in st.session_state.nodes.items():
        cat = data.get("category") or "(aucune)"
        doc.add_paragraph(f"- {data.get('label', node_id)}  —  Catégorie : {cat}")

    doc.add_heading("Liens (Parent → Enfant)", level=1)
    if st.session_state.edges:
        for src, tgt in st.session_state.edges:
            src_label = st.session_state.nodes[src]["label"]
            tgt_label = st.session_state.nodes[tgt]["label"]
            doc.add_paragraph(f"- {src_label}  →  {tgt_label}")
    else:
        doc.add_paragraph("(aucun lien)")

    bio = BytesIO()
    doc.save(bio)
    bio.seek(0)
    return bio

if st.button("Exporter en Word (.docx)"):
    content = generate_docx_bytes()
    if content:
        st.download_button(
            label="Télécharger le document",
            data=content,
            file_name="arbre_des_causes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
