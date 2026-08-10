import json
from pathlib import Path

import streamlit as st


# =========================================================
# LOAD DATA
# =========================================================

def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


knowledge_graph = load_json(
    "data/knowledge_graph.json",
    {},
)

evidence_db = load_json(
    "data/evidence_database.json",
    [],
)


# =========================================================
# HELPERS
# =========================================================

def get_nodes():
    if isinstance(
        knowledge_graph,
        dict,
    ):

        nodes = knowledge_graph.get(
            "nodes",
            [],
        )

        if isinstance(nodes, list):
            return nodes

    return []


def get_edges():
    if isinstance(
        knowledge_graph,
        dict,
    ):

        edges = knowledge_graph.get(
            "edges",
            [],
        )

        if isinstance(edges, list):
            return edges

    return []


def get_node_label(node):
    if not isinstance(
        node,
        dict,
    ):
        return str(node)

    return (
        node.get("label")
        or node.get("name")
        or node.get("id")
        or "Unnamed node"
    )


def get_node_type(node):
    if not isinstance(
        node,
        dict,
    ):
        return "Unknown"

    return (
        node.get("type")
        or node.get("category")
        or "Unknown"
    )


def get_edge_source(edge):
    if not isinstance(
        edge,
        dict,
    ):
        return ""

    return (
        edge.get("source")
        or edge.get("from")
        or ""
    )


def get_edge_target(edge):
    if not isinstance(
        edge,
        dict,
    ):
        return ""

    return (
        edge.get("target")
        or edge.get("to")
        or ""
    )


def get_edge_relation(edge):
    if not isinstance(
        edge,
        dict,
    ):
        return "related to"

    return (
        edge.get("relation")
        or edge.get("type")
        or edge.get("label")
        or "related to"
    )


def build_node_lookup(nodes):
    lookup = {}

    for node in nodes:

        if not isinstance(
            node,
            dict,
        ):
            continue

        node_id = (
            node.get("id")
            or node.get("name")
            or node.get("label")
        )

        if node_id:
            lookup[
                str(node_id)
            ] = node

    return lookup


def count_clinical_areas():
    areas = set()

    for record in evidence_db:

        if not isinstance(
            record,
            dict,
        ):
            continue

        translation = record.get(
            "clinical_translation",
            {},
        )

        if not isinstance(
            translation,
            dict,
        ):
            continue

        area = translation.get(
            "clinical_area",
            "",
        )

        if (
            isinstance(area, str)
            and area.strip()
        ):
            areas.add(
                area.strip()
            )

    return len(
        areas
    )


# =========================================================
# DATA
# =========================================================

nodes = get_nodes()
edges = get_edges()

node_lookup = build_node_lookup(
    nodes
)


# =========================================================
# HEADER
# =========================================================

st.caption(
    "RESEARCH RELATIONSHIPS"
)

st.title(
    "Knowledge Graph"
)

st.write(
    "Explore how clinical problems, interventions, mechanisms, "
    "outcomes, and research concepts connect across the evidence base."
)

st.write("")


# =========================================================
# SUMMARY METRICS
# =========================================================

node_types = {}

for node in nodes:

    node_type = get_node_type(
        node
    )

    node_types[
        node_type
    ] = (
        node_types.get(
            node_type,
            0,
        )
        + 1
    )


m1, m2, m3, m4 = st.columns(
    4,
    gap="medium",
)

with m1:

    st.metric(
        "Knowledge Nodes",
        len(nodes),
        border=True,
    )


with m2:

    st.metric(
        "Relationships",
        len(edges),
        border=True,
    )


with m3:

    st.metric(
        "Node Types",
        len(
            node_types
        ),
        border=True,
    )


with m4:

    st.metric(
        "Clinical Areas",
        count_clinical_areas(),
        border=True,
    )


st.write("")


# =========================================================
# EMPTY STATE
# =========================================================

if not nodes and not edges:

    st.info(
        "No knowledge graph data is currently available. "
        "Run the knowledge-graph stage of your research pipeline "
        "to populate this page."
    )

    st.stop()


# =========================================================
# SEARCH + FILTER
# =========================================================

search_col, type_col = st.columns(
    [3, 1],
    gap="medium",
)

with search_col:

    search = st.text_input(
        "Search graph",
        placeholder=(
            "Search a condition, intervention, mechanism, "
            "outcome, or concept..."
        ),
        label_visibility="collapsed",
    )


type_options = sorted(
    node_types.keys()
)

with type_col:

    selected_type = st.selectbox(
        "Node type",
        [
            "All Types",
            *type_options,
        ],
        label_visibility="collapsed",
    )


# =========================================================
# FILTER NODES
# =========================================================

filtered_nodes = []

for node in nodes:

    label = get_node_label(
        node
    )

    node_type = get_node_type(
        node
    )

    if search:

        query = search.lower().strip()

        searchable = (
            f"{label} {node_type}"
        ).lower()

        if query not in searchable:
            continue

    if (
        selected_type
        != "All Types"
        and node_type
        != selected_type
    ):
        continue

    filtered_nodes.append(
        node
    )


# =========================================================
# NODE TYPE OVERVIEW
# =========================================================

st.subheader(
    "Graph Overview"
)

