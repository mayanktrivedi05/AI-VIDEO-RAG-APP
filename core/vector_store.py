import os 
from langchain_chroma import Chroma 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

EMBEDDING_MODEL = "all-MiniLM-L6-v2"
_CURRENT_VECTOR_STORE = None

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,
        model_kwargs = {"device" : 'cpu'}
    )

def build_vector_store(transcript: str) -> Chroma:
    global _CURRENT_VECTOR_STORE
    print("Building in-memory Vector Store...")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50,
    )
    texts = splitter.split_text(transcript)

    documents = [
        Document(
            page_content = text,
            metadata = {"chunk_id": i}
        )
        for i, text in enumerate(texts)
    ]

    embeddings = get_embeddings()

    # In-Memory Chroma Vector Store (0% SQLite File Lock / Code 14 Error)
    vector_store = Chroma.from_documents(
        documents = documents,
        embedding = embeddings
    )

    _CURRENT_VECTOR_STORE = vector_store
    print(f"Vector Store Built in memory with {len(documents)} chunks.")
    return vector_store


def load_vector_store() -> Chroma:
    global _CURRENT_VECTOR_STORE
    return _CURRENT_VECTOR_STORE
