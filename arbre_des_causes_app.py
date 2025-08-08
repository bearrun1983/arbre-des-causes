import streamlit as st
import graphviz
from collections import defaultdict, deque
from io import BytesIO

# Try to import python-docx for Word export
try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

# --- Constantes ---
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#5B9BD5", "desc": "Bleu (plus soutenu)"},
    "HUMAINE": {"color": "#ED7D31", "desc": "Orange (plus soutenu)"},
    "TECHNIQUE": {"color": "#A6A6A6", "desc": "Gris (plus soutenu)"},
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

def export_to_docx():
    """Construit un document Word (texte uniquement) décrivant l'arbre."""
    if not DOCX_AVAILABLE:
        st.error("Le module python-docx n'est pas disponible dans cet environnement.")
        return None

    doc = Document()

    # Titre = label de la racine
    root_label = st.session_state.nodes.get("root", {}).get("label", "Racine")
    doc.add_heading(f"Arbre des Causes — {root_label}", level=1)

    # Légende
    doc.add_heading("Légende des catégories", level=2)
    for name, meta in CATEGORIES.items():
        p = doc.add_paragraph()
        run = p.add_run(f"{name} — {meta['desc']}")
        run.font.size = Pt(10)

    # Nœuds
    doc.add_heading("Nœuds", level=2)
    for node_id, data in st.session_state.nodes.items():
        cat = data.get("category")
        cat_txt = cat if cat in CATEGORIES else "Aucune"
        doc.add_paragraph(f"- {data.get('label', node_id)}  [catégorie: {cat_txt}]")

    # Arêtes
    doc.add_heading("Liens (Parent → Enfant)", level=2)
    if st.session_state.edges:
        for src, tgt in st.session_state.edges:
            src_label = st.session_state.nodes.get(src, {}).get("label", src)
            tgt_label = st.session_state.nodes.get(tgt, {}).get("label", tgt)
            doc.add_paragraph(f"- {src_label}  →  {tgt_label}")
    else:
        doc.add_paragraph("(aucun lien)")

    # Buffer
    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# =========================
# Racine modifiable
# =========================
st.subheader("Paramètres de la racine")
root_current = st.session_state.nodes["root"]["label"]
new_root_label = st.text_input("Nom de la racine", value=root_current, key="root_label_input")
if st.button("Mettre à jour la racine"):
    st.session_state.nodes["root"]["label"] = new_root_label.strip() or root_current
    st.success("Nom de la racine mis à jour.")

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
    help="ORGANISATIONNELLE = bleu soutenu, HUMAINE = orange soutenu, TECHNIQUE = gris soutenu"
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
    # Catégorie
    all_cats = list(CATEGORIES.keys())
    default_idx = all_cats.index(cur_cat) if cur_cat in all_cats else 0
    edit_cat = st.selectbox(
        "Nouvelle catégorie",
        options=all_cats,
        index=default_idx,
        key="edit_category"
    )

    # Re-attacher sous un nouveau parent (sauf pour la racine)
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
# Right-to-Left: la racine est à droite, les causes se développent vers la gauche
dot.attr(rankdir=DEFAULT_RANKDIR)

# Nœuds colorés selon la catégorie (couleurs plus soutenues)
for node_id, data in st.session_state.nodes.items():
    label = data.get("label", node_id)
    cat = data.get("category")
    if cat in CATEGORIES:
        dot.node(node_id, label, style="filled", fillcolor=CATEGORIES[cat]["color"])
    else:
        dot.node(node_id, label)

# Arêtes Parent -> Enfant (donc flèches de droite vers gauche visuellement)
for src, tgt in st.session_state.edges:
    if ARROW_MODE == "PARENT_TO_CHILD":
        dot.edge(src, tgt)
    else:
        dot.edge(tgt, src)

st.graphviz_chart(dot)

# =========================
# Export Word (texte uniquement)
# =========================
st.header("Exporter")
if st.button("Exporter en Word (.docx)"):
    buf = export_to_docx()
    if buf is not None:
        st.download_button(
            label="Télécharger le document Word",
            data=buf.getvalue(),
            file_name="arbre_des_causes.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )
