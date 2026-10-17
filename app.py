
import streamlit as st
from datetime import datetime

from incident_copilot.log_parser import analyze_log_text
from incident_copilot.sample_data import load_sample_log

from incident_copilot.monitor import (
    check_for_incident,
    load_payment_api_logs,
)

from incident_copilot.incident_store import (
    record_incident,
    list_incidents,
    recover_stale_incidents,
)

from incident_copilot.investigation_engine import (
    investigate_incident,
)


# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="Agentic Incident Response Copilot",
    page_icon="🔎",
    layout="wide",
)

st.title("🔎 Agentic Incident Response Copilot")

st.caption(
    "Monitor simulated services, detect incidents, "
    "retrieve operational evidence, and investigate failures using AI."
)

st.caption(
    f"Dashboard last refreshed: "
    f"{datetime.now().astimezone().strftime('%H:%M:%S')}"
)

st.write(
    "An AI-powered incident response system that monitors "
    "simulated services, detects recurring errors, retrieves "
    "operational evidence, and investigates potential root causes "
    "using an LLM."
)


# ==================================================
# 2. AUTOMATIC INCIDENT MONITORING
# ==================================================

st.divider()
st.subheader("1. Automatic Incident Monitoring")

st.caption(
    "Monitoring uses the latest Payment API logs whenever "
    "the dashboard runs. Refresh the browser to check again."
)

log_text = load_payment_api_logs()

if log_text.strip():

    monitor_result = check_for_incident(log_text)

    if monitor_result:

        # Save or update the active incident.
        saved_incident = record_incident(monitor_result)

        st.error("Incident detected!")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Service",
            monitor_result["service"],
        )

        col2.metric(
            "Errors detected",
            monitor_result["error_count"],
        )

        col3.metric(
            "Detection window",
            f'{monitor_result["window_seconds"]} sec',
        )

        st.markdown(
            f"### {monitor_result['title']}"
        )

        st.warning(
            f"Severity: {monitor_result['severity']}"
        )

        st.write(
            monitor_result["description"]
        )

        st.caption(
            f"Incident ID: {saved_incident['id']} | "
            f"Status: {saved_incident['status']}"
        )

        st.caption(
            f"First seen (UTC): {monitor_result['first_seen']}"
        )

        st.caption(
            f"Latest error event (UTC): {monitor_result['last_seen']}"
        )

        st.markdown("**Evidence collected**")

        for line in monitor_result["evidence"]:
            st.code(line, language="text")

        st.caption(
            "The detector found an error pattern. "
            "This is not a confirmed root cause."
        )

    else:

        recovered_count = recover_stale_incidents(
            recovery_after_seconds=30
        )

        if recovered_count:
            st.success(
                f"{recovered_count} incident(s) marked as recovered."
            )
        else:
            st.info(
                "No incident detected in the recent log window."
            )

else:
    st.info(
        "Waiting for Payment API logs. "
        "Start the API and traffic simulator to generate test events."
    )


# ==================================================
# 3. INCIDENT HISTORY
# ==================================================

st.divider()
st.subheader("2. Incident History")

incidents = list_incidents(limit=50)

# Preserve reports during Streamlit reruns.
if "investigation_reports" not in st.session_state:
    st.session_state["investigation_reports"] = {}


