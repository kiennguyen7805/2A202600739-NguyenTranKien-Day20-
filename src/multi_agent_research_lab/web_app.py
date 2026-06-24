import streamlit as st
import time
import os
import re
from multi_agent_research_lab.core.schemas import ResearchQuery, SourceDocument
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.core.config import get_settings

# Configure Page aesthetics
st.set_page_config(
    page_title="Multi-Agent Research Lab UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling
st.markdown("""
<style>
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stButton>button {
        background-color: #238636;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 8px 16px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        border: none;
    }
    .metric-card {
        background-color: #161b22;
        border: 1px solid #30363d;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        margin-bottom: 10px;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #58a6ff;
    }
    .metric-label {
        font-size: 12px;
        color: #8b949e;
        text-transform: uppercase;
        margin-top: 5px;
    }
</style>
""", unsafe_allow_html=True)

st.title("🧬 Multi-Agent Research System Lab")
st.markdown("Hệ thống trợ lý nghiên cứu đa tác nhân chạy trên đồ thị trạng thái LangGraph.")

# Load settings
settings = get_settings()

# Sidebar configuration
st.sidebar.header("⚙️ Cấu hình hệ thống")
if not settings.openai_api_key:
    st.sidebar.error("❌ Chưa cấu hình OPENAI_API_KEY trong file .env!")
else:
    st.sidebar.success("✅ Đã kết nối LLM API Key")

model_choice = st.sidebar.text_input("LLM Model", value=settings.openai_model)
max_iter = st.sidebar.slider("Số lượt chạy tối đa (Max Iterations)", 2, 10, value=settings.max_iterations)
audience = st.sidebar.selectbox("Đối tượng độc giả", ["technical learners", "general public", "academic researchers", "executives"])

st.sidebar.markdown("---")
st.sidebar.markdown("### 👩‍💻 Các Agent tham gia:")
st.sidebar.markdown("- **Supervisor**: Điều phối và định tuyến thông minh.")
st.sidebar.markdown("- **Researcher**: Tìm kiếm thông tin & ghi chú thô.")
st.sidebar.markdown("- **Analyst**: Phân tích, so sánh & phản biện.")
st.sidebar.markdown("- **Writer**: Viết báo cáo khoa học & chèn trích dẫn.")

# Input Query Form
st.subheader("🔍 Đặt câu hỏi nghiên cứu của bạn")
query_input = st.text_area(
    "Nhập chủ đề hoặc câu hỏi nghiên cứu của bạn dưới đây:",
    value="Research GraphRAG state-of-the-art and write a 300-word summary",
    height=80
)

col1, col2 = st.columns(2)
with col1:
    run_baseline = st.button("🚀 Chạy Single-Agent Baseline")
with col2:
    run_multi = st.button("⚡ Chạy Multi-Agent Workflow")

# Result container
if run_baseline or run_multi:
    if not settings.openai_api_key:
        st.error("Vui lòng cấu hình API Key trong file .env trước khi chạy!")
    else:
        request = ResearchQuery(query=query_input, max_sources=5, audience=audience)
        state = ResearchState(request=request)
        
        # Placeholder for progress
        progress_bar = st.progress(0)
        status_text = st.empty()
        log_container = st.container()
        
        start_time = time.perf_counter()
        
        if run_baseline:
            status_text.info("Đang chạy Single-Agent Baseline...")
            progress_bar.progress(30)
            
            client = LLMClient()
            try:
                response = client.complete(
                    system_prompt="You are a helpful research assistant. Write a comprehensive, detailed, and well-structured report answering the query.",
                    user_prompt=query_input,
                )
                progress_bar.progress(100)
                status_text.success("Hoàn thành Single-Agent Baseline!")
                latency = time.perf_counter() - start_time
                
                # Display output
                st.subheader("📝 Báo cáo kết quả (Single-Agent Baseline):")
                st.markdown(response.content)
                
                # Metrics Cards
                st.markdown("### 📊 Chỉ số đo lường (Metrics):")
                m_col1, m_col2, m_col3 = st.columns(3)
                with m_col1:
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{latency:.2f}s</div><div class="metric-label">Thời gian phản hồi</div></div>', unsafe_allow_html=True)
                with m_col2:
                    cost_val = f"${response.cost_usd:.5f}" if response.cost_usd else "N/A"
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{cost_val}</div><div class="metric-label">Chi phí ước tính</div></div>', unsafe_allow_html=True)
                with m_col3:
                    st.markdown(f'<div class="metric-card"><div class="metric-value">0</div><div class="metric-label">Nguồn trích dẫn thực tế</div></div>', unsafe_allow_html=True)
                    
            except Exception as e:
                st.error(f"Lỗi: {e}")
                
        elif run_multi:
            status_text.info("Khởi động LangGraph Multi-Agent Workflow...")
            progress_bar.progress(10)
            
            workflow = MultiAgentWorkflow()
            graph = workflow.build()
            
            with log_container:
                st.markdown("### 🤖 Nhật ký luồng chạy thực tế (Agent Logs):")
                
            # Stream graph execution
            try:
                current_state = state
                steps_count = 0
                
                # Setup generator for streaming
                for event in graph.stream(current_state):
                    for node, node_state in event.items():
                        steps_count += 1
                        progress_val = min(15 + steps_count * 15, 90)
                        progress_bar.progress(progress_val)
                        
                        # Display step info
                        with log_container:
                            with st.expander(f"🔹 Bước {steps_count}: Tác nhân `{node.upper()}` hoạt động", expanded=True):
                                if node == "supervisor":
                                    routes = node_state.route_history
                                    if routes:
                                        st.write(f"Supervisor phân tích trạng thái và định tuyến tiếp theo: **{routes[-1]}**")
                                elif node == "researcher":
                                    st.write(f"Researcher đã tìm kiếm tài liệu và ghi chú thô.")
                                    st.write(f"- Số nguồn đã lấy: `{len(node_state.sources)}` nguồn.")
                                elif node == "analyst":
                                    st.write("Analyst đã đối chiếu các ghi chú nghiên cứu và đưa ra phân tích chuyên sâu.")
                                elif node == "writer":
                                    st.write("Writer đã tổng hợp báo cáo và định dạng các trích dẫn nguồn.")
                        
                        current_state = node_state
                
                progress_bar.progress(100)
                status_text.success("Hoàn thành Multi-Agent Workflow!")
                latency = time.perf_counter() - start_time
                
                # Display output
                st.subheader("📝 Báo cáo nghiên cứu khoa học cuối cùng (Multi-Agent Report):")
                st.markdown(current_state.final_answer or "Không có kết quả trả về.")
                
                # Calculate cost from trace
                estimated_cost = 0.0
                for event in current_state.trace:
                    payload = event.get("payload", {})
                    if isinstance(payload, dict):
                        estimated_cost += payload.get("cost_usd", 0.0) or 0.0
                
                # Count citations
                citation_count = 0
                if current_state.final_answer:
                    citations = re.findall(r'\[Source \d+\]|\[\d+\]|\[.*?\]\(https?://.*?\)', current_state.final_answer)
                    citation_count = len(set(citations))

                # Metrics Cards
                st.markdown("### 📊 Chỉ số đo lường (Metrics):")
                m_col1, m_col2, m_col3, m_col4 = st.columns(4)
                with m_col1:
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{latency:.2f}s</div><div class="metric-label">Thời gian phản hồi</div></div>', unsafe_allow_html=True)
                with m_col2:
                    cost_val = f"${estimated_cost:.5f}" if estimated_cost > 0.0 else "N/A"
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{cost_val}</div><div class="metric-label">Chi phí ước tính</div></div>', unsafe_allow_html=True)
                with m_col3:
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{citation_count}</div><div class="metric-label">Nguồn trích dẫn thực tế</div></div>', unsafe_allow_html=True)
                with m_col4:
                    st.markdown(f'<div class="metric-card"><div class="metric-value">{current_state.iteration}</div><div class="metric-label">Số lượt chuyển tiếp (Steps)</div></div>', unsafe_allow_html=True)
                
                # Sidebar detailing state variables
                st.sidebar.markdown("---")
                st.sidebar.markdown("### 🔎 Chi tiết trạng thái (ResearchState):")
                st.sidebar.markdown(f"**Lịch sử định tuyến**: `{current_state.route_history}`")
                
                with st.sidebar.expander("📚 Xem danh sách nguồn (Sources list)"):
                    for idx, src in enumerate(current_state.sources):
                        st.markdown(f"**[{idx+1}] {src.title}**")
                        st.caption(f"URL: {src.url}")
                        st.markdown(f"*{src.snippet[:100]}...*")
                
                with st.sidebar.expander("📝 Xem ghi chú nghiên cứu (Research Notes)"):
                    st.write(current_state.research_notes)
                    
                with st.sidebar.expander("⚖️ Xem phân tích phản biện (Analysis Notes)"):
                    st.write(current_state.analysis_notes)
                    
            except Exception as e:
                st.error(f"Gặp lỗi khi chạy luồng đồ thị: {e}")
                st.exception(e)
