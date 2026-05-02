from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,      # bigger = more context
        chunk_overlap=150,   # preserves continuity
        separators=["\n\n", "\n", ".", " "]  # smarter splitting
    )
    return splitter.split_text(text)