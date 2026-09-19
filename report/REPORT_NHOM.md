# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** YBY1
**Thành viên:** Vũ Quang Tiến - 2A202602872
                     Nguyễn Đức Anh - 2A202602625
                     Nguyễn Hoàng Duy - 2A202602751
                     Nguyễn Đặng Nam Khánh - 2A202602741
**Ngày:** 19/09/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Chủ đề (Domain) & Lý Do Chọn

**Chủ đề:** Dịch vụ học vụ và hỗ trợ sinh viên HCMUT

**Tại sao nhóm chọn chủ đề này?**
> Nhóm chọn chủ đề này vì các tài liệu học vụ, học phí, giấy xác nhận, phúc tra và nhập học đều có nguồn công khai, có cấu trúc thủ tục rõ ràng và phù hợp với yêu cầu L3A về dịch vụ/quy định đại học. Bộ tài liệu cũng có metadata như `audience`, `department`, `topic`, `doc_type`, giúp thử nghiệm retrieval có filter và so sánh các chiến lược chunking.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Quy trình đăng ký môn học | `https://mybk.hcmut.edu.vn/bksi/public/vi/article/111.com` | 2026-09-19 / not-stated | 14001 | `audience=student`, `department=academic-affairs`, `category=registration`, `topic=course_registration`, `doc_type=procedure`, `language=vi` |
| 2 | Đăng ký môn học - Quy định - Hướng dẫn chung | `https://mybk.hcmut.edu.vn/bksi/public/vi/blog/dang-ky-mon-hoc-quy-trinh-huong-dan-chung` | 2026-09-19 / not-stated | 17554 | `audience=student`, `department=academic-affairs`, `category=registration`, `topic=course_registration`, `doc_type=guide`, `language=vi` |
| 3 | Phúc tra bài thi cuối kỳ | `https://mybk.hcmut.edu.vn/bksi/public/vi/blog/phuc-tra-bai-thi-cuoi-ky` | 2026-09-19 / not-stated | 3832 | `audience=student`, `department=quality-assurance`, `category=assessment`, `topic=grade_appeal`, `doc_type=procedure`, `language=vi` |
| 4 | Các bước xác nhận nhập học dành cho tân sinh viên khóa 2025 | `https://fme.hcmut.edu.vn/cac-buoc-thuc-hien-xac-nhan-nhap-hoc-danh-cho-tan-sinh-vien-khoa-2025.html` | 2026-09-19 / 2025-08-22 | 20620 | `audience=student`, `department=admissions`, `category=admission`, `topic=dormitory`, `doc_type=procedure`, `language=vi` |
| 5 | Cấp giấy chứng nhận sinh viên | `https://mybk.hcmut.edu.vn/bksi/public/vi/blog/cap-giay-chung-nhan-sinh-vien` | 2026-09-19 / not-stated | 3468 | `audience=student`, `department=student-affairs`, `category=student_services`, `topic=student_certificate`, `doc_type=procedure`, `language=vi` |
| 6 | Các phòng ban - đơn vị liên quan | `https://mybk.hcmut.edu.vn/bksi/public/vi/blog/cac-phong-ban-don-vi-lien-quan` | 2026-09-19 / not-stated | 6293 | `audience=all`, `department=student-affairs`, `category=student_services`, `topic=scholarship`, `doc_type=reference`, `language=vi` |
| 7 | Học phí | `https://mybk.hcmut.edu.vn/bksi/public/vi/blog/hoc-phi` | 2026-09-19 / not-stated | 3632 | `audience=student`, `department=finance`, `category=tuition`, `topic=tuition`, `doc_type=policy`, `language=vi` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu (Corpus) chỉ chứa nguồn công khai/được phép dùng và không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` (hoặc ngày hiệu lực) trong metadata.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `tuition-payment` | Định danh tài liệu gốc; dùng để xóa toàn bộ chunk và đối chiếu gold answer. |
| `source_url` | string | `https://mybk.hcmut.edu.vn/.../hoc-phi` | Truy vết nguồn, kiểm chứng provenance. |
| `retrieved_at` | date string | `2026-09-19` | Biết thời điểm lấy dữ liệu, hỗ trợ đánh giá độ mới. |
| `document_version` | string | `2025-08-22`, `not-stated` | Ghi ngày hiệu lực/phiên bản nếu nguồn có nêu. |
| `audience` | enum/string | `student`, `all` | Lọc theo đối tượng sử dụng tài liệu. |
| `department` | string | `academic-affairs`, `finance` | Lọc theo đơn vị/phòng ban phụ trách. |
| `category` | string | `registration`, `tuition` | Nhóm tài liệu theo loại dịch vụ. |
| `topic` | string | `course_registration`, `grade_appeal` | Filter hẹp hơn `audience`, giúp giảm nhiễu khi query mơ hồ. |
| `doc_type` | string | `procedure`, `policy`, `guide` | Phân biệt quy trình, chính sách, hướng dẫn, tài liệu tham chiếu. |
| `language` | string | `vi` | Hỗ trợ lọc ngôn ngữ khi corpus đa ngữ. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| `course-registration-process` | FixedSizeChunker (`fixed_size`) | 31 | 488.6 | Trung bình; dễ cắt ngang bảng/thủ tục dài. |
| `course-registration-process` | SentenceChunker (`by_sentences`) | 34 | 398.9 | Khá; giữ nguyên câu nhưng chưa hiểu heading/bảng. |
| `course-registration-process` | RecursiveChunker (`recursive`) | 42 | 322.3 | Khá tốt; ưu tiên đoạn/dòng trước khi cắt nhỏ. |
| `tuition-payment` | FixedSizeChunker (`fixed_size`) | 8 | 461.2 | Trung bình; có thể cắt ngang mục học phí. |
| `tuition-payment` | SentenceChunker (`by_sentences`) | 8 | 414.8 | Khá; nội dung ngắn nên ít vỡ câu. |
| `tuition-payment` | RecursiveChunker (`recursive`) | 10 | 329.8 | Tốt; giữ các mục nhỏ dễ truy xuất hơn. |
| `final-exam-grade-review` | FixedSizeChunker (`fixed_size`) | 8 | 478.4 | Trung bình; quy trình có thể bị cắt giữa bước. |
| `final-exam-grade-review` | SentenceChunker (`by_sentences`) | 6 | 576.0 | Khá; ít chunk hơn nhưng mỗi chunk hơi dài. |
| `final-exam-grade-review` | RecursiveChunker (`recursive`) | 10 | 342.9 | Tốt; giữ mục quy trình/quy định tương đối rõ. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Vũ Quang Tiến**
- **Loại chiến lược:** Custom heading/section chunker
- **Mô tả & lý do chọn cho chủ đề này:** Dữ liệu HCMUT là tài liệu hướng dẫn/quy định, thường được chia theo tiêu đề, mục đánh số và các phần quy trình. Vì vậy chiến lược này tách theo heading hoặc mục số trước để giữ một đơn vị ngữ nghĩa trọn vẹn; nếu section quá dài thì fallback sang `RecursiveChunker`, đồng thời gắn lại heading vào từng chunk con để không mất ngữ cảnh.
- **Code snippet (nếu custom):**
```python
# Dòng chiến lược trong bench.py
CHUNKER = HeadingChunker(max_chunk_size=900)
```

