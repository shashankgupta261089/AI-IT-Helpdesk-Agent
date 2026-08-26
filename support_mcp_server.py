from fastmcp import FastMCP

from database import add_comment, create_ticket, find_tickets, get_ticket


mcp = FastMCP("ITSupportServer")


def normalize_employee_name(name: str) -> str:
    """Normalize employee names so casing and extra spaces do not matter."""

    return " ".join(name.strip().casefold().split())


def ticket_matches_employee(
    ticket: dict,
    *,
    requester_employee_name: str,
    requester_employee_number: str,
) -> bool:
    """Check whether the requester owns the ticket."""

    ticket_name = normalize_employee_name(ticket.get("employee_name", ""))
    requester_name = normalize_employee_name(requester_employee_name)
    ticket_number = ticket.get("employee_number", "").strip().upper()
    requester_number = requester_employee_number.strip().upper()
    return ticket_name == requester_name and ticket_number == requester_number


def format_ticket(ticket: dict) -> str:
    """Return the customer-safe ticket details."""

    return (
        f"Ticket {ticket['id']} is {ticket['status']}. "
        f"Priority: {ticket['priority']}. Summary: {ticket['summary']}"
    )


@mcp.tool
def create_support_ticket(
    employee_name: str,
    employee_number: str,
    category: str,
    priority: str,
    summary: str,
) -> str:
    """Create an IT support ticket after explicit user approval."""

    ticket = create_ticket(
        employee_name=employee_name,
        employee_number=employee_number,
        category=category,
        priority=priority,
        summary=summary,
    )
    return f"Ticket {ticket['id']} created successfully."


@mcp.tool
def get_ticket_status(
    ticket_id: str,
    requester_employee_name: str,
    requester_employee_number: str,
) -> str:
    """Look up ticket status only when requester details match the ticket."""

    ticket = get_ticket(ticket_id)
    if ticket is None:
        return f"No ticket was found for ID {ticket_id}."
    if not ticket_matches_employee(
        ticket,
        requester_employee_name=requester_employee_name,
        requester_employee_number=requester_employee_number,
    ):
        return (
            "I cannot share those ticket details because the employee name and "
            "Employee ID do not match the ticket owner."
        )
    return format_ticket(ticket)


@mcp.tool
def find_support_tickets(
    identifier: str,
    requester_employee_name: str,
    requester_employee_number: str,
) -> str:
    """Find tickets only for the matching employee name and Employee ID."""

    normalized_identifier = identifier.strip().upper()
    requester_number = requester_employee_number.strip().upper()

    if not normalized_identifier.startswith("INC-") and normalized_identifier != requester_number:
        return "I can only look up tickets for the signed-in employee."

    tickets = find_tickets(identifier)
    if not tickets:
        return f"No tickets were found for {identifier}."

    authorized_tickets = [
        ticket
        for ticket in tickets
        if ticket_matches_employee(
            ticket,
            requester_employee_name=requester_employee_name,
            requester_employee_number=requester_employee_number,
        )
    ]

    if not authorized_tickets:
        return (
            "I cannot share those ticket details because the employee name and "
            "Employee ID do not match the ticket owner."
        )

    return "\n".join(format_ticket(ticket) for ticket in authorized_tickets)


@mcp.tool
def add_ticket_comment(ticket_id: str, comment: str) -> str:
    """Add a comment to an existing support ticket after approval."""

    ticket = add_comment(ticket_id, comment)
    if ticket is None:
        return f"No ticket was found for ID {ticket_id}."
    return f"Comment added to ticket {ticket['id']}."


if __name__ == "__main__":
    mcp.run()
