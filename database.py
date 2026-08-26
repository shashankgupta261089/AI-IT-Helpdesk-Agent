from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from supabase.client import Client, create_client


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", encoding="utf-8-sig")

TICKETS_TABLE_NAME = os.getenv("SUPABASE_TICKETS_TABLE_NAME", "support_tickets")


def get_supabase_client() -> Client:
    """Create the Supabase client used by support ticket tools."""

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_SECRET_KEY")
    )
    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Supabase is not configured. Add SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in Streamlit Cloud Secrets for deployment "
            "or App/.env for local runs."
        )
    return create_client(supabase_url, supabase_key)


def initialize_database() -> None:
    """Verify the Supabase ticket table is available."""

    try:
        get_supabase_client().from_(TICKETS_TABLE_NAME).select("id").limit(1).execute()
    except Exception as exc:
        raise RuntimeError(
            f"Cannot access Supabase ticket table '{TICKETS_TABLE_NAME}'. "
            "Check that Streamlit Cloud Secrets point to the same Supabase "
            "project where setup_supabase.sql was run, and confirm "
            "SUPABASE_SERVICE_ROLE_KEY and SUPABASE_TICKETS_TABLE_NAME are correct. "
            f"Original error: {exc}"
        ) from exc


def create_ticket(
    employee_name: str,
    employee_number: str,
    category: str,
    priority: str,
    summary: str,
) -> dict:
    """Create one support ticket in Supabase and return the stored record."""

    initialize_database()
    payload = {
        "employee_name": employee_name.strip(),
        "employee_number": employee_number.strip().upper(),
        "category": category.strip().lower(),
        "priority": priority.strip().lower(),
        "summary": summary.strip(),
        "status": "open",
        "comments": "Created by AI IT Helpdesk Agent demo.",
    }
    response = get_supabase_client().from_(TICKETS_TABLE_NAME).insert(payload).execute()
    if not response.data:
        raise RuntimeError("Supabase did not return the created support ticket.")
    return response.data[0]


def get_ticket(ticket_id: str) -> dict | None:
    """Return a ticket by ticket ID, or None when it is not found."""

    initialize_database()
    normalized_id = ticket_id.strip().upper()
    response = (
        get_supabase_client()
        .from_(TICKETS_TABLE_NAME)
        .select("*")
        .eq("id", normalized_id)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None


def get_tickets_by_employee_number(employee_number: str, *, limit: int = 5) -> list[dict]:
    """Return recent tickets for an employee number."""

    initialize_database()
    normalized_employee_number = employee_number.strip().upper()
    response = (
        get_supabase_client()
        .from_(TICKETS_TABLE_NAME)
        .select("*")
        .eq("employee_number", normalized_employee_number)
        .order("created_at", desc=True)
        .limit(limit)
        .execute()
    )
    return response.data or []


def find_tickets(identifier: str, *, limit: int = 5) -> list[dict]:
    """Find tickets by ticket ID or employee number."""

    normalized = identifier.strip().upper()
    if normalized.startswith("INC-"):
        ticket = get_ticket(normalized)
        return [ticket] if ticket else []
    return get_tickets_by_employee_number(normalized, limit=limit)


def add_comment(ticket_id: str, comment: str) -> dict | None:
    """Append a comment to an existing Supabase ticket."""

    ticket = get_ticket(ticket_id)
    if ticket is None:
        return None
    updated_comments = f"{ticket['comments']}\n{comment.strip()}"
    response = (
        get_supabase_client()
        .from_(TICKETS_TABLE_NAME)
        .update({"comments": updated_comments})
        .eq("id", ticket["id"])
        .execute()
    )
    return response.data[0] if response.data else get_ticket(ticket["id"])
