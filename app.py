import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from app_utils import HelpdeskAppUtils
from helpdesk_agent import create_ticket_after_approval, handle_support_request
from models import triage_to_text


BASE_DIR = Path(__file__).resolve().parent

# Local runs read values from App/.env. Streamlit Cloud uses st.secrets.
load_dotenv(BASE_DIR / ".env", encoding="utf-8-sig")


st.set_page_config(
    page_title="AI IT Helpdesk Agent",
    page_icon=":material/support_agent:",
    layout="wide",
)

# Prepare cloud secrets, dark theme, and Streamlit session defaults.
HelpdeskAppUtils.apply_streamlit_secrets_to_environment()
HelpdeskAppUtils.apply_app_styles()
HelpdeskAppUtils.initialize_session_state()


@st.dialog("Create support ticket")
def show_ticket_creation_dialog() -> None:
    """Confirm ticket creation and show the generated ticket ID."""

    if st.session_state.ticket_result:
        st.success(
            HelpdeskAppUtils.clean_ticket_confirmation(st.session_state.ticket_result)
        )
        st.info(HelpdeskAppUtils.farewell_message())
        if st.button("OK", type="primary", use_container_width=True):
            HelpdeskAppUtils.reset_home()
            st.rerun()
        return

    st.write("Create a support ticket for this employee?")
    st.caption(f"Employee: {st.session_state.current_employee_name}")
    st.caption(f"Employee ID: {st.session_state.current_employee_id}")
    if st.session_state.triage:
        st.caption(f"Summary: {st.session_state.triage.summary}")

    create_column, cancel_column = st.columns(2)
    with create_column:
        create_clicked = st.button("Create Ticket", type="primary", use_container_width=True)
    with cancel_column:
        cancel_clicked = st.button("Cancel", use_container_width=True)

    if cancel_clicked:
        st.session_state.show_ticket_dialog = False
        st.rerun()

    if create_clicked:
        if not st.session_state.current_employee_id:
            st.error("Employee ID is required before creating the ticket.")
            return

        with st.spinner("Creating ticket..."):
            try:
                ticket_result = create_ticket_after_approval(
                    employee_name=st.session_state.current_employee_name,
                    employee_number=st.session_state.current_employee_id,
                    original_query=st.session_state.last_query,
                    triage=st.session_state.triage,
                )
            except Exception as exc:
                st.error(str(exc))
            else:
                st.session_state.ticket_result = HelpdeskAppUtils.clean_ticket_confirmation(
                    ticket_result
                )
                st.rerun()


