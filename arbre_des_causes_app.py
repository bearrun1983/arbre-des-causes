{
    "chunks": [
        {
            "type": "txt",
            "chunk_number": 1,
            "lines": [
                {
                    "line_number": 1,
                    "text": ""
                },
                {
                    "line_number": 2,
                    "text": "import streamlit as st"
                },
                {
                    "line_number": 3,
                    "text": "import graphviz"
                },
                {
                    "line_number": 4,
                    "text": ""
                },
                {
                    "line_number": 5,
                    "text": "# Initialisation des \u00e9tats de session"
                },
                {
                    "line_number": 6,
                    "text": "if \"nodes\" not in st.session_state:"
                },
                {
                    "line_number": 7,
                    "text": "st.session_state.nodes = {\"root\": {\"label\": \"Racine\"}}"
                },
                {
                    "line_number": 8,
                    "text": "if \"edges\" not in st.session_state:"
                },
                {
                    "line_number": 9,
                    "text": "st.session_state.edges = []"
                },
                {
                    "line_number": 10,
                    "text": ""
                },
                {
                    "line_number": 11,
                    "text": "st.title(\"Arbre des Causes Interactif\")"
                },
                {
                    "line_number": 12,
                    "text": ""
                },
                {
                    "line_number": 13,
                    "text": "# Section pour ajouter un n\u0153ud"
                },
                {
                    "line_number": 14,
                    "text": "st.header(\"Ajouter un n\u0153ud\")"
                },
                {
                    "line_number": 15,
                    "text": "new_node_label = st.text_input(\"Nom du nouveau n\u0153ud\")"
                },
                {
                    "line_number": 16,
                    "text": "parent_id = st.selectbox("
                },
                {
                    "line_number": 17,
                    "text": "\"S\u00e9lectionner le n\u0153ud parent\","
                },
                {
                    "line_number": 18,
                    "text": "options=list(st.session_state.nodes.keys()),"
                },
                {
                    "line_number": 19,
                    "text": "format_func=lambda x: st.session_state.nodes[x][\"label\"]"
                },
                {
                    "line_number": 20,
                    "text": ")"
                },
                {
                    "line_number": 21,
                    "text": ""
                },
                {
                    "line_number": 22,
                    "text": "if st.button(\"Ajouter\"):"
                },
                {
                    "line_number": 23,
                    "text": "new_node_id = f\"node_{len(st.session_state.nodes)}\""
                },
                {
                    "line_number": 24,
                    "text": "st.session_state.nodes[new_node_id] = {\"label\": new_node_label}"
                },
                {
                    "line_number": 25,
                    "text": "st.session_state.edges.append((parent_id, new_node_id))"
                },
                {
                    "line_number": 26,
                    "text": "st.success(f\"N\u0153ud '{new_node_label}' ajout\u00e9 sous '{st.session_state.nodes[parent_id]['label']}'\")"
                },
                {
                    "line_number": 27,
                    "text": ""
                },
                {
                    "line_number": 28,
                    "text": "# Section pour supprimer un n\u0153ud"
                },
                {
                    "line_number": 29,
                    "text": "st.header(\"Supprimer un n\u0153ud\")"
                },
                {
                    "line_number": 30,
                    "text": "if len(st.session_state.nodes) > 1:"
                },
                {
                    "line_number": 31,
                    "text": "node_to_delete = st.selectbox("
                },
                {
                    "line_number": 32,
                    "text": "\"S\u00e9lectionner le n\u0153ud \u00e0 supprimer\","
                },
                {
                    "line_number": 33,
                    "text": "options=[nid for nid in st.session_state.nodes if nid != \"root\"],"
                },
                {
                    "line_number": 34,
                    "text": "format_func=lambda x: st.session_state.nodes[x][\"label\"]"
                },
                {
                    "line_number": 35,
                    "text": ")"
                },
                {
                    "line_number": 36,
                    "text": "if st.button(\"Supprimer\"):"
                },
                {
                    "line_number": 37,
                    "text": "# Supprimer les ar\u00eates associ\u00e9es"
                },
                {
                    "line_number": 38,
                    "text": "st.session_state.edges = ["
                },
                {
                    "line_number": 39,
                    "text": "(src, tgt) for src, tgt in st.session_state.edges"
                },
                {
                    "line_number": 40,
                    "text": "if tgt != node_to_delete and src != node_to_delete"
                },
                {
                    "line_number": 41,
                    "text": "]"
                },
                {
                    "line_number": 42,
                    "text": "# Supprimer le n\u0153ud"
                },
                {
                    "line_number": 43,
                    "text": "deleted_label = st.session_state.nodes[node_to_delete][\"label\"]"
                },
                {
                    "line_number": 44,
                    "text": "del st.session_state.nodes[node_to_delete]"
                },
                {
                    "line_number": 45,
                    "text": "st.success(f\"N\u0153ud '{deleted_label}' supprim\u00e9\")"
                },
                {
                    "line_number": 46,
                    "text": ""
                },
                {
                    "line_number": 47,
                    "text": "# Affichage de l'arbre des causes"
                },
                {
                    "line_number": 48,
                    "text": "st.header(\"Visualisation de l'arbre\")"
                },
                {
                    "line_number": 49,
                    "text": "dot = graphviz.Digraph(\"Arbre des Causes\", format=\"png\")"
                },
                {
                    "line_number": 50,
                    "text": "dot.attr(rankdir=\"RL\")"
                },
                {
                    "line_number": 51,
                    "text": ""
                },
                {
                    "line_number": 52,
                    "text": "# Ajouter les n\u0153uds"
                },
                {
                    "line_number": 53,
                    "text": "for node_id, data in st.session_state.nodes.items():"
                },
                {
                    "line_number": 54,
                    "text": "dot.node(node_id, data[\"label\"])"
                },
                {
                    "line_number": 55,
                    "text": ""
                },
                {
                    "line_number": 56,
                    "text": "# Ajouter les ar\u00eates"
                },
                {
                    "line_number": 57,
                    "text": "for src, tgt in st.session_state.edges:"
                },
                {
                    "line_number": 58,
                    "text": "dot.edge(src, tgt)"
                },
                {
                    "line_number": 59,
                    "text": ""
                },
                {
                    "line_number": 60,
                    "text": "st.graphviz_chart(dot)"
                }
            ],
            "token_count": 240
        }
    ]
}