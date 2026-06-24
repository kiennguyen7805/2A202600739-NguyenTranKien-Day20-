from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self) -> None:
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        Extract key claims, compare viewpoints, and flag weak evidence.
        """
        if not state.research_notes:
            state.analysis_notes = "No research notes were available to analyze."
            state.add_trace_event(self.name, {"status": "completed with no notes"})
            return state

        system_prompt = (
            "You are an Analyst Agent. Your job is to take raw research notes and analyze them. "
            "Perform the following structured analysis:\n"
            "1. **Key Claims & Findings**: Extract the central assertions, technologies, or findings.\n"
            "2. **Comparison of Viewpoints/Methodologies**: Highlight differing perspectives, approaches, or opinions.\n"
            "3. **Evidence Assessment**: Flag any weak evidence, potential biases, or gaps in the research notes.\n\n"
            "Present your analysis in a clear, structured markdown format. Reference the original sources (e.g., [Source 1], [Source 2]) if they were referenced in the research notes."
        )

        user_prompt = f"User Request: {state.request.query}\n\nResearch Notes to Analyze:\n{state.research_notes}"

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            state.analysis_notes = response.content
            state.add_trace_event(
                self.name,
                {
                    "status": "success",
                    "analysis_length": len(response.content),
                    "cost_usd": response.cost_usd or 0.0,
                }
            )
        except Exception as e:
            state.errors.append(f"Analyst LLM call failed: {str(e)}")
            state.analysis_notes = f"Failed to perform analysis due to error: {str(e)}"
            state.add_trace_event(self.name, {"status": "failed"})

        return state

