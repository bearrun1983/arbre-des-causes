# fichier: arbre_des_causes_app.py
import os
from io import BytesIO
from collections import defaultdict, deque

import streamlit as st
import graphviz
from docx import Document  # python-docx

# =============== CONSTANTES ===============
CATEGORIES = {
    "ORGANISATIONNELLE": {"color": "#5B9BD5", "desc": "Bleu soutenu"},
    "HUMAINE": {"color": "#ED7D31", "desc": "Orange soutenu"},
    "TECHNIQUE": {"color": "#A6A6A6", "desc": "Gris soutenu"},
}
RANKDIR = "RL"               # racine à droite -> causes à gauche
ARROW_MODE = "PARENT_TO_CHILD"  # flèches Parent -> Enfant

# =============== ETATS INITIAUX ===============
if "page" not in st.session_state:
    st.session_state.page = "Arbre des causes"

# Arbre des causes
if "nodes" not in st.session_state:
    st.session_state.nodes = {"root": {"label": "Racine", "category": None}}
if "edges" not in st.session_state:
    st.session_state.edges = []
if "root_label" not in st.session_state:
    st.session_state.root_label = "Racine"

# 5 Pourquoi (si tu veux garder la page)
if "why" not in st.session_state:
    st.session_state.why = []
if "why_problem" not in st.session_state:
    st.session_state.why_problem = ""

# Assistant IA (texte d’entrée + sortie textuelle, + sélection)
if "ai_doc_text" not in st.session_state:
    st.session_state.ai_doc_text = ""
if "ai_questions_text" not in st.session_state:
    st.session_state.ai_questions_text = ""
if "ai_detected_questions" not in st.session_state:
    st.session_state.ai_detected_questions = []  # liste des questions extraites du bloc texte

# =============== HELPERS GLOBAUX ===============
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
    """True si query_id est dans le sous-arbre de root_id (Parent->Enfant)."""
    children = build_children_map(st.session_state.edges)
    q = deque([root_id])
    while q:
        n = q.popleft()
        if n == query_id:
            return True
        q.extend(children.get(n, []))
    return False

def export_arbre_docx(title, nodes, edges) -> BytesIO:
    doc = Document()
    doc.add_heading(title or "Arbre des causes", 0)

    doc.add_heading("Catégories", level=1)
    for cat, info in CATEGORIES.items():
        doc.add_paragraph(f"- {cat} : {info['desc']}")

    doc.add_heading("Nœuds", level=1)
    for nid, data in nodes.items():
        label = data.get("label", "")
        cat = data.get("category") or "Non défini"
        doc.add_paragraph(f"- {label} ({cat})")

    doc.add_heading("Liens Parent → Enfant", level=1)
    for src, tgt in edges:
        doc.add_paragraph(f"{nodes[src]['label']} → {nodes[tgt]['label']}")

    buf = BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf

# -------- Extraction texte .docx (paragraphes + tableaux) --------
def extract_docx_text(file_bytes: BytesIO) -> str:
    doc = Document(file_bytes)
    parts = []
    for p in doc.paragraphs:
        if p.text and p.text.strip():
            parts.append(p.text.strip())
    # tableaux -> cellules concaténées par tabulation, lignes par saut de ligne
    for table in doc.tables:
        for row in table.rows:
            cells = [cell.text.strip() for cell in row.cells]
            if any(cells):
                parts.append("\t".join(c for c in cells if c))
    return "\n".join(parts).strip()

# -------- IA: OpenAI (questions profondes) ou heuristique locale --------
def ai_questions_only(text: str) -> str:
    """
    Renvoie un seul bloc de texte (markdown simple) à copier-coller,
    contenant des QUESTIONS d’enquête profondes, organisées par thèmes.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)

            system = (
                "Tu es un expert HSE. Tu vas proposer UNIQUEMENT des QUESTIONS d'enquête "
                "ouvertes, précises, actionnables, classées par thèmes. Réponds en texte clair."
            )
            user = f"""
Analyse le recueil d'effets ci-dessous (accident du travail). 
Produis un texte prêt à copier-coller (pas de JSON), avec des sections par thème et des puces.

Thèmes attendus (si pertinents) :
- Chronologie
- Organisation
- Humain
- Technique
- Environnement
- Barrières/Contrôles

Pour chaque question :
- Formulation ouverte et précise
- Si utile, ajoute entre parenthèses une piste de "preuves attendues" (documents/observations).

