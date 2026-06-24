from unittest.mock import MagicMock, patch
import pytest

from multi_agent_research_lab.agents.supervisor import SupervisorAgent
from multi_agent_research_lab.agents.researcher import ResearcherAgent
from multi_agent_research_lab.agents.analyst import AnalystAgent
from multi_agent_research_lab.agents.writer import WriterAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


@patch("multi_agent_research_lab.services.llm_client.OpenAI")
def test_supervisor_agent_routing(mock_openai) -> None:
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "researcher"
    mock_completion.usage.prompt_tokens = 10
    mock_completion.usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_completion

    state = ResearchState(request=ResearchQuery(query="Explain GraphRAG"))
    
    with patch.dict("os.environ", {"OPENAI_API_KEY": "mock-key"}):
        supervisor = SupervisorAgent()
        result = supervisor.run(state)
        assert result.route_history == ["researcher"]
        assert result.iteration == 1


@patch("multi_agent_research_lab.services.llm_client.OpenAI")
def test_researcher_agent_synthesis(mock_openai) -> None:
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_completion = MagicMock()
    mock_completion.choices = [MagicMock()]
    mock_completion.choices[0].message.content = "Research notes content."
    mock_completion.usage.prompt_tokens = 10
    mock_completion.usage.completion_tokens = 5
    mock_client.chat.completions.create.return_value = mock_completion

    state = ResearchState(request=ResearchQuery(query="Explain GraphRAG"))
    
    with patch.dict("os.environ", {"OPENAI_API_KEY": "mock-key"}):
        researcher = ResearcherAgent()
        result = researcher.run(state)
        # Using fallback mock search, so we should have sources
        assert len(result.sources) > 0
        assert result.research_notes == "Research notes content."
