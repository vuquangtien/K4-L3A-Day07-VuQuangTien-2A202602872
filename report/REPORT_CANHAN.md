# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Vũ Quang Tiến
**Nhóm:** YBY1
**Ngày:** 19/09/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding trỏ gần cùng hướng trong không gian vector, nên hai đoạn văn bản có ý nghĩa gần nhau dù có thể không dùng cùng từ vựng. Với text embedding, điểm càng gần 1 thì nội dung càng tương đồng về nghĩa.

**Ví dụ có độ tương tự CAO:**
- Câu A: Sinh viên cần nộp học phí trước thời hạn của học kỳ.
- Câu B: Người học phải thanh toán khoản phí đào tạo đúng hạn mỗi kỳ.
- Tại sao tương đồng: Hai câu dùng từ khác nhau nhưng cùng nói về nghĩa vụ đóng học phí đúng hạn.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Sinh viên cần nộp học phí trước thời hạn của học kỳ.
- Câu B: Thư viện bổ sung cơ sở dữ liệu sách điện tử mới.
- Tại sao khác: Hai câu nói về hai chủ đề khác nhau: học phí và dịch vụ thư viện.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity tập trung vào hướng của vector, tức là mẫu ý nghĩa của văn bản, thay vì độ lớn tuyệt đối của vector. Với text embeddings thường được chuẩn hóa, cosine ổn định hơn khoảng cách Euclid và dot product trên vector chuẩn hóa cũng tương đương cosine.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((10000 - 50) / (500 - 50)) = ceil(9950 / 450) = ceil(22.11) = 23`.
> *Đáp án:* 23 chunks. Kiểm tra bằng `FixedSizeChunker(chunk_size=500, overlap=50).chunk('a' * 10000)` cũng trả về 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi `overlap=100`, số chunk là `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = 25`, nên số chunk tăng từ 23 lên 25. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới giữa hai chunk, nhưng đổi lại làm tăng số chunk, dung lượng lưu trữ và chi phí embedding/search.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])(?:\s+|\n+)` để tách tại vị trí sau dấu kết thúc câu mà vẫn giữ lại dấu câu trong kết quả. Sau đó tôi strip khoảng trắng thừa và gom mỗi `max_sentences_per_chunk` câu thành một chunk; text rỗng trả về `[]`. Edge case còn hạn chế là chữ viết tắt như `TS.`, `v.v.` và số thập phân có thể bị tách sai vì regex hiện tại chưa hiểu ngữ cảnh ngôn ngữ.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Tôi thử tách theo thứ tự separator từ lớn đến nhỏ: đoạn văn, dòng, câu, từ, rồi ký tự/kích thước cố định. Nếu một mảnh vẫn dài hơn `chunk_size`, `_split` gọi đệ quy với danh sách separator còn lại; nếu các mảnh nhỏ thì gom ngược lại cho đến gần `chunk_size` để tránh tạo quá nhiều chunk vụn. Base case là text rỗng, text đã ngắn hơn `chunk_size`, hoặc hết separator thì fallback sang cắt theo kích thước cố định.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Tôi dùng store in-memory: mỗi `Document` được chuẩn hóa thành một record gồm `id`, `content`, bản sao `metadata`, và `embedding`. `add_documents` không tự chunk; mỗi `Document` đầu vào tương ứng một record, còn việc tách chunk nằm ở tầng ngoài. Khi search, tôi embed query rồi tính dot product với embedding của từng record; vì vector mock đã chuẩn hóa nên dot product tương đương cosine similarity.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc metadata trước rồi mới chạy similarity search trên tập ứng viên đã lọc, để tránh trường hợp top-k bị chiếm bởi tài liệu sai metadata. `delete_document` xóa tất cả record có `metadata["doc_id"]` khớp với `doc_id` cần xóa và trả `True` nếu có ít nhất một record bị xóa, ngược lại trả `False`.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> `answer` chạy retrieval top-k từ `EmbeddingStore`, đánh số từng chunk dạng `[1]`, `[2]`, `[3]` kèm source và score, rồi đưa toàn bộ context vào prompt. Prompt yêu cầu LLM chỉ dùng ngữ cảnh được cung cấp, trích dẫn số chunk khi trả lời, và nói rõ nếu không tìm thấy thông tin thay vì bịa. Nếu store rỗng hoặc không có kết quả, agent trả thông báo không tìm thấy và không gọi LLM vô ích.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
============================= test session starts ==============================
platform linux -- Python 3.13.5, pytest-9.1.1, pluggy-1.6.0 -- /home/tien/K4-L3A-Data-Foundations/.venv/bin/python
cachedir: .pytest_cache
rootdir: /home/tien/K4-L3A-Data-Foundations
collecting ... collected 42 items

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED    [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED   [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED [100%]

============================== 42 passed in 0.06s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Sinh viên cần thanh toán học phí đúng hạn. | Người học phải nộp khoản phí đào tạo trước hạn. | cao | 0.668 | Đúng |
| 2 | Sinh viên đăng ký môn học trên MyBK. | Người học chọn học phần qua hệ thống trực tuyến của trường. | cao | 0.478 | Đúng một phần |
| 3 | Phòng Công tác sinh viên cấp giấy xác nhận. | Thư viện bổ sung cơ sở dữ liệu sách điện tử. | thấp | 0.331 | Đúng |
| 4 | Môn thi trắc nghiệm không được phúc tra. | Bài thi dạng trắc nghiệm không thuộc diện phúc tra. | cao | 0.786 | Đúng |
| 5 | Tân sinh viên xác nhận nhập học trực tuyến. | Học phí học kỳ hè thanh toán trước tuần học đầu tiên. | thấp | 0.460 | Đúng một phần |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Kết quả bất ngờ nhất là cặp 5: hai câu khác chủ đề nhưng vẫn có điểm 0.460, cao hơn kỳ vọng thấp ban đầu. Điều này cho thấy embedding thật biểu diễn ngữ nghĩa mềm hơn so khớp từ khóa; các câu cùng bối cảnh học vụ/sinh viên vẫn có thể gần nhau ở mức vừa phải dù không trả lời cùng một câu hỏi.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Sinh viên đăng ký môn học Đợt 1 ở đâu và cần lưu ý giới hạn tín chỉ nào? | `course-registration-process#2` — chứa hướng dẫn đăng ký tại MyBK trong Đợt 1. | 0.6662 | Có | Có thể trả lời: đăng ký tại MyBK > Đăng ký môn học; Đợt 1 tối đa 25 tín chỉ, HV/NCS tối đa 20 tín chỉ. |
| 2 | Nếu sinh viên không đăng ký môn học và không có thời khóa biểu trong học kỳ thì có thể bị xử lý thế nào? | `course-registration-rules#2` — tài liệu quy định đăng ký môn học, top-3 chứa câu về xóa tên vì không có thời khóa biểu. | 0.6366 | Có | Có thể trả lời: sinh viên có thể bị xử lý ra quyết định xóa tên vì không có thời khóa biểu. |
| 3 | Học phí HK1 và HK2 phải thanh toán vào thời điểm nào? | `tuition-payment#1` — chunk học phí có thông tin 100% học phí và tuần 4. | 0.7266 | Có | Có thể trả lời: HK1/HK2 thanh toán 100% học phí, kết thúc ở tuần 4 của học kỳ. |
| 4 | Những môn nào không được phúc tra bài thi cuối kỳ? | `final-exam-grade-review#0` — top-3 cùng tài liệu phúc tra, có chunk chứa danh sách môn không được phúc tra. | 0.5863 | Có | Có thể trả lời: trắc nghiệm, thí nghiệm, thực hành, thực tập, đồ án, đề cương luận văn, luận văn tốt nghiệp. |
| 5 | Đăng ký giấy chứng nhận sinh viên thực hiện trên hệ thống nào và nhận ở đâu? | `student-certificate#1` — chunk giấy chứng nhận sinh viên, top-3 cùng tài liệu chứa hệ thống đăng ký và nơi nhận. | 0.7239 | Có | Có thể trả lời: đăng ký tại MyBK > Ứng dụng cho Sinh viên > Đăng ký in Giấy xác nhận sinh viên; khi “Đã in” thì nhận tại Phòng Công tác sinh viên. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Ghi chú về embedding backend:** Benchmark này chạy bằng OpenAI `text-embedding-3-small` với cache theo hash nội dung trong `bench.py`. Kết quả retrieval có ý nghĩa ngữ nghĩa hơn so với mock và top-3 của cả 5 câu đều chứa chunk trả lời được gold answer.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Chấm theo `doc_id` là chưa đủ vì có trường hợp đúng tài liệu lọt top-3 nhưng chunk không chứa câu trả lời. Cần kiểm tra nội dung chunk bằng các cụm đặc trưng của gold answer, nếu không kết quả retrieval sẽ bị thổi phồng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
