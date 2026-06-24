from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self) -> None:
        self.llm_client = LLMClient()
        self.search_client = SearchClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        Implement search, source filtering, citation capture, and notes.
        """
        # Step 1: Generate search queries using LLM
        system_prompt_query = (
            "You are a search query generator. Based on the user's research request, "
            "generate up to 2 distinct search queries (one per line) to find the most relevant "
            "and factual information on the web. Do not include any numbers, symbols, or extra text."
        )
        user_prompt_query = f"User Request: {state.request.query}"
        
        queries = [state.request.query]  # Default to original query
        try:
            response = self.llm_client.complete(system_prompt_query, user_prompt_query)
            llm_queries = [q.strip() for q in response.content.split("\n") if q.strip()]
            if llm_queries:
                queries = llm_queries[:2]
        except Exception as e:
            state.errors.append(f"Researcher failed to generate search queries: {str(e)}")

        # Step 2: Execute search queries
        new_sources = []
        for q in queries:
            try:
                results = self.search_client.search(q, max_results=state.request.max_sources)
                new_sources.extend(results)
            except Exception as e:
                state.errors.append(f"Search query '{q}' failed: {str(e)}")

        # Step 3: De-duplicate sources (by URL or title if URL is None)
        seen_urls = set()
        seen_titles = set()
        unique_sources = list(state.sources)  # Keep existing sources if any
        
        # Populate seen sets with existing sources
        for src in unique_sources:
            if src.url:
                seen_urls.add(src.url)
            seen_titles.add(src.title.lower().strip())

        for src in new_sources:
            url_key = src.url
            title_key = src.title.lower().strip()
            if url_key and url_key in seen_urls:
                continue
            if title_key in seen_titles:
                continue
            
            if url_key:
                seen_urls.add(url_key)
            seen_titles.add(title_key)
            unique_sources.append(src)

        # Enforce max sources limit from request
        state.sources = unique_sources[:state.request.max_sources]

        # Step 4: Synthesize search results into structured research notes
        if not state.sources:
            state.research_notes = "No search sources were retrieved. Failed to collect research notes."
            state.add_trace_event(self.name, {"status": "completed with no sources"})
            return state

        sources_text = ""
        for idx, doc in enumerate(state.sources):
            sources_text += f"Source [{idx + 1}]:\nTitle: {doc.title}\nURL: {doc.url}\nSnippet: {doc.snippet}\n\n"

        system_prompt_synthesis = (
            "You are a Research Assistant. Your task is to analyze the provided search sources "
            "and compile raw, factual, and structured research notes answering the user request.\n"
            "Include key facts, concepts, definitions, and technical details.\n"
            "You MUST cite your sources in the text using [Source 1], [Source 2], etc. corresponding "
            "to the sources listed in the prompt. Do not write the final report, just compile the notes."
        )
        user_prompt_synthesis = f"User Request: {state.request.query}\n\nRetrieved Search Results:\n{sources_text}"

        try:
            response = self.llm_client.complete(system_prompt_synthesis, user_prompt_synthesis)
            state.research_notes = response.content
            state.add_trace_event(
                self.name,
                {
                    "status": "success",
                    "sources_count": len(state.sources),
                    "notes_length": len(response.content),
                    "cost_usd": response.cost_usd or 0.0,
                }
            )
        except Exception as e:
            state.errors.append(f"Research synthesis LLM call failed: {str(e)}")
            state.research_notes = f"Failed to synthesize research notes due to error: {str(e)}"
            state.add_trace_event(self.name, {"status": "failed"})

        return state

