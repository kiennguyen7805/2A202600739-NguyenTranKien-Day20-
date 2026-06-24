from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        Synthesize a clear response with citations or source references.
        """
        if not state.research_notes:
            state.final_answer = "Error: Cannot write final report because research notes are missing."
            state.add_trace_event(self.name, {"status": "failed with missing research notes"})
            return state

        sources_text = ""
        for idx, doc in enumerate(state.sources):
            sources_text += f"Source {idx + 1}: {doc.title} (URL: {doc.url or 'None'})\n"

        system_prompt = (
            "You are a Writer Agent. Your job is to take raw research notes and structured analysis notes, "
            "and synthesize them into a highly polished, comprehensive, and well-structured report for the target audience.\n\n"
            "Guidelines:\n"
            "1. Directly and thoroughly answer the user request.\n"
            "2. Structure the report beautifully using markdown headings, lists, and emphasis.\n"
            "3. Ensure all claims are backed by source citations.\n"
            "4. Format citations as markdown hyperlinks referencing the source list index or title, for example: [Source Title](URL). If no URL is available, use [Source Title].\n"
            "5. Tailor the tone to the requested audience."
        )

        user_prompt = (
            f"User Request: {state.request.query}\n"
            f"Audience: {state.request.audience}\n\n"
            f"Research Notes:\n{state.research_notes}\n\n"
            f"Analysis Notes:\n{state.analysis_notes}\n\n"
            f"Available Sources:\n{sources_text}"
        )

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            state.final_answer = response.content
            state.add_trace_event(
                self.name,
                {
                    "status": "success",
                    "report_length": len(response.content),
                    "cost_usd": response.cost_usd or 0.0,
                }
            )
        except Exception as e:
            state.errors.append(f"Writer LLM call failed: {str(e)}")
            state.final_answer = f"Failed to synthesize final report due to error: {str(e)}"
            state.add_trace_event(self.name, {"status": "failed"})

        return state

