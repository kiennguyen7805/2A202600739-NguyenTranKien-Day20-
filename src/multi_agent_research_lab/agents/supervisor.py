from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.services.llm_client import LLMClient


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self) -> None:
        self.settings = get_settings()
        self.llm_client = LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        Suggested steps:
        - Inspect request, current notes, and missing fields.
        - Choose one of: researcher, analyst, writer, done.
        - Enforce max iterations and failure fallback.
        """
        # Guardrail: Check max iterations
        if state.iteration >= self.settings.max_iterations:
            # Force Done or Writer if no final answer yet
            chosen_route = "writer" if not state.final_answer else "done"
            state.record_route(chosen_route)
            state.add_trace_event(
                self.name,
                {"action": f"Forced route to {chosen_route} due to max iterations", "iteration": state.iteration}
            )
            return state

        system_prompt = """You are the Supervisor Agent of a Multi-Agent Research System.
Your job is to orchestrate the workflow between specialized worker agents:
1. 'researcher': Runs search queries and compiles raw research notes with sources.
2. 'analyst': Analyzes the researcher's notes, compares view points, and highlights critical insights.
3. 'writer': Takes the research and analysis notes and synthesizes the final comprehensive report with citations.
4. 'done': Signals that the final answer is complete, accurate, and of high quality, ending the loop.

Determine the next step for this query. You must output ONLY one word from this list: ['researcher', 'analyst', 'writer', 'done']. Do not write anything else.

Guidelines:
- If we do not have search sources or research notes, route to 'researcher'.
- If we have research notes but do NOT have analysis notes, route to 'analyst'.
- If we have both research and analysis notes but do NOT have a final answer (or the final answer needs revision), route to 'writer'.
- If the final answer is complete, detailed, and directly answers the user's query, route to 'done'.
"""

        user_prompt = f"""User Query: {state.request.query}
Current Iteration: {state.iteration}
Has Research Notes: {state.research_notes is not None}
Has Analysis Notes: {state.analysis_notes is not None}
Has Final Answer: {state.final_answer is not None}

Workspace State:
---
[Research Notes]:
{state.research_notes or "Empty"}
---
[Analysis Notes]:
{state.analysis_notes or "Empty"}
---
[Final Answer]:
{state.final_answer or "Empty"}
"""

        try:
            response = self.llm_client.complete(system_prompt, user_prompt)
            chosen_route = response.content.strip().lower()
            cost = response.cost_usd or 0.0
        except Exception as e:
            # Fallback to rule-based decision on LLM failure
            state.errors.append(f"Supervisor LLM call failed: {str(e)}")
            chosen_route = "fallback"
            cost = 0.0

        # Validate the route
        valid_routes = ["researcher", "analyst", "writer", "done"]
        if chosen_route not in valid_routes:
            # Rule-based fallback logic
            if not state.research_notes:
                chosen_route = "researcher"
            elif not state.analysis_notes:
                chosen_route = "analyst"
            elif not state.final_answer:
                chosen_route = "writer"
            else:
                chosen_route = "done"

        state.record_route(chosen_route)
        state.add_trace_event(
            self.name,
            {"action": f"Routed to {chosen_route}", "iteration": state.iteration, "cost_usd": cost}
        )
        return state

