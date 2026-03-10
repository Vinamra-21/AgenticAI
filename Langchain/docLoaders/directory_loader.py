from langchain_community.document_loaders import DirectoryLoader, PyPDFLoader

loader = DirectoryLoader(
    path='books',
    glob='*.pdf',
    loader_cls=PyPDFLoader
)

docs = loader.lazy_load() #load and lazy load , lazy load loads only when needed

for document in docs:
    print(document.metadata)