if node_types:

    type_items = sorted(
        node_types.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    type_cols = st.columns(
        min(
            4,
            len(type_items),
        ),
        gap="medium",
    )

    for col, (
        node_type,
        count,
    ) in zip(
        type_cols,
        type_items[:4],
    ):

        with col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    f"**{node_type}**"
                )

                st.metric(
                    "Nodes",
                    count,
                )


st.write("")


# =========================================================
# MOST CONNECTED NODES
# =========================================================

st.subheader(
    "Most Connected Concepts"
)

connection_counts = {}

for edge in edges:

    source = str(
        get_edge_source(
            edge
        )
    )

    target = str(
        get_edge_target(
            edge
        )
    )

    if source:
        connection_counts[
            source
        ] = (
            connection_counts.get(
                source,
                0,
            )
            + 1
        )

    if target:
        connection_counts[
            target
        ] = (
            connection_counts.get(
                target,
                0,
            )
            + 1
        )


most_connected = sorted(
    connection_counts.items(),
    key=lambda item: item[1],
    reverse=True,
)[:8]


if most_connected:

    connected_cols = st.columns(
        4,
        gap="medium",
    )

    for index, (
        node_id,
        count,
    ) in enumerate(
        most_connected
    ):

        col = connected_cols[
            index % 4
        ]

        node = node_lookup.get(
            node_id,
            {},
        )

        label = (
            get_node_label(
                node
            )
            if node
            else node_id
        )

        node_type = (
            get_node_type(
                node
            )
            if node
            else "Unknown"
        )

        with col:

            with st.container(
                border=True,
            ):

                st.markdown(
                    f"**{label}**"
                )

                st.caption(
                    node_type
                )

                st.metric(
                    "Connections",
                    count,
                )

else:

    st.caption(
        "Connection counts are not available yet."
    )


st.write("")


# =========================================================
# NODE EXPLORER
# =========================================================

st.subheader(
    "Node Explorer"
)

st.caption(
    f"{len(filtered_nodes)} nodes shown"
)


for node in filtered_nodes[:30]:

    label = get_node_label(
        node
    )

    node_type = get_node_type(
        node
    )

    node_id = (
        node.get("id")
        if isinstance(
            node,
            dict,
        )
        else None
    )

    with st.expander(
        f"{label} • {node_type}"
    ):

        if isinstance(
            node,
            dict,
        ):

            description = (
                node.get(
                    "description"
                )
                or node.get(
                    "summary"
                )
                or ""
            )

            if description:

                st.write(
                    description
                )

        connected_edges = []

        for edge in edges:

            source = str(
                get_edge_source(
                    edge
                )
            )

            target = str(
                get_edge_target(
                    edge
                )
            )

            possible_ids = {
                str(node_id),
                str(label),
            }

            if (
                source in possible_ids
                or target in possible_ids
            ):
                connected_edges.append(
                    edge
                )

        st.metric(
            "Connections",
            len(
                connected_edges
            ),
        )

        if connected_edges:

            st.markdown(
                "**Relationships**"
            )

            for edge in (
                connected_edges[:15]
            ):

                source_id = str(
                    get_edge_source(
                        edge
                    )
                )

                target_id = str(
                    get_edge_target(
                        edge
                    )
                )

                relation = (
                    get_edge_relation(
                        edge
                    )
                )

                source_node = (
                    node_lookup.get(
                        source_id,
                        {},
                    )
                )

                target_node = (
                    node_lookup.get(
                        target_id,
                        {},
                    )
                )

                source_label = (
                    get_node_label(
                        source_node
                    )
                    if source_node
                    else source_id
                )

                target_label = (
                    get_node_label(
                        target_node
                    )
                    if target_node
                    else target_id
                )

                st.write(
                    f"• {source_label} → "
                    f"{relation} → {target_label}"
                )

        else:

            st.caption(
                "No relationships found for this node."
            )


st.write("")


# =========================================================
# RELATIONSHIP EXPLORER
# =========================================================

st.subheader(
    "Relationship Explorer"
)

relation_filter_options = sorted(
    {
        get_edge_relation(
            edge
        )
        for edge in edges
    }
)

selected_relation = st.selectbox(
    "Relationship type",
    [
        "All Relationships",
        *relation_filter_options,
    ],
)


shown_edges = 0

for edge in edges:

    relation = (
        get_edge_relation(
            edge
        )
    )

    if (
        selected_relation
        != "All Relationships"
        and relation
        != selected_relation
    ):
        continue

    source_id = str(
        get_edge_source(
            edge
        )
    )

    target_id = str(
        get_edge_target(
            edge
        )
    )

    source_node = (
        node_lookup.get(
            source_id,
            {},
        )
    )

    target_node = (
        node_lookup.get(
            target_id,
            {},
        )
    )

    source_label = (
        get_node_label(
            source_node
        )
        if source_node
        else source_id
    )

    target_label = (
        get_node_label(
            target_node
        )
        if target_node
        else target_id
    )

    with st.container(
        border=True,
    ):

        st.markdown(
            f"**{source_label}**"
        )

        st.caption(
            relation
        )

        st.write(
            f"→ {target_label}"
        )

    shown_edges += 1

    if shown_edges >= 25:
        break


if shown_edges == 0:

    st.info(
        "No relationships match the current filter."
    )
