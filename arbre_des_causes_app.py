import streamlit as st
import graphviz
from collections import defaultdict, deque
from io import BytesIO

# Essayez d'importer python-docx; si absent, on désactivera l'export Word proprement.
try:
    from docx import Document
    from docx.shared import Pt
    DOCX_AVAILABLE = True
except Exception:
    DOCX_AVAILABLE = False

st.set_page_config(page_title="Analyse - Arbre des causes & 5 Pourquoi", layout="wide")

# =========================
# Constantes & Styles
# =========================
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#5B9BD5", "desc": "Bleu soutenu"},
    "HUMAINE": {"color": "#ED7D31", "desc": "Orange soutenu"},
    "TECHNIQUE": {"color": "#A6A6A6", "desc": "Gris soutenu"},
}
DEFAULT_RANKDIR = "RL"             # racine à droite -> causes à gauche
ARROW_MODE = "PARENT_TO_CHILD"     # flèches Parent -> Enfant

# =========================
# State init (arbre des causes)
# =========================
if "nodes" not in st.session_state:
    # Chaque nœud: {label: str, category: Optional[str]}
    st.session_state.nodes = {"root": {"label": "Racine", "category": None}}
if "edges" not in st.session_state:
    st.session_state.edges = []
if "root_name" not in st.session_state:
    st.session_state.root_name = "Racine"

# =========================
# State init (5 Pourquoi)
# =========================
if "five_why_problem" not in st.session_state:
    st.session_state.five_why_problem = ""
if "five_why_answers" not in st.session_state:
    # Liste de réponses successives aux "Pourquoi ?"
    st.session_state.five_why_answers = [""]  # commence avec 1 pourquoi
if "five_why_title" not in st.session_state:
    st.session_state.five_why_title = "Analyse 5 Pourquoi"

# =========================
# Helpers - Arbre des causes
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

def export_tree_to_docx_bytes() -> bytes:
    if not DOCX_AVAILABLE:
        return b""
    doc = Document()
    # Styles simples
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    doc.add_heading(f"Arbre des causes — {st.session_state.root_name}", level=1)
    # Légende
    doc.add_heading("Légende des catégories", level=2)
    for k, v in CATEGORIES.items():
        doc.add_paragraph(f"• {k} — {v['desc']} ({v['color']})")

    # Nœuds
    doc.add_heading("Nœuds", level=2)
    for nid, data in st.session_state.nodes.items():
        label = data.get("label", nid)
        cat = data.get("category")
        cat_txt = cat if cat in CATEGORIES else "Non défini"
        if nid == "root":
            label_display = f"{label} (Racine)"
        else:
            label_display = label
        doc.add_paragraph(f"- {label_display} — Catégorie : {cat_txt}")

    # Liens
    doc.add_heading("Liens (Parent → Enfant)", level=2)
    for src, tgt in st.session_state.edges:
        s_label = st.session_state.nodes[src]["label"]
        t_label = st.session_state.nodes[tgt]["label"]
        doc.add_paragraph(f"- {s_label} → {t_label}")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

def export_5why_to_docx_bytes() -> bytes:
    if not DOCX_AVAILABLE:
        return b""
    doc = Document()
    style = doc.styles['Normal']
    style.font.name = 'Calibri'
    style.font.size = Pt(11)

    doc.add_heading(st.session_state.five_why_title, level=1)
    doc.add_heading("Problème", level=2)
    doc.add_paragraph(st.session_state.five_why_problem or "(non renseigné)")

    doc.add_heading("Analyse — 5 Pourquoi", level=2)
    for idx, ans in enumerate(st.session_state.five_why_answers, start=1):
        doc.add_paragraph(f"{idx}) Pourquoi ? → {ans or '(vide)'}")

    if len(st.session_state.five_why_answers) > 0:
        doc.add_heading("Cause racine (proposée)", level=2)
        doc.add_paragraph(st.session_state.five_why_answers[-1] or "(non renseigné)")

    bio = BytesIO()
    doc.save(bio)
    return bio.getvalue()

# =========================
# UI: Choix de la méthode
# =========================
st.sidebar.title("Méthode d'analyse")
mode = st.sidebar.radio(
    "Choisir une méthode",
    options=["Arbre des causes", "5 Pourquoi"],
    index=0
)

