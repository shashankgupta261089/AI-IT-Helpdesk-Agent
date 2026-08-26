import os
import re

import streamlit as st


class HelpdeskAppUtils:
    """Small helpers that keep the Streamlit app file focused on workflow."""

    ENV_KEYS = [
        "OPENAI_API_KEY",
        "OPENAI_MODEL",
        "SUPABASE_URL",
        "SUPABASE_SERVICE_ROLE_KEY",
        "SUPABASE_TABLE_NAME",
        "SUPABASE_QUERY_NAME",
        "SUPABASE_TICKETS_TABLE_NAME",
        "SEED_SUPABASE_ON_STARTUP",
        "LANGSMITH_TRACING",
        "LANGSMITH_API_KEY",
        "LANGSMITH_PROJECT",
        "LANGSMITH_ENDPOINT",
    ]

    SESSION_DEFAULTS = {
        "issue_key": 0,
        "identity_key": 0,
        "current_employee_name": "",
        "current_employee_id": "",
        "last_query": "",
        "triage": None,
        "response": "",
        "ticket_result": "",
        "show_ticket_dialog": False,
    }

    @staticmethod
    def apply_streamlit_secrets_to_environment() -> None:
        """Copy Streamlit Cloud secrets into environment variables."""

        # The rest of the app reads from os.environ, so local .env and cloud
        # secrets behave the same way.
        for key in HelpdeskAppUtils.ENV_KEYS:
            try:
                value = st.secrets.get(key)
            except FileNotFoundError:
                value = None
            if value and not os.environ.get(key):
                os.environ[key] = str(value)

    @staticmethod
    def initialize_session_state() -> None:
        """Create the session values used across Streamlit reruns."""

        for key, default in HelpdeskAppUtils.SESSION_DEFAULTS.items():
            st.session_state.setdefault(key, default)

    @staticmethod
    def reset_home() -> None:
        """Return the app to the starting screen after a support outcome."""

        st.session_state.issue_key += 1
        st.session_state.identity_key += 1
        st.session_state.current_employee_name = ""
        st.session_state.current_employee_id = ""
        st.session_state.last_query = ""
        st.session_state.triage = None
        st.session_state.response = ""
        st.session_state.ticket_result = ""
        st.session_state.show_ticket_dialog = False

    @staticmethod
    def clean_ticket_confirmation(message: str) -> str:
        """Show customers only the generated ticket ID, not raw MCP metadata."""

        ticket_match = re.search(r"\bINC-\d+\b", str(message))
        if ticket_match:
            return f"Ticket {ticket_match.group(0)} created successfully."
        if "ticket" in str(message).lower() and "created" in str(message).lower():
            return "Ticket created successfully."
        return str(message)

    @staticmethod
    def farewell_message() -> str:
        """One shared closing message for both support outcomes."""

        return "Thanks for using AI Helpdesk Agent today. Have a great day."

    @staticmethod
    def apply_app_styles() -> None:
        """Apply the compact dark helpdesk theme."""

        # Streamlit handles the layout. This CSS keeps the demo readable and
        # gives the app a polished dark dashboard style.
        st.markdown(
            """
            <style>
            :root {
                --ink: #e5edf7;
                --muted: #94a3b8;
                --line: #273548;
                --panel: #111827;
                --panel-soft: #172235;
                --field: #0b1220;
                --teal: #2dd4bf;
                --teal-dark: #14b8a6;
                --amber: #f59e0b;
            }
            .stApp {
                background: #0b1120;
            }

            /* Main page shell */
            .block-container {
                padding-top: 1rem;
                padding-bottom: 2rem;
                max-width: 1220px;
            }
            header[data-testid="stHeader"] {
                background: transparent;
                height: 0;
            }
            [data-testid="stToolbar"] {
                display: none;
            }

            /* Header and simple dashboard tiles */
            .helpdesk-header {
                background: linear-gradient(135deg, #111827 0%, #12333f 56%, #115e59 100%);
                border-radius: 8px;
                color: white;
                padding: 1.35rem 1.5rem;
                margin-bottom: 1rem;
                border: 1px solid #284457;
                box-shadow: 0 16px 36px rgba(0, 0, 0, 0.28);
            }
            .helpdesk-header h1 {
                font-size: 1.85rem;
                line-height: 1.15;
                margin: 0 0 0.4rem;
                letter-spacing: 0;
            }
            .helpdesk-header p {
                margin: 0;
                color: #d1fae5;
                font-size: 0.98rem;
            }
            .status-grid {
                display: grid;
                grid-template-columns: repeat(4, minmax(0, 1fr));
                gap: 0.75rem;
                margin: 0 0 1rem;
            }
            .status-tile {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 0.9rem 1rem;
                min-height: 84px;
                box-shadow: 0 10px 22px rgba(0, 0, 0, 0.20);
            }
            .status-label {
                color: var(--muted);
                font-size: 0.76rem;
                font-weight: 750;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-bottom: 0.3rem;
            }
            .status-value {
                color: var(--ink);
                font-size: 1.05rem;
                font-weight: 750;
                line-height: 1.25;
            }
            .status-note {
                color: var(--muted);
                font-size: 0.82rem;
                margin-top: 0.2rem;
            }

            /* Reusable panel styles */
            .soft-panel {
                background: var(--panel);
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 1rem 1.05rem;
                box-shadow: 0 10px 22px rgba(0, 0, 0, 0.20);
                margin-bottom: 1rem;
            }
            .section-kicker {
                color: var(--teal);
                font-size: 0.78rem;
                font-weight: 750;
                letter-spacing: 0.06em;
                text-transform: uppercase;
                margin-bottom: 0.25rem;
            }
            .section-title {
                color: var(--ink);
                font-size: 1.15rem;
                font-weight: 750;
                margin-bottom: 0.35rem;
            }
            .muted-copy {
                color: var(--muted);
                font-size: 0.95rem;
                margin-bottom: 0;
            }
            .quick-examples {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.55rem;
                margin-top: 0.75rem;
            }
            .quick-example {
                background: var(--panel-soft);
                border: 1px solid var(--line);
                border-radius: 8px;
                color: #cbd5e1;
                font-size: 0.84rem;
                padding: 0.55rem 0.65rem;
                min-height: 52px;
            }

            /* Service status list */
            .service-row {
                display: flex;
                align-items: center;
                justify-content: space-between;
                gap: 1rem;
                border-bottom: 1px solid var(--line);
                padding: 0.55rem 0;
            }
            .service-row:last-child {
                border-bottom: 0;
            }
            .service-name {
                color: var(--ink);
                font-weight: 650;
            }
            .service-pill {
                border-radius: 999px;
                font-size: 0.78rem;
                font-weight: 750;
                padding: 0.22rem 0.55rem;
                white-space: nowrap;
            }
            .service-ok {
                background: rgba(34, 197, 94, 0.16);
                border: 1px solid rgba(34, 197, 94, 0.35);
                color: #86efac;
            }
            .service-warn {
                background: rgba(245, 158, 11, 0.16);
                border: 1px solid rgba(245, 158, 11, 0.35);
                color: #fbbf24;
            }

            /* Form controls and buttons */
            [data-testid="stForm"] {
                border: 0;
                padding: 0;
            }
            [data-testid="stTextArea"] textarea,
            [data-testid="stTextInput"] input {
                border-radius: 7px;
                border: 1px solid var(--line);
                background: var(--field);
                color: var(--ink);
            }
            [data-testid="stTextArea"] textarea:focus,
            [data-testid="stTextInput"] input:focus {
                border-color: var(--teal);
                box-shadow: 0 0 0 1px var(--teal);
            }
            div[data-testid="stCodeBlock"] {
                border-radius: 8px;
            }
            .stButton > button {
                border-radius: 7px;
                font-weight: 650;
                border-color: var(--line);
                background: #172235;
                color: var(--ink);
            }
            .stButton > button[kind="primary"] {
                background: var(--teal);
                border-color: var(--teal-dark);
                color: #042f2e;
            }
            div[data-testid="stAlert"] {
                border-radius: 8px;
            }
            @media (max-width: 900px) {
                .status-grid,
                .quick-examples {
                    grid-template-columns: 1fr;
                }
                .block-container {
                    padding-left: 1rem;
                    padding-right: 1rem;
                }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
