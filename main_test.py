from app.loaders.pdf_loader import PDFLoader
from app.chunking.text_chunker import TextChunker
from app.embeddings.embedder import Embedder
from app.utils.similarity import cosine_similarity


def main():

    documents = [
    "Employees receive 30 annual leave days.",
    "Python is a programming language.",
    "Cats are friendly animals.",
    "Cars require regular maintenance.",
    "Doctors treat patients." ]

    embedder = Embedder()
    embed_list=[]
    for doc in documents:
        embed_list.append(embedder.embed(doc))

    query=input("Enter your query: ")
    query_embed=embedder.embed(query)

    cos_list=[]
    count=0
    for doc_embed in embed_list:
        cos_list.append(cosine_similarity(query_embed,doc_embed))
        print(f"\n doc embed list entry is ",count)
        print(f"\n doc embed value is ",doc_embed[:10])
        count+=1

    cos_list_sorted=sorted(cos_list,reverse=True)
    print("below is the top 3 cosine similarity scores\n")
    print(cos_list_sorted[0:3])


if __name__ == "__main__":
    main()