# =========================
# Mode: Arbre des causes
# =========================
if mode == "Arbre des causes":
    st.title("Analyse par Arbre des Causes")

    # Bloc configuration de la racine
    with st.expander("Paramètres généraux", expanded=True):
        st.session_state.root_name = st.text_input("Nom de la racine", value=st.session_state.root_name)
        # Synchroniser le label du nœud root
        st.session_state.nodes["root"]["label"] = st.session_state.root_name

        col_a, col_b, col_c = st.columns(3)
        with col_a:
            if st.button("Réinitialiser (tout effacer)"):
                st.session_state.nodes = {"root": {"label": st.session_state.root_name, "category": None}}
                st.session_state.edges = []
                st.success("Arbre réinitialisé.")
        with col_b:
            disable_export = not DOCX_AVAILABLE
            if disable_export:
                st.caption("L'export Word nécessite le paquet python-docx (ajoute-le à requirements.txt).")
            if st.button("Exporter en Word (.docx)", disabled=disable_export):
                content = export_tree_to_docx_bytes()
                if content:
                    st.download_button(
                        label="Télécharger le document Word",
                        data=content,
                        file_name="arbre_des_causes.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        with col_c:
            st.caption("Orientation: racine à droite (Right-to-Left), flèches Parent → Enfant.")

    # Ajout d'un nœud
    st.subheader("Ajouter un nœud")
    new_node_label = st.text_input("Nom du nouveau nœud", key="add_label")
    parent_id = st.selectbox(
        "Sélectionner le nœud parent",
        options=list(st.session_state.nodes.keys()),
        format_func=lambda x: st.session_state.nodes[x]["label"],
        key="add_parent"
    )
    new_node_category = st.selectbox(
        "Catégorie (détermine la couleur de la bulle)",
        options=list(CATEGORIES.keys()),
        index=0,
        help="ORGANISATIONNELLE = bleu, HUMAINE = orange, TECHNIQUE = gris",
        key="add_category"
    )
    if st.button("Ajouter le nœud"):
        if new_node_label.strip():
            new_node_id = f"node_{len(st.session_state.nodes)}"
            st.session_state.nodes[new_node_id] = {
                "label": new_node_label.strip(),
                "category": new_node_category,
            }
            st.session_state.edges.append((parent_id, new_node_id))  # Parent -> Enfant
            st.success(
                f"Nœud '{new_node_label}' ajouté sous "
                f"'{st.session_state.nodes[parent_id]['label']}' "
                f"avec catégorie {new_node_category}."
            )
        else:
            st.warning("Veuillez entrer un nom de nœud valide.")

    # Édition d'un nœud
    st.subheader("Modifier un nœud existant")
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
        all_cats = list(CATEGORIES.keys())
        default_idx = all_cats.index(cur_cat) if cur_cat in all_cats else 0
        edit_cat = st.selectbox(
            "Nouvelle catégorie",
            options=all_cats,
            index=default_idx,
            key="edit_category"
        )

        # Re-attacher sous un nouveau parent (sauf pour la racine qui n'a pas de parent)
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

        cols = st.columns(2)
        with cols[0]:
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
        with cols[1]:
            if node_to_edit != "root" and st.button("Supprimer ce nœud"):
                # Supprimer arêtes associées + le nœud
                st.session_state.edges = [
                    (src, tgt) for src, tgt in st.session_state.edges
                    if tgt != node_to_edit and src != node_to_edit
                ]
                deleted_label = st.session_state.nodes[node_to_edit]["label"]
                del st.session_state.nodes[node_to_edit]
                st.success(f"Nœud '{deleted_label}' supprimé.")

    # Visualisation
    st.subheader("Visualisation de l'arbre")
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

    st.caption(
        "Couleurs — ORGANISATIONNELLE: bleu • HUMAINE: orange • TECHNIQUE: gris"
    )

# =========================
# Mode: 5 Pourquoi
# =========================
else:
    st.title("Analyse par la méthode des 5 Pourquoi")

    with st.expander("Paramètres / Export", expanded=True):
        st.session_state.five_why_title = st.text_input("Titre de l'analyse", value=st.session_state.five_why_title)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Réinitialiser l'analyse 5 Pourquoi"):
                st.session_state.five_why_problem = ""
                st.session_state.five_why_answers = [""]
                st.success("Analyse réinitialisée.")
        with c2:
            disable_export = not DOCX_AVAILABLE
            if disable_export:
                st.caption("L'export Word nécessite le paquet python-docx (ajoute-le à requirements.txt).")
            if st.button("Exporter en Word (.docx)", disabled=disable_export):
                content = export_5why_to_docx_bytes()
                if content:
                    st.download_button(
                        label="Télécharger le document Word",
                        data=content,
                        file_name="analyse_5_pourquoi.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                    )
        with c3:
            st.caption("Conseil: visez 4 à 6 'Pourquoi' selon la complexité.")

    st.subheader("1) Décrire le problème")
    st.session_state.five_why_problem = st.text_area(
        "Problème observé",
        value=st.session_state.five_why_problem,
        height=100
    )

    st.subheader("2) Poser successivement 'Pourquoi ?'")
    # Afficher les champs pour chaque Pourquoi
    to_remove_indices = []
    for i, ans in enumerate(st.session_state.five_why_answers):
        cols = st.columns([1, 8, 1])
        with cols[0]:
            st.markdown(f"**{i+1}**")
        with cols[1]:
            st.session_state.five_why_answers[i] = st.text_input(
                f"Réponse au Pourquoi n°{i+1}",
                value=ans,
                key=f"five_why_{i}"
            )
        with cols[2]:
            if i > 0:
                if st.button("🗑️", key=f"del_{i}"):
                    to_remove_indices.append(i)

    # Appliquer suppressions
    if to_remove_indices:
        for idx in sorted(to_remove_indices, reverse=True):
            st.session_state.five_why_answers.pop(idx)
        st.experimental_rerun()

    c_add, c_root = st.columns(2)
    with c_add:
        if st.button("➕ Ajouter un 'Pourquoi'"):
            st.session_state.five_why_answers.append("")
            st.experimental_rerun()

    # Synthèse
    st.subheader("3) Synthèse")
    if st.session_state.five_why_answers:
        st.write("**Cause racine proposée :**")
        st.info(st.session_state.five_why_answers[-1] or "—")
    else:
        st.info("Ajoutez au moins un 'Pourquoi'.")
