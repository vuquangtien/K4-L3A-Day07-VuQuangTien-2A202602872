from __future__ import annotations

import hashlib
import json
import re
import os
from pathlib import Path

from dotenv import load_dotenv

from src import (
    Document,
    EMBEDDING_PROVIDER_ENV,
    EmbeddingStore,
    FixedSizeChunker,
    GeminiEmbedder,
    LocalEmbedder,
    OpenAIEmbedder,
    RecursiveChunker,
    SentenceChunker,
    _mock_embed,
)


DATA_DIR = Path("data/hcmut")
TOP_K = 3
CACHE_DIR = Path(".embedding-cache")
load_dotenv(override=False)
BACKEND = (
    os.getenv(EMBEDDING_PROVIDER_ENV)
    or os.getenv("EMBEDDING_BACKEND")
    or "mock"
).strip().lower()


class HeadingChunker:
    """Split policy-style Markdown by headings/numbered sections.

    Long sections fall back to RecursiveChunker. Each child chunk keeps the
    section heading so the retrieved text still has local context.
    """

    def __init__(self, max_chunk_size: int = 900) -> None:
        self.max_chunk_size = max_chunk_size
        self.fallback = RecursiveChunker(chunk_size=max_chunk_size)

    def chunk(self, text: str) -> list[str]:
        if not text.strip():
            return []

        sections = self._sections(text)
        chunks: list[str] = []
        for heading, body in sections:
            section_text = f"{heading}\n\n{body}".strip() if heading else body.strip()
            if not section_text:
                continue
            if len(section_text) <= self.max_chunk_size:
                chunks.append(section_text)
                continue

            fallback_text = body.strip() if heading else section_text
            for child in self.fallback.chunk(fallback_text):
                chunks.append(f"{heading}\n\n{child}".strip() if heading else child)
        return chunks

    def _sections(self, text: str) -> list[tuple[str, str]]:
        heading_pattern = re.compile(
            r"^(#{1,6}\s+.+|\d+\s*[.-]\s+.+|[IVX]+\.\s+.+)$",
            re.MULTILINE,
        )
        matches = list(heading_pattern.finditer(text))
        if not matches:
            return [("", text)]

        sections: list[tuple[str, str]] = []
        prefix = text[: matches[0].start()].strip()
        if prefix:
            sections.append(("", prefix))

        for index, match in enumerate(matches):
            start = match.end()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            heading = match.group(1).strip()
            body = text[start:end].strip()
            sections.append((heading, body))
        return sections


# Mỗi thành viên chỉ đổi dòng này để thử chiến lược riêng.
CHUNKER = HeadingChunker(max_chunk_size=900)


BENCHMARK_QUERIES = [
    {
        "query": "Sinh viên đăng ký môn học Đợt 1 ở đâu và cần lưu ý giới hạn tín chỉ nào?",
        "gold": "Sinh viên đăng ký tại MyBK > Đăng ký môn học; Đợt 1 đăng ký tối đa 25 tín chỉ, còn HV/NCS tối đa 20 tín chỉ.",
        "metadata_filter": {"audience": "student"},
        "expected_doc_id": "course-registration-process",
        "required_phrases": ["Đăng ký tại MyBK", "tối đa 25 tín chỉ"],
    },
    {
        "query": "Nếu sinh viên không đăng ký môn học và không có thời khóa biểu trong học kỳ thì có thể bị xử lý thế nào?",
        "gold": "Sinh viên không đăng ký môn học, không có thời khóa biểu trong học kỳ, sẽ bị xử lý ra quyết định xóa tên vì không có thời khóa biểu.",
        "metadata_filter": {"audience": "student"},
        "expected_doc_id": "course-registration-rules",
        "required_phrases": ["Xóa tên vì không có thời khóa biểu"],
    },
    {
        "query": "Học phí HK1 và HK2 phải thanh toán vào thời điểm nào?",
        "gold": "Học phí HK1 và HK2 thanh toán 100% học phí, kết thúc ở tuần 4 của học kỳ, với thời gian thanh toán trong 1 tuần.",
        "metadata_filter": {"topic": "tuition"},
        "expected_doc_id": "tuition-payment",
        "required_phrases": ["Kết thúc ở tuần 4", "100% học phí"],
    },
    {
        "query": "Những môn nào không được phúc tra bài thi cuối kỳ?",
        "gold": "Các môn không được phúc tra gồm môn thi trắc nghiệm, môn thí nghiệm, môn thực hành, thực tập, đồ án, đề cương luận văn và luận văn tốt nghiệp.",
        "metadata_filter": {"topic": "grade_appeal"},
        "expected_doc_id": "final-exam-grade-review",
        "required_phrases": ["môn thi trắc nghiệm", "môn thí nghiệm", "luận văn tốt nghiệp"],
    },
    {
        "query": "Đăng ký giấy chứng nhận sinh viên thực hiện trên hệ thống nào và nhận ở đâu?",
        "gold": "Sinh viên đăng ký tại MyBK > Ứng dụng cho Sinh viên > Đăng ký in Giấy xác nhận sinh viên; khi trạng thái chuyển Đã in thì đến Phòng Công tác sinh viên để nhận.",
        "metadata_filter": {"audience": "student"},
        "expected_doc_id": "student-certificate",
        "required_phrases": ["Đăng ký in Giấy xác nhận sinh viên", "Phòng Công tác sinh viên"],
    },
]


