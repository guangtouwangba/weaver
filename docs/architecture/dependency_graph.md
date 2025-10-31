# Component Dependency Graph

```mermaid
graph TD
    subgraph API
        RouterIngest[apps/api/app/routers/ingest.py]
        RouterSearch[apps/api/app/routers/search.py]
        RouterQA[apps/api/app/routers/qa.py]
    end

    subgraph Services
        IngestSvc[packages/rag-core/rag_core/pipeline/services/ingest_service.py]
        QASvc[packages/rag-core/rag_core/pipeline/services/qa_service.py]
    end

    subgraph Dependencies
        Settings[apps/api/app/dependencies.py]
        Retriever[packages/rag-core/rag_core/chains/vectorstore.py\n(get_vector_store)]
    end

    subgraph Graphs
        IngestGraph[packages/rag-core/rag_core/graphs/ingest_graph.py]
        QAGraph[packages/rag-core/rag_core/graphs/qa_graph.py]
    end

    subgraph Chains
        Loader[packages/rag-core/rag_core/chains/loaders.py]
        Splitter[packages/rag-core/rag_core/chains/splitters.py]
        Embeddings[packages/rag-core/rag_core/chains/embeddings.py]
        VectorStore[packages/rag-core/rag_core/chains/vectorstore.py]
        QAChain[packages/rag-core/rag_core/chains/qa_chain.py]
    end

    RouterIngest --> IngestSvc
    RouterSearch --> QASvc
    RouterQA --> QAGraph

    IngestSvc --> IngestGraph
    QASvc --> Retriever

    Settings --> Retriever
    Settings --> QAGraph
    Settings --> IngestGraph

    IngestGraph --> Loader
    IngestGraph --> Splitter
    IngestGraph --> Embeddings
    IngestGraph --> VectorStore

    QAGraph --> VectorStore
    QAGraph --> QAChain
```