**Thành viên 2 — Nguyễn Đức Anh**
- **Loại chiến lược:** SentenceChunker (`max_sentences_per_chunk=5`)
- **Mô tả & lý do chọn:** Chiến lược gom cụm theo câu giúp bảo toàn tính toàn vẹn ngữ pháp và ngữ nghĩa của từng điều khoản quy định, tránh việc các câu hướng dẫn hay số liệu quan trọng bị chia cắt giữa chừng. Với bộ 5 câu hỏi thực tế của HCMUT, các đáp án thường nằm tập trung trong 1-2 câu trọn vẹn, nên SentenceChunker với 76 chunk đạt độ chính xác tuyệt đối 10/10 khi kết hợp với OpenAI Embeddings (`text-embedding-3-small`).
- **Code snippet (nếu custom):**
```python
# Cấu hình chiến lược của Nguyễn Đức Anh
CHUNKER = SentenceChunker(max_sentences_per_chunk=5)
```

**Thành viên 3 — Nguyễn Hoàng Duy**
- **Loại chiến lược:** FixedSizeChunker (`chunk_size=700`, `overlap=80`)
- **Mô tả & lý do chọn:** Chia nhỏ văn bản theo độ dài cố định 700 ký tự với sliding window gối đầu 80 ký tự. Chiến lược này giúp kiểm soát chính xác dung lượng từng chunk đưa vào embedding model, đồng thời overlap giúp duy trì mạch thông tin giữa hai chunk liền kề, tránh bị đứt gãy câu ở mép cắt.
- **Code snippet (nếu custom):**
```python
# Cấu hình chiến lược của Nguyễn Hoàng Duy
CHUNKER = FixedSizeChunker(chunk_size=700, overlap=80)
```

