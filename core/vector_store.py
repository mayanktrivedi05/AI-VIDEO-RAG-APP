import os 
import shutil
from langchain_chroma import Chroma 
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHROMA_DIR = "vector_db"
COLLECTION_NAME = "meeting_transcript"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def get_embeddings():
    return HuggingFaceEmbeddings(
        model_name = EMBEDDING_MODEL,
        model_kwargs = {"device" : 'cpu'}
    )

def clear_vector_store():
    """Clear previous vector database to prevent data leak across videos."""
    if os.path.exists(CHROMA_DIR):
        try:
            shutil.rmtree(CHROMA_DIR, ignore_errors=True)
            print("Cleared previous vector store.")
        except Exception as e:
            print(f"Warning clearing vector store: {e}")

def build_vector_store(transcript : str)->Chroma:
    print("Building vector Store...")
    clear_vector_store()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 500,
        chunk_overlap = 50,
    )
    texts = splitter.split_text(transcript)

    documents = [
        Document(
            page_content = text,
            metadata = {"chunk_id":i}
        )
        for i, text in enumerate(texts)
    ]

    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(
        documents = documents,
        embedding = embeddings,
        persist_directory = CHROMA_DIR,
        collection_name = COLLECTION_NAME
    )

    print(f"Vector Store Built with {len(documents)} chunks")
    return vector_store


def load_vector_store() ->Chroma:
    embeddings = get_embeddings()
    vector_store = Chroma(
        persist_directory = CHROMA_DIR,
        embedding_function = embeddings,
        collection_name = COLLECTION_NAME
    )
    return vector_store

def get_retriever(k : int = 3):
    vector_store = load_vector_store()
    return vector_store.as_retriever(
        search_type = "similarity",
        search_kwargs = {"k":k}
    )
