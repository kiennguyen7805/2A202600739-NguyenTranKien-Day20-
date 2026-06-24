# Lab Guide: Multi-Agent Research System

## Scenario

Bạn cần xây dựng một research assistant có thể nhận câu hỏi dài, tìm thông tin, phân tích và viết câu trả lời cuối cùng. Lab yêu cầu so sánh hai cách làm:

1. **Single-agent baseline**: một agent làm toàn bộ.
2. **Multi-agent workflow**: Supervisor điều phối Researcher, Analyst, Writer.

## Quy tắc quan trọng

- Không thêm agent nếu không có lý do rõ ràng.
- Mỗi agent phải có responsibility riêng.
- Shared state phải đủ rõ để debug.
- Phải có trace hoặc log cho từng bước.
- Phải benchmark, không chỉ nhìn output bằng cảm tính.

## Milestone 1: Baseline

File gợi ý:

- `src/multi_agent_research_lab/cli.py`
- `src/multi_agent_research_lab/services/llm_client.py`

TODO(student): thay baseline placeholder bằng một call LLM thật.

## Milestone 2: Supervisor

File gợi ý:

- `src/multi_agent_research_lab/agents/supervisor.py`
- `src/multi_agent_research_lab/graph/workflow.py`

TODO(student): implement routing policy.

Gợi ý câu hỏi thiết kế:

- Khi nào gọi Researcher?
- Khi nào gọi Analyst?
- Khi nào gọi Writer?
- Khi nào stop?
- Nếu agent fail thì retry hay fallback?

## Milestone 3: Worker agents

File gợi ý:

- `agents/researcher.py`
- `agents/analyst.py`
- `agents/writer.py`

TODO(student): implement từng worker.

## Milestone 4: Trace và benchmark

File gợi ý:

- `observability/tracing.py`
- `evaluation/benchmark.py`
- `evaluation/report.py`

Benchmark tối thiểu:

| Metric | Cách đo gợi ý |
|---|---|
| Latency | wall-clock time |
| Cost | token usage hoặc provider usage |
| Quality | rubric 0-10 do peer review |
| Citation coverage | số claims có source / tổng claims chính |
| Failure rate | số query fail / tổng query |

## Exit ticket

Mỗi nhóm trả lời 2 câu:

1. **Case nào nên dùng multi-agent? Vì sao?**
   - **Trả lời**: Nên dùng trong các bài toán nghiên cứu sâu, viết tài liệu kỹ thuật, lập kế hoạch nhiều bước (multi-step planning), hay kiểm toán mã nguồn.
   - **Vì sao**: Vì các công việc này đòi hỏi sự phản biện độc lập, kiểm chứng chéo thông tin (triangulation), và có sự tách biệt rõ ràng giữa thu thập dữ liệu (Researcher), phản biện luận điểm (Analyst) và trình bày (Writer). Cách tiếp cận đa tác nhân làm giảm đáng kể hiện tượng ảo giác (hallucination) và nâng cao chất lượng/tính tin cậy của bài viết.

2. **Case nào không nên dùng multi-agent? Vì sao?**
   - **Trả lời**: Không nên dùng cho các câu hỏi tra cứu nhanh (Q&A đơn giản), tác vụ chuyển đổi dữ liệu nhanh, hoặc các ứng dụng nhạy cảm với thời gian phản hồi (chương trình chat thời gian thực).
   - **Vì sao**: Hệ thống Multi-Agent có độ trễ (latency) rất cao do phải gọi LLM nhiều lần tuần tự qua các node của đồ thị và chi phí token (cost) tích lũy lớn qua mỗi vòng lặp. Nó không tối ưu về mặt chi phí và tốc độ đối với các tác vụ đơn giản.

