# System Architecture

The following diagram represents the core architecture and data flow of the AAROGYA Rural Healthcare Companion.

```mermaid
graph TD
    Telegram[Telegram Bot Client] <-->|Voice, Image, Messages| API[FastAPI Backend Gateway]
    NextJS[Next.js Dashboard UI] <-->|HTTP REST / JWT| API
    
    API <-->|AI StateGraph| Agent[LangGraph Agent Layer]
    Agent <-->|JSON Tools Schema| MCP[MCP Tool Layer]
    Agent <-->|Inference| Gemini[Gemini LLM API]
    
    API <-->|SQLAlchemy ORM| DB[(PostgreSQL Database)]
    API <-->|Task Broker| Redis[(Redis Message Broker)]
    Redis <-->|Background Jobs| Celery[Celery Async Workers]
    Celery <-->|DB Writes / Sync| DB
```

---

## Technology Stack

### Frontend
- **Next.js**: Single Page React framework for high-performance dashboard layouts.
- **TypeScript**: Strictly typed development.
- **TailwindCSS**: Premium responsive utilities and custom light healthcare color scheme.
- **Lucide Icons**: Modern high-fidelity interface assets.
- **Framer Motion**: Micro-animations and layout transitions.

### Backend
- **FastAPI**: Modern, high-performance web framework for Python.
- **SQLAlchemy**: Python SQL toolkit and Object Relational Mapper (ORM).
- **PostgreSQL**: Robust persistent relational database.
- **Redis**: Fast caching store and celery message broker.
- **Celery**: Distributed asynchronous task execution queue.

### AI Engine
- **Gemini**: Vision, OCR extraction, audio translation, and natural language explanations.
- **LangGraph**: Structured multi-agent workflow routing and conversational state management.

### Communication & Protocol
- **Telegram Bot API**: End-user messaging interface.
- **Model Context Protocol (MCP)**: Standardized schemas mapping clinical APIs directly to autonomous agent intents.
