from app.loaders.pdf_loader import PDFLoader
from app.chunking.text_chunker import TextChunker
from app.embeddings.embedder import Embedder
from app.utils.similarity import cosine_similarity


def main():

    loader = PDFLoader("data/IIA_HR_Policy.pdf")

    document = loader.load()

"""     print(document[:1000])
    print(type(document))
    print(len(document))
    print(document[-500:]) """

    '''chunker = TextChunker(chunk_size=100, overlap=20)

    chunks = chunker.split_text(document)

    print(f"Total Chunks: {len(chunks)}")

    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}")
        #print(chunk)

    embedder = Embedder()

    sentence1 = "I want to buy a car."

    sentence2 = "I want to purchase an automobile."

    embedding1 = embedder.embed(sentence1)

    embedding2 = embedder.embed(sentence2)

    sentence3 = "Tigers live in forests."

    embedding3 = embedder.embed(sentence3)

    print(type(embedding1))

    print(len(embedding1))

    print(embedding1[:10])
    print(embedding3[:10])
    sim_1_2 = cosine_similarity(embedding1, embedding2)  
    sim_1_3 = cosine_similarity(embedding1, embedding3)  
    sim_2_3 = cosine_similarity(embedding2, embedding3)  


    print(f"Similarity between sentence 1 and 2: {sim_1_2}")
    print(f"Similarity between sentence 1 and 3: {sim_1_3}")
    print(f"Similarity between sentence 2 and 3: {sim_2_3}")'''


if __name__ == "__main__":
    main()