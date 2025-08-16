from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from qdrant_client import QdrantClient, models
from qdrant_client.http.models import PointStruct
import os, glob
import uuid
import openai

openai.api_key = "openai-api-key"

def read_data_from_pdf(pdf_path: str) -> str:
    text: str = ""
    with open(pdf_path, 'rb') as file:
        pdf_reader = PdfReader(file)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text


def get_text_chunks(text: str) -> list[str]:
    text_splitter = CharacterTextSplitter(
        separator="\n", chunk_size=1000, chunk_overlap=200,
    )
    chunks: list[str] = text_splitter.split_text(text)
    return chunks


def get_embedding(text_chunks: list[str]) -> list[dict]:
    points: list[dict] = []
    for chunk in text_chunks:
        chunk: str = chunk.replace("\n", " ")
        response = openai.embeddings.create(
            input = chunk, model="text-embedding-ada-002"
        )
 
        embeddings: list[str] = response.data[0].embedding
        point_id = str(uuid.uuid4())
        points.append(PointStruct(id=point_id, vector=embeddings, payload={"text": chunk}))

    return points


def create_answer_with_context(query: str) -> str:
    response = openai.embeddings.create(
        input = query,
        model="text-embedding-ada-002",
    )

    embeddings = response.data[0].embedding
    
    search_results: str = connection.search(
        collection_name = "resume_collection",
        query_vector=embeddings,
        limit = 3
    )
    print("Question: ", query, '\n')

    prompt: str = ""
    for result in search_results:
        prompt += result.payload['text']
    prompt_with_message: str = " ".join([prompt,query])
    completion = openai.completions.create(
        model = "gpt-3.5-turbo-instruct",
        prompt = prompt_with_message,
        # messages = [
        #     {"role": "user", "content" : concatenated_string}
        # ]
        temperature=0.1,
        max_tokens=2048
    )
    
    return completion.choices[0].text.strip()


###            MAIN            ###   
path = "C:/Users/agordinschii/OneDrive - DataArt Inc/Desktop/AI learning course tasks/ai-learning-course-tasks/sample_dataset"    

###           qdrant             ###

connection = QdrantClient(url="localhost:6333/dashboard")

# connection.create_collection(
#     collection_name="resume_collection",
#     vectors_config=models.VectorParams(size=1536, distance=models.Distance.COSINE),
# )

# info = connection.get_collection(collection_name="resume_collection")

# for filename in glob.glob(
#     os.path.join(path, "*.pdf")
# ):  # glob is used to match .pdf files only
#     if os.path.getsize(filename) == 0:
#         print("The following file is empty: ", filename)
#         continue
#     text = read_data_from_pdf(filename)
#     # print(text)
#     chunks = get_text_chunks(text)
#     # print_chunks(chunks)
#     points = get_embedding(chunks)
#     # print(points[1])
#     connection.upsert(
#             collection_name="resume_collection",
#             wait=True,
#             points=points,
#         )

question = "Are there any python devs mentioned in the above text? How many are there?"

answer = create_answer_with_context(question)

print("Answer : ", answer, "\n")


streamlit
техники prompt engineering
