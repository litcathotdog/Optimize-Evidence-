import json
from pathlib import Path

import streamlit as st


# =========================================================
# App config
# =========================================================

st.set_page_config(
    page_title="Optimize Evidence",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)


# =========================================================
# Load CSS
# =========================================================

STYLE_PATH = Path("assets/style.css")

if STYLE_PATH.exists():
    with STYLE_PATH.open("r", encoding="utf-8") as file:
        st.markdown(
            f"<style>{file.read()}</style>",
            unsafe_allow_html=True,
        )


# =========================================================
# Helpers
# =========================================================

def load_json(path):
    path = Path(path)

    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def set_page(page_name):
    st.session_state.page = page_name
    st.rerun()


def set_problem(problem_name):
    st.session_state.selected_problem = problem_name
    st.session_state.page = "Problem Detail"
    st.rerun()


def set_specialist(name):
    st.session_state.selected_specialist = name
    st.session_state.page = "AI Specialists"
    st.rerun()


# =========================================================
# Session state
# =========================================================

if "page" not in st.session_state:
    st.session_state.page = "Home"

if "selected_problem" not in st.session_state:
    st.session_state.selected_problem = "Patellar Tendinopathy"

if "selected_specialist" not in st.session_state:
    st.session_state.selected_specialist = "Athena"


# =========================================================
# Load dashboard data
# =========================================================

dashboard = load_json("data/dashboard.json")
journal_club = load_json("data/journal_club.json")

overview = dashboard.get("overview", {})


# =========================================================
# Demo clinical problem data
# Replace later with generated JSON if desired
# =========================================================

clinical_problems = [
    {
        "name": "Patellar Tendinopathy",
        "short_name": "Patellar Tendinopathy",
        "icon": "🦵",
        "studies": 143,
        "strength": "VERY STRONG",
        "confidence": 91,
        "insight": "2 days ago",
        "tags": ["Treatment", "Rehab"],
        "summary": (
            "Progressive tendon loading remains central to rehabilitation. "
            "Recent evidence continues to evaluate load magnitude, contraction "
            "type, adjunct therapies, and return-to-sport progression."
        ),
    },
    {
        "name": "Hamstring Strain",
        "short_name": "Hamstring Strain",
        "icon": "🏃",
        "studies": 98,
        "strength": "STRONG",
        "confidence": 84,
        "insight": "3 days ago",
        "tags": ["Rehab", "Return to Sport"],
        "summary": (
            "Evidence supports progressive eccentric and high-speed running "
            "exposure, with increasing emphasis on individualized return-to-sport criteria."
        ),
    },
    {
        "name": "Stress Fractures",
        "short_name": "Stress Fractures",
        "icon": "🦴",
        "studies": 76,
        "strength": "STRONG",
        "confidence": 83,
        "insight": "5 days ago",
        "tags": ["Women's Health", "Bone"],
        "summary": (
            "Bone stress injury research increasingly integrates training load, "
            "nutrition, hormonal status, biomechanics, and bone health."
        ),
    },
    {
        "name": "Relative Energy Deficiency in Sport",
        "short_name": "RED-S",
        "icon": "♀",
        "studies": 64,
        "strength": "STRONG",
        "confidence": 82,
        "insight": "3 days ago",
        "tags": ["Women's Health", "Endocrine"],
        "summary": (
            "Current RED-S research focuses on low energy availability, endocrine "
            "adaptation, bone health, performance effects, screening, and recovery."
        ),
    },
    {
        "name": "Explosive Performance",
        "short_name": "Explosive Performance",
        "icon": "⚡",
        "studies": 224,
        "strength": "MODERATE",
        "confidence": 76,
        "insight": "1 day ago",
        "tags": ["Performance", "Power"],
        "summary": (
            "Explosive performance research spans sprint mechanics, force-velocity "
            "profiling, plyometrics, strength development, and power-oriented programming."
        ),
    },
]


# =========================================================
# AI specialists
# =========================================================

