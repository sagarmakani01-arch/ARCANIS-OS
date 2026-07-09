# Semantic Search Example

import "std/ai" { cosine_similarity, semantic_search }
import "std/io"

struct Document {
    title: String
    content: String
}

fn search_documents(query: String, docs: [Document]) -> [(Document, f64)] {
    let query_emb = embed(query)
    let results: [(Document, f64)] = []

    for doc in docs {
        let doc_emb = embed(doc.title ++ " " ++ doc.content)
        let similarity = cosine_similarity(query_emb, doc_emb)
        results.push((doc, similarity))
    }

    results.sort(|a, b| b.1 - a.1)
    return results[:5]
}

let docs = [
    Document("AI Basics", "Introduction to artificial intelligence..."),
    Document("Language Design", "How to create a programming language..."),
    Document("OS Kernels", "Building operating systems from scratch...")
]

let results = search_documents("How do I build a language?", docs)
for (doc, score) in results {
    print("{doc.title}: {score}")
}
