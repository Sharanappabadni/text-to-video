from fastapi import FastAPI, Query, HTTPException, Body
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel
from datetime import datetime
import uuid
from helper_functions import *
from transformer import router, get_matching_video
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.include_router(router)

# Allow requests from the React application's domain
# origins = ["http://localhost:3000", "http://localhost:63342"]  # Add your frontend's domain

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all HTTP headers
)


class User(BaseModel):
    email: str
    name: str
    password: str
    gender: str
    age: int
    location: str


cluster = Cluster(["localhost"])


@app.post("/add_user/")
async def add_user(user: User):
    # Insert user details into the Cassandra database
    session = cluster.connect("text_to_video")
    query = f"INSERT INTO text_to_video.users (email, name, password, gender, age, location) VALUES ('{user.email}', '{user.name}', '{user.password}', '{user.gender}', {user.age}, '{user.location}')"
    session.execute(query)
    return {"message": "User added successfully"}


@app.post("/login/")
def login_user(email: str = Body(...), password: str = Body(...)):
    session = cluster.connect("text_to_video")
    query = f"SELECT * FROM text_to_video.users WHERE email = '{email}'"
    print(f"The query of login {query}")
    result = session.execute(query)
    print(f"The result of login {query}")

    if result:
        stored_password = result[0].password
        if stored_password == password:
            return {"message": "Login Successful"}
    # If the credentials do not match, return an error
    raise HTTPException(status_code=401, detail="Login failed, credentials are incorrect")


@app.post("/add_video_log/")
async def add_video_log(user_email: str, video_id: str, prompt: str, action: str,
                        prompt_submitted_time: datetime):
    try:
        session = cluster.connect("text_to_video")

        # Insert data into the video_logs table
        query = (
            "INSERT INTO text_to_video.video_logs (user_email, video_id, prompt, action, prompt_submitted_time) "
            f"VALUES ('{user_email}', {video_id}, '{prompt}', '{action}', '{prompt_submitted_time}')"
        )

        # Add the log entry
        session.execute(query)

        return {"message": "Video log added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create_keyspace/")
async def create_keyspace_endpoint(keyspace_name: str = Query(default='text_to_video', enum=['text_to_video'])):
    result = create_keyspace(keyspace_name)
    return {"message": result}


@app.post("/create_table/")
async def create_table_endpoint(keyspace_name: str = Query(default='text_to_video', enum=['text_to_video']),
                                table: str = Query(default='users', enum=['users', 'video_data', 'video_logs'])):
    result = create_table(keyspace_name, table)
    return {"message": result}


@app.post("/add_video_data/")
async def add_video_data(user_email: str, video_title: str, video_description: str, video_url: str, prompt: str,
                         prompt_sent_timestamp: str = None):
    try:
        session = cluster.connect("text_to_video")
        if not prompt_sent_timestamp:
            prompt_sent_timestamp = datetime.utcnow()
        # Generate a unique UUID for the video_id
        video_id = uuid.uuid4()

        # Insert data into the video_data table
        query = (
            "INSERT INTO text_to_video.video_data (video_id, user_email, video_title, video_description, video_url, prompt, "
            "prompt_sent_timestamp, video_stored_timestamp) "
            f"VALUES ({video_id}, '{user_email}', '{video_title}', '{video_description}', '{video_url}', '{prompt}', "
            f"'{prompt_sent_timestamp}', '{datetime.utcnow()}')"
        )
        session.execute(query)

        return {"message": "Video data added successfully", "video_id": str(video_id)}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class GetResponse(BaseModel):
    user_email: str
    prompt: str
    action: str


def split_prompt(prompt):
    # Calculate the middle index of the prompt
    middle_index = len(prompt) // 2

    # Split the prompt into two parts at the middle index
    first_part = prompt[:middle_index]
    second_part = prompt[middle_index:]

    return first_part, second_part


@app.post("/get_response/")
async def get_response(get_response_input: GetResponse):
    prompt = get_response_input.prompt
    action = get_response_input.action
    user_email = get_response_input.user_email
    prompt_sent_timestamp = datetime.utcnow()
    session = cluster.connect("text_to_video")
    # Execute the SELECT query
    query = f"SELECT name, location FROM text_to_video.users where email = '{user_email}'"
    result = session.execute(query).one()
    print(result)
    prompt = result.name + ' ' + result.location + ' ' + prompt
    print(prompt)
    if action == 'retrieve':
        matching_video_details = (await get_matching_video(user_email, prompt))
        matching_video_id = matching_video_details['video_id']
        max_similarity = matching_video_details['similarity']
        if matching_video_id:
            # Retrieve the video URL for the matching video_id from video_data
            video_url_query = f"SELECT video_url FROM text_to_video.video_data WHERE video_id = {matching_video_id}"
            video_url_result = session.execute(video_url_query)
            video_url = video_url_result[0].video_url if video_url_result else None

            if video_url:
                await add_video_log(user_email, matching_video_id, prompt, action, prompt_sent_timestamp)
                return {
                    "message": "Matching video found",
                    "video_id": str(matching_video_id),
                    "similarity": max_similarity,
                    "video_url": video_url
                }
            else:
                return {"message": "Matching video found, but video URL not available"}

        else:
            return {"message": "No matching video found"}

    if action == 'generate':
        video_title = 'xyz'
        video_description = 'xyz'
        from sd_pipeline import pipeline
        prompt_first_part, prompt_last_part = split_prompt(prompt)
        print(prompt_first_part, prompt_last_part)
        video_name = str(uuid.uuid4())
        video_path = pipeline.walk(
            prompts=[prompt_first_part, prompt_last_part],
            seeds=[42, 1337],
            num_interpolation_steps=1,
            height=512,  # use multiples of 64 if > 512. Multiples of 8 if < 512.
            width=512,  # use multiples of 64 if > 512. Multiples of 8 if < 512.
            output_dir='dreams',  # Where images/videos will be saved
            name=video_name,  # Subdirectory of output_dir where images/videos will be saved
            guidance_scale=8.5,  # Higher adheres to prompt more, lower lets model take the wheel
            num_inference_steps=5,  # Number of diffusion steps per image generated. 50 is good default
        )
        video_url = f'./dreams/{video_name}/{video_name}.mp4'
        video_id = video_name
        await add_video_data(user_email, video_title, video_description, video_url, prompt, prompt_sent_timestamp)
        await add_video_log(user_email, video_id, prompt, action, prompt_sent_timestamp)
        return {
            "message": "Video generated",
            "video_id": str(video_id),
            "video_url": video_url
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("api:app", host="0.0.0.0", port=9000, reload=True)
