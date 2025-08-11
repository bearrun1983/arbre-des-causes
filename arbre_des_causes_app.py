import streamlit as st
import graphviz
from collections import defaultdict, deque

try:
    from docx import Document
except Exception:
    Document = None

# =====================
# Constantes & couleurs
# =====================
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#5B9BD5", "desc": "Bleu (organisationnelle)"},
    "HUMAINE": {"color": "#ED7D31", "desc": "Orange (humaine)"},
    "TECHNIQUE": {"color": "#A6A6A6", "desc": "Gris (technique)"},
}

DEFAULT_RANKDIR = "RL"           # racine à droite -> causes à gauche
ARROW_MODE = "PARENT_TO_CHILD"   # flèches Parent -> Enfant

# =====================
# États de session init
# =====================
if "page" not in st.session_state:
    st.session_state.page = "Accueil"

# Arbre des causes
if "nodes" not in st.session_state:
    st.session_state.nodes = {"root": {"label": "Racine", "category": None}}
if "edges" not in st.session_state:
    st.session_state.edges = []
if "root_label" not in st.session_state:
    st.session_state.root_label = "Racine"

# 5 Pourquoi
if "fivewhy_problem" not in st.session_state:
    st.session_state.fivewhy_problem = ""
if "fivewhy_answers" not in st.session_state:
    st.session_state.fivewhy_answers = []  # list[str]

# ===============
# Sidebar routing
# ===============
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Aller à",
    ["Accueil", "Arbre des causes", "Méthode des 5 Pourquoi"],
    index=["Accueil", "Arbre des causes", "Méthode des 5 Pourquoi"].index(st.session_state.page),
)
st.session_state.page = page

# ========================
# Fonctions utilitaires
# ========================
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
    """Retourne True si query_id est dans le sous-arbre de root_id (Parent->Enfant)."""
    children = build_children_map(st.session_state.edges)
    from collections import deque as _dq
    q = _dq([root_id])
    while q:
        n = q.popleft()
        if n == query_id:
            return True
        q.extend(children.get(n, []))
    return False

def export_tree_to_docx(nodes, edges, root_label):
    if Document is None:
        st.error("Le module python-docx n'est pas disponible dans cet environnement.")
        return

    doc = Document()
    doc.add_heading(f"Arbre des causes — {root_label}", level=1)

    # Légende
    doc.add_heading("Légende des catégories", level=2)
    for k, v in CATEGORIES.items():
        doc.add_paragraph(f"- {k}")

    # Nœuds
    doc.add_heading("Nœuds", level=2)
    for nid, data in nodes.items():
        label = data.get("label", nid)
        cat = data.get("category")
        doc.add_paragraph(f"• {label}  [{cat if cat else 'Aucune catégorie'}]")

    # Liens
    doc.add_heading("Liens (Parent → Enfant)", level=2)
    for src, tgt in edges:
        src_label = nodes[src]["label"]
        tgt_label = nodes[tgt]["label"]
        doc.add_paragraph(f"• {src_label} → {tgt_label}")

    return doc

def export_fivewhy_to_docx(problem: str, answers: list[str]):
    if Document is None:
        st.error("Le module python-docx n'est pas disponible dans cet environnement.")
        return

    doc = Document()
    doc.add_heading("Analyse — Méthode des 5 Pourquoi", level=1)
    doc.add_paragraph("Conseils : viser 5 pourquoi.")

    doc.add_heading("Problème observé", level=2)
    doc.add_paragraph(problem or "(non renseigné)")

    doc.add_heading("Chaîne des 'Pourquoi ?'", level=2)
    if answers:
        for i, ans in enumerate(answers, start=1):
            doc.add_paragraph(f"{i}. Pourquoi ? — {ans}")
    else:
        doc.add_paragraph("(aucune réponse pour l'instant)")

    return doc

# ===================
# Page: Accueil
# ===================
if page == "Accueil":
    st.title("LOGICIEL — Analyse des causes")
    st.markdown(
        "- Choisissez **Arbre des causes** pour une analyse multi-facteurs.\n"
        "- Choisissez **Méthode des 5 Pourquoi** pour remonter linéairement à la cause racine."
    )

