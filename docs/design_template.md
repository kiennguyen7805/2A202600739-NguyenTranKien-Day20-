# Design Template

## Problem

Xây dựng hệ thống trợ lý nghiên cứu tự động (Research Assistant) có khả năng nhận câu hỏi phức tạp từ người dùng, tìm kiếm nguồn thông tin thực tế trên web, phân tích đối chiếu các nguồn dữ liệu và tổng hợp thành một bài báo cáo khoa học hoàn chỉnh có nguồn trích dẫn đầy đủ dưới dạng Markdown.

## Why multi-agent?

Một tác nhân đơn lẻ (Single-Agent) thường gặp khó khăn lớn khi xử lý các tác vụ dài hơi và phức tạp:
1. **Dễ ảo giác (Hallucination)**: Do phải đảm nhận cả vai trò tìm kiếm, phân tích và viết báo cáo cùng lúc, mô hình dễ tự sinh thông tin không chính xác.
2. **Thiếu khả năng phản biện**: Single-Agent khó có thể tự đánh giá tính khách quan và kiểm chứng chéo giữa các tài liệu tìm thấy.
3. **Quá tải context**: Context window bị loãng khi nhồi nhét quá nhiều thông tin không lọc lọc.

Mô hình Multi-Agent giải quyết bằng cách chia nhỏ trách nhiệm (Separation of Concerns):
- **Researcher** chỉ tập trung tìm kiếm và ghi chú thông tin thô.
- **Analyst** tập trung phản biện và đối chiếu các thông tin nghiên cứu được.
- **Writer** tập trung trình bày mạch lạc và chèn nguồn trích dẫn chuẩn xác.
- **Supervisor** điều phối tổng thể và làm nhiệm vụ kiểm soát chất lượng (Quality Control).

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| **Supervisor** | Điều phối luồng chạy của hệ thống, quyết định agent nào chạy tiếp theo dựa trên trạng thái workspace hiện tại. | `ResearchState` (lịch sử chạy, các note hiện tại). | Tên agent tiếp theo (`researcher`, `analyst`, `writer`, `done`). | Vòng lặp vô hạn (khắc phục bằng giới hạn `max_iterations`). |
| **Researcher** | Lập câu hỏi tìm kiếm, thực hiện tìm kiếm web và biên soạn ghi chú nghiên cứu thô. | Truy vấn của người dùng, `tavily_api_key` hoặc Mock DB. | `state.sources`, `state.research_notes`. | Không tìm thấy nguồn tốt (khắc phục bằng Mock Search fallback). |
| **Analyst** | Phân tích ghi chú thô, đối chiếu thông tin trái chiều, đánh giá độ tin cậy và tìm lỗ hổng thông tin. | Ghi chú nghiên cứu thô `state.research_notes`. | Bản phân tích sâu `state.analysis_notes`. | Phân tích phiến diện (khắc phục bằng prompt định hướng phản biện). |
| **Writer** | Tổng hợp từ ghi chú nghiên cứu và ghi chú phân tích để viết báo cáo khoa học hoàn chỉnh có chứa các liên kết nguồn trích dẫn. | `research_notes`, `analysis_notes`, `sources`. | Báo cáo hoàn chỉnh `state.final_answer`. | Trích dẫn sai nguồn (khắc phục bằng prompt định dạng markdown nghiêm ngặt). |

## Shared state

Hệ thống sử dụng một lớp trạng thái dùng chung `ResearchState` lưu trữ trong suốt chu kỳ chạy:
- `request`: Chứa thông tin câu hỏi gốc, cấu hình số lượng nguồn tối đa (`max_sources`), và đối tượng người đọc (`audience`).
- `sources`: Danh sách tài liệu thô được tìm kiếm để hiển thị đường dẫn URL trích dẫn chính xác.
- `research_notes` & `analysis_notes`: Chứa kết quả trung gian của các bước nghiên cứu và phân tích để chuyển tiếp ngữ cảnh giữa các agent một cách rõ ràng.
- `final_answer`: Báo cáo khoa học hoàn chỉnh cuối cùng.
- `iteration` & `route_history`: Lưu vết các bước đã đi qua để Supervisor kiểm soát điều kiện dừng.
- `trace` & `errors`: Ghi lại chi tiết thời gian chạy, token cost của từng agent và danh sách lỗi để phục vụ benchmark & debug.

## Routing policy

```text
               User Query
                   |
                   v
           [supervisor_node] <----------------------+
                   |                                |
        (LLM Routing Decision)                      |
                   |                                |
       +-----------+-----------+                    |
       |           |           |                    |
       v           v           v                    |
  researcher    analyst     writer     done         |
       |           |           |         |          |
       v           v           v         v          |
   [run search] [analyze]   [write]   [__END__]     |
       |           |           |                    |
       +-----------+-----------+--------------------+
```
- Định tuyến động thông qua Supervisor bằng LLM kết hợp thuật toán rule-based fallback:
  - Nếu chưa có ghi chú nghiên cứu -> Chạy `researcher`.
  - Có ghi chú nghiên cứu nhưng chưa phân tích -> Chạy `analyst`.
  - Có cả nghiên cứu và phân tích nhưng chưa có bài viết hoàn chỉnh -> Chạy `writer`.
  - Đã có bài viết hoàn chỉnh và đạt yêu cầu -> Chạy `done` (kết thúc).

## Guardrails

- **Max iterations**: Giới hạn tối đa 6 vòng lặp để ngăn chặn việc hệ thống chạy vô hạn khi gặp câu hỏi khó hoặc LLM bị lặp định tuyến.
- **Timeout**: Áp dụng thời gian chờ (timeout) 60 giây đối với các API request ngoài.
- **Retry**: Thư viện `tenacity` tự động thử lại 3 lần với cơ chế exponential backoff khi gặp lỗi kết nối API.
- **Fallback**: Tự động chuyển sang Mock Search nếu kết nối Tavily bị lỗi; Tự động chuyển sang định tuyến cứng (rule-based) nếu LLM của Supervisor gặp sự cố.
- **Validation**: Pydantic tự động xác thực kiểu dữ liệu đầu vào và cấu trúc của `ResearchState`.

## Benchmark plan

- **Queries mẫu để kiểm tra**: "Research GraphRAG state-of-the-art", "Explain Multi-Agent System architectures".
- **Metrics đo lường**:
  - *Latency*: Thời gian hoàn thành tính bằng giây.
  - *Cost*: Chi phí sử dụng API tính bằng USD.
  - *Quality*: Thang điểm 0-10 đánh giá độ chuyên sâu và chính xác.
  - *Citations*: Số lượng nguồn thực tế được trích dẫn chính xác.
- **Kết quả kỳ vọng**: Hệ thống Multi-Agent sẽ có latency và cost cao hơn đáng kể so với Single-Agent (khoảng 3-5 lần), nhưng sẽ cho chất lượng thông tin sâu sắc hơn, độ tin cậy cao hơn và tỷ lệ ảo giác thấp hơn.
