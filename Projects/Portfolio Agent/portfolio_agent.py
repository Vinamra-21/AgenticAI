from dotenv import load_dotenv
from openai import OpenAI
import json
import os
import requests
from pypdf import PdfReader
import gradio as gr

load_dotenv(override=True)

def push(text):
    requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": os.getenv("PUSHOVER_TOKEN"),
            "user": os.getenv("PUSHOVER_USER"),
            "message": text,
        }
    )


# def record_user_details(email, name="Name not provided", notes="not provided"):
#     push(f"Recording {name} with email {email} and notes {notes}")
#     return {"recorded": "ok"}

def record_unknown_question(question):
    push(f"Recording {question}")
    return {"recorded": "ok"}

def provide_resume_link():
    return {"resume_url": "https://vinamra-garg.vercel.app/Vinamra_Resume.pdf", "message": "Here's the link to download the resume"}

def provide_contact_links():
    return {
        "portfolio": "https://vinamra-garg.vercel.app",
        "linkedin": "https://www.linkedin.com/in/vinamra-garg",
        "github": "https://github.com/vinamra-garg",
        "email": "gargvinamra21@gmail.com",
        "message": "Here are all the contact links"
    }

def send_mail(name, email, message):
    # push(f"Email from {name} ({email}): {message}")
    try:
        response = requests.post(
            "https://vinamra-garg.vercel.app/api/mail",
            json={"name": name, "email": email, "message": message},
            timeout=10
        )
        if response.status_code == 200:
            return {"status": "success", "message": "Your message has been sent successfully!"}
        else:
            return {"status": "error", "message": "Failed to send message. Please try again later."}
    except Exception as e:
        print(f"Error sending email: {e}", flush=True)
        return {"status": "error", "message": "Failed to send message. Please try again later."}

# record_user_details_json = {
#     "name": "record_user_details",
#     "description": "Use this tool to record that a user is interested in being in touch and provided an email address",
#     "parameters": {
#         "type": "object",
#         "properties": {
#             "email": {
#                 "type": "string",
#                 "description": "The email address of this user"
#             },
#             "name": {
#                 "type": "string",
#                 "description": "The user's name, if they provided it"
#             }
#             ,
#             "notes": {
#                 "type": "string",
#                 "description": "Any additional information about the conversation that's worth recording to give context"
#             }
#         },
#         "required": ["email"],
#         "additionalProperties": False
#     }
# }

record_unknown_question_json = {
    "name": "record_unknown_question",
    "description": "Always use this tool to record any question that couldn't be answered as you didn't know the answer",
    "parameters": {
        "type": "object",
        "properties": {
            "question": {
                "type": "string",
                "description": "The question that couldn't be answered"
            },
        },
        "required": ["question"],
        "additionalProperties": False
    }
}

provide_resume_link_json = {
    "name": "provide_resume_link",
    "description": "Use this tool when the user asks for a resume, CV, or wants to download credentials",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
}

provide_contact_links_json = {
    "name": "provide_contact_links",
    "description": "Use this tool when the user asks for contact information, social media links, LinkedIn, GitHub, or how to connect",
    "parameters": {
        "type": "object",
        "properties": {},
        "required": [],
        "additionalProperties": False
    }
}

send_mail_json = {
    "name": "send_mail",
    "description": "Use this tool to send an email message from the user. Only use when the user explicitly wants to send a message or contact via email",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of the person sending the email"
            },
            "email": {
                "type": "string",
                "description": "The email address of the sender"
            },
            "message": {
                "type": "string",
                "description": "The body/content of the email message"
            }
        },
        "required": ["name", "email", "message"],
        "additionalProperties": False
    }
}

tools = [{"type": "function", "function": record_unknown_question_json},
        {"type": "function", "function": provide_resume_link_json},
        {"type": "function", "function": provide_contact_links_json},
        {"type": "function", "function": send_mail_json}]


class Me:
    def __init__(self):
        self.openai = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY")
        )
        self.name = "Vinamra Garg"
        reader = PdfReader("me/Profile.pdf")
        self.linkedin = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.linkedin += text
        with open("me/summary.txt", "r", encoding="utf-8") as f:
            self.summary = f.read()
        reader = PdfReader("me/Vinamra_Resume.pdf")
        self.resume = ""
        for page in reader.pages:
            text = page.extract_text()
            if text:
                self.resume += text

    def handle_tool_call(self, tool_calls):
        results = []
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)
            print(f"Tool called: {tool_name}", flush=True)
            tool = globals().get(tool_name)
            result = tool(**arguments) if tool else {}
            results.append({"role": "tool","content": json.dumps(result),"tool_call_id": tool_call.id})
        return results
    
    def system_prompt(self):
        system_prompt = f"You are acting as {self.name}.\
            You are answering questions on {self.name}'s website, \
            particularly questions related to {self.name}'s career, background, skills and experience. \
            Your responsibility is to represent {self.name} for interactions on the website as faithfully as possible. \
            You are given a summary of {self.name}'s background, a resume and LinkedIn profile which you can use to answer questions. \
            Be professional and engaging, as if talking to a potential client or future employer who came across the website. \
            For detailed information about {self.name}'s projects, direct users to https://vinamra-garg.vercel.app/projects where they can view all projects with descriptions, tech stacks, GitHub links, and demos. \
            If you don't know the answer to any question, use your record_unknown_question tool to record the question that you couldn't answer, even if it's about something trivial or unrelated to career. \
            If the user is engaging in discussion and wants to get in touch, use the send_mail tool to help them send an email message. \
            Always provide helpful, accurate information based on the resume, LinkedIn profile, and summary provided."

        system_prompt += f"\n\n## Summary:\n{self.summary}\n\n## LinkedIn Profile:\n{self.linkedin}\n\n ## Resume:\n{self.resume}\n\n"
        system_prompt += f"With this context, please chat with the user, always staying in character as {self.name}."
        return system_prompt
    
    def chat(self, message, history):
        messages = [{"role": "system", "content": self.system_prompt()}] + history + [{"role": "user", "content": message}]
        done = False
        while not done:
            response = self.openai.chat.completions.create(
                model="nvidia/nemotron-3-nano-30b-a3b:free",
                messages=messages,
                tools=tools,
                extra_headers={
                    "HTTP-Referer": "https://vinamra-garg.vercel.app",
                    "X-Title": "Vinamra Garg Portfolio Agent"
                },
                extra_body={}
            )
            if response.choices[0].finish_reason=="tool_calls":
                message = response.choices[0].message
                tool_calls = message.tool_calls
                results = self.handle_tool_call(tool_calls)
                messages.append(message)
                messages.extend(results)
            else:
                done = True
        return response.choices[0].message.content
    

if __name__ == "__main__":
    me = Me()
    gr.ChatInterface(me.chat).launch()
    