specialists = [
    {
        "name": "Atlas",
        "icon": "🌱",
        "specialty": "Regenerative Medicine",
        "description": "I evaluate biologics, healing, tissue regeneration, and emerging therapies.",
        "activity": "Reviewed 27 papers",
        "insight": "3 practice-changing findings",
    },
    {
        "name": "Vector",
        "icon": "⚡",
        "specialty": "Sports Performance",
        "description": "I analyze training, performance, adaptation, and recovery science.",
        "activity": "Reviewed 31 papers",
        "insight": "2 new performance insights",
    },
    {
        "name": "Newton",
        "icon": "⚙️",
        "specialty": "Biomechanics",
        "description": "I decode movement, forces, injury mechanisms, and mechanical relationships.",
        "activity": "Reviewed 22 papers",
        "insight": "Connected 53 new relationships",
    },
    {
        "name": "Athena",
        "icon": "♡",
        "specialty": "Women's Athlete Health",
        "description": "I focus on female athlete health, endocrine factors, RED-S, and bone health.",
        "activity": "Reviewed 19 papers",
        "insight": "4 evidence gaps flagged",
    },
    {
        "name": "Euler",
        "icon": "Σ",
        "specialty": "Statistical Review",
        "description": "I scrutinize study design, methods, uncertainty, and statistical conclusions.",
        "activity": "Reviewed 25 papers",
        "insight": "7 statistical concerns identified",
    },
    {
        "name": "Artemis",
        "icon": "📖",
        "specialty": "Journal Club",
        "description": "I curate important papers and facilitate evidence-based discussion.",
        "activity": "Curated 10 papers",
        "insight": "Discussion ready",
    },
]


# =========================================================
# Sidebar
# =========================================================