Recueil d'effets:
\"\"\"{text}\"\"\"
"""
            resp = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "system", "content": system},
                          {"role": "user", "content": user}],
                temperature=0.2,
            )
            content = resp.choices[0].message.content
            return content.strip()
        except Exception as e:
            st.warning(f"IA OpenAI indisponible ({e}). Passage en mode local.")
            return heuristic_questions_text(text)
    else:
        return heuristic_questions_text(text)

def heuristic_questions_text(text: str) -> str:
    """Fallback local: questions par thèmes (pas juste paraphrase)."""
    lower = text.lower()

    sections = []
    chrono = [
        "- Déroulez minute par minute l’heure qui a précédé l’événement (preuves: main courante, radios, badges).",
        "- Quels changements de plan ont eu lieu le jour J ? Par qui et pourquoi (preuves: briefing, ordres de travail) ?",
    ]
    orga = [
        "- Quelles procédures/consignations/permits étaient applicables et ont-elles été réellement suivies (preuves: permis, signatures) ?",
        "- La charge de travail et la supervision étaient-elles adaptées (preuves: planning, entretiens) ?",
    ]
    humain = [
        "- Quelles compétences/habilitations spécifiques avaient les intervenants (preuves: registres de formation) ?",
        "- Des signes de fatigue/stress/distraction ont-ils été observés (preuves: horaires, témoignages) ?",
    ]
    tech = [
        "- Quel était l’état réel des équipements (défauts connus, interlocks, maintenance) (preuves: GMAO, rapports d’essai) ?",
        "- Quels EPI/protections étaient requis et portés/en place (preuves: consignes, photos) ?",
    ]
    envt = [
        "- Conditions météo/visibilité/bruit/éclairage : quel impact (preuves: météo, mesures, photos) ?",
        "- D’autres activités à proximité ont-elles créé des interférences (preuves: planning global) ?",
    ]
    barri = [
        "- Quelles barrières (prévention/protection) étaient prévues ? Laquelle a échoué en premier (preuves: analyse risques) ?",
        "- Quels contrôles de dernière minute ont été réalisés (LOTO, point d’arrêt, check-lists) (preuves: documents signés) ?",
    ]

    if any(k in lower for k in ["autorout", "trafic", "balisage", "signalisation"]):
        envt.append("- Le balisage/ITPC était-il conforme (espacements, limites, visibilité) (preuves: plan balisage, photos) ?")
        orga.append("- Les communications radio avec PC trafic/astreinte ont-elles couvert les phases clés (preuves: logs radio) ?")

    sections.append(("Chronologie", chrono))
    sections.append(("Organisation", orga))
    sections.append(("Humain", humain))
    sections.append(("Technique", tech))
    sections.append(("Environnement", envt))
    sections.append(("Barrières/Contrôles", barri))

    out = []
    for title, qs in sections:
        out.append(f"### {title}")
        out.extend(qs)
        out.append("")
    return "\n".join(out).strip()

# -------- Parseur des questions (depuis le bloc texte IA) --------
def detect_questions_from_text(text: str):
    """
    Détecte les puces/questions dans un bloc texte IA.
    Règles: lignes commençant par -, *, • (avec ou sans espace), et/ou finissant par ?.
    Ignore les titres (### ...).
    """
    detected = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("###"):
            continue
        bullet = line.startswith(("-", "*", "•"))
        if bullet:
            line = line.lstrip("-*• ").strip()
        if bullet or line.endswith("?"):
            if len(line) >= 3:
                detected.append(line)
    # dédoublonnage simple
    uniq = []
    seen = set()
    for q in detected:
        k = q.lower()
        if k not in seen:
            seen.add(k)
            uniq.append(q)
    return uniq

# =============== NAVIGATION ===============
st.sidebar.title("Navigation")
page = st.sidebar.radio(
    "Aller vers :",
    ["Arbre des causes", "5 Pourquoi"],
    index=["Arbre des causes", "5 Pourquoi"].index(st.session_state.page)
)
st.session_state.page = page

# =============== PAGES ===============
if page == "Arbre des causes":
    st.title("Arbre des causes")

    # Mise en page compacte : deux colonnes
    col_left, col_right = st.columns([1, 2], gap="medium")

    with col_left:
        with st.expander("Nom de la racine", expanded=False):
            st.caption("Définis le libellé de la case ‘racine’.")
            st.session_state.root_label = st.text_input("Nom", value=st.session_state.root_label, label_visibility="collapsed")
            st.session_state.nodes["root"]["label"] = st.session_state.root_label

        with st.expander("Ajouter un nœud", expanded=False):
            st.caption("Ajoute une cause et rattache-la à un parent.")
            new_node_label = st.text_input("Libellé", key="add_label", label_visibility="collapsed")
            parent_id = st.selectbox(
                "Parent",
                options=list(st.session_state.nodes.keys()),
                format_func=lambda x: st.session_state.nodes[x]["label"],
                key="add_parent"
            )
            new_node_category = st.selectbox("Catégorie", options=list(CATEGORIES.keys()), index=0, key="add_cat")
            if st.button("Ajouter", key="add_btn"):
                if new_node_label.strip():
                    new_node_id = f"node_{len(st.session_state.nodes)}"
                    st.session_state.nodes[new_node_id] = {"label": new_node_label.strip(), "category": new_node_category}
                    st.session_state.edges.append((parent_id, new_node_id))
                    st.success("Nœud ajouté.")
                else:
                    st.warning("Libellé vide.")

        with st.expander("Modifier un nœud existant", expanded=False):
            node_to_edit = st.selectbox(
                "Nœud",
                options=list(st.session_state.nodes.keys()),
                format_func=lambda x: st.session_state.nodes[x]["label"],
                key="edit_select"
            )
            cur_label = st.session_state.nodes[node_to_edit]["label"]
            cur_cat = st.session_state.nodes[node_to_edit].get("category")
            cur_parent = get_parent(node_to_edit)
            edit_label = st.text_input("Nouveau libellé", value=cur_label, key="edit_label")
            edit_cat_index = list(CATEGORIES.keys()).index(cur_cat) if cur_cat in CATEGORIES else 0
            edit_cat = st.selectbox("Catégorie", options=list(CATEGORIES.keys()), index=edit_cat_index, key="edit_cat")

            # Parents possibles sans créer de cycle
            parents_candidates = [nid for nid in st.session_state.nodes.keys() if nid != node_to_edit]
            parents_candidates = [nid for nid in parents_candidates if not is_descendant(node_to_edit, nid)]

            if node_to_edit == "root":
                st.info("La racine ne peut pas être rattachée à un parent.")
                edit_parent = None
            else:
                default_parent_idx = parents_candidates.index(cur_parent) if cur_parent in parents_candidates else 0
                edit_parent = st.selectbox(
                    "Nouveau parent",
                    options=parents_candidates,
                    index=default_parent_idx if parents_candidates else 0,
                    format_func=lambda x: st.session_state.nodes[x]["label"],
                    key="edit_parent"
                ) if parents_candidates else None

            if st.button("Mettre à jour", key="edit_btn"):
                st.session_state.nodes[node_to_edit]["label"] = edit_label.strip() or cur_label
                st.session_state.nodes[node_to_edit]["category"] = edit_cat
                if node_to_edit != "root" and edit_parent is not None and edit_parent != cur_parent:
                    st.session_state.edges = [(s, t) for (s, t) in st.session_state.edges if not (s == cur_parent and t == node_to_edit)]
                    st.session_state.edges.append((edit_parent, node_to_edit))
                st.success("Nœud mis à jour.")
                st.rerun()

        with st.expander("Assistant IA (Recueil d’effets → Questions)", expanded=False):
            st.caption("Uploade un .docx **ou** colle ton texte. La sortie est un **bloc à copier-coller** ET une **liste à cocher** pour injecter directement des questions comme nœuds.")
            up = st.file_uploader("Importer un fichier Word (.docx)", type=["docx"])
            if up is not None:
                file_bytes = BytesIO(up.read())
                try:
                    st.session_state.ai_doc_text = extract_docx_text(file_bytes)
                    st.success("Texte extrait du .docx.")
                except Exception as e:
                    st.error(f"Impossible de lire le .docx : {e}")
                    st.session_state.ai_doc_text = ""

            st.session_state.ai_doc_text = st.text_area(
                "Ou coller le texte ici",
                value=st.session_state.ai_doc_text,
                height=160
            )

            col_q1, col_q2 = st.columns([1,1])
            with col_q1:
                if st.button("Générer les questions", key="ai_make_questions"):
                    st.session_state.ai_questions_text = ai_questions_only(st.session_state.ai_doc_text)
                    # détecter des questions individuelles pour la liste à cocher
                    st.session_state.ai_detected_questions = detect_questions_from_text(st.session_state.ai_questions_text)
                    st.success("Questions générées.")
            with col_q2:
                if st.button("Effacer la sortie IA", key="ai_clear"):
                    st.session_state.ai_questions_text = ""
                    st.session_state.ai_detected_questions = []

            if st.session_state.ai_questions_text:
                st.caption("Questions proposées (bloc à copier-coller) :")
                st.text_area(
                    "Questions",
                    value=st.session_state.ai_questions_text,
                    height=220,
                    label_visibility="collapsed"
                )

            if st.session_state.ai_detected_questions:
                st.divider()
                st.caption("Cocher des questions pour les ajouter comme nœuds dans l’Arbre :")
                selected_items = []
                for i, q in enumerate(st.session_state.ai_detected_questions):
                    # clef stable par contenu pour éviter persistance indésirable
                    key = f"aiq_{abs(hash(q)) % (10**9)}_{i}"
                    if st.checkbox(q, key=key):
                        selected_items.append(q)

                if selected_items:
                    inj_parent = st.selectbox(
                        "Parent pour les nouvelles questions",
                        options=list(st.session_state.nodes.keys()),
                        format_func=lambda x: st.session_state.nodes[x]["label"],
                        key="inj_parent_ai"
                    )
                    inj_cat = st.selectbox(
                        "Catégorie à appliquer",
                        options=list(CATEGORIES.keys()),
                        index=0,
                        key="inj_cat_ai"
                    )
                    if st.button("Ajouter les questions sélectionnées dans l’Arbre", key="inj_btn_ai"):
                        count = 0
                        for q in selected_items:
                            new_id = f"node_{len(st.session_state.nodes)}"
                            st.session_state.nodes[new_id] = {"label": q, "category": inj_cat}
                            st.session_state.edges.append((inj_parent, new_id))
                            count += 1
                        st.success(f"{count} question(s) ajoutée(s) comme nœud(s).")
                        # réinitialiser les cases cochées
                        for i, q in enumerate(st.session_state.ai_detected_questions):
                            k = f"aiq_{abs(hash(q)) % (10**9)}_{i}"
                            if k in st.session_state:
                                st.session_state[k] = False
                        st.rerun()

        with st.expander("Exporter", expanded=False):
            if st.button("Exporter l’arbre en Word (.docx)", key="export_arbre"):
                buf = export_arbre_docx(st.session_state.root_label, st.session_state.nodes, st.session_state.edges)
                st.download_button(
                    "Télécharger le fichier Word",
                    buf,
                    file_name="arbre_des_causes.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                )

    with col_right:
        st.subheader("Visualisation", anchor=False)
        dot = graphviz.Digraph("Arbre des Causes", format="png")
        dot.attr(rankdir=RANKDIR)
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
        st.graphviz_chart(dot, use_container_width=True)

elif page == "5 Pourquoi":
    st.title("5 Pourquoi")
    st.markdown("**Conseils : viser 5 pourquoi.**")

    st.session_state.why_problem = st.text_area("1) Décrire le problème", value=st.session_state.why_problem)
    st.subheader("2) Poser successivement 'Pourquoi ?'")

    col_a, col_b, col_c = st.columns([1,1,1])
    with col_a:
        if st.button("Ajouter un 'Pourquoi'"):
            st.session_state.why.append("")
    with col_b:
        if st.button("Retirer le dernier"):
            if st.session_state.why:
                st.session_state.why.pop()
    with col_c:
        if st.button("Réinitialiser"):
            st.session_state.why = []
            st.rerun()

    for i in range(len(st.session_state.why)):
        st.session_state.why[i] = st.text_input(f"Réponse au Pourquoi n°{i+1}", value=st.session_state.why[i], key=f"why_{i}")

    st.subheader("Récapitulatif")
    if st.session_state.why_problem:
        st.write(f"**Problème observé :** {st.session_state.why_problem}")
    for i, ans in enumerate(st.session_state.why, 1):
        if ans.strip():
            st.write(f"{i}. Pourquoi ? — {ans.strip()}")

    with st.expander("Exporter", expanded=False):
        if st.button("Exporter en Word (.docx)", key="export_why"):
            doc = Document()
            doc.add_heading("Analyse 5 Pourquoi", 0)
            if st.session_state.why_problem:
                doc.add_paragraph(f"Problème observé : {st.session_state.why_problem}")
            for i, ans in enumerate(st.session_state.why, 1):
                if ans.strip():
                    doc.add_paragraph(f"{i}. Pourquoi ? — {ans.strip()}")
            buf = BytesIO()
            doc.save(buf)
            buf.seek(0)
            st.download_button(
                "Télécharger le fichier Word",
                buf,
                file_name="analyse_5_pourquoi.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
