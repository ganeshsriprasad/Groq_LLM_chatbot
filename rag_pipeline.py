import os
import time
import pytesseract
from PIL import Image
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from pypdf import PdfReader
import openai
import chromadb
from chromadb.config import Settings
from neo4j import GraphDatabase

# --- CONFIG ---
KNOWLEDGE_BASE_DIR = 'knowledge_base'
CHROMA_DB_DIR = 'chroma_db'
NEO4J_URI = 'bolt://localhost:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'password'  # Change this!
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# --- INIT ---
chroma_client = chromadb.Client(Settings(persist_directory=CHROMA_DB_DIR))
db = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# --- UTILS ---
def extract_text_from_pdf(pdf_path):
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

def extract_text_from_image(image_path):
    image = Image.open(image_path)
    return pytesseract.image_to_string(image)

def extract_text_from_txt(txt_path):
    with open(txt_path, 'r', encoding='utf-8') as f:
        return f.read()

def chunk_text(text, chunk_size=500, overlap=50):
    words = text.split()
    chunks = []
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i+chunk_size])
        if chunk:
            chunks.append(chunk)
    return chunks

def embed_text(text):
    client = openai.OpenAI(api_key=OPENAI_API_KEY)
    resp = client.embeddings.create(input=[text], model="text-embedding-ada-002")
    return resp.data[0].embedding

def add_to_chroma(doc_id, chunk, embedding):
    collection = chroma_client.get_or_create_collection('knowledge')
    collection.add(documents=[chunk], embeddings=[embedding], ids=[doc_id])

def add_to_neo4j(file_id, chunk_id, chunk_text):
    with db.session() as session:
        session.run("MERGE (f:File {id: $file_id})", file_id=file_id)
        session.run("MERGE (c:Chunk {id: $chunk_id, text: $text})", chunk_id=chunk_id, text=chunk_text)
        session.run("MATCH (f:File {id: $file_id}), (c:Chunk {id: $chunk_id}) MERGE (f)-[:CONTAINS]->(c)", file_id=file_id, chunk_id=chunk_id)

# --- FILE HANDLER ---
class KnowledgeBaseHandler(FileSystemEventHandler):
    def process_file(self, file_path):
        ext = os.path.splitext(file_path)[1].lower()
        file_id = os.path.basename(file_path)
        if ext == '.pdf':
            text = extract_text_from_pdf(file_path)
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']:
            text = extract_text_from_image(file_path)
        elif ext in ['.txt', '.md']:
            text = extract_text_from_txt(file_path)
        else:
            print(f"Unsupported file type: {file_path}")
            return
        chunks = chunk_text(text)
        for idx, chunk in enumerate(chunks):
            chunk_id = f"{file_id}_chunk_{idx}"
            embedding = embed_text(chunk)
            add_to_chroma(chunk_id, chunk, embedding)
            add_to_neo4j(file_id, chunk_id, chunk)
        print(f"Processed {file_path} with {len(chunks)} chunks.")

    def on_created(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_modified(self, event):
        if not event.is_directory:
            self.process_file(event.src_path)

    def on_deleted(self, event):
        if not event.is_directory:
            file_id = os.path.basename(event.src_path)
            # Remove from Chroma and Neo4j
            collection = chroma_client.get_or_create_collection('knowledge')
            ids_to_remove = [doc['id'] for doc in collection.get()['metadatas'] if doc['id'].startswith(file_id)]
            if ids_to_remove:
                collection.delete(ids=ids_to_remove)
            with db.session() as session:
                session.run("MATCH (f:File {id: $file_id}) DETACH DELETE f", file_id=file_id)
            print(f"Deleted {file_id} from vector and graph DB.")

# --- MAIN ---

def start_monitor():
    event_handler = KnowledgeBaseHandler()
    observer = Observer()
    observer.schedule(event_handler, KNOWLEDGE_BASE_DIR, recursive=False)
    observer.start()
    print(f"Monitoring {KNOWLEDGE_BASE_DIR} for changes...")
    # Initial scan: process only if there are files
    processed_files = set()
    try:
        while True:
            files = set(f for f in os.listdir(KNOWLEDGE_BASE_DIR) if os.path.isfile(os.path.join(KNOWLEDGE_BASE_DIR, f)))
            new_files = files - processed_files
            if new_files:
                for f in new_files:
                    event_handler.process_file(os.path.join(KNOWLEDGE_BASE_DIR, f))
                processed_files.update(new_files)
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_monitor()
