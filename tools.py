from langchain.tools import tool

from knowledge_base import build_retriever


SYSTEM_STATUS = {
    "vpn": "operational",
    "email": "operational",
    "outlook": "operational",
    "wifi": "degraded",
    "password": "operational",
    "access": "operational",
}

_RETRIEVER = None


def get_retriever():
    """Build the retriever once per Python process."""

    global _RETRIEVER
    if _RETRIEVER is None:
        _RETRIEVER = build_retriever()
    return _RETRIEVER


@tool
def search_helpdesk_knowledge(query: str) -> str:
    """Search approved internal IT helpdesk documentation."""

    docs = get_retriever().invoke(query)
    if not docs:
        return "No approved helpdesk documentation was found."

    formatted_docs = []
    for doc in docs:
        source = doc.metadata.get("source", "unknown source")
        category = doc.metadata.get("category", "unknown")
        formatted_docs.append(
            f"Source: {source} | Category: {category}\n{doc.page_content}"
        )
    return "\n\n---\n\n".join(formatted_docs)


@tool
def check_system_status(service: str) -> str:
    """Check the current demo status for a company IT service."""

    normalized = service.strip().lower()
    status = SYSTEM_STATUS.get(normalized)
    if status is None:
        known = ", ".join(sorted(SYSTEM_STATUS))
        return f"Unknown service '{service}'. Known services: {known}."
    return f"{normalized} status: {status}"
