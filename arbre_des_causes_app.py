import streamlit as st
import graphviz
import uuid

# Initialize session state for nodes
if 'nodes' not in st.session_state:
    st.session_state.nodes = {'root': {'label': 'Problème', 'children': []}}

# Function to recursively draw the tree
def draw_tree(graph, node_id):
    node = st.session_state.nodes[node_id]
    for child_id in node['children']:
        child = st.session_state.nodes[child_id]
        graph.edge(node['label'], child['label'])
        draw_tree(graph, child_id)

# Title of the app
st.title("🌳 Arbre des Causes Interactif")

# Section to add a new cause
st.header("➕ Ajouter une cause")
with st.form("add_node_form"):
    parent_label = st.selectbox("Sélectionner le nœud parent", [st.session_state.nodes[n]['label'] for n in st.session_state.nodes])
    new_label = st.text_input("Nom de la nouvelle cause")
    submitted = st.form_submit_button("Ajouter")
    if submitted and new_label:
        # Find parent node ID
        parent_id = next(n for n in st.session_state.nodes if st.session_state.nodes[n]['label'] == parent_label)
        new_id = str(uuid.uuid4())
        st.session_state.nodes[new_id] = {'label': new_label, 'children': []}
        st.session_state.nodes[parent_id]['children'].append(new_id)
        st.success(f"Cause '{new_label}' ajoutée sous '{parent_label}'")

# Section to supprimer un nœud
st.header("❌ Supprimer une cause")
with st.form("delete_node_form"):
    deletable_labels = [st.session_state.nodes[n]['label'] for n in st.session_state.nodes if n != 'root']
    if deletable_labels:
        delete_label = st.selectbox("Sélectionner la cause à supprimer", deletable_labels)
        delete_submit = st.form_submit_button("Supprimer")
        if delete_submit:
            delete_id = next(n for n in st.session_state.nodes if st.session_state.nodes[n]['label'] == delete_label)
            # Remove from parent's children
            for node in st.session_state.nodes.values():
                if delete_id in node['children']:
                    node['children'].remove(delete_id)
            # Remove the node
            del st.session_state.nodes[delete_id]
            st.success(f"Cause '{delete_label}' supprimée")

# Section to display the tree
st.header("📌 Arbre des causes actuel")
dot = graphviz.Digraph()
draw_tree(dot, 'root')
st.graphviz_chart(dot)
