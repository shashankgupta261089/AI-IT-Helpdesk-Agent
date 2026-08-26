import os
import re
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.tools import tool
from langchain_openai import ChatOpenAI

from mcp_tools import invoke_support_mcp_tool
from models import SupportRequest
from tools import check_system_status, search_helpdesk_knowledge


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env", encoding="utf-8-sig")

BASE_SYSTEM_PROMPT = """
You are an internal IT Helpdesk assistant for employees.

Rules:
- Use approved documentation when answering company-specific troubleshooting or policy questions.
- Search the knowledge base when troubleshooting information is needed.
- Check system status when outage information might matter.
- When the employee asks about tickets or provides a ticket ID or employee number for lookup, use the ticket lookup tool.
- Never create a support ticket or add a ticket comment unless the application explicitly says write actions are approved.
- Agent recommendation is not permission. Human approval is required before write actions.
- Do not invent company policy.
- Clearly say when approved documentation does not contain the answer.
- Give concise, practical next steps.
"""


def get_model() -> ChatOpenAI:
    """Create the chat model used throughout the capstone."""

    return ChatOpenAI(
        model=os.getenv("OPENAI_MODEL", "gpt-4.1-mini"),
        temperature=0,
    )


def triage_request(user_query: str) -> SupportRequest:
    """Convert free text into a validated SupportRequest object."""

    structured_model = get_model().with_structured_output(SupportRequest)
    return structured_model.invoke(
        [
            (
                "system",
                "Classify the employee helpdesk request. Use high severity for urgent blocked work or security risk.",
            ),
            ("human", user_query),
        ]
    )


def build_ticket_lookup_tool(employee_name: str, employee_number: str):
    """Create a sync LangChain tool that calls the MCP ticket lookup server."""

    @tool
    def find_support_tickets(identifier: str) -> str:
        """Find support tickets by ticket ID or employee ID for this employee only."""

        return invoke_support_mcp_tool(
            "find_support_tickets",
            {
                "identifier": identifier,
                "requester_employee_name": employee_name,
                "requester_employee_number": employee_number,
            },
        )

    return find_support_tickets


def create_helpdesk_agent(
    *,
    employee_name: str = "Employee",
    employee_number: str = "EMP-0001",
    allow_write_actions: bool = False,
):
    """Create the Session 22 agent with local tools plus approved MCP tools."""

    # The agent receives a sync wrapper tool. The wrapper calls MCP internally.
    ticket_lookup_tool = build_ticket_lookup_tool(employee_name, employee_number)
    approval_text = (
        "Write actions are approved for this turn."
        if allow_write_actions
        else "Write actions are not approved for this turn."
    )
    system_prompt = (
        BASE_SYSTEM_PROMPT
        + f"\nEmployee name for ticket actions: {employee_name}."
        + f"\nEmployee number for ticket actions: {employee_number}."
        + f"\n{approval_text}"
    )
    return create_agent(
        model=get_model(),
        tools=[search_helpdesk_knowledge, check_system_status, ticket_lookup_tool],
        system_prompt=system_prompt,
    )


def extract_final_text(agent_result: dict[str, Any]) -> str:
    """Pull the last assistant message text from a LangChain agent result."""

    messages = agent_result.get("messages", [])
    if not messages:
        return ""
    final_message = messages[-1]
    content = getattr(final_message, "content", final_message)
    if isinstance(content, list):
        return "\n".join(str(item) for item in content)
    return str(content)


def handle_support_request(
    user_query: str,
    *,
    employee_name: str = "Employee",
    employee_number: str = "EMP-0001",
    allow_write_actions: bool = False,
) -> dict[str, Any]:
    """Run the full Session 22 flow."""

    # First classify the request, then let the agent choose the right tools.
    triage = triage_request(user_query)
    agent = create_helpdesk_agent(
        employee_name=employee_name,
        employee_number=employee_number,
        allow_write_actions=allow_write_actions,
    )
    prompt = (
        f"Employee request: {user_query}\n\n"
        f"Triage result: {triage.model_dump()}\n\n"
        f"Write actions approved: {allow_write_actions}\n\n"
        "Help the employee using the available tools when useful. "
        "For ticket lookup requests, call the ticket lookup tool. "
        "The tool will deny access unless the employee name and Employee ID match the ticket owner."
    )
    result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
    return {"triage": triage, "response": extract_final_text(result), "raw": result}


def create_ticket_after_approval(
    *,
    employee_name: str,
    employee_number: str,
    original_query: str,
    triage: SupportRequest,
) -> str:
    """Create exactly one approved support ticket through MCP."""

    # This function is called only after the user clicks the approval button.
    ticket_result = invoke_support_mcp_tool(
        "create_support_ticket",
        {
            "employee_name": employee_name,
            "employee_number": employee_number,
            "category": triage.category,
            "priority": triage.severity,
            "summary": f"{triage.summary} Original request: {original_query}",
        },
    )
    ticket_match = re.search(r"\bINC-\d+\b", ticket_result)
    if ticket_match:
        return f"Ticket {ticket_match.group(0)} created successfully."
    return "Ticket created successfully."


def find_support_tickets(
    identifier: str,
    *,
    requester_employee_name: str,
    requester_employee_number: str,
) -> str:
    """Find support tickets by ticket ID or employee number through MCP."""

    return invoke_support_mcp_tool(
        "find_support_tickets",
        {
            "identifier": identifier,
            "requester_employee_name": requester_employee_name,
            "requester_employee_number": requester_employee_number,
        },
    )


def check_ticket_status(
    ticket_id: str,
    *,
    requester_employee_name: str,
    requester_employee_number: str,
) -> str:
    """Use the MCP ticket lookup tool through the agent."""

    return find_support_tickets(
        ticket_id,
        requester_employee_name=requester_employee_name,
        requester_employee_number=requester_employee_number,
    )