def parse_markdown(path: Path) -> tuple[dict[str, str], str]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}, text

    _, frontmatter, content = text.split("---", 2)
    metadata: dict[str, str] = {}
    for line in frontmatter.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.strip().strip('"')
    return metadata, content.strip()


def load_chunk_documents(data_dir: Path) -> list[Document]:
    return load_chunk_documents_with_chunker(data_dir, CHUNKER)


def load_chunk_documents_with_chunker(data_dir: Path, chunker) -> list[Document]:
    documents: list[Document] = []
    for path in sorted(data_dir.glob("*.md")):
        frontmatter, content = parse_markdown(path)
        for index, chunk in enumerate(chunker.chunk(content)):
            metadata = {
                **frontmatter,
                "doc_id": path.stem,
                "chunk_index": index,
                "source_file": str(path),
            }
            documents.append(
                Document(
                    id=f"{path.stem}#{index}",
                    content=chunk,
                    metadata=metadata,
                )
            )
    return documents


class CachedEmbedder:
    def __init__(self, embedder, cache_name: str) -> None:
        self.embedder = embedder
        self._backend_name = f"{getattr(embedder, '_backend_name', embedder.__class__.__name__)} + cache"
        CACHE_DIR.mkdir(exist_ok=True)
        safe_name = re.sub(r"[^a-zA-Z0-9_.-]+", "_", cache_name).strip("_") or "embeddings"
        self.cache_path = CACHE_DIR / f"{safe_name}.json"
        if self.cache_path.exists():
            self.cache = json.loads(self.cache_path.read_text(encoding="utf-8"))
        else:
            self.cache = {}

    def __call__(self, text: str) -> list[float]:
        key = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if key not in self.cache:
            self.cache[key] = self.embedder(text)
            self.cache_path.write_text(json.dumps(self.cache), encoding="utf-8")
        return [float(value) for value in self.cache[key]]


def make_embedder():
    if BACKEND == "local":
        try:
            return CachedEmbedder(LocalEmbedder(), "local")
        except Exception as error:
            print(f"WARNING: local embedder unavailable ({error}); falling back to mock.")
            return _mock_embed
    if BACKEND == "openai":
        try:
            model_name = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
            return CachedEmbedder(OpenAIEmbedder(model_name=model_name), f"openai_{model_name}")
        except Exception as error:
            print(f"WARNING: OpenAI embedder unavailable ({error}); falling back to mock.")
            return _mock_embed
    if BACKEND == "gemini":
        try:
            model_name = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")
            return CachedEmbedder(GeminiEmbedder(model_name=model_name), f"gemini_{model_name}")
        except Exception as error:
            print(f"WARNING: Gemini embedder unavailable ({error}); falling back to mock.")
            return _mock_embed
    return _mock_embed


def score_results(item: dict, results: list[dict]) -> tuple[bool, bool, int]:
    expected_doc_id = item["expected_doc_id"]
    doc_ranks = [
        rank
        for rank, result in enumerate(results, start=1)
        if result["metadata"].get("doc_id") == expected_doc_id
    ]
    doc_hit = bool(doc_ranks)

    combined_context = "\n".join(result["content"].lower() for result in results)
    phrase_hit = all(phrase.lower() in combined_context for phrase in item["required_phrases"])

    if doc_ranks and doc_ranks[0] == 1 and phrase_hit:
        score = 2
    elif doc_hit and phrase_hit:
        score = 1
    else:
        score = 0
    return doc_hit, phrase_hit, score


