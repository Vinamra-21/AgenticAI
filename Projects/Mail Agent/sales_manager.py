from dotenv import load_dotenv
from agents import Agent, Runner, trace, function_tool, OpenAIChatCompletionsModel, input_guardrail, output_guardrail, GuardrailFunctionOutput, AgentOutputSchema
from typing import Dict, List, Optional
import sendgrid
import os
from sendgrid.helpers.mail import Mail, Email, To, Content
import asyncio
from openai import AsyncOpenAI
from pydantic import BaseModel, Field, ConfigDict
import re
load_dotenv(override=True)


class EmailDraft(BaseModel):
    """Structured output for email drafts"""
    model_config = ConfigDict(extra='forbid')
    
    email_body: str = Field(description="Complete email content following the outline: greeting, opening hook, value proposition, call-to-action, and closing")
    tone: str = Field(description="Tone: professional, engaging, or concise")

class EmailSubject(BaseModel):
    """Structured output for email subjects"""
    model_config = ConfigDict(extra='forbid')
    
    subject_line: str = Field(description="The subject line for the email")

class HTMLEmail(BaseModel):
    """Structured output for HTML emails"""
    model_config = ConfigDict(extra='forbid')
    
    html_content: str = Field(description="Complete HTML email content")

instructions1 = """You are a professional sales agent for ContentGenius - an AI-powered SaaS platform for social media content creation and scheduling.

Write a professional, serious cold email following this outline:
- Greeting
- Opening hook (attention-grabbing)
- Value proposition (explain benefits)
- Social proof or credibility
- Clear call-to-action
- Professional closing

Be persuasive but respectful."""

instructions2 = """You are an engaging, humorous sales agent for ContentGenius - an AI-powered SaaS platform for social media content creation and scheduling.

Write a witty, engaging cold email following this outline:
- Friendly greeting
- Humorous or relatable opening
- Value proposition (with personality)
- Light social proof
- Casual call-to-action
- Warm closing

Be funny but professional."""

instructions3 = """You are a busy sales agent for ContentGenius - an AI-powered SaaS platform for social media content creation and scheduling.

Write a concise, to-the-point cold email following this outline:
- Brief greeting
- Direct value proposition
- Quick social proof
- Clear call-to-action
- Short closing

Keep it under 150 words."""

gemini_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)
gemini_model = OpenAIChatCompletionsModel(
    model="nvidia/nemotron-3-nano-30b-a3b:free",
    openai_client=gemini_client
)

sales_agent1 = Agent(
        name="Professional Sales Agent",
        instructions=instructions1,
        model=gemini_model,
        output_type=AgentOutputSchema(EmailDraft, strict_json_schema=False)
)

sales_agent2 = Agent(
        name="Engaging Sales Agent",
        instructions=instructions2,
        model=gemini_model,
        output_type=AgentOutputSchema(EmailDraft, strict_json_schema=False)
)

sales_agent3 = Agent(
        name="Busy Sales Agent",
        instructions=instructions3,
        model=gemini_model,
        output_type=AgentOutputSchema(EmailDraft, strict_json_schema=False)
)

subject_instructions = """Write a compelling subject line for the given cold sales email. 
Make it attention-grabbing and relevant. Keep it under 60 characters."""

html_instructions = """Convert the given text email to clean, professional HTML.
Use simple styling with good readability. Include proper spacing and formatting."""

subject_writer = Agent(
    name="Email subject writer", 
    instructions=subject_instructions, 
    model=gemini_model,
    output_type=AgentOutputSchema(EmailSubject, strict_json_schema=False)
)
subject_tool = subject_writer.as_tool(tool_name="subject_writer", tool_description="Write a subject for a cold sales email")

html_converter = Agent(
    name="HTML email body converter", 
    instructions=html_instructions, 
    model=gemini_model,
    output_type=AgentOutputSchema(HTMLEmail, strict_json_schema=False)
)
html_tool = html_converter.as_tool(tool_name="html_converter",tool_description="Convert a text email body to an HTML email body")

@function_tool
def send_html_email(subject: str, html_body: str, sender_email: str, receiver_email: str) -> Dict[str, str]:
    """ Send out an email with the given subject and HTML body from sender to receiver """
    try:
        api_key = os.environ.get('SENDGRID_API_KEY')
        if not api_key:
            return {"status": "error", "message": "SENDGRID_API_KEY not found in environment variables"}
        
        sg = sendgrid.SendGridAPIClient(api_key=api_key)
        from_email = Email(sender_email)
        to_email = To(receiver_email)
        content = Content("text/html", html_body)
        mail = Mail(from_email, to_email, subject, content)
        
        response = sg.client.mail.send.post(request_body=mail.get())
        
        print(f"\n Email sent successfully!")
        return {
            "status": "success", 
            "from": sender_email, 
            "to": receiver_email,
            "response_code": response.status_code
        }
    except Exception as e:
        error_msg = f"Failed to send email: {str(e)}"
        return {"status": "error", "message": error_msg}


