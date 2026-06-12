#!/usr/bin/env xcrun swift
/// Benchmark: Apple Natural Language framework embedding (macOS built-in)
///
/// macOS 内置，零安装。注意：
/// - 仅英文支持（中文会被拆成单字）
/// - 512 维固定维度
/// - 底层走 CPU AMX 协处理器
///
/// Usage:
///   swiftc -o /tmp/run_apple_nl run_apple_nl.swift && /tmp/run_apple_nl
///   # 或直接用 swift run_apple_nl.swift（解释模式，略慢，但不影响）
///
/// 结果输出为 JSON，可通过 Python 解析：
///   swift run_apple_nl.swift | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['texts_per_sec'], 'texts/s')"

import Foundation
import NaturalLanguage

/// 120 mixed Chinese-English test texts
let testTexts: [String] = [
    "Artificial intelligence is transforming industries worldwide.",
    "Deep learning has achieved breakthrough results in NLP.",
    "Vector databases are essential for semantic search at scale.",
    "RAG combines retrieval and generation for accurate AI responses.",
    "What is the weather like in Beijing today?",
    "Quantum computing may surpass classical computers in specific domains.",
    "The attention mechanism is key to the Transformer architecture.",
    "Digital transformation faces data silo challenges.",
    "Consistency, availability, and partition tolerance must be balanced.",
    "Low-code platforms enable non-developers to build applications.",
    "ML model deployment requires continuous monitoring and tuning.",
    "Edge computing extends data processing from cloud to devices.",
    "Information security relies on confidentiality, integrity, and availability.",
    "Open source communities accelerate software innovation.",
    "Multimodal models can understand text, images, and audio.",
    "Container technology enables rapid application deployment.",
    "Microservices decompose monolithic apps into independent services.",
    "Knowledge graphs power recommendation and Q&A systems.",
    "Data privacy is becoming a global regulatory focus.",
    "Automated testing is crucial for software quality assurance.",
    "The quick brown fox jumps over the lazy dog.",
    "Machine learning transforms how we process and analyze data.",
    "Cloud computing enables organizations to scale on demand.",
    "Python dominates data science and machine learning.",
    "Apple Silicon revolutionized Mac performance with unified memory.",
    "The Transformer architecture was introduced in 2017.",
    "Vector embeddings convert text to numerical representations.",
    "Open source powers modern technology infrastructure.",
    "Database indexing involves trade-offs in read and write performance.",
    "Neural networks minimize loss functions through gradient descent.",
    "APIs define communication between software components.",
    "Git is essential for collaborative software development.",
    "Container orchestration manages distributed application lifecycles.",
    "The Internet of Things connects billions of devices worldwide.",
    "Prompt engineering is crucial for working with LLMs.",
    "Multi-factor authentication is a security best practice.",
    "Large language models perform tasks they weren't trained on.",
    "Time series analysis is used in finance and forecasting.",
    "Regular expressions provide powerful text matching.",
    "What is the difference between supervised and unsupervised learning?",
    "How does batch normalization stabilize neural network training?",
    "Explain transfer learning and when to use it.",
    "Compare B-Tree and LSM-Tree indexes.",
    "Describe TCP and UDP protocol differences.",
    "What is the CAP theorem and why does it matter?",
    "How does garbage collection work in modern JVMs?",
    "Explain sharding in distributed databases.",
    "What is the difference between AOT and JIT compilation?",
    "How does HNSW achieve fast approximate nearest neighbor search?",
    "Describe the role of attention masks in transformer models.",
    "Compare eager execution and graph mode in ML frameworks.",
    "How does gRPC handle bi-directional streaming?",
    "Explain the sliding window protocol in reliable data transmission.",
    "Compare SIMD and MIMD parallel architectures.",
    "How does Raft consensus ensure safety during network partitions?",
    "Explain consistent hashing for load distribution.",
    "What is the purpose of write-ahead logging in databases?",
    "Best way to learn deep learning in 2026.",
    "Why is RAG better than fine-tuning for custom data?",
    "Is Apple Silicon good for ML workloads?",
    "How to choose the right vector database.",
    "What is the difference between embedding and tokenization?",
    "CUDA vs Metal Performance Shaders on Mac.",
    "How to benchmark embedding model performance.",
    "Why does batch size affect embedding throughput?",
    "BGE vs OpenAI embedding quality comparison.",
    "When to use sparse vs dense vector retrieval.",
    "How to set up a local AI development environment on Mac.",
    "What are best practices for prompt engineering?",
    "Is M3 Ultra overkill for local LLM inference?",
    "How to quantize models for Apple Silicon.",
    "What is the future of local AI assistants?",
    "How to build a personal RAG system on Mac.",
    "What are embedding pooling strategies?",
    "How to cache embeddings for faster retrieval.",
    "Cross-encoder vs bi-encoder for re-ranking.",
    "Binary embeddings vs float embeddings trade-offs.",
    "How does batch normalization work in practice?",
    "What are the best practices for data pipeline design?",
    "Explain the concept of data lineage and its importance.",
    "How do modern CPU branch predictors work?",
    "What is the memory hierarchy and why does it matter?",
    "Describe the observer pattern in software design.",
    "How do database query optimizers work internally?",
    "What is the difference between RAID levels?",
    "Explain the working principle of a bloom filter.",
    "How do modern NAND flash SSDs manage wear leveling?",
    "Describe the differences between hypervisors and containers.",
    "What is tail latency and why should you care?",
    "Explain circuit breaking in microservice architectures.",
    "How does TCP congestion control work?",
    "Describe the concept of eventual consistency.",
    "What is the difference between rate limiting and throttling?",
    "Explain the role of a service mesh in Kubernetes.",
    "How do cryptographic hash functions differ from encryption?",
    "Describe the producer-consumer problem and its solutions.",
    "What is the difference between row and columnar storage?",
    "Explain how vectorized query execution improves performance.",
    "How do modern compilers optimize loop performance?",
    "Describe the differences between stack and heap memory.",
    "What is the purpose of a write buffer in CPU architecture?",
    "Explain the concept of NUMA and its performance implications.",
    "How do distributed consensus algorithms maintain consistency?",
    "Describe the differences between message queues and event streams.",
    "What is the role of a schema registry in data streaming?",
    "Explain the concept of data locality in distributed systems.",
    "How do approximate query processing techniques work?",
    "Describe the trade-offs between materialized views and views.",
    "What is the difference between push and pull data pipelines?",
    "Explain how columnar compression achieves high compression ratios.",
    "How do database transaction isolation levels prevent anomalies?",
    "Describe the concept of data skipping in modern data lakes.",
    "What is the role of a catalog service in data mesh architecture?",
    "Explain the difference between optimistic and pessimistic locking.",
    "How do performance monitoring tools measure CPU utilization?",
    "Describe the concept of thread safety and common synchronization patterns.",
]

