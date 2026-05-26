import numpy as np
from sentence_transformers import SentenceTransformer
import chromadb

model = SentenceTransformer("all-MiniLM-L6-v2")
chroma_client = chromadb.PersistentClient(path="./chroma_db")

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def deduplicate_with_similarity(documents, metadatas, distances, threshold=0.95):
    if not documents:
        return documents, metadatas, distances
    
    embeddings = model.encode(documents)
    deduped_docs = [documents[0]]
    deduped_meta = [metadatas[0]]
    deduped_dist = [distances[0]]
    deduped_embs = [embeddings[0]]
    
    for i in range(1, len(documents)):
        is_duplicate = False
        for kept_emb in deduped_embs:
            sim = cosine_similarity(embeddings[i], kept_emb)
            if sim > threshold:
                is_duplicate = True
                break
        if not is_duplicate:
            deduped_docs.append(documents[i])
            deduped_meta.append(metadatas[i])
            deduped_dist.append(distances[i])
            deduped_embs.append(embeddings[i])
    
    return deduped_docs, deduped_meta, deduped_dist

def retrieve(query, collection=None, top_k=3):
    # connect here, not at import time
    if collection is None:
        collection = chroma_client.get_collection(name="tenant-rights")
    
    query_embedding = model.encode([query])[0].tolist()
    
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k * 3,
        include=["metadatas", "documents", "distances"]
    )
    
    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]
    
    documents, metadatas, distances = deduplicate_with_similarity(
        documents, metadatas, distances
    )
    
    return {
        "documents": [documents[:top_k]],
        "metadatas": [metadatas[:top_k]],
        "distances": [distances[:top_k]]
    }