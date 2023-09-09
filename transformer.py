from sentence_transformers import SentenceTransformer, util
from cassandra_df import session
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix='/transformer', tags=['Transformer'])

try:
    # Load the Sentence Transformer model from the saved directory
    model = SentenceTransformer('./models/paraphrase-MiniLM')
except:
    # Load the Sentence Transformer model
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
    model.save('./models/paraphrase-MiniLM')

@router.post("/get_matching_video/")
async def get_matching_video(user_email: str, input_prompt: str):
    try:
        # Encode the input prompt
        input_embedding = model.encode(input_prompt, convert_to_tensor=True)

        # Retrieve prompts and embeddings from the video_data table
        query = "SELECT video_id, prompt FROM text_to_video.video_data"
        rows = session.execute(query)

        # Calculate cosine similarity and find the video with the maximum similarity
        max_similarity = -1.0
        matching_video_id = None

        for row in rows:
            stored_prompt = row.prompt
            stored_embedding = model.encode(stored_prompt, convert_to_tensor=True)

            # Calculate cosine similarity
            similarity = util.pytorch_cos_sim(input_embedding, stored_embedding).item()

            if similarity > max_similarity:
                max_similarity = similarity
                matching_video_id = row.video_id

        if matching_video_id:
            return {"message": "Matching video found", "video_id": str(matching_video_id), "similarity": max_similarity}
        else:
            return {"message": "No matching video found"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
