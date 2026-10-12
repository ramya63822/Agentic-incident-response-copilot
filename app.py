import streamlit as st

from incident_copilot.log_parser import analyze_log_text
from incident_copilot.sample_data import load_sample_log

st.set_page_config(
    page_title="Agentic Incident Response Copilot",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Agentic Incident Response Copilot")
st.caption("A step-by-step AI engineering portfolio project")

st.write(
    "Investigate software incidents by examining logs, deployment context, "
    "runbooks, and historical incidents. This starter currently includes "
    "incident intake and basic rule-based log analysis; AI investigation "
    "will be added in later milestones."
)

with st.form("incident_form"):
    st.subheader("1. Incident intake")
    title = st.text_input(
        "Incident title",
        value="Payment service returning HTTP 500 errors",
    )
    severity = st.selectbox("Severity", ["Low", "Medium", "High", "Critical"], index=2)
    description = st.text_area(
        "What happened?",
        value="Payment requests started failing after the latest deployment.",
        height=120,
    )
    submitted = st.form_submit_button("Create incident", type="primary")

if submitted:
    if not title.strip() or not description.strip():
        st.error("Please provide both an incident title and description.")
    else:
        st.session_state["incident"] = {
            "title": title.strip(),
            "severity": severity,
            "description": description.strip(),
        }
        st.success("Incident captured for investigation.")

incident = st.session_state.get("incident")

if incident:
    st.divider()
    st.subheader("2. Incident summary")
    c1, c2 = st.columns([3, 1])
    with c1:
        st.markdown(f"**Title:** {incident['title']}")
        st.markdown(f"**Description:** {incident['description']}")
    with c2:
        st.metric("Severity", incident["severity"])

    st.subheader("3. Initial log analysis")
    st.write(
        "This first version uses transparent rules to identify common error "
        "signals. It does not yet use an LLM or claim to determine root cause."
    )

    sample_log = load_sample_log()
    log_text = st.text_area(
        "Log text",
        value=sample_log,
        height=220,
        help="Use the sample log or replace it with your own non-sensitive test logs.",
    )

    if st.button("Analyze logs"):
        result = analyze_log_text(log_text)
        a, b, c = st.columns(3)
        a.metric("Total lines", result["total_lines"])
        b.metric("Error-like lines", result["error_count"])
        c.metric("Warning-like lines", result["warning_count"])

        if result["signals"]:
            st.markdown("**Detected signals**")
            for signal in result["signals"]:
                st.write(f"- {signal}")
        else:
            st.info("No error or warning keywords were detected.")

        if result["matching_lines"]:
            st.markdown("**Matching log lines**")
            for line in result["matching_lines"]:
                st.code(line, language="text")

        st.caption(
            "Rule-based output is a starting point, not a confirmed diagnosis. "
            "Next we will connect evidence retrieval and an AI investigation workflow."
        )

st.divider()
st.subheader("Planned modules")
st.markdown(
    """
    - **Log analysis:** detect and summarize error patterns.
    - **Knowledge retrieval:** search runbooks and previous incident reports.
    - **Investigation agent:** coordinate tools and compare evidence.
    - **Report generation:** produce hypotheses, evidence, uncertainty, and next steps.
    - **Evaluation:** test against incidents with known causes.
    """
)