# Header
st.markdown(
    """
    <div class="helpdesk-header">
        <h1>AI IT Helpdesk Agent</h1>
        <p>Internal support workflow with Supabase knowledge search, MCP ticket actions, and human approval.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Static architecture summary for learners.
st.markdown(
    """
    <div class="status-grid">
        <div class="status-tile">
            <div class="status-label">Knowledge</div>
            <div class="status-value">Supabase RAG</div>
            <div class="status-note">Approved helpdesk docs</div>
        </div>
        <div class="status-tile">
            <div class="status-label">Actions</div>
            <div class="status-value">MCP Tools</div>
            <div class="status-note">Ticket operations</div>
        </div>
        <div class="status-tile">
            <div class="status-label">Ticket Store</div>
            <div class="status-value">Supabase</div>
            <div class="status-note">No SQLite dependency</div>
        </div>
        <div class="status-tile">
            <div class="status-label">Write Safety</div>
            <div class="status-value">Human Approval</div>
            <div class="status-note">Required before creation</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left_column, right_column = st.columns([1.55, 0.85], gap="large")

with left_column:
    # One input path handles troubleshooting and ticket lookup. The agent
    # chooses whether to use RAG, status tools, or MCP ticket tools.
    st.markdown(
        """
        <div class="soft-panel">
            <div class="section-kicker">New Request</div>
            <div class="section-title">Ask for support or ticket status</div>
            <p class="muted-copy">Share your details and issue. The assistant will choose the right knowledge, status, or MCP ticket tool.</p>
            <div class="quick-examples">
                <div class="quick-example">How do I reset my password?</div>
                <div class="quick-example">Check ticket INC-1001.</div>
                <div class="quick-example">Show tickets for EMP-0001.</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form("support_request_form", clear_on_submit=False):
        name_column, id_column = st.columns(2)
        with name_column:
            employee_name = st.text_input(
                "Employee Name",
                placeholder="Your name",
                key=f"employee_name_{st.session_state.identity_key}",
            )
        with id_column:
            employee_id = st.text_input(
                "Employee ID",
                placeholder="EMP-0001",
                key=f"employee_id_{st.session_state.identity_key}",
            )

        user_query = st.text_area(
            "Issue Description",
            placeholder="Example: My VPN connects but I still cannot access internal tools. Or: Check ticket INC-1001.",
            height=120,
            key=f"issue_description_{st.session_state.issue_key}",
        )
        submitted = st.form_submit_button(
            "Talk to Support",
            type="primary",
            use_container_width=True,
        )

with right_column:
    # Ticket lookup happens through the agent input, not through a manual form.
    st.markdown(
        """
        <div class="soft-panel">
            <div class="section-kicker">Service Status</div>
            <div class="service-row">
                <div class="service-name">VPN</div>
                <div class="service-pill service-ok">Operational</div>
            </div>
            <div class="service-row">
                <div class="service-name">Email and Outlook</div>
                <div class="service-pill service-ok">Operational</div>
            </div>
            <div class="service-row">
                <div class="service-name">Password and access</div>
                <div class="service-pill service-ok">Operational</div>
            </div>
            <div class="service-row">
                <div class="service-name">WiFi</div>
                <div class="service-pill service-warn">Degraded</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

if submitted and user_query.strip():
    # Normal runs are read-only: the agent can answer and look up tickets, but
    # ticket creation still requires the approval button below.
    if not employee_name.strip() or not employee_id.strip():
        st.error("Employee name and Employee ID are required.")
        st.stop()

    st.session_state.current_employee_name = employee_name.strip()
    st.session_state.current_employee_id = employee_id.strip().upper()
    st.session_state.last_query = user_query
    st.session_state.ticket_result = ""

    with st.spinner("Thinking..."):
        try:
            result = handle_support_request(
                user_query,
                employee_name=st.session_state.current_employee_name,
                employee_number=st.session_state.current_employee_id,
                allow_write_actions=False,
            )
        except Exception as exc:
            st.error(str(exc))
        else:
            st.session_state.triage = result["triage"]
            st.session_state.response = result["response"]
elif submitted:
    st.warning("Describe the employee issue before talking to support.")

with left_column:
    # Show the latest request, triage, and final agent response.
    if st.session_state.last_query:
        with st.chat_message("user"):
            st.write(st.session_state.last_query)

    if st.session_state.triage:
        with st.container(border=True):
            st.subheader("Request Analysis")
            st.code(triage_to_text(st.session_state.triage))

    if st.session_state.response:
        with st.chat_message("assistant"):
            st.write(st.session_state.response)

    if (
        st.session_state.triage
        and st.session_state.response
        and not st.session_state.triage.requires_ticket
    ):
        # The request is complete and no ticket is needed. Let the user close
        # the conversation and return to the starting screen.
        if st.button("OK", type="primary", use_container_width=True):
            st.success(HelpdeskAppUtils.farewell_message())
            time.sleep(2)
            HelpdeskAppUtils.reset_home()
            st.rerun()

    if st.session_state.triage and st.session_state.triage.requires_ticket:
        # Human chooses whether to create a ticket or close the issue.
        with st.container(border=True):
            st.warning("Escalation may be required.")
            ticket_column, resolved_column = st.columns(2)
            with ticket_column:
                create_ticket_clicked = st.button(
                    "Create Support Ticket",
                    type="primary",
                    use_container_width=True,
                )
            with resolved_column:
                steps_worked_clicked = st.button(
                    "Ticket not required, Steps Worked",
                    use_container_width=True,
                )

            if create_ticket_clicked:
                st.session_state.show_ticket_dialog = True
                st.rerun()

            if steps_worked_clicked:
                st.success(HelpdeskAppUtils.farewell_message())
                time.sleep(2)
                HelpdeskAppUtils.reset_home()
                st.rerun()

if st.session_state.show_ticket_dialog:
    show_ticket_creation_dialog()
