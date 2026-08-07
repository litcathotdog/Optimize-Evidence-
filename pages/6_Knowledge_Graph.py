import json
from collections import Counter, defaultdict
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Knowledge Graph",
    page_icon="🕸️",
    layout="wide",
)


# ---------------------------------------------------------
# Load CSS
# ---------------------------------------------------------

STYLE_PATH = Path("assets/style.css")

if STYLE_PATH.exists():
    with STYLE_PATH.open("r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------
# Load data
# ---------------------------------------------------------

def load_json(path, default):
    path = Path(path)

    if not path.exists():
        return default

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


graph = load_json(
    "data/knowledge_graph.json",
    {},
)

evidence_db = load_json(
    "data/evidence_database.json",
    [],
)


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def safe_dict(value):
    return value if isinstance(value, dict) else {}


def safe_list(value):
    return value if isinstance(value, list) else []


nodes = safe_list(
    graph.get("nodes")
)

edges = safe_list(
    graph.get("edges")
)

syntheses = safe_list(
    graph.get("evidence_synthesis")
)

graph_stats = safe_dict(
    graph.get("statistics")
)


# ---------------------------------------------------------
# Header
# ---------------------------------------------------------

st.markdown(
    """
    <div class="hero-eyebrow">
        EVIDENCE CONNECTIONS
    </div>

    <h1 class="hero-title">
        Explore the <span>knowledge graph</span>
    </h1>

    <p class="hero-subtitle">
        See how clinical problems connect to interventions, outcomes,
        specialties, study designs, tissues, and emerging evidence.
    </p>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------
# Overview metrics
# ---------------------------------------------------------

m1, m2, m3, m4 = st.columns(4)

m1.metric(
    "Graph Nodes",
    graph_stats.get(
        "total_nodes",
        len(nodes),
    ),
)

m2.metric(
    "Connections",
    graph_stats.get(
        "total_edges",
        len(edges),
    ),
)

m3.metric(
    "Evidence Concepts",
    len(syntheses),
)

m4.metric(
    "Indexed Papers",
    len(evidence_db),
)


# ---------------------------------------------------------
# Concept explorer
# ---------------------------------------------------------

st.markdown(
    "## Explore a Concept"
)

concept_nodes = [
    node
    for node in nodes
    if isinstance(node, dict)
    and node.get("type")
    not in {
        "paper",
        "journal",
    }
]


concept_nodes.sort(
    key=lambda node: (
        str(
            node.get(
                "type",
                "",
            )
        ),
        str(
            node.get(
                "label",
                "",
            )
        ),
    )
)


concept_options = {
    (
        f"{node.get('label', 'Unknown')} "
        f"— {str(node.get('type', '')).replace('_', ' ').title()}"
    ): node
    for node in concept_nodes
}


selected_label = st.selectbox(
    "Choose a concept",
    [
        "Select a concept...",
        *concept_options.keys(),
    ],
)


if selected_label != "Select a concept...":

    selected_node = concept_options[
        selected_label
    ]

    selected_id = selected_node.get(
        "id"
    )

    selected_type = selected_node.get(
        "type",
        "",
    )

    selected_name = selected_node.get(
        "label",
        "",
    )

    st.markdown(
        f"### {selected_name}"
    )

    st.caption(
        str(
            selected_type
        ).replace(
            "_",
            " ",
        ).title()
    )


    # -----------------------------------------------------
    # Connected papers and concepts
    # -----------------------------------------------------

    connected_papers = []
    connected_concepts = []

    for edge in edges:

        if not isinstance(
            edge,
            dict,
        ):
            continue

        source = edge.get(
            "source"
        )

        target = edge.get(
            "target"
        )

        relationship = edge.get(
            "relationship",
            "",
        )

        if target == selected_id:

            source_node = next(
                (
                    node
                    for node in nodes
                    if isinstance(
                        node,
                        dict,
                    )
                    and node.get(
                        "id"
                    )
                    == source
                ),
                None,
            )

            if source_node:

                if source_node.get(
                    "type"
                ) == "paper":
                    connected_papers.append(
                        {
                            "relationship": relationship,
                            "node": source_node,
                        }
                    )

                else:
                    connected_concepts.append(
                        {
                            "relationship": relationship,
                            "node": source_node,
                        }
                    )


        elif source == selected_id:

            target_node = next(
                (
                    node
                    for node in nodes
                    if isinstance(
                        node,
                        dict,
                    )
                    and node.get(
                        "id"
                    )
                    == target
                ),
                None,
            )

            if target_node:

                if target_node.get(
                    "type"
                ) == "paper":
                    connected_papers.append(
                        {
                            "relationship": relationship,
                            "node": target_node,
                        }
                    )

                else:
                    connected_concepts.append(
                        {
                            "relationship": relationship,
                            "node": target_node,
                        }
                    )


    # -----------------------------------------------------
    # Metrics
    # -----------------------------------------------------

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Connected Papers",
        len(
            connected_papers
        ),
    )

    c2.metric(
        "Connected Concepts",
        len(
            connected_concepts
        ),
    )

    matching_synthesis = next(
        (
            synthesis
            for synthesis in syntheses
            if isinstance(
                synthesis,
                dict,
            )
            and synthesis.get(
                "concept_id"
            )
            == selected_id
        ),
        None,
    )

    if matching_synthesis:

        c3.metric(
            "Avg Evidence",
            matching_synthesis.get(
                "average_evidence_score",
                "—",
            ),
        )

    else:

        c3.metric(
            "Avg Evidence",
            "—",
        )


    # -----------------------------------------------------
    # Evidence direction
    # -----------------------------------------------------

    if matching_synthesis:

        st.markdown(
            "### Evidence Direction"
        )

        directions = safe_dict(
            matching_synthesis.get(
                "result_direction"
            )
        )

        d1, d2, d3, d4 = st.columns(4)

        d1.metric(
            "Favorable",
            directions.get(
                "favorable",
                0,
            ),
        )

        d2.metric(
            "Neutral",
            directions.get(
                "neutral",
                0,
            ),
        )

        d3.metric(
            "Unfavorable",
            directions.get(
                "unfavorable",
                0,
            ),
        )

        d4.metric(
            "Unclear",
            directions.get(
                "unclear",
                0,
            ),
        )


    # -----------------------------------------------------
    # Related concepts
    # -----------------------------------------------------

    st.markdown(
        "### Related Concepts"
    )

    if connected_concepts:

        relationship_groups = defaultdict(
            list
        )

        for item in connected_concepts:

            relationship = str(
                item.get(
                    "relationship",
                    "",
                )
            ).replace(
                "_",
                " ",
            ).title()

            node = safe_dict(
                item.get("node")
            )

            label = node.get(
                "label",
                "",
            )

            if label:
                relationship_groups[
                    relationship
                ].append(
                    label
                )


        for (
            relationship,
            labels,
        ) in relationship_groups.items():

            with st.expander(
                relationship
            ):

                for label in sorted(
                    set(labels)
                ):
                    st.write(
                        f"• {label}"
                    )

    else:

        st.info(
            "No related concepts are currently connected."
        )


    # -----------------------------------------------------
    # Connected papers
    # -----------------------------------------------------

    st.markdown(
        "### Connected Papers"
    )

    if connected_papers:

        connected_papers.sort(
            key=lambda item: (
                safe_dict(
                    item.get(
                        "node"
                    )
                ).get(
                    "evidence_score",
                    0,
                )
            ),
            reverse=True,
        )


        for item in connected_papers[:20]:

            paper = safe_dict(
                item.get(
                    "node"
                )
            )

            relationship = str(
                item.get(
                    "relationship",
                    "",
                )
            ).replace(
                "_",
                " ",
            ).title()

            title = paper.get(
                "label",
                "Untitled paper",
            )

            with st.expander(
                title
            ):

                st.caption(
                    relationship
                )

                p1, p2, p3 = st.columns(
                    3
                )

                p1.metric(
                    "Evidence",
                    paper.get(
                        "evidence_score",
                        0,
                    ),
                )

                p2.metric(
                    "Statistics",
                    paper.get(
                        "statistics_score",
                        0,
                    ),
                )

                p3.metric(
                    "Relevance",
                    paper.get(
                        "practitioner_relevance",
                        0,
                    ),
                )

                st.write(
                    f"**Direction:** "
                    f"{paper.get('result_direction', 'Unknown')}"
                )

                st.write(
                    f"**Practice readiness:** "
                    f"{paper.get('practice_readiness', 'Unknown')}"
                )

    else:

        st.info(
            "No connected papers found for this concept."
        )


# ---------------------------------------------------------
# Most connected concepts
# ---------------------------------------------------------

st.markdown(
    "## Most Connected Concepts"
)

connection_counts = Counter()

for edge in edges:

    if not isinstance(
        edge,
        dict,
    ):
        continue

    connection_counts[
        edge.get(
            "target"
        )
    ] += 1

    connection_counts[
        edge.get(
            "source"
        )
    ] += 1


ranked_concepts = []

for node in concept_nodes:

    node_id = node.get(
        "id"
    )

    ranked_concepts.append(
        (
            node.get(
                "label",
                "Unknown",
            ),
            node.get(
                "type",
                "",
            ),
            connection_counts.get(
                node_id,
                0,
            ),
        )
    )


ranked_concepts.sort(
    key=lambda item: item[2],
    reverse=True,
)


if ranked_concepts:

    cols = st.columns(4)

    for col, (
        label,
        node_type,
        count,
    ) in zip(
        cols,
        ranked_concepts[:4],
    ):

        with col:

            st.markdown(
                f"""
                <div class="knowledge-concept-card">

                    <div class="knowledge-concept-type">
                        {str(node_type).replace("_", " ").upper()}
                    </div>

                    <div class="knowledge-concept-title">
                        {label}
                    </div>

                    <div class="knowledge-concept-count">
                        {count} connections
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )


# ---------------------------------------------------------
# Evidence synthesis explorer
# ---------------------------------------------------------

st.markdown(
    "## Evidence Synthesis"
)

synthesis_type_options = sorted(
    {
        str(
            item.get(
                "concept_type",
                "",
            )
        )
        for item in syntheses
        if isinstance(
            item,
            dict,
        )
        and item.get(
            "concept_type"
        )
    }
)


selected_type = st.selectbox(
    "Concept type",
    [
        "All",
        *[
            option.replace(
                "_",
                " ",
            ).title()
            for option
            in synthesis_type_options
        ],
    ],
)


filtered_syntheses = []

for synthesis in syntheses:

    if not isinstance(
        synthesis,
        dict,
    ):
        continue

    concept_type = str(
        synthesis.get(
            "concept_type",
            "",
        )
    )

    if (
        selected_type != "All"
        and concept_type.replace(
            "_",
            " ",
        ).title()
        != selected_type
    ):
        continue

    filtered_syntheses.append(
        synthesis
    )


filtered_syntheses.sort(
    key=lambda item: (
        item.get(
            "paper_count",
            0,
        ),
        item.get(
            "average_evidence_score",
            0,
        )
        or 0,
    ),
    reverse=True,
)


for synthesis in filtered_syntheses[:20]:

    concept = synthesis.get(
        "concept",
        "Unknown",
    )

    with st.expander(
        concept
    ):

        c1, c2, c3, c4 = st.columns(
            4
        )

        c1.metric(
            "Papers",
            synthesis.get(
                "paper_count",
                0,
            ),
        )

        c2.metric(
            "Avg Evidence",
            synthesis.get(
                "average_evidence_score",
                "—",
            ),
        )

        c3.metric(
            "Avg Statistics",
            synthesis.get(
                "average_statistics_score",
                "—",
            ),
        )

        c4.metric(
            "Practice Informing",
            synthesis.get(
                "practice_informing_papers",
                0,
            ),
        )

        study_designs = safe_dict(
            synthesis.get(
                "study_designs"
            )
        )

        if study_designs:

            st.markdown(
                "**Study designs**"
            )

            for design, count in (
                study_designs.items()
            ):
                st.write(
                    f"• {design}: {count}"
                )


# ---------------------------------------------------------
# Graph architecture summary
# ---------------------------------------------------------

st.markdown(
    "## How the Evidence Connects"
)

st.markdown(
    """
    **Clinical Problem**
    → **Intervention**
    → **Outcome**
    → **Evidence Quality**
    → **Specialist Review**
    → **Practice Readiness**

    The knowledge graph is a structured map of these relationships.
    It is not a causal graph and does not imply that a connection proves
    effectiveness.
    """
)
