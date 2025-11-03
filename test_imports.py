#!/usr/bin/env python3
"""Test script to verify imports work correctly."""

import sys

print("Testing imports...\n")
errors = []

# Test 1
try:
    print("1. Testing embed_chunks import...")
    from rag_core.chains.embeddings import embed_chunks
    print("   ✅ embed_chunks imported successfully\n")
except ImportError as e:
    print(f"   ❌ Failed: {e}\n")
    errors.append(("embed_chunks", e))

# Test 2
try:
    print("2. Testing build_embedding_function import...")
    from rag_core.chains.embeddings import build_embedding_function
    print("   ✅ build_embedding_function imported successfully\n")
except ImportError as e:
    print(f"   ❌ Failed: {e}\n")
    errors.append(("build_embedding_function", e))

# Test 3
try:
    print("3. Testing OpenRouterEmbeddings import...")
    from rag_core.chains.embeddings import OpenRouterEmbeddings
    print("   ✅ OpenRouterEmbeddings imported successfully\n")
except ImportError as e:
    print(f"   ❌ Failed: {e}\n")
    errors.append(("OpenRouterEmbeddings", e))

# Test 4
try:
    print("4. Testing chains package import...")
    from rag_core.chains import build_embedding_function
    print("   ✅ build_embedding_function from chains package imported successfully\n")
except ImportError as e:
    print(f"   ❌ Failed: {e}\n")
    errors.append(("chains package", e))

# Test 5
try:
    print("5. Testing ingest_graph import...")
    from rag_core.graphs.ingest_graph import build_ingest_graph
    print("   ✅ ingest_graph imported successfully\n")
except ImportError as e:
    print(f"   ❌ Failed: {e}\n")
    errors.append(("ingest_graph", e))

# Test 6
try:
    print("6. Testing qa_graph import...")
    from rag_core.graphs.qa_graph import build_qa_graph
    print("   ✅ qa_graph imported successfully\n")
except ImportError as e:
    print(f"   ❌ Failed: {e}\n")
    errors.append(("qa_graph", e))

# Test 7
try:
    print("7. Testing graphs package import...")
    from rag_core.graphs import build_ingest_graph, build_qa_graph
    print("   ✅ graphs package imported successfully\n")
except ImportError as e:
    print(f"   ❌ Failed: {e}\n")
    errors.append(("graphs package", e))

# Test 8 - Cross imports
try:
    print("8. Testing cross-module imports...")
    from rag_core.chains.embeddings import embed_chunks
    from rag_core.chains.vectorstore import persist_embeddings
    from rag_core.graphs.state import DocumentIngestState
    print("   ✅ Cross-module imports successful\n")
except ImportError as e:
    print(f"   ❌ Failed: {e}\n")
    errors.append(("cross-module", e))

# Summary
print("=" * 60)
if errors:
    print(f"❌ {len(errors)} test(s) failed:\n")
    for name, error in errors:
        print(f"  - {name}: {error}")
    sys.exit(1)
else:
    print("✅ All imports successful! Circular import issue is resolved.")
    sys.exit(0)

