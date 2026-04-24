from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager
from typing import Optional
import os
import base64
from dotenv import load_dotenv

# LangChain libraries (unchanged from original)
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.messages import HumanMessage, SystemMessage

load_dotenv()

# --- Global singletons (initialized once at startup) ---
vectorstore = None
llm = None
DB_FAISS_PATH = 'vectorstore/db_faiss'


def initialize_knowledge_base():
    """Initialize the FAISS vector store from PDFs or cache. (Unchanged RAG logic)"""
    global vectorstore

    # HuggingFace Embeddings Model
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    # 1. Check if previously saved Embeddings exist
    if os.path.exists(DB_FAISS_PATH):
        print("Using previously created Embeddings (Cache)...")
        try:
            vectorstore = FAISS.load_local(
                DB_FAISS_PATH, embeddings, allow_dangerous_deserialization=True
            )
            print(" Knowledge Base Loaded from Cache!")
            return
        except Exception as e:
            print(f" Cache loading error: {e}. Rebuilding...")

    # 2. New pdf embeddings creating
    print("Reading PDFs and creating embeddings...")

    pdf_paths = [
        "data/Maternal & Newborn Strat Plan .pdf",
        "data/maternal_care_healthcare_workers.pdf",
    ]

    all_docs = []
    for pdf_path in pdf_paths:
        if os.path.exists(pdf_path):
            print(f"   Loading: {pdf_path}")
            loader = PyPDFLoader(pdf_path)
            docs = loader.load()
            all_docs.extend(docs)
        else:
            print(f" PDF not found: {pdf_path}")

    if all_docs:
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=100
        )
        splits = text_splitter.split_documents(all_docs)

        # Vector Store development
        vectorstore = FAISS.from_documents(documents=splits, embedding=embeddings)

        # 3. Save into local directory for future use
        vectorstore.save_local(DB_FAISS_PATH)
        print(" Knowledge Base Created & Saved Locally!")
    else:
        print(" NO PDFs loaded. Knowledge Base is empty.")


# --- FastAPI Lifespan (replaces Flask's module-level init) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize knowledge base and LLM once on startup."""
    global llm
    initialize_knowledge_base()
    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
    print("LLM initialized.")
    yield


# --- FastAPI App ---
app = FastAPI(
    title="Maternal & Newborn Health Chatbot API",
    description="AI-powered chatbot for maternal and newborn health queries in Sri Lanka. "
    "Uses RAG (Retrieval-Augmented Generation) with FAISS vector store and Google Gemini.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow Flutter app and any origin during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Request / Response Models ---
class ChatRequest(BaseModel):
    question: str = Field(..., description="The user's question text", examples=["මාතෘ සෞඛ්‍ය යනු කුමක්ද?"])
    image: Optional[str] = Field(
        None,
        description="Optional Base64 encoded image string (JPEG/PNG)",
    )


class ChatResponse(BaseModel):
    answer: str = Field(..., description="Generated answer from the chatbot")
    error: Optional[str] = Field(None, description="Error message if something went wrong")


# --- Root Redirect ---
@app.get("/", include_in_schema=False)
async def root():
    """Redirect root to Swagger docs."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/docs")


# --- Health Check ---
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint for Choreo and monitoring."""
    return {
        "status": "healthy",
        "knowledge_base_loaded": vectorstore is not None,
    }


# --- Chat Endpoint (RAG logic unchanged) ---
@app.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat(request: ChatRequest):
    """
    Send a question (and optional image) to the maternal health chatbot.

    The chatbot uses RAG to retrieve relevant context from the knowledge base
    and generates an answer using Google Gemini.
    """
    user_question = request.question
    image_base64 = request.image

    # LLM already initialized at startup — use global instance

    system_instruction = (
        "ඔබ ශ්‍රී ලංකාවේ මාතෘ සහ ළදරු සෞඛ්‍ය පිළිබඳ සහායක AI නිලධාරියෙකි. "
        " ප්‍රශ්නය සිංහලෙන් අසයිනම් පමණක් පිළිතුරු සිංහලෙන් ලබා දෙන්න. මෙය වෛද්‍ය උපදෙසක් නොවන බව කරුණාවෙන් සලකන්න."
        " පරිශීලකයා විසින් ලබා දී ඇති පසුබැසීම සහ ඡායාරූපය අනුව පිළිතුරු සපයන්න."
        "මාතෘ සහ ළදරු සෞඛ්‍ය  හැර අසනන ප්‍රශ්න සඳහා පිළිතුරු නොදෙන්න hi,Hello,කොහොමද,What is your name? යන වැනි සාමාන්‍ය ආමන්ත්‍රවාචී ප්‍රශ්න සඳහාද පිළිතුරු දෙන්න."
        " අවශ්‍ය නම්, 'සමාවන්න, මට ඒ ගැන තොරතුරු නැත' යනුවෙන් පිළිතුරු දෙන්න."
    )

    context_text = ""
    if vectorstore:
        try:
            retriever = vectorstore.as_retriever()
            relevant_docs = retriever.invoke(user_question)
            context_text = "\n\n".join([d.page_content for d in relevant_docs])
        except Exception as e:
            print(f"Retrieval Error: {e}")

    messages = [SystemMessage(content=system_instruction)]

    if image_base64:
        content = [
            {
                "type": "text",
                "text": f"Context: {context_text}\n\nQuestion: {user_question}",
            },
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"},
            },
        ]
        messages.append(HumanMessage(content=content))
    else:
        messages.append(
            HumanMessage(
                content=f"Context: {context_text}\n\nQuestion: {user_question}"
            )
        )

    try:
        response = llm.invoke(messages)
        return ChatResponse(answer=response.content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"answer": "සමාවන්න, දෝෂයක් ඇති විය.", "error": str(e)},
        )


# --- Run with Uvicorn ---
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=port, reload=False)
