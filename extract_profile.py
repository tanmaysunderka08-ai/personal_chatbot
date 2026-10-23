import os
from dotenv import load_dotenv
from groq import Groq
import json
import pymupdf as fitz
import docx
from models import Resume
from pathlib import Path

base_dir=Path(__file__).parent
resume_dir=base_dir / "resume"
profile_path=base_dir / "profile.json"

if profile_path.exists():
    raise SystemExit(f"Profile file already exists at {profile_path}. Please remove it before running the script.")

load_dotenv()
my_api_key = os.getenv("GROQ_API_KEY")
if not my_api_key:
    raise ValueError("GROQ_API_KEY environment variable not set")

my_client = Groq(api_key=my_api_key)
my_model = "openai/gpt-oss-120b"

 
def parse_resume(folder_path):
    resmes = []
    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if file.lower().endswith(".pdf"):
            try:
                text = ""
                with fitz.open(file_path) as doc:
                    for page in doc:
                        text += page.get_text()
                resmes.append(text)
            except Exception as e:
                print(f"Error occurred while processing {file}: {e}")
        elif file.lower().endswith(".docx"):
            try:
                doc = docx.Document(file_path)
                text = "\n".join([paragraph.text for paragraph in doc.paragraphs])
                resmes.append(text)
            except Exception as e:
                print(f"Error occurred while processing {file}: {e}")
 
    return resmes
 
 
resume_schema = Resume.model_json_schema()
 
resume_response = {
    "type": "json_object"
}
 
res = parse_resume(resume_dir)

if not res:
    raise SystemExit(f"No resumes found in {resume_dir}. Please add at least one resume in PDF or DOCX format.")

resume_extraction_prompt = f"""
You are a resume parser. You will be given a resume in text format. Your task is
to extract the following information from the resume. copy dates, numbers and names exactly as written, 
don’t summarize or reword bullets, don’t infer anything not on the page, and leave a field empty when it is absent. 
Do not invent skills, experience, or grades and return it as a JSON object that adheres to the following schema: 
{json.dumps(resume_schema)}.
Ignore any information that is not relevant to the schema. If a field is not present in the resume, 
return null for single values and [] for lists.
"""

resume_extraction_message = {
    "role": "system",
    "content": resume_extraction_prompt
}

message = {
    "role": "user",
    "content": f"Resume: {res[0]}"
}

resume_extraction_messages = [resume_extraction_message, message]

resume_extraction_response = my_client.chat.completions.create(
    model=my_model,
    messages=resume_extraction_messages,
    response_format=resume_response,
    temperature=0
)

resume_extraction_answer = resume_extraction_response.choices[0].message.content
resume_json = json.loads(resume_extraction_answer)
resume_obj = Resume(**resume_json)

with open(profile_path, "w", encoding="utf-8") as f:
    f.write(resume_obj.model_dump_json(indent=2))

print(f"Resume parsed and saved to {profile_path}.")