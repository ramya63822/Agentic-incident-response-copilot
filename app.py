
import streamlit as st

from incident_copilot.log_parser import analyze_log_text
from streamlit_autorefresh import st_autorefresh
from datetime import datetime
from incident_copilot.sample_data import load_sample_log
from incident_copilot.monitor import (
    SAMPLE_ALERT_LOGS,
    check_for_incident,
    load_payment_api_logs,
)

st.set_page_config(
    page_title="Agentic Incident Response Copilot",
    page_icon="🔎",
    layout="wide",
)
# Refresh the dashboard every 3 seconds
refresh_count = st_autorefresh(
    interval=3000,
    limit=None,
    key="incident_monitor_refresh",
)

st.info(f"Dashboard refresh count: {refresh_count}")
st.caption(
    f"Dashboard last rerun: "
    f"{datetime.now().astimezone().strftime('%H:%M:%S')}"
)

st.title("🔎 Agentic Incident Response Copilot")
st.caption("A step-by-step AI engineering portfolio project")

st.write(
    "Investigate software incidents by examining logs, deployment context, "
    "runbooks, and historical incidents. This version includes incident intake, "
    "rule-based log analysis, and simulated monitoring."
)



# --------------------------------------------------
# 1. Automatic Incident Monitoring
# --------------------------------------------------

st.divider()
st.subheader("1. Automatic Incident Monitoring")

st.caption(
    "Dashboard refreshes every 3 seconds and checks the latest "
    "Payment API logs automatically."
)

log_text = load_payment_api_logs()

if log_text.strip():
    monitor_result = check_for_incident(log_text)

    if monitor_result:
        st.error("Incident detected!")

        m1, m2, m3 = st.columns(3)
        m1.metric("Service", monitor_result["service"])
        m2.metric("Errors detected", monitor_result["error_count"])
        m3.metric(
            "Detection window",
            f'{monitor_result["window_seconds"]} sec',
        )

        st.markdown(f"### {monitor_result['title']}")
        st.warning(f"Severity: {monitor_result['severity']}")
        st.write(monitor_result["description"])

        st.markdown("**Evidence collected**")
        for line in monitor_result["evidence"]:
            st.code(line, language="text")

        st.caption(
            "The detector found an error pattern. "
            "This is not a confirmed root cause."
        )
    else:
        st.info("No incident detected in the current logs.")
else:
    st.info(
        "Waiting for Payment API logs. Start the API and traffic simulator."
    )

# --------------------------------------------------
# 2. Manual incident intake
# --------------------------------------------------

st.divider()

with st.form("incident_form"):
    st.subheader("2. Incident Intake")

    title = st.text_input(
        "Incident title",
        value="Payment service returning HTTP 500 errors",
    )

    severity = st.selectbox(
        "Severity",
        ["Low", "Medium", "High", "Critical"],
        index=2,
    )

    description = st.text_area(
        "What happened?",
        value="Payment requests started failing after the latest deployment.",
        height=120,
    )

    submitted = st.form_submit_button(
        "Create incident",
        type="primary",
    )

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

# --------------------------------------------------
# 3. Existing incident summary and log analysis
# --------------------------------------------------

incident = st.session_state.get("incident")

if incident:
    st.divider()
    st.subheader("3. Incident Summary")

    c1, c2 = st.columns([3, 1])

    with c1:
        st.markdown(f"**Title:** {incident['title']}")
        st.markdown(f"**Description:** {incident['description']}")

    with c2:
        st.metric("Severity", incident["severity"])

    st.subheader("4. Initial Log Analysis")

    st.write(
        "This section uses transparent rules to identify common error signals. "
        "It does not yet use an LLM or determine the confirmed root cause."
    )

    sample_log = load_sample_log()

    log_text = st.text_area(
        "Log text",
        value=sample_log,
        height=220,
        key="incident_log_text",
        help="Use the sample log or replace it with non-sensitive test logs.",
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
            "Evidence retrieval and AI investigation will be added later."
        )

# --------------------------------------------------
# 4. Project roadmap
# --------------------------------------------------

st.divider()
st.subheader("Planned Modules")

st.markdown(
    """
    - **Monitoring:** simulate incoming logs and detect error patterns.
    - **Log analysis:** detect and summarize error signals.
    - **Knowledge retrieval:** search runbooks and historical incidents.
    - **Investigation agent:** coordinate tools and compare evidence.
    - **Report generation:** produce hypotheses, evidence, uncertainty, and next steps.
    - **Evaluation:** test against incidents with known causes.
    """
)
