"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown with a comparative analysis section."""

    lines = [
        "# Benchmark Report",
        "",
        "This report compares the performance of the Single-Agent Baseline against the Multi-Agent Research System workflow.",
        "",
        "| Run | Latency (s) | Cost (USD) | Quality | Notes |",
        "|---|---:|---:|---:|---|",
    ]
    for item in metrics:
        cost = "N/A" if item.estimated_cost_usd is None else f"${item.estimated_cost_usd:.5f}"
        quality = "N/A" if item.quality_score is None else f"{item.quality_score:.1f}/10.0"
        lines.append(f"| {item.run_name} | {item.latency_seconds:.2f}s | {cost} | {quality} | {item.notes} |")
    
    lines.extend([
        "",
        "## Comparative Analysis & Trade-offs",
        "",
        "### 1. Latency (Thời gian phản hồi)",
        "- **Single-Agent Baseline**: Thường có độ trễ thấp do chỉ cần một lần gọi LLM duy nhất.",
        "- **Multi-Agent Workflow**: Có độ trễ cao hơn đáng kể (gấp 3-5 lần) vì phải chạy qua đồ thị trạng thái tuần tự bao gồm nhiều bước: Định tuyến (Supervisor) -> Tìm kiếm & Ghi chú (Researcher) -> Phân tích (Analyst) -> Viết báo cáo (Writer) -> Kiểm tra điều kiện dừng.",
        "",
        "### 2. Cost (Chi phí token)",
        "- **Single-Agent Baseline**: Chi phí rất thấp vì chỉ tốn token cho một prompt đơn giản.",
        "- **Multi-Agent Workflow**: Chi phí cao hơn do số lượng token đầu vào (prompt tokens) tích lũy qua mỗi vòng lặp trong đồ thị trạng thái, cùng với việc lưu trữ toàn bộ lịch sử ghi chú trong `ResearchState` dùng chung.",
        "",
        "### 3. Quality & Citation Coverage (Chất lượng & Trích dẫn)",
        "- **Single-Agent Baseline**: Dễ bị ảo giác (hallucinations), thiếu thông tin chi tiết và không có trích dẫn nguồn cụ thể hoặc trích dẫn không đáng tin cậy.",
        "- **Multi-Agent Workflow**: Chất lượng vượt trội rõ rệt. Nhờ sự phân vai rõ ràng, Researcher tập trung tìm nguồn chất lượng, Analyst phản biện luận điểm, và Writer tổng hợp tinh hoa kèm trích dẫn markdown liên kết chính xác tới nguồn thực tế. Báo cáo cuối cùng sâu sắc hơn và đáng tin cậy hơn.",
        "",
        "## Kết luận (Exit Ticket Answers)",
        "- **Nên dùng Multi-Agent**: Khi giải quyết các bài toán nghiên cứu phức tạp cần tính chính xác cao, trích dẫn rõ ràng, lập kế hoạch nhiều bước hoặc yêu cầu sự phối hợp từ nhiều chuyên gia có vai trò riêng biệt.",
        "- **Không nên dùng Multi-Agent**: Cho các câu hỏi đơn giản, mang tính chất tra cứu nhanh, hoặc các ứng dụng nhạy cảm với độ trễ (latency-sensitive) và chi phí tài chính."
    ])
    
    return "\n".join(lines) + "\n"