if incidents:

    st.caption(
        f"Showing {len(incidents)} most recent saved incidents."
    )

    active_count = sum(
        1
        for incident in incidents
        if incident["status"] == "Active"
    )

    recovered_count = sum(
        1
        for incident in incidents
        if incident["status"] == "Recovered"
    )

    col1, col2, col3 = st.columns(3)

    col1.metric(
        "Saved incidents",
        len(incidents),
    )

    col2.metric(
        "Active incidents",
        active_count,
    )

    col3.metric(
        "Recovered incidents",
        recovered_count,
    )

    # Display every saved incident.
    for saved in incidents:

        incident_id = saved["id"]

        with st.expander(
            f"#{incident_id} — {saved['title']} "
            f"({saved['status']})"
        ):

            # --------------------------------------
            # Incident details
            # --------------------------------------

            st.markdown("### Incident Details")

            st.write(
                f"**Service:** {saved['service']}"
            )

            st.write(
                f"**Severity:** {saved['severity']}"
            )

            st.write(
                f"**Status:** {saved['status']}"
            )

            st.write(
                f"**Errors detected:** {saved['error_count']}"
            )

            st.write(
                f"**First seen (UTC):** {saved['first_seen']}"
            )

            st.write(
                f"**Latest error (UTC):** {saved['last_seen']}"
            )

            st.write(
                f"**Record created (UTC):** {saved['created_at']}"
            )

            if saved.get("recovered_at"):
                st.write(
                    f"**Recovered at (UTC):** "
                    f"{saved['recovered_at']}"
                )

            # --------------------------------------
            # Stored evidence
            # --------------------------------------

            st.divider()
            st.markdown("### Stored Evidence")

            if saved["evidence"]:

                for line in saved["evidence"]:
                    st.code(line, language="text")

            else:
                st.info(
                    "No evidence is stored for this incident."
                )

            # --------------------------------------
            # AI investigation
            # --------------------------------------

            st.divider()
            st.markdown("### AI Incident Investigation")

            if st.button(
                "Investigate with AI",
                key=f"investigate_{incident_id}",
                type="primary",
            ):

                try:

                    with st.spinner(
                        "AI is retrieving evidence and investigating "
                        "the incident. Please wait..."
                    ):

                        report = investigate_incident(saved)

                        st.session_state[
                            "investigation_reports"
                        ][incident_id] = report

                    st.success(
                        "AI investigation completed successfully!"
                    )

                except Exception as error:

                    st.error(
                        f"Investigation failed: {error}"
                    )

            # --------------------------------------
            # Display AI investigation report
            # --------------------------------------

            report = st.session_state[
                "investigation_reports"
            ].get(incident_id)

            if report:

                st.divider()

                st.markdown("## AI Investigation Report")

                # Incident summary
                st.markdown("### Incident Summary")

                st.write(
                    report["incident_summary"]
                )

                # Observed facts
                st.markdown("### Observed Facts")

                for fact in report["observed_facts"]:
                    st.write(f"- {fact}")

                # Possible causes
                st.markdown("### Possible Root Causes")

                if report["possible_causes"]:

                    for index, cause in enumerate(
                        report["possible_causes"],
                        start=1,
                    ):

                        st.markdown(
                            f"#### Hypothesis {index}: "
                            f"{cause['hypothesis']}"
                        )

                        st.write(
                            f"**Confidence:** {cause['confidence']}"
                        )

                        st.markdown("**Supporting Evidence**")

                        for evidence in cause[
                            "supporting_evidence"
                        ]:
                            st.write(f"- {evidence}")

                        st.markdown("**Missing Evidence**")

                        for evidence in cause[
                            "missing_evidence"
                        ]:
                            st.write(f"- {evidence}")

                        st.divider()

                else:
                    st.info(
                        "The AI did not identify any possible causes."
                    )

                # Recommended checks
                st.markdown(
                    "### Recommended Diagnostic Checks"
                )

                for check in report["recommended_checks"]:
                    st.write(f"- {check}")

                # Root cause status
                st.markdown("### Root Cause Assessment")

                if report["root_cause_confirmed"]:

                    st.success(
                        "The AI report indicates a confirmed root cause. "
                        "Verify the supporting evidence before acting."
                    )

                else:

                    st.warning(
                        "Root cause is not confirmed. "
                        "Further investigation is required."
                    )

                # Limitations
                st.markdown(
                    "### Investigation Limitations"
                )

                for limitation in report["limitations"]:
                    st.write(f"- {limitation}")

                # Evidence sources
                st.markdown("### Evidence Sources")

                sources = report["evidence_sources"]

                st.markdown("**Current incident logs**")
                for source in sources["current_logs"]:
                    st.write(f"- {source}")

                st.markdown("**Runbooks**")
                for source in sources["runbooks"]:
                    st.write(f"- {source}")

                st.markdown("**Historical incidents**")
                for source in sources["historical_incidents"]:
                    st.write(f"- {source}")

                # Model information
                st.divider()

                usage = report.get("usage", {})

                st.caption(
                    f"Model: {report.get('model', 'Unknown')} | "
                    f"Tokens used: {usage.get('total_tokens', 'Unknown')}"
                )


else:

    st.info(
        "No incidents have been saved yet. "
        "Start the API and traffic simulator to generate test events."
    )


# ==================================================
# 4. MANUAL INCIDENT INTAKE
# ==================================================

st.divider()
st.subheader("3. Manual Incident Intake")

with st.form("incident_form"):

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
        value=(
            "Payment requests started failing after "
            "the latest deployment."
        ),
        height=120,
    )

    submitted = st.form_submit_button(
        "Create incident",
        type="primary",
    )


if submitted:

    if not title.strip() or not description.strip():

        st.error(
            "Please provide both an incident title and description."
        )

    else:

        st.session_state["incident"] = {
            "title": title.strip(),
            "severity": severity,
            "description": description.strip(),
        }

        st.success(
            "Incident captured for initial investigation."
        )


# ==================================================
# 5. INCIDENT SUMMARY AND INITIAL LOG ANALYSIS
# ==================================================

incident = st.session_state.get("incident")

if incident:

    st.divider()
    st.subheader("4. Incident Summary")

    col1, col2 = st.columns([3, 1])

    with col1:

        st.markdown(
            f"**Title:** {incident['title']}"
        )

        st.markdown(
            f"**Description:** {incident['description']}"
        )

    with col2:

        st.metric(
            "Severity",
            incident["severity"],
        )

    st.subheader("5. Initial Log Analysis")

    st.write(
        "Transparent rules identify common error signals. "
        "This analysis does not confirm the incident's root cause."
    )

    sample_log = load_sample_log()

    log_text = st.text_area(
        "Log text",
        value=sample_log,
        height=220,
        key="incident_log_text",
        help="Use sample logs or paste non-sensitive test logs.",
    )

    if st.button("Analyze logs"):

        result = analyze_log_text(log_text)

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Total lines",
            result["total_lines"],
        )

        col2.metric(
            "Error-like lines",
            result["error_count"],
        )

        col3.metric(
            "Warning-like lines",
            result["warning_count"],
        )

        if result["signals"]:

            st.markdown("**Detected signals**")

            for signal in result["signals"]:
                st.write(f"- {signal}")

        else:

            st.info(
                "No error or warning keywords were detected."
            )

        if result["matching_lines"]:

            st.markdown("**Matching log lines**")

            for line in result["matching_lines"]:
                st.code(line, language="text")

        st.caption(
            "Rule-based output is a starting point, not a confirmed diagnosis."
        )


# ==================================================
# 6. PROJECT ROADMAP
# ==================================================

st.divider()
st.subheader("Project Modules")

st.markdown(
    """
    - **Monitoring:** Detect recurring errors in simulated service logs.
    - **Incident persistence:** Store incidents and their history in SQLite.
    - **Log analysis:** Identify and summarize error signals.
    - **Evidence retrieval:** Search operational runbooks and historical incidents.
    - **AI investigation:** Compare possible causes against retrieved evidence.
    - **Report generation:** Present findings, uncertainty, and next steps.
    - **Agent orchestration:** Coordinate investigation steps using LangGraph.
    - **Evaluation:** Test the system against incidents with known causes.
    """
)
