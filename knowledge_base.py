import os
from pathlib import Path

from dotenv import load_dotenv
from langchain_community.vectorstores import SupabaseVectorStore
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from supabase.client import Client, create_client


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

load_dotenv(BASE_DIR / ".env", encoding="utf-8-sig")

CATEGORY_BY_FILE = {
    "vpn_guide.md": "vpn",
    "password_reset.md": "password",
    "outlook_troubleshooting.md": "outlook",
    "wifi_troubleshooting.md": "wifi",
    "access_policy.md": "access",
}


def load_knowledge_documents(data_dir: Path = DATA_DIR) -> list[Document]:
    """Load the fictional internal helpdesk documents."""

    documents: list[Document] = []
    for path in sorted(data_dir.glob("*.md")):
        documents.append(
            Document(
                page_content=path.read_text(encoding="utf-8"),
                metadata={
                    "source": path.name,
                    "category": CATEGORY_BY_FILE.get(path.name, "other"),
                },
            )
        )
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    """Split documents into chunks that fit comfortably inside tool results."""

    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=120)
    chunks = splitter.split_documents(documents)
    for index, chunk in enumerate(chunks):
        source = chunk.metadata.get("source", "document")
        chunk_id = f"helpdesk-{Path(source).stem}-{index}"
        chunk.id = chunk_id
        chunk.metadata["chunk_id"] = chunk_id
    return chunks


def get_supabase_client() -> Client:
    """Create the Supabase client used by the vector store."""

    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = (
        os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        or os.getenv("SUPABASE_SERVICE_KEY")
        or os.getenv("SUPABASE_SECRET_KEY")
    )
    if not supabase_url or not supabase_key:
        raise RuntimeError(
            "Supabase RAG is not configured. Add SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY to App/.env, then run setup_supabase.sql "
            "in the Supabase SQL editor."
        )
    return create_client(supabase_url, supabase_key)


def create_vector_store() -> SupabaseVectorStore:
    """Create a LangChain Supabase vector store."""

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    return SupabaseVectorStore(
        client=get_supabase_client(),
        embedding=embeddings,
        table_name=os.getenv("SUPABASE_TABLE_NAME", "documents"),
        query_name=os.getenv("SUPABASE_QUERY_NAME", "match_documents"),
        chunk_size=500,
    )


def clear_knowledge_base() -> None:
    """Delete old demo helpdesk chunks before inserting a fresh class dataset."""

    table_name = os.getenv("SUPABASE_TABLE_NAME", "documents")
    try:
        get_supabase_client().from_(table_name).delete().like("id", "helpdesk-%").execute()
    except Exception as exc:
        raise RuntimeError(
            "Could not clear existing Supabase RAG rows. Confirm setup_supabase.sql "
            "has been run and the service role key is configured."
        ) from exc


def seed_knowledge_base(*, clear_existing: bool = True) -> list[str]:
    """Clear old rows, then upsert local helpdesk documents with stable chunk IDs."""

    chunks = split_documents(load_knowledge_documents())
    vector_store = create_vector_store()
    if clear_existing:
        clear_knowledge_base()
    return vector_store.add_documents(chunks, ids=[chunk.id for chunk in chunks])


def build_retriever(k: int = 3):
    """Create a Supabase-backed vector retriever from the local knowledge base."""

    vector_store = create_vector_store()
    if os.getenv("SEED_SUPABASE_ON_STARTUP", "true").lower() in {"1", "true", "yes"}:
        seed_knowledge_base(clear_existing=True)
    return vector_store.as_retriever(search_kwargs={"k": k})
