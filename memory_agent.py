import os
import atexit
from dotenv import load_dotenv
from pathlib import Path
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

PROJECT_ROOT = Path(__file__).resolve().parent
GROQ_MODEL = "openai/gpt-oss-20b"

os.environ.setdefault("MEM0_DIR",str(PROJECT_ROOT / ".mem0"))
os.environ.setdefault("MEM_THRESHOLD","False")

load_dotenv(dotenv_path=PROJECT_ROOT / ".env")

from mem0 import Memory

MEM0_CONFIG = {
    "llm": {
        "provider": "groq",
        "config": {
            "model": GROQ_MODEL,
            "temperature": 0.1
        },
    },
    "vector_store": {
        "provider": "qdrant",
        "config": {
            "collection_name": "mem0_interview_prep",
            "embedding_model_dims": 768,
            "path": str(PROJECT_ROOT / "qdrant_data"),
        },
    },
    "embedder": {
        "provider": "gemini",
        "config": {
            "model": "models/gemini-embedding-001",
            "embedding_dims": 768,
        },
    },
}

SYSTEM_PROMPT = """You are an AI interview prep coach. Use the following memories \
about the candidate to personalize your questions, avoid repeating covered topics, \
and focus on their weak areas and target role.

Candidate memories:
{memories}

Based on this, either (a) ask the next interview question tailored to them, \
or (b) evaluate their answer and give concise feedback. Be specific and concise."""

CHAIN = ChatPromptTemplate.from_messages(
    [
    ("system", SYSTEM_PROMPT),
    ("human", "{question}"),
]) | ChatGroq(model=GROQ_MODEL, temperature=0.3) | StrOutputParser()

try:
    MEMORY = Memory.from_config(MEM0_CONFIG)
    MEMORY_INIT_ERROR = None
except Exception as e:
    memory = None
    MEMORY_INIT_ERROR = str(e)

def _format_memories(search_results)->str:
    items = search_results.get("results",[]) if isinstance(search_results,dict) else search_results
    memories = [
        f"- {item['memory']}"
        for item in items
        if isinstance(item,dict) and item.get("memory")
    ]
    return "\n".join(memories) if memories else "No relevant memories found."

def _close_memory() -> None:
    if memory:
        memory.close()
        memory = None

def get_memory_agent(question:str)->str:
    if MEMORY is None:
        return
    
    try:
        MEMORY.vector_store.client.close()
    except Exception as e:
        pass
    
    try:
        MEMORY.close()
    except Exception as e:
        pass

atexit.register(_close_memory)

def chat(user_id:str, user_message:str)->str:
    """Fetch relevant memories, call the LLM and then persis the exchange"""
    if MEMORY is None:
        return f"Error: Memory initialization failed: {MEMORY_INIT_ERROR}"
    
    try:
        search_results = MEMORY.search(query=user_message, filters={"user_id": user_id}, limit=5) 
        reply = CHAIN.invoke({"memories":_format_memories(search_results),"question":user_message})
        MEMORY.add(
            [
                {"role":"user", "content":user_message},
                {"role":"assistant", "content":reply},
            ],
            user_id=user_id,
        )
        return reply
    except Exception as e:
        return f"Error: {str(e)}"

def get_all_memories(user_id:str):
    if MEMORY is None:
        return f"Error: Memory initialization failed: {MEMORY_INIT_ERROR}"
    
    try:
        memories = MEMORY.get_all(user_id=user_id)
        return memories
    except Exception as e:
        return {"error": str(e), "results":[]}