func benchmark() -> [String: Any] {
    guard let embedder = NLEmbedding.sentenceEmbedding(for: .english) else {
        return ["error": "Failed to create NLEmbedding"]
    }
    
    let dim = embedder.dimension
    let warmupRuns = 2
    let measureRuns = 5
    let batchSize = testTexts.count
    var latencies: [Double] = []
    
    // Warmup
    for _ in 0..<warmupRuns {
        for text in testTexts {
            _ = embedder.vector(for: text)
        }
    }
    
    // Measure
    for _ in 0..<measureRuns {
        let t0 = CFAbsoluteTimeGetCurrent()
        for text in testTexts {
            _ = embedder.vector(for: text)
        }
        let t1 = CFAbsoluteTimeGetCurrent()
        latencies.append(t1 - t0)
    }
    
    let totalTexts = Double(testTexts.count * measureRuns)
    let totalTime = latencies.reduce(0, +)
    let textsPerSec = totalTexts / totalTime
    let sortedLat = latencies.sorted()
    let avgMs = latencies.reduce(0, +) / Double(latencies.count) * 1000
    let p50Ms = sortedLat[sortedLat.count / 2] * 1000
    
    return [
        "texts_per_sec": Int(textsPerSec),
        "latency_avg_ms": Int(avgMs),
        "latency_p50_ms": Int(p50Ms),
        "dimension": dim,
        "language": "english",
        "num_texts": testTexts.count,
        "num_runs": measureRuns,
        "total_time_s": Int(totalTime),
    ]
}

let result = benchmark()
if let jsonData = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]),
   let jsonStr = String(data: jsonData, encoding: .utf8) {
    print("=== Apple Natural Language Embedding Benchmark ===")
    print(jsonStr)
}
