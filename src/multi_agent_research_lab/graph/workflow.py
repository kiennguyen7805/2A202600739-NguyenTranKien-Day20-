from langgraph.graph import StateGraph, END
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def build(self) -> object:
        """Create a LangGraph graph.

        Implement nodes, edges, conditional routing, and stop condition.
        Suggested nodes: supervisor, researcher, analyst, writer, optional critic.
        """
        supervisor = SupervisorAgent()
        researcher = ResearcherAgent()
        analyst = AnalystAgent()
        writer = WriterAgent()

        # Node functions that execute agents and return updated state
        def supervisor_node(state: ResearchState) -> ResearchState:
            return supervisor.run(state)

        def researcher_node(state: ResearchState) -> ResearchState:
            return researcher.run(state)

        def analyst_node(state: ResearchState) -> ResearchState:
            return analyst.run(state)

        def writer_node(state: ResearchState) -> ResearchState:
            return writer.run(state)

        # Create StateGraph passing Pydantic schema
        builder = StateGraph(ResearchState)

        # Add Nodes
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("researcher", researcher_node)
        builder.add_node("analyst", analyst_node)
        builder.add_node("writer", writer_node)

        # Entry point is supervisor
        builder.set_entry_point("supervisor")

        # Routing decision logic
        def route_decision(state: ResearchState) -> str:
            if not state.route_history:
                return "supervisor"
            last_route = state.route_history[-1]
            if last_route == "done":
                return END
            return last_route

        # Add conditional edges from supervisor
        builder.add_conditional_edges(
            "supervisor",
            route_decision,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
                END: END
            }
        )

        # Workers always return to supervisor
        builder.add_edge("researcher", "supervisor")
        builder.add_edge("analyst", "supervisor")
        builder.add_edge("writer", "supervisor")

        return builder.compile()

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.

        Compile graph, invoke it, and convert result back to ResearchState.
        """
        graph = self.build()
        result = graph.invoke(state)
        if isinstance(result, dict):
            return ResearchState.model_validate(result)
        return result