# ===================
# Page: Arbre des causes
# ===================
elif page == "Arbre des causes":
    st.title("Arbre des Causes — Interface")

    # Nom de la racine modifiable
    st.subheader("Nom de la racine")
    st.session_state.root_label = st.text_input("Nom de la racine", value=st.session_state.root_label)
    st.session_state.nodes["root"]["label"] = st.session_state.root_label

    # Ajout
    st.subheader("Ajouter un nœud")
    new_node_label = st.text_input("Nom du nouveau nœud", key="tree_new_label")
    parent_id = st.selectbox(
        "Sélectionner le nœud parent",
        options=list(st.session_state.nodes.keys()),
        format_func=lambda x: st.session_state.nodes[x]["label"],
        key="tree_parent_select"
    )
    new_node_category = st.selectbox(
        "Catégorie du nœud",
        options=list(CATEGORIES.keys()),
        index=0,
        key="tree_new_category",
        help="ORGANISATIONNELLE (bleu), HUMAINE (orange), TECHNIQUE (gris)"
    )
    if st.button("Ajouter", key="tree_add_btn"):
        if new_node_label.strip():
            new_node_id = f"node_{len(st.session_state.nodes)}"
            st.session_state.nodes[new_node_id] = {
                "label": new_node_label.strip(),
                "category": new_node_category,
            }
            st.session_state.edges.append((parent_id, new_node_id))
            st.success(f"Nœud '{new_node_label}' ajouté sous '{st.session_state.nodes[parent_id]['label']}'.")
        else:
            st.warning("Veuillez entrer un nom de nœud valide.")

    # Edition
    st.subheader("Modifier un nœud existant")
    if len(st.session_state.nodes) > 0:
        node_to_edit = st.selectbox(
            "Choisir le nœud à modifier",
            options=list(st.session_state.nodes.keys()),
            format_func=lambda x: st.session_state.nodes[x]["label"],
            key="tree_edit_node_select"
        )
        cur_label = st.session_state.nodes[node_to_edit]["label"]
        cur_cat = st.session_state.nodes[node_to_edit].get("category")
        cur_parent = get_parent(node_to_edit)

        edit_label = st.text_input("Nouveau libellé", value=cur_label, key="tree_edit_label")
        all_cats = list(CATEGORIES.keys())
        default_idx = all_cats.index(cur_cat) if cur_cat in all_cats else 0
        edit_cat = st.selectbox("Nouvelle catégorie", options=all_cats, index=default_idx, key="tree_edit_category")

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
                key="tree_edit_parent_select"
            ) if parents_candidates else None

        if st.button("Mettre à jour", key="tree_update_btn"):
            st.session_state.nodes[node_to_edit]["label"] = edit_label.strip() or cur_label
            st.session_state.nodes[node_to_edit]["category"] = edit_cat
            if node_to_edit != "root" and edit_parent is not None and edit_parent != cur_parent:
                st.session_state.edges = [
                    (src, tgt) for src, tgt in st.session_state.edges
                    if not (src == cur_parent and tgt == node_to_edit)
                ]
                st.session_state.edges.append((edit_parent, node_to_edit))
            st.success("Nœud mis à jour.")

    # Visualisation
    st.subheader("Visualisation de l'arbre")
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

    # Export Word
    st.subheader("Exporter")
    if st.button("Exporter en Word (.docx)", key="tree_export_btn"):
        doc = export_tree_to_docx(st.session_state.nodes, st.session_state.edges, st.session_state.root_label)
        if doc is not None:
            tmp_path = "arbre_des_causes.docx"
            doc.save(tmp_path)
            with open(tmp_path, "rb") as f:
                st.download_button("Télécharger le document", f, file_name="arbre_des_causes.docx")

# ===================
# Page: 5 Pourquoi
# ===================
elif page == "Méthode des 5 Pourquoi":
    st.title("Méthode des 5 Pourquoi")
    st.caption("Conseils : viser 5 pourquoi.")

    # 1) Décrire le problème
    st.subheader("1) Décrire le problème")
    st.session_state.fivewhy_problem = st.text_area("Problème observé", value=st.session_state.fivewhy_problem, key="fw_problem")

    # 2) Poser successivement 'Pourquoi ?'
    st.subheader("2) Poser successivement 'Pourquoi ?'")
    # Render existing why inputs
    for i in range(len(st.session_state.fivewhy_answers)):
        st.text_input(
            f"Réponse au Pourquoi n°{i+1}",
            value=st.session_state.fivewhy_answers[i],
            key=f"fw_ans_{i}",
            on_change=None
        )

    cols = st.columns(3)
    if cols[0].button("➕ Ajouter un 'Pourquoi'"):
        st.session_state.fivewhy_answers.append("")
        # Rerun using new API (experimental_rerun is removed)
        try:
            st.rerun()
        except Exception:
            pass

    if cols[1].button("➖ Retirer le dernier"):
        if st.session_state.fivewhy_answers:
            st.session_state.fivewhy_answers.pop()
            try:
                st.rerun()
            except Exception:
                pass

    if cols[2].button("🔁 Réinitialiser"):
        st.session_state.fivewhy_problem = ""
        st.session_state.fivewhy_answers = []
        try:
            st.rerun()
        except Exception:
            pass

    # Sync edited inputs back to session state
    for i in range(len(st.session_state.fivewhy_answers)):
        st.session_state.fivewhy_answers[i] = st.session_state.get(f"fw_ans_{i}", "")

    # 3) Récapitulatif vertical (problème + pourquoi 1..n)
    st.subheader("Récapitulatif (du haut vers le bas)")
    if st.session_state.fivewhy_problem or any(st.session_state.fivewhy_answers):
        st.markdown(f"**Problème :** {st.session_state.fivewhy_problem or '(non renseigné)'}")
        for i, ans in enumerate(st.session_state.fivewhy_answers, start=1):
            st.markdown(f"**{i}. Pourquoi ?** — {ans or '(vide)'}")
    else:
        st.info("Saisissez le problème et ajoutez des 'Pourquoi ?' pour voir le récapitulatif.")

    # Export Word
    st.subheader("Exporter")
    if st.button("Exporter en Word (.docx)", key="fw_export_btn"):
        doc = export_fivewhy_to_docx(st.session_state.fivewhy_problem, st.session_state.fivewhy_answers)
        if doc is not None:
            tmp_path = "5_pourquoi.docx"
            doc.save(tmp_path)
            with open(tmp_path, "rb") as f:
                st.download_button("Télécharger le document", f, file_name="5_pourquoi.docx")
