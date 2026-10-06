# AI IT Helpdesk Agent

End-to-End Agentic AI Capstone with LangChain, RAG, Pydantic, MCP and Streamlit

## Session 21 App

This is the full runnable app for Session 21. It includes everything from Session 20, then adds:

- FastMCP support-ticket tools over stdio
- LangChain MCP adapter integration
- Human approval before ticket creation
- Supabase-backed support ticket table
- Ticket creation and protected lookup by ticket ID or employee ID
- LangSmith tracing configuration

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
```

On macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Run `setup_supabase.sql` once in the Supabase SQL Editor before using RAG or ticket actions.

## Environment

Set these in `.env`:

```text
OPENAI_API_KEY=your-key-here
OPENAI_MODEL=gpt-4.1-mini
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key
SUPABASE_TABLE_NAME=documents
SUPABASE_QUERY_NAME=match_documents
SUPABASE_TICKETS_TABLE_NAME=support_tickets
SEED_SUPABASE_ON_STARTUP=true
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=your-langsmith-key-here
LANGSMITH_PROJECT="AI Help Desk Agent"
```

## Run

From the project root:

```bash
streamlit run App/app.py
```

Or from this `App` folder:

```bash
streamlit run app.py
```

The app launches the local stdio MCP server automatically through `sys.executable` and the project-relative `App/support_mcp_server.py` path. No Codex MCP config or separate MCP deployment is required; Streamlit calls the MCP tools directly through the app code.

Ticket lookup is protected in the app MCP server. Ticket details are returned only when the employee name and Employee ID match the ticket owner.

If the deployed app says `support_tickets` is not available, MCP is running but Supabase table access is failing. Check Streamlit Cloud Secrets for `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and `SUPABASE_TICKETS_TABLE_NAME`, then confirm `setup_supabase.sql` was run in that same Supabase project.

## MCP Testing

From the project root:

Inspector UI:

```bash
npx -y @modelcontextprotocol/inspector python App/support_mcp_server.py
```

Inspector CLI:

```bash
npx -y @modelcontextprotocol/inspector --cli python App/support_mcp_server.py --method tools/list
```

Windows PowerShell fallback:

```bash
cmd /c npx -y @modelcontextprotocol/inspector --cli python App\support_mcp_server.py --method tools/list
```

## Deployment

Use the project-level `STREAMLIT_CLOUD_DEPLOYMENT_GUIDE.md`.