with st.sidebar:

    st.markdown(
        """
        <div class="sidebar-brand">
            <div class="brand-mark">🧠</div>
            <div>
                <div class="brand-title">OPTIMIZE</div>
                <div class="brand-title">EVIDENCE</div>
                <div class="brand-subtitle">
                    Better evidence.<br>
                    Better outcomes.
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    nav_items = [
        ("Home", "⌂"),
        ("Clinical Problems", "♧"),
        ("Evidence Library", "▣"),
        ("AI Specialists", "♧"),
        ("Journal Club", "▤"),
        ("Knowledge Graph", "⌘"),
        ("Evidence Gaps", "△"),
        ("Statistics Review", "▥"),
        ("Saved", "♡"),
        ("Settings", "⚙"),
    ]

    current_page = st.session_state.page

    if current_page == "Problem Detail":
        current_page = "Clinical Problems"

    for nav_name, icon in nav_items:

        selected = current_page == nav_name

        button_type = "primary" if selected else "secondary"

        if st.button(
            f"{icon}   {nav_name}",
            key=f"nav_{nav_name}",
            use_container_width=True,
            type=button_type,
        ):
            set_page(nav_name)

    st.markdown("<div class='sidebar-spacer'></div>", unsafe_allow_html=True)

    st.markdown(
        """
        <div class="athena-sidebar-card">
            <div class="athena-orb">✦</div>
            <div class="athena-sidebar-title">Ask Athena</div>
            <div class="athena-sidebar-copy">
                Ask a question or get evidence-based insights.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button(
        "Chat with Athena  →",
        use_container_width=True,
        key="sidebar_athena",
    ):
        set_specialist("Athena")


# =========================================================
# Shared top header
# =========================================================

def render_header(title=None, subtitle=None, home=False):

    top_left, top_right = st.columns([1.45, 1])

    with top_left:

        if home:
            st.markdown(
                """
                <div class="greeting">
                    Good morning, Catherine! 👋
                </div>

                <div class="hero-title">
                    What <span>problems</span> are we solving today?
                </div>

                <div class="hero-subtitle">
                    AI specialists continuously review, critique, and synthesize
                    evidence so you can make better clinical decisions.
                </div>
                """,
                unsafe_allow_html=True,
            )

        else:
            st.markdown(
                f"""
                <div class="page-title">{title}</div>
                <div class="page-subtitle">{subtitle or ""}</div>
                """,
                unsafe_allow_html=True,
            )

    with top_right:

        search = st.text_input(
            "Search",
            placeholder="Search problems, interventions, papers...",
            label_visibility="collapsed",
            key=f"search_{st.session_state.page}",
        )

        controls_1, controls_2 = st.columns(2)

        with controls_1:
            st.button("📅  Aug 8, 2026", use_container_width=True)

        with controls_2:
            st.button("This Week  ⌄", use_container_width=True)

    return search


# =========================================================
# HOME PAGE
# =========================================================

if st.session_state.page == "Home":

    render_header(home=True)

    st.markdown("<div class='vertical-gap-small'></div>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # KPI panel
    # -----------------------------------------------------

    kpi_data = [
        {
            "icon": "▧",
            "value": overview.get("total_papers", 156),
            "label": "New Papers",
            "change": "↑ 22% vs last week",
            "class": "teal",
        },
        {
            "icon": "☆",
            "value": overview.get("practice_informing_papers", 38),
            "label": "Practice-Informing Papers",
            "change": "↑ 18%",
            "class": "gold",
        },
        {
            "icon": "◎",
            "value": 74,
            "label": "Clinical Problems Covered",
            "change": "↑ 11%",
            "class": "purple",
        },
        {
            "icon": "△",
            "value": 11,
            "label": "Evidence Gaps",
            "change": "↑ 10%",
            "class": "pink",
        },
        {
            "icon": "〽",
            "value": "91%",
            "label": "Avg. Evidence Confidence",
            "change": "↑ 5%",
            "class": "blue",
        },
    ]

    st.markdown("<div class='kpi-shell'>", unsafe_allow_html=True)

    kpi_cols = st.columns(5)

    for col, item in zip(kpi_cols, kpi_data):

        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-icon {item['class']}">
                        {item['icon']}
                    </div>

                    <div>
                        <div class="kpi-value">{item['value']}</div>
                        <div class="kpi-label">{item['label']}</div>
                        <div class="kpi-change">{item['change']}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)

    # -----------------------------------------------------
    # Main dashboard split
    # -----------------------------------------------------

    main_col, right_col = st.columns([3.2, 1])

    with main_col:

        # =================================================
        # Clinical problems
        # =================================================

        section_left, section_right = st.columns([5, 1])

        with section_left:
            st.markdown(
                "<div class='section-title'>Top Clinical Problems</div>",
                unsafe_allow_html=True,
            )

        with section_right:
            if st.button(
                "View All Problems  →",
                key="view_all_problems",
                use_container_width=True,
            ):
                set_page("Clinical Problems")

        problem_cols = st.columns(5)

        for col, problem in zip(problem_cols, clinical_problems):

            with col:

                st.markdown(
                    f"""
                    <div class="problem-card">
                        <div class="problem-top">
                            <div class="problem-icon">{problem['icon']}</div>
                            <div class="problem-name">
                                {problem['short_name']}
                            </div>
                        </div>

                        <div class="problem-meta">
                            {problem['studies']} studies
                        </div>

                        <div class="strength-pill">
                            {problem['strength']}
                        </div>

                        <div class="confidence-row">
                            ★★★★☆ <span>({problem['confidence']}%)</span>
                        </div>

                        <div class="problem-meta small">
                            Newest insight
                        </div>

                        <div class="problem-insight">
                            {problem['insight']}
                        </div>

                        <div class="tag-row">
                            {" ".join(
                                [f"<span class='tag'>{tag}</span>"
                                 for tag in problem['tags']]
                            )}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Open problem →",
                    key=f"open_{problem['name']}",
                    use_container_width=True,
                ):
                    set_problem(problem["name"])

        st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

        # =================================================
        # AI specialists strip
        # =================================================

        specialist_title_col, specialist_link_col = st.columns([5, 1])

        with specialist_title_col:
            st.markdown(
                "<div class='section-title'>Your AI Specialists</div>",
                unsafe_allow_html=True,
            )

        with specialist_link_col:
            if st.button(
                "Meet the team  →",
                key="meet_team",
                use_container_width=True,
            ):
                set_page("AI Specialists")

        specialist_cols = st.columns(6)

        for col, specialist in zip(specialist_cols, specialists):

            with col:

                st.markdown(
                    f"""
                    <div class="specialist-mini-card">
                        <div class="specialist-avatar">
                            {specialist['icon']}
                        </div>

                        <div class="specialist-mini-name">
                            {specialist['name']}
                        </div>

                        <div class="specialist-mini-role">
                            {specialist['specialty']}
                        </div>

                        <div class="specialist-mini-copy">
                            {specialist['description']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "Open",
                    key=f"specialist_home_{specialist['name']}",
                    use_container_width=True,
                ):
                    set_specialist(specialist["name"])

        st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

        # =================================================
        # Bottom row
        # =================================================

        chart_col, paper_col, trend_col = st.columns([1.1, 1, 1])

        with chart_col:

            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="section-title">
                        Evidence Overview
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            mini_1, mini_2, mini_3, mini_4 = st.columns(4)

            mini_1.metric("New Papers", 156, "22%")
            mini_2.metric("Practice", 38, "18%")
            mini_3.metric("Gaps", 11, "10%")
            mini_4.metric("Conflicts", 7, "-2%")

            st.line_chart(
                {
                    "New Papers": [
                        28,
                        46,
                        55,
                        34,
                        43,
                        38,
                        49,
                        52,
                        41,
                        48,
                        57,
                        44,
                        35,
                        47,
                        62,
                        59,
                        82,
                        84,
                    ]
                },
                height=190,
            )

        with paper_col:

            st.markdown(
                """
                <div class="dashboard-card paper-card-shell">
                    <div class="section-title">
                        ☆ Paper of the Week
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            paper = journal_club.get("paper_of_the_week", {})

            if paper:

                st.markdown(
                    f"""
                    <div class="paper-type">
                        {paper.get("study_design", "Research Study")}
                    </div>

                    <div class="paper-title">
                        {paper.get("title", "")}
                    </div>

                    <div class="paper-summary">
                        {paper.get("practitioner_takeaway", "")}
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            else:

                st.markdown(
                    """
                    <div class="paper-type">
                        RANDOMIZED CONTROLLED TRIAL
                    </div>

                    <div class="paper-title">
                        Platelet-Rich Plasma for Patellar Tendinopathy:
                        A Double-Blind RCT
                    </div>

                    <div class="paper-summary">
                        Example journal club entry. Your automated research
                        pipeline can replace this card when new evidence is available.
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            evidence_col, stats_col, impact_col = st.columns(3)

            evidence_col.metric("Evidence", "9.4/10")
            stats_col.metric("Statistics", "9.1/10")
            impact_col.metric("Impact", "9.7/10")

            if st.button(
                "Read Summary  →",
                key="read_summary",
                use_container_width=True,
            ):
                set_page("Journal Club")

        with trend_col:

            st.markdown(
                """
                <div class="dashboard-card">
                    <div class="section-title">
                        🔥 Trending Topics
                    </div>

                    <div class="trend-row">
                        <span>Exosomes</span>
                        <span class="trend-up">↑ 42%</span>
                    </div>

                    <div class="trend-row">
                        <span>Blood Flow Restriction</span>
                        <span class="trend-up">↑ 37%</span>
                    </div>

                    <div class="trend-row">
                        <span>Sprint Force-Velocity</span>
                        <span class="trend-up">↑ 31%</span>
                    </div>

                    <div class="trend-row">
                        <span>RED-S</span>
                        <span class="trend-up">↑ 28%</span>
                    </div>

                    <div class="trend-row">
                        <span>Tendon Mechanobiology</span>
                        <span class="trend-up">↑ 26%</span>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "Explore All Trends  →",
                key="explore_trends",
                use_container_width=True,
            ):
                set_page("Evidence Library")

    # =====================================================
    # Right rail
    # =====================================================

    with right_col:

        st.markdown(
            """
            <div class="rail-card">
                <div class="rail-header">
                    <span>AI Team Activity</span>
                    <span class="live-dot">● Live</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        for specialist in specialists:

            st.markdown(
                f"""
                <div class="activity-row">
                    <div class="activity-avatar">
                        {specialist['icon']}
                    </div>

                    <div class="activity-main">
                        <div class="activity-name">
                            {specialist['name']}
                        </div>

                        <div class="activity-role">
                            {specialist['specialty']}
                        </div>
                    </div>

                    <div class="activity-right">
                        <div>{specialist['activity']}</div>
                        <div class="activity-insight">
                            {specialist['insight']}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

        st.markdown(
            """
            <div class="rail-card">
                <div class="rail-header">
                    <span>Top Evidence Gaps</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        evidence_gaps = [
            (
                "Optimal PRP formulation for tendinopathy",
                "High impact • 27 papers",
            ),
            (
                "Long-term outcomes in female athletes",
                "High impact • 19 papers",
            ),
            (
                "Return-to-sport criteria after hamstring strain",
                "High impact • 16 papers",
            ),
            (
                "Menstrual cycle & performance interactions",
                "Moderate impact • 14 papers",
            ),
            (
                "Heavy vs. explosive strength for power",
                "Moderate impact • 13 papers",
            ),
        ]

        for index, (gap, meta) in enumerate(evidence_gaps, start=1):

            st.markdown(
                f"""
                <div class="gap-row">
                    <div class="gap-number">{index}</div>

                    <div>
                        <div class="gap-title">{gap}</div>
                        <div class="gap-meta">{meta}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        if st.button(
            "View All Evidence Gaps  →",
            key="all_gaps",
            use_container_width=True,
        ):
            set_page("Evidence Gaps")


# =========================================================
# CLINICAL PROBLEMS PAGE
# =========================================================

elif st.session_state.page == "Clinical Problems":

    search = render_header(
        title="Clinical Problems",
        subtitle=(
            "Explore conditions, performance questions, and clinical "
            "topics through continuously synthesized evidence."
        ),
    )

    filtered_problems = clinical_problems

    if search:

        filtered_problems = [
            problem
            for problem in clinical_problems
            if search.lower() in problem["name"].lower()
            or any(
                search.lower() in tag.lower()
                for tag in problem["tags"]
            )
        ]

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    for problem in filtered_problems:

        left, center, right = st.columns([3, 1, 1])

        with left:

            st.markdown(
                f"""
                <div class="list-card">
                    <div class="list-icon">{problem['icon']}</div>

                    <div>
                        <div class="list-title">
                            {problem['name']}
                        </div>

                        <div class="list-copy">
                            {problem['summary']}
                        </div>

                        <div class="tag-row">
                            {" ".join(
                                [f"<span class='tag'>{tag}</span>"
                                 for tag in problem['tags']]
                            )}
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        with center:
            st.metric("Studies", problem["studies"])
            st.metric("Confidence", f"{problem['confidence']}%")

        with right:
            st.markdown(
                f"""
                <div class="strength-large">
                    {problem['strength']}
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                "View problem →",
                key=f"clinical_{problem['name']}",
                use_container_width=True,
            ):
                set_problem(problem["name"])


# =========================================================
# PROBLEM DETAIL PAGE
# =========================================================

elif st.session_state.page == "Problem Detail":

    problem = next(
        (
            item
            for item in clinical_problems
            if item["name"] == st.session_state.selected_problem
        ),
        clinical_problems[0],
    )

    render_header(
        title=problem["name"],
        subtitle=(
            "Evidence synthesis, key findings, research gaps, "
            "and practice-relevant interpretation."
        ),
    )

    if st.button("← Back to Clinical Problems"):
        set_page("Clinical Problems")

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Studies", problem["studies"])
    c2.metric("Evidence Strength", problem["strength"])
    c3.metric("Confidence", f"{problem['confidence']}%")
    c4.metric("Newest Insight", problem["insight"])

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    left, right = st.columns([2, 1])

    with left:

        st.markdown("### Evidence Summary")

        st.write(problem["summary"])

        st.markdown("### Current Practice-Relevant Findings")

        st.markdown(
            """
            - Evidence synthesis will populate from your research pipeline.
            - Findings can be grouped by intervention, population, outcome, and study design.
            - AI specialists can flag conflicting evidence or methodological weaknesses.
            - Statistical confidence can later be calculated dynamically.
            """
        )

        st.markdown("### Key Papers")

        for index in range(1, 4):

            with st.container(border=True):

                st.markdown(
                    f"**Key paper {index}: evidence synthesis placeholder**"
                )

                st.caption(
                    "This will later populate with PMID, authors, year, "
                    "study design, sample size, and evidence score."
                )

    with right:

        st.markdown("### Evidence Gaps")

        with st.container(border=True):
            st.write("Optimal intervention dosing remains unclear.")

        with st.container(border=True):
            st.write("Long-term outcome data are limited.")

        with st.container(border=True):
            st.write("Population-specific evidence remains incomplete.")

        st.markdown("### Ask the Team")

        if st.button(
            "Ask Athena",
            use_container_width=True,
            key="detail_athena",
        ):
            set_specialist("Athena")

        if st.button(
            "Ask Euler",
            use_container_width=True,
            key="detail_euler",
        ):
            set_specialist("Euler")


# =========================================================
# EVIDENCE LIBRARY
# =========================================================

elif st.session_state.page == "Evidence Library":

    search = render_header(
        title="Evidence Library",
        subtitle=(
            "Search the papers collected and analyzed by your research pipeline."
        ),
    )

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    filter_col, design_col, sort_col = st.columns(3)

    with filter_col:
        topic = st.selectbox(
            "Topic",
            [
                "All Topics",
                "Regenerative Medicine",
                "Sports Performance",
                "Biomechanics",
                "Women's Athlete Health",
            ],
        )

    with design_col:
        study_design = st.selectbox(
            "Study Design",
            [
                "All Designs",
                "Randomized Controlled Trial",
                "Cohort",
                "Systematic Review",
                "Meta-analysis",
            ],
        )

    with sort_col:
        sort_by = st.selectbox(
            "Sort By",
            [
                "Newest",
                "Highest Evidence Score",
                "Most Practice-Relevant",
            ],
        )

    st.markdown("### Research Library")

    for index in range(1, 7):

        with st.container(border=True):

            st.markdown(
                f"#### Example Evidence Paper {index}"
            )

            st.caption(
                "2026 • Randomized Controlled Trial • Evidence score 8.9/10"
            )

            st.write(
                "A structured research summary will appear here after "
                "your evidence pipeline generates paper-level analyses."
            )


# =========================================================
# AI SPECIALISTS
# =========================================================

elif st.session_state.page == "AI Specialists":

    render_header(
        title="AI Specialists",
        subtitle=(
            "A coordinated research team analyzing evidence through "
            "different scientific and clinical lenses."
        ),
    )

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    specialist_cols = st.columns(3)

    for index, specialist in enumerate(specialists):

        col = specialist_cols[index % 3]

        with col:

            selected = (
                specialist["name"]
                == st.session_state.selected_specialist
            )

            extra_class = " selected" if selected else ""

            st.markdown(
                f"""
                <div class="specialist-large-card{extra_class}">
                    <div class="specialist-large-avatar">
                        {specialist['icon']}
                    </div>

                    <div class="specialist-large-name">
                        {specialist['name']}
                    </div>

                    <div class="specialist-large-role">
                        {specialist['specialty']}
                    </div>

                    <div class="specialist-large-copy">
                        {specialist['description']}
                    </div>

                    <div class="specialist-activity">
                        {specialist['activity']}
                    </div>

                    <div class="specialist-insight">
                        {specialist['insight']}
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.button(
                f"Open {specialist['name']}",
                key=f"open_specialist_{specialist['name']}",
                use_container_width=True,
            ):
                st.session_state.selected_specialist = specialist["name"]
                st.rerun()

    selected_specialist = next(
        specialist
        for specialist in specialists
        if specialist["name"]
        == st.session_state.selected_specialist
    )

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    st.markdown(
        f"## {selected_specialist['name']} Workspace"
    )

    st.write(selected_specialist["description"])

    question = st.text_area(
        f"Ask {selected_specialist['name']} a research question",
        placeholder="What does the evidence suggest?",
    )

    if st.button("Analyze question"):

        if question:
            st.info(
                "LLM integration can be connected here next. "
                "For now, this confirms the interface is wired correctly."
            )

        else:
            st.warning("Enter a question first.")


# =========================================================
# JOURNAL CLUB
# =========================================================

elif st.session_state.page == "Journal Club":

    render_header(
        title="Journal Club",
        subtitle=(
            "A curated discussion space for the most clinically "
            "important new research."
        ),
    )

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    paper = journal_club.get("paper_of_the_week", {})

    with st.container(border=True):

        st.markdown("### Paper of the Week")

        if paper:

            st.markdown(
                f"## {paper.get('title', 'Paper of the Week')}"
            )

            st.caption(
                paper.get("study_design", "")
            )

            st.write(
                paper.get("practitioner_takeaway", "")
            )

        else:

            st.markdown(
                "## Your research pipeline has not selected a paper yet."
            )

            st.write(
                "When your scheduled evidence refresh runs, Artemis can "
                "automatically select and summarize a Paper of the Week."
            )

    st.markdown("### Discussion Framework")

    c1, c2, c3 = st.columns(3)

    with c1:
        st.info("**Clinical relevance**\n\nDoes this change practice?")

    with c2:
        st.info("**Methodological quality**\n\nCan we trust the findings?")

    with c3:
        st.info("**Next question**\n\nWhat evidence is still missing?")


# =========================================================
# KNOWLEDGE GRAPH
# =========================================================

elif st.session_state.page == "Knowledge Graph":

    render_header(
        title="Knowledge Graph",
        subtitle=(
            "Explore relationships between conditions, mechanisms, "
            "interventions, outcomes, and evidence."
        ),
    )

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    st.info(
        "The interactive knowledge graph can be built next using "
        "PyVis, NetworkX, or a custom graph component."
    )

    st.markdown(
        """
        ### Example relationships

        **Patellar Tendinopathy**  
        → Tendon load  
        → Collagen remodeling  
        → Heavy slow resistance  
        → Pain/function outcomes

        **RED-S**  
        → Low energy availability  
        → Endocrine adaptation  
        → Bone health  
        → Performance / injury risk
        """
    )


# =========================================================
# EVIDENCE GAPS
# =========================================================

elif st.session_state.page == "Evidence Gaps":

    render_header(
        title="Evidence Gaps",
        subtitle=(
            "Questions where current research remains insufficient, "
            "conflicting, or clinically uncertain."
        ),
    )

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    gaps = [
        {
            "title": "Optimal PRP formulation for tendinopathy",
            "impact": "High",
            "papers": 27,
        },
        {
            "title": "Long-term outcomes in female athletes",
            "impact": "High",
            "papers": 19,
        },
        {
            "title": "Return-to-sport criteria after hamstring strain",
            "impact": "High",
            "papers": 16,
        },
        {
            "title": "Menstrual cycle and performance interactions",
            "impact": "Moderate",
            "papers": 14,
        },
        {
            "title": "Heavy versus explosive strength for power",
            "impact": "Moderate",
            "papers": 13,
        },
    ]

    for gap in gaps:

        left, middle, right = st.columns([5, 1, 1])

        with left:
            st.markdown(f"### {gap['title']}")

        with middle:
            st.metric("Impact", gap["impact"])

        with right:
            st.metric("Papers", gap["papers"])

        st.divider()


# =========================================================
# STATISTICS REVIEW
# =========================================================

elif st.session_state.page == "Statistics Review":

    render_header(
        title="Statistics Review",
        subtitle=(
            "Euler evaluates study design, statistical reasoning, "
            "uncertainty, and methodological quality."
        ),
    )

    st.markdown("<div class='vertical-gap'></div>", unsafe_allow_html=True)

    st.markdown("### Statistical Review Workspace")

    study_design = st.selectbox(
        "Study design",
        [
            "Randomized Controlled Trial",
            "Cross-sectional Study",
            "Prospective Cohort",
            "Method Comparison Study",
            "Systematic Review",
            "Meta-analysis",
        ],
    )

    variables = st.text_area(
        "Describe your variables",
        placeholder=(
            "Example: DXA body fat percentage and AI-estimated "
            "body fat percentage measured once per participant."
        ),
    )

    if st.button("Suggest statistical approach"):

        st.success(
            f"Selected design: {study_design}. "
            "This workspace can later connect Euler to an LLM "
            "for statistical method recommendations."
        )


# =========================================================
# SAVED
# =========================================================

elif st.session_state.page == "Saved":

    render_header(
        title="Saved",
        subtitle="Your bookmarked papers, clinical problems, and evidence summaries.",
    )

    st.info("Saved items will appear here.")


# =========================================================
# SETTINGS
# =========================================================

elif st.session_state.page == "Settings":

    render_header(
        title="Settings",
        subtitle="Configure research preferences and dashboard behavior.",
    )

    st.toggle(
        "Automatically refresh evidence",
        value=True,
    )

    st.selectbox(
        "Evidence refresh frequency",
        [
            "Daily",
            "Weekdays",
            "Weekly",
        ],
    )

    st.multiselect(
        "Priority research domains",
        [
            "Regenerative Medicine",
            "Sports Performance",
            "Biomechanics",
            "Women's Athlete Health",
            "Statistics",
        ],
        default=[
            "Regenerative Medicine",
            "Sports Performance",
            "Women's Athlete Health",
        ],
    )