**Thành viên 4 — Nguyễn Đặng Nam Khánh**
- **Loại chiến lược:** RecursiveChunker (`chunk_size=700`)
- **Mô tả & lý do chọn:** Văn bản được chia đệ quy theo thứ tự ưu tiên `["\n\n", "\n", ". ", " ", ""]`. Nếu một đoạn vẫn dài hơn `chunk_size`, hệ thống tiếp tục dùng separator nhỏ hơn. Các đoạn nhỏ sau đó được ghép lại theo thứ tự từ trái sang phải miễn là không vượt quá giới hạn chunk. Chiến lược này giúp giữ cấu trúc tự nhiên của văn bản tốt hơn fixed-size chunking và hạn chế cắt nội dung giữa câu hoặc đoạn.
- **Code snippet (nếu custom):**
```python
# Cấu hình chiến lược của Nguyễn Đặng Nam Khánh
CHUNKER = RecursiveChunker(chunk_size=700)
```

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Vũ Quang Tiến | HeadingChunker (`max_chunk_size=900`) | 10/10 | Tách theo heading/mục số, giữ đơn vị ngữ nghĩa của văn bản quy định; section dài được fallback recursive. | Phụ thuộc vào chất lượng heading/mục trong tài liệu; nếu source lẫn menu/nội dung lặp thì vẫn cần làm sạch dữ liệu. |
| Nguyễn Đức Anh | SentenceChunker (`max_sentences_per_chunk=5`) | 10/10 | Giữ nguyên câu, ít làm đứt cú pháp; hoạt động tốt với câu hỏi cần thông tin cụ thể. | Không hiểu heading/bảng, nên nếu tài liệu dài hơn có thể gom nhiều ý khác nhau. |
| Nguyễn Hoàng Duy | FixedSizeChunker (`chunk_size=700`, `overlap=80`) | 8/10 | Số chunk vừa phải, dễ triển khai, giữ được overlap giữa các đoạn. | Có thể cắt ngang section nên có lúc đúng tài liệu nhưng thiếu cụm trả lời trong top-3. |
| Nguyễn Đặng Nam Khánh | RecursiveChunker (`chunk_size=700`) | 8/10 | Chia nhỏ theo paragraph/dòng/từ nên linh hoạt với văn bản dài. | Có thể tạo nhiều chunk nhỏ; một số câu đúng `doc_id` nhưng top-3 chưa chứa đủ cụm trả lời. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Với OpenAI `text-embedding-3-small`, SentenceChunker và HeadingChunker cùng đạt 10/10. Nhóm chọn HeadingChunker là chiến lược phù hợp nhất về mặt thiết kế cho corpus này vì tài liệu quy định/hướng dẫn HCMUT có nhiều tiêu đề, mục đánh số và quy trình; tách theo section giúp chunk giữ được ngữ cảnh "đang nói về mục nào". SentenceChunker cũng rất mạnh trong bộ câu hỏi hiện tại vì các đáp án nằm trong một vài câu rõ ràng.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Sinh viên đăng ký môn học Đợt 1 ở đâu và cần lưu ý giới hạn tín chỉ nào? | Sinh viên đăng ký tại MyBK > Đăng ký môn học; Đợt 1 đăng ký tối đa 25 tín chỉ, còn HV/NCS tối đa 20 tín chỉ. | `course-registration-process` |
| 2 | Nếu sinh viên không đăng ký môn học và không có thời khóa biểu trong học kỳ thì có thể bị xử lý thế nào? | Sinh viên không đăng ký môn học, không có thời khóa biểu trong học kỳ, sẽ bị xử lý ra quyết định xóa tên vì không có thời khóa biểu. | `course-registration-rules` |
| 3 | Học phí HK1 và HK2 phải thanh toán vào thời điểm nào? | Học phí HK1 và HK2 thanh toán 100% học phí, kết thúc ở tuần 4 của học kỳ, với thời gian thanh toán trong 1 tuần. | `tuition-payment` |
| 4 | Những môn nào không được phúc tra bài thi cuối kỳ? | Các môn không được phúc tra gồm môn thi trắc nghiệm, môn thí nghiệm, môn thực hành, thực tập, đồ án, đề cương luận văn và luận văn tốt nghiệp. | `final-exam-grade-review` |
| 5 | Đăng ký giấy chứng nhận sinh viên thực hiện trên hệ thống nào và nhận ở đâu? | Sinh viên đăng ký tại MyBK > Ứng dụng cho Sinh viên > Đăng ký in Giấy xác nhận sinh viên; khi trạng thái chuyển Đã in thì đến Phòng Công tác sinh viên để nhận. | `student-certificate`; dùng `metadata_filter={"audience": "student"}` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Sinh viên đăng ký môn học Đợt 1 ở đâu và cần lưu ý giới hạn tín chỉ nào? | Sentence / Heading | Có | Heading top-3 chứa cả chunk hướng dẫn “Đăng ký tại MyBK” và chunk “tối đa 25 tín chỉ”; Fixed/Recursive đúng `doc_id` nhưng thiếu đủ cụm đáp án nên chỉ nhìn `doc_id` sẽ bị thổi phồng. |
| 2 | Nếu sinh viên không đăng ký môn học và không có thời khóa biểu trong học kỳ thì có thể bị xử lý thế nào? | Fixed / Sentence / Recursive / Heading | Có | Cả bốn chiến lược đều đưa `course-registration-rules` và cụm “Xóa tên vì không có thời khóa biểu” vào top-3. |
| 3 | Học phí HK1 và HK2 phải thanh toán vào thời điểm nào? | Fixed / Sentence / Recursive / Heading | Có | Top-3 chứa chunk `tuition-payment` có “100% học phí” và “kết thúc ở tuần 4”. |
| 4 | Những môn nào không được phúc tra bài thi cuối kỳ? | Fixed / Sentence / Recursive / Heading | Có | Top-3 chứa chunk `final-exam-grade-review` có danh sách môn không được phúc tra. |
| 5 | Đăng ký giấy chứng nhận sinh viên thực hiện trên hệ thống nào và nhận ở đâu? | Fixed / Sentence / Recursive / Heading | Có | Top-3 chứa `student-certificate` và các cụm “Đăng ký in Giấy xác nhận sinh viên”, “Phòng Công tác sinh viên”. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> A/B trên câu 5 cho thấy filter `{"audience": "student"}` có giúp ích. Với FixedSize và Heading, top-3 sau khi filter đều là `student-certificate`, loại được tài liệu `student-service-offices` có `audience=all`. Với Recursive, filter đưa `student-certificate` lên top-1 thay vì để `student-service-offices` đứng đầu. Riêng Sentence vẫn còn lẫn tài liệu nhập học vì chúng cũng có `audience=student`, cho thấy `audience` tăng precision theo đối tượng nhưng nếu muốn lọc thật sạch nên kết hợp thêm `topic="student_certificate"`.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> - Chấm ở mức `doc_id` là chưa đủ; phải kiểm tra chunk có thật sự chứa chuỗi/cụm thông tin trả lời được gold answer.
> - Embedder thật làm kết quả retrieval có ý nghĩa hơn rõ rệt: HeadingChunker và SentenceChunker đạt 10/10, trong khi mock trước đó chủ yếu phản ánh nhiễu hash.
> - Metadata filter giúp loại bớt tài liệu sai đối tượng nhưng không thay thế được metadata theo `topic`/`category`.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng một corpus nhưng chiến lược chunking tạo số chunk và mức độ mạch lạc khác nhau: SentenceChunker ít chunk hơn và đạt điểm rất tốt vì giữ nguyên câu trả lời; HeadingChunker giữ cấu trúc mục tốt hơn nên hợp tài liệu quy định; FixedSize và Recursive vẫn có doc-level hit nhưng có thể thiếu đúng chunk chứa đáp án. Vì vậy nhóm cần chấm theo nội dung chunk chứ không chỉ theo `doc_id`.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ bổ sung tài liệu song song cùng chủ đề nhưng khác `audience` như quy trình dành cho sinh viên và quy trình nội bộ dành cho staff để kiểm tra metadata filter rõ hơn. Nhóm cũng sẽ giữ cache embedding thật để chạy lại benchmark ổn định, ít tốn chi phí và so sánh công bằng giữa các chiến lược.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 9 / 10 |
| Thiết kế chiến lược (Strategy Design) | 14 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 9 / 10 |
| Thuyết trình (Demo) | 4 / 5 |
| **Tổng phần nhóm** | **36 / 40** |
