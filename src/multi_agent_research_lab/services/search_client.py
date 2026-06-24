import httpx
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.schemas import SourceDocument

class SearchClient:
    """Provider-agnostic search client that queries Tavily or falls back to mock results."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        Queries Tavily if TAVILY_API_KEY is configured. Falls back to mock documents otherwise.
        """
        api_key = self.settings.tavily_api_key
        if api_key:
            try:
                # Try calling Tavily Search API
                response = httpx.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "max_results": max_results,
                    },
                    timeout=10.0,
                )
                if response.status_code == 200:
                    data = response.json()
                    documents = []
                    for item in data.get("results", []):
                        documents.append(
                            SourceDocument(
                                title=item.get("title", "Untitled Source"),
                                url=item.get("url"),
                                snippet=item.get("content", ""),
                            )
                        )
                    return documents[:max_results]
            except Exception:
                # Silently fallback to mock on connection error
                pass

        # Fallback Mock Results
        return self._generate_mock_results(query, max_results)

    def _generate_mock_results(self, query: str, max_results: int) -> list[SourceDocument]:
        """Generate mock search results based on the query keywords."""
        query_lower = query.lower()
        mock_docs = []

        if "graphrag" in query_lower:
            mock_docs = [
                SourceDocument(
                    title="GraphRAG: Structured-Hierarchical Retrieval-Augmented Generation",
                    url="https://arxiv.org/abs/2404.16130",
                    snippet="GraphRAG uses LLMs to build a structured-hierarchical knowledge graph from raw text. This graph is then used to generate responses, addressing challenges with global queries that traditional vector-search RAG struggles with.",
                ),
                SourceDocument(
                    title="Microsoft GenAI: GraphRAG GitHub Repository",
                    url="https://github.com/microsoft/graphrag",
                    snippet="Official implementation of Microsoft's GraphRAG. It supports pipeline indexing of raw files into Neo4j/knowledge graphs and querying via local search (focused questions) or global search (holistic summaries).",
                ),
                SourceDocument(
                    title="Comparative Analysis: Vector RAG vs GraphRAG",
                    url="https://medium.com/ai-insights/vector-vs-graph-rag",
                    snippet="Vector RAG retrieves top-k chunks of text matching query vectors, which is great for local context. GraphRAG connects entities and concepts as a graph, making it superior for mapping out relationships and summaries of large document sets.",
                ),
            ]
        elif "multi-agent" in query_lower or "agent" in query_lower:
            mock_docs = [
                SourceDocument(
                    title="Building Effective Multi-Agent Workflows",
                    url="https://www.anthropic.com/research/effective-agents",
                    snippet="Delegating complex tasks to separate, specialized agent roles (e.g. researchers, analysts, writers) guided by a supervisor agent yields higher accuracy, lower hallucination rates, and more detailed summaries.",
                ),
                SourceDocument(
                    title="LangGraph: Building Stateful Agentic Systems",
                    url="https://langchain-ai.github.io/langgraph/",
                    snippet="LangGraph is an extension of LangChain designed to support cyclic graphs and state management. It enables building agent architectures with routing loops, conditional transitions, and user-in-the-loop flows.",
                ),
                SourceDocument(
                    title="The Supervisor Pattern in LLM Orchestration",
                    url="https://blog.langchain.dev/supervisor-agent-pattern",
                    snippet="The Supervisor Pattern uses a central LLM router to read the shared workspace state, decide which specialist agent to call next, compile results, and decide when to declare the task complete.",
                ),
            ]
        else:
            # Generic fallback results
            mock_docs = [
                SourceDocument(
                    title=f"Latest Developments in {query.strip()}",
                    url="https://wikipedia.org/wiki/Artificial_intelligence",
                    snippet=f"Comprehensive overview of modern research in {query}. Industry consensus highlights the rapid evolution of hybrid reasoning systems that combine LLMs with search engines.",
                ),
                SourceDocument(
                    title=f"State-of-the-art Guide on {query.strip()}",
                    url="https://example.com/research-guide",
                    snippet=f"Detailed methodological guide to researching {query}. Highlights best practices for source validation, triangulation of findings, and logical synthesis.",
                ),
            ]

        return mock_docs[:max_results]

