# ai/tasks.py
from celery import shared_task
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from .models import LeaseDocument, LeaseChunk

@shared_task
def process_lease_document(document_id: int):
    # 1. Lock the document status
    doc = LeaseDocument.objects.get(id=document_id)
    doc.status = "processing"
    doc.save(update_fields=["status"])

    try:
        # 2. Extract text natively from the PDF file path
        loader = PyPDFLoader(doc.file.path)
        pages = loader.load()

        # 3. Split into semantically meaningful chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,  # Prevents cutting sentences in half
            separators=["\n\n", "\n", " ", ""]
        )
        chunks = text_splitter.split_documents(pages)

        # 4. Generate 384-dimensional embeddings locally
        embeddings_model = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2"
        )

        # 5. Bind chunks strictly to the workspace context for zero-trust isolation
        chunk_records = []
        for index, chunk in enumerate(chunks):
            vector = embeddings_model.embed_query(chunk.page_content)
            chunk_records.append(
                LeaseChunk(
                    workspace=doc.workspace,
                    document=doc,
                    content=chunk.page_content,
                    embedding=vector,
                    chunk_index=index
                )
            )

        # 6. Perform a single batch insert to pgvector for high performance
        LeaseChunk.objects.bulk_create(chunk_records)

        doc.status = "completed"
        doc.save(update_fields=["status"])

    except Exception as e:
        doc.status = "failed"
        doc.save(update_fields=["status"])
        raise e