def print_results(item: dict, results: list[dict]) -> int:
    for rank, result in enumerate(results, start=1):
        metadata = result["metadata"]
        preview = " ".join(result["content"].split())[:180]
        print(
            f"  {rank}. score={result['score']:.4f} "
            f"doc_id={metadata.get('doc_id')} chunk={metadata.get('chunk_index')} "
            f"title={metadata.get('title')}"
        )
        print(f"     {preview}...")

    doc_hit, phrase_hit, score = score_results(item, results)
    print(f"Doc-level hit top-3: {doc_hit}")
    print(f"Content-level required phrases found: {phrase_hit}")
    print(f"Score: {score}/2")
    return score


def run_strategy(name: str, chunker, embedder) -> tuple[int, list[tuple[int, bool, bool, int]]]:
    docs = load_chunk_documents_with_chunker(DATA_DIR, chunker)
    store = EmbeddingStore(collection_name=f"hcmut_{name}", embedding_fn=embedder)
    store.add_documents(docs)
    print(f"=== Strategy: {name} ===")
    print(f"Loaded chunks: {store.get_collection_size()}")
    total = 0
    detail: list[tuple[int, bool, bool, int]] = []
    for index, item in enumerate(BENCHMARK_QUERIES, start=1):
        results = store.search_with_filter(item["query"], top_k=TOP_K, metadata_filter=item.get("metadata_filter"))
        doc_hit, phrase_hit, score = score_results(item, results)
        total += score
        detail.append((index, doc_hit, phrase_hit, score))
        print(f"Q{index}: doc_hit={doc_hit} phrase_hit={phrase_hit} score={score}/2")
    print(f"Total: {total}/10")
    print()
    return total, detail


def run_filter_ab(embedder) -> None:
    item = BENCHMARK_QUERIES[4]
    strategies = {
        "fixed_size": FixedSizeChunker(chunk_size=700, overlap=80),
        "by_sentences": SentenceChunker(max_sentences_per_chunk=5),
        "recursive": RecursiveChunker(chunk_size=700),
        "heading": HeadingChunker(max_chunk_size=900),
    }

    print("=== A/B metadata filter for Query 5 ===")
    print(f"Query: {item['query']}")
    for name, chunker in strategies.items():
        docs = load_chunk_documents_with_chunker(DATA_DIR, chunker)
        store = EmbeddingStore(collection_name=f"ab_{name}", embedding_fn=embedder)
        store.add_documents(docs)

        unfiltered = store.search_with_filter(item["query"], top_k=TOP_K, metadata_filter=None)
        filtered = store.search_with_filter(item["query"], top_k=TOP_K, metadata_filter=item["metadata_filter"])
        print(f"Strategy: {name}")
        print("  No filter:", [result["metadata"].get("doc_id") for result in unfiltered])
        print("  Filtered :", [result["metadata"].get("doc_id") for result in filtered])
    print()


def main() -> int:
    embedder = make_embedder()
    docs = load_chunk_documents(DATA_DIR)
    store = EmbeddingStore(collection_name="hcmut_benchmark", embedding_fn=embedder)
    store.add_documents(docs)

    print(f"Data dir: {DATA_DIR}")
    print(f"Chunker: {CHUNKER.__class__.__name__}")
    print(f"Embedding backend: {getattr(embedder, '_backend_name', embedder.__class__.__name__)}")
    if embedder is _mock_embed:
        print("WARNING: MockEmbedder does not encode semantic meaning; retrieval scores are noisy.")
    print(f"Loaded chunks: {store.get_collection_size()}")
    print()

    total = 0
    for index, item in enumerate(BENCHMARK_QUERIES, start=1):
        query = item["query"]
        metadata_filter = item.get("metadata_filter")
        print(f"Query {index}: {query}")
        print(f"Filter: {metadata_filter or None}")
        print(f"Gold: {item['gold']}")
        print(f"Expected doc_id: {item['expected_doc_id']}")
        print(f"Required phrases: {item['required_phrases']}")

        results = store.search_with_filter(query, top_k=TOP_K, metadata_filter=metadata_filter)
        total += print_results(item, results)
        print()

    print(f"Heading strategy total score: {total}/10")
    print()
    print("=== Strategy comparison summary ===")
    strategies = {
        "fixed_size": FixedSizeChunker(chunk_size=700, overlap=80),
        "by_sentences": SentenceChunker(max_sentences_per_chunk=5),
        "recursive": RecursiveChunker(chunk_size=700),
        "heading": CHUNKER,
    }
    for name, chunker in strategies.items():
        run_strategy(name, chunker, embedder)

    run_filter_ab(embedder)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