description = "Write a cold sales email"
tool1 = sales_agent1.as_tool(tool_name="sales_agent1", tool_description=description)
tool2 = sales_agent2.as_tool(tool_name="sales_agent2", tool_description=description)
tool3 = sales_agent3.as_tool(tool_name="sales_agent3", tool_description=description)


handoff_instructions ="You are an email formatter and sender. You receive the body of an email to be sent along with sender and receiver information. \
You first extract the sender email address and receiver email address from the message. \
Then use the subject_writer tool to write a subject for the email, then use the html_converter tool to convert the body to HTML. \
Finally, you use the send_html_email tool to send the email with the subject, HTML body, sender email, and receiver email. \
If sender or receiver email is not provided in the message, ask the user for this information."


emailer_agent = Agent(
    name="Email Manager",
    instructions=handoff_instructions,
    tools=[subject_tool, html_tool, send_html_email],
    model=gemini_model,
    handoff_description="Convert an email to HTML and send it")


class InputValidation(BaseModel):
    """input validation"""
    model_config = ConfigDict(extra='forbid')
    
    has_valid_emails: bool
    is_safe: bool
    issues: List[str]

class OutputValidation(BaseModel):
    """output validation"""
    model_config = ConfigDict(extra='forbid')
    
    is_professional: bool
    has_spam_content: bool
    quality_score: int  # 1-10
    issues: List[str]

input_validator = Agent(
    name="Input Validator",
    instructions="""Check the input message for:
    1. Valid email addresses (sender and receiver)
    2. No harmful or threatening content
    3. No obvious spam patterns
    
    Be concise and only flag serious issues.""",
    output_type=AgentOutputSchema(InputValidation, strict_json_schema=False),
    model=gemini_model
)

output_validator = Agent(
    name="Output Validator",
    instructions="""Check the email output for:
    1. Professional tone
    2. Excessive spam triggers
    3. Overall quality (score 1-10)
    
    Be lenient - only flag major problems.""",
    output_type=AgentOutputSchema(OutputValidation, strict_json_schema=False),
    model=gemini_model
)

@input_guardrail
async def validate_input(ctx, agent, message):
    """Simplified agent-based input validation"""
    
    result = await Runner.run(input_validator, message, context=ctx.context)
    validation = result.final_output
    
    triggered = not validation.has_valid_emails or not validation.is_safe
    
    if validation.issues:
        print("   Issues found:")
        for issue in validation.issues:
            print(f"  {issue}")
    else:
        print("Validation passed")
    
    return GuardrailFunctionOutput(
        output_info={"validation": validation},
        tripwire_triggered=triggered
    )

@output_guardrail
async def validate_output(ctx, agent, output):
    """output validation"""
    
    email_content = str(output)
    result = await Runner.run(output_validator, f"Check this email:\n{email_content}", context=ctx.context)
    validation = result.final_output
    
    triggered = validation.quality_score < 5 or validation.has_spam_content
    
    print(f"   Quality Score: {validation.quality_score}/10")
    
    if validation.issues:
        print("   Issues found:")
        for issue in validation.issues:
            print(f"  {issue}")
    else:
        print("Validation passed")
    
    return GuardrailFunctionOutput(
        output_info={"validation": validation},
        tripwire_triggered=triggered
    )

sales_manager_instructions = """
You are a Sales Manager at ContentGenius. Your goal is to find the single best cold sales email using the sales_agent tools.
 
Follow these steps carefully:
1. Generate Drafts: Use all three sales_agent tools to generate three different email drafts. Do not proceed until all three drafts are ready.
 
2. Evaluate and Select: Review the drafts and choose the single best email using your judgment of which one is most effective.
   You can use the tools multiple times if you're not satisfied with the results from the first try.
 
3. Handoff for Sending: Pass ONLY the winning email draft and the sender and receiver information to the 'Email Manager' agent. 
   The Email Manager will take care of formatting and sending.
 
Crucial Rules:
- You must use the sales agent tools to generate the drafts — do not write them yourself.
- You must hand off exactly ONE email to the Email Manager — never more than one.
"""

#main
sales_manager = Agent(
    name="Sales Manager",
    instructions=sales_manager_instructions,
    tools=[tool1, tool2, tool3],
    handoffs=[emailer_agent],
    input_guardrails=[validate_input],
    output_guardrails=[validate_output],
    model=gemini_model)

message = "Send out a cold sales email addressed to Dear Garg (example@example.com) from Vinamra (example@example.com)"

async def main():
    with trace("Automated SDR with Guardrails"):
        result = await Runner.run(sales_manager, message)
        print(f"\n{result}")

if __name__ == "__main__":
    asyncio.run(main())

    #https://platform.openai.com/logs?api=traces