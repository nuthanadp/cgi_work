import asyncio
from dotenv import load_dotenv
import os
import streamlit as st
from PyPDF2 import PdfReader
from langchain_text_splitters import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.llms.ollama import Ollama
from langchain.chains import RetrievalQA
from langchain_community.embeddings import OllamaEmbeddings

# Cache the text splitting and embedding generation process
@st.cache_data
def process_pdf(pdf):
    pdf_reader = PdfReader(pdf)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()

    text_splitter = CharacterTextSplitter(
        separator="\n",
        chunk_size=1000,
        chunk_overlap=100,  # Reduce overlap to speed up
        length_function=len
    )
    chunks = text_splitter.split_text(text)
    
    # Batch embeddings
    embeddings = OllamaEmbeddings(model="llama3.1")
    knowledge_base = FAISS.from_texts(chunks, embeddings)
    
    return knowledge_base

async def query_qa(knowledge_base, user_qstn):
    llm = Ollama(model="llama3.1")
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm, chain_type="stuff", retriever=knowledge_base.as_retriever())
    llm_answer = qa_chain.invoke({"query": user_qstn})
    return llm_answer

def main():
    load_dotenv()
    st.set_page_config(page_title="ask pdf")
    os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY')

    st.header("ask pdf")

    pdf = st.file_uploader("upload pdf", type="pdf")

    if pdf is not None:
        try:
            knowledge_base = process_pdf(pdf)
            user_qstn = st.text_input("ask any question")

            if user_qstn:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                llm_answer = loop.run_until_complete(query_qa(knowledge_base, user_qstn))
                st.write(llm_answer)

        except Exception as e:
            st.error(f"An error occurred: {e}")

if __name__ == '__main__':
    main()
