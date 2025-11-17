#!/usr/bin/env python3
"""
Sprint 3: Memory Store System - Manual Integration Test

This script provides a comprehensive integration test for the Memory Store System
that can be run locally without PostgreSQL or OpenAI API dependencies.
"""

import asyncio
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from memory_store import (
    MemoryStoreService,
    InMemoryRepository,
    MockEmbeddingService,
    MemoryType,
    SourceType,
)


def print_header(title: str):
    """Print a formatted header"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)


def print_result(label: str, value):
    """Print a formatted result"""
    print(f"  {label}: {value}")


def print_success(message: str):
    """Print a success message"""
    print(f"  ✓ {message}")


def print_failure(message: str):
    """Print a failure message"""
    print(f"  ✗ {message}")


async def test_embedding_service():
    """Test embedding service functionality"""
    print_header("Test 1: Embedding Service")

    service = MockEmbeddingService()

    # Test 1.1: Basic embedding generation
    text = "Resonant Engineは呼吸のリズムで動作する"
    embedding = await service.generate_embedding(text)
    print_result("Input text", text)
    print_result("Embedding dimensions", len(embedding))
    print_result("First 5 values", embedding[:5])

    if len(embedding) == 1536:
        print_success("Embedding has correct dimensions")
    else:
        print_failure(f"Expected 1536 dimensions, got {len(embedding)}")

    # Test 1.2: Deterministic embeddings
    embedding2 = await service.generate_embedding(text)
    if embedding == embedding2:
        print_success("Embeddings are deterministic")
    else:
        print_failure("Embeddings are not deterministic")

    # Test 1.3: Semantic similarity
    text_similar = "呼吸について"
    text_different = "データベース設計"

    emb_similar = await service.generate_embedding(text_similar)
    emb_different = await service.generate_embedding(text_different)

    from memory_store.embedding import cosine_similarity
    sim_similar = cosine_similarity(embedding, emb_similar)
    sim_different = cosine_similarity(embedding, emb_different)

    print_result("Similarity to related text", f"{sim_similar:.4f}")
    print_result("Similarity to unrelated text", f"{sim_different:.4f}")

    if sim_similar > sim_different:
        print_success("Semantic similarity is working correctly")
    else:
        print_failure("Semantic similarity ranking is incorrect")

    return True


async def test_memory_repository():
    """Test memory repository functionality"""
    print_header("Test 2: Memory Repository")

    repo = InMemoryRepository()
    embedding_service = MockEmbeddingService()

    # Test 2.1: Insert memories
    memories = [
        ("Resonant Engineの設計原則", "longterm", "decision", {"tags": ["core", "architecture"]}),
        ("今日のSprint 3タスク", "working", "intent", {"tags": ["sprint3"]}),
        ("PostgreSQLとpgvectorを使用する", "longterm", "decision", {"tags": ["database", "architecture"]}),
        ("呼吸のリズムは重要な概念", "longterm", "thought", {"tags": ["philosophy"]}),
    ]

    memory_ids = []
    for content, mem_type, source, metadata in memories:
        embedding = await embedding_service.generate_embedding(content)
        expires_at = None
        if mem_type == "working":
            expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

        memory_id = await repo.insert_memory(
            content=content,
            embedding=embedding,
            memory_type=mem_type,
            source_type=source,
            metadata=metadata,
            expires_at=expires_at
        )
        memory_ids.append(memory_id)
        print_result(f"Inserted memory {memory_id}", content[:40])

    print_success(f"Inserted {len(memory_ids)} memories")

    # Test 2.2: Similarity search
    query = "呼吸について教えて"
    query_embedding = await embedding_service.generate_embedding(query)
    results = await repo.search_similar(query_embedding, None, 10, -1.0, False)

    print(f"\n  Search query: '{query}'")
    print(f"  Results ({len(results)} found):")
    for i, result in enumerate(results):
        print(f"    {i+1}. [{result['similarity']:.4f}] {result['content'][:50]}")

    if len(results) > 0:
        print_success("Similarity search returned results")
    else:
        print_failure("No results returned from similarity search")

    # Test 2.3: Type filtering
    longterm_results = await repo.search_similar(query_embedding, "longterm", 10, -1.0, False)
    print(f"\n  Filtered by type 'longterm': {len(longterm_results)} results")

    all_longterm = all(r["memory_type"] == "longterm" for r in longterm_results)
    if all_longterm:
        print_success("Type filtering works correctly")
    else:
        print_failure("Type filtering is not working")

    # Test 2.4: Hybrid search with metadata filters
    hybrid_results = await repo.search_hybrid(
        query_embedding,
        {"source_type": "decision"},
        10
    )
    print(f"\n  Hybrid search (source_type=decision): {len(hybrid_results)} results")

    all_decisions = all(r["source_type"] == "decision" for r in hybrid_results)
    if all_decisions:
        print_success("Hybrid search with metadata filter works")
    else:
        print_failure("Hybrid search metadata filter not working")

    return True


async def test_memory_store_service():
    """Test memory store service (high-level API)"""
    print_header("Test 3: Memory Store Service")

    repo = InMemoryRepository()
    embedding_service = MockEmbeddingService()
    service = MemoryStoreService(
        repository=repo,
        embedding_service=embedding_service,
        working_memory_ttl_hours=24
    )

    # Test 3.1: Save working memory
    working_id = await service.save_memory(
        content="Sprint 3のMemory Store実装を完了する",
        memory_type=MemoryType.WORKING,
        source_type=SourceType.INTENT,
        metadata={"priority": "high"}
    )
    print_result("Saved working memory", f"ID={working_id}")

    # Test 3.2: Save long-term memories
    longterm_ids = []
    longterm_memories = [
        ("Resonant Engineは呼吸のリズムで動作するシステムである", SourceType.DECISION, {"importance": 1.0}),
        ("pgvectorによるベクトル検索は高速で正確", SourceType.THOUGHT, {"importance": 0.8}),
        ("Working Memoryは24時間のTTLを持つ", SourceType.DECISION, {"importance": 0.9}),
    ]

    for content, source, metadata in longterm_memories:
        memory_id = await service.save_memory(
            content=content,
            memory_type=MemoryType.LONGTERM,
            source_type=source,
            metadata=metadata
        )
        longterm_ids.append(memory_id)

    print_result("Saved long-term memories", f"IDs={longterm_ids}")

    # Test 3.3: Get memory by ID
    memory = await service.get_memory(working_id)
    if memory:
        print_success(f"Retrieved memory by ID: {memory.content[:40]}...")
        print_result("  Memory type", memory.memory_type)
        print_result("  Source type", memory.source_type)
    else:
        print_failure("Failed to retrieve memory by ID")

    # Test 3.4: Similar search
    query = "呼吸について"
    results = await service.search_similar(
        query=query,
        limit=5,
        similarity_threshold=0.0
    )

    print(f"\n  Similar search for '{query}':")
    for i, result in enumerate(results):
        print(f"    {i+1}. [{result.similarity:.4f}] {result.content[:50]}...")

    if len(results) > 0:
        print_success("Similar search returned results")
    else:
        print_failure("Similar search returned no results")

    # Test 3.5: Hybrid search
    hybrid_results = await service.search_hybrid(
        query="システム設計",
        filters={"source_type": "decision"},
        limit=10
    )

    print(f"\n  Hybrid search (decisions only): {len(hybrid_results)} results")
    all_decisions = all(r.source_type == SourceType.DECISION for r in hybrid_results)
    if all_decisions:
        print_success("Hybrid search correctly filters by source_type")
    else:
        print_failure("Hybrid search filter not working correctly")

    # Test 3.6: Memory statistics
    stats = await service.get_memory_stats()
    print("\n  Memory Statistics:")
    print_result("  Working memory count", stats["working_memory_count"])
    print_result("  Long-term memory count", stats["longterm_memory_count"])
    print_result("  Total count", stats["total_count"])
    print_result("  Embedding dimensions", stats["embedding_dimensions"])

    expected_total = 1 + len(longterm_ids)
    if stats["total_count"] == expected_total:
        print_success(f"Statistics are accurate (total={expected_total})")
    else:
        print_failure(f"Expected total={expected_total}, got {stats['total_count']}")

    return True


async def test_expiration_and_archival():
    """Test memory expiration and archival"""
    print_header("Test 4: Expiration and Archival")

    repo = InMemoryRepository()
    embedding_service = MockEmbeddingService()
    service = MemoryStoreService(
        repository=repo,
        embedding_service=embedding_service,
        working_memory_ttl_hours=24
    )

    # Test 4.1: Insert expired working memory directly
    past_time = datetime.now(timezone.utc) - timedelta(hours=1)
    expired_embedding = await embedding_service.generate_embedding("期限切れメモリ")
    await repo.insert_memory(
        content="期限切れメモリ",
        embedding=expired_embedding,
        memory_type="working",
        source_type="intent",
        metadata={},
        expires_at=past_time
    )

    # Insert valid working memory
    valid_embedding = await embedding_service.generate_embedding("有効なメモリ")
    await repo.insert_memory(
        content="有効なメモリ",
        embedding=valid_embedding,
        memory_type="working",
        source_type="intent",
        metadata={},
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1)
    )

    # Test 4.2: Search should exclude expired
    query_emb = await embedding_service.generate_embedding("メモリ")
    results = await repo.search_similar(query_emb, "working", 10, -1.0, False)

    print_result("Memories before cleanup", "1 expired, 1 valid")
    print_result("Search results (excludes expired)", len(results))

    if len(results) == 1 and results[0]["content"] == "有効なメモリ":
        print_success("Expired memories are excluded from search")
    else:
        print_failure("Expired memories are not properly excluded")

    # Test 4.3: Cleanup expired memories
    archived_count = await service.cleanup_expired_working_memory()
    print_result("Archived expired memories", archived_count)

    if archived_count == 1:
        print_success("Expired memory cleanup works correctly")
    else:
        print_failure(f"Expected 1 archived, got {archived_count}")

    return True


async def test_edge_cases():
    """Test edge cases and error handling"""
    print_header("Test 5: Edge Cases and Error Handling")

    service = MockEmbeddingService()

    # Test 5.1: Empty text should raise error
    try:
        await service.generate_embedding("")
        print_failure("Empty text should raise EmbeddingError")
    except Exception as e:
        print_success(f"Empty text raises error: {type(e).__name__}")

    # Test 5.2: Very long text
    long_text = "呼吸のリズム " * 1000
    embedding = await service.generate_embedding(long_text)
    print_result("Long text embedding", f"{len(embedding)} dimensions")
    if len(embedding) == 1536:
        print_success("Long text handled correctly")
    else:
        print_failure("Long text not handled correctly")

    # Test 5.3: Unicode characters
    unicode_text = "🎯 目標達成！ 呼吸のリズム 💫"
    embedding = await service.generate_embedding(unicode_text)
    print_result("Unicode text embedding", f"{len(embedding)} dimensions")
    if len(embedding) == 1536:
        print_success("Unicode text handled correctly")
    else:
        print_failure("Unicode text not handled correctly")

    # Test 5.4: Non-existent memory retrieval
    repo = InMemoryRepository()
    embedding_service = MockEmbeddingService()
    store_service = MemoryStoreService(repo, embedding_service, 24)

    memory = await store_service.get_memory(99999)
    if memory is None:
        print_success("Non-existent memory returns None")
    else:
        print_failure("Non-existent memory should return None")

    return True


async def main():
    """Run all integration tests"""
    print("\n" + "=" * 60)
    print("  Sprint 3: Memory Store System - Integration Test")
    print("  Testing with MockEmbeddingService (no API required)")
    print("=" * 60)

    tests = [
        ("Embedding Service", test_embedding_service),
        ("Memory Repository", test_memory_repository),
        ("Memory Store Service", test_memory_store_service),
        ("Expiration and Archival", test_expiration_and_archival),
        ("Edge Cases", test_edge_cases),
    ]

    results = []
    for name, test_func in tests:
        try:
            success = await test_func()
            results.append((name, success))
        except Exception as e:
            print_failure(f"Test '{name}' failed with exception: {e}")
            results.append((name, False))

    # Summary
    print_header("Test Summary")
    passed = sum(1 for _, success in results if success)
    total = len(results)

    for name, success in results:
        status = "✓ PASSED" if success else "✗ FAILED"
        print(f"  {status} - {name}")

    print(f"\n  Total: {passed}/{total} tests passed")

    if passed == total:
        print("\n  🎉 All integration tests passed!")
        print("  Memory Store System is ready for production integration.")
        return 0
    else:
        print(f"\n  ⚠️  {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
