
import asyncio
from research_manager import ResearchManager
from guardrails import InputGuardrails
from clarifying_questions import ClarifyingQuestionsTool
from load_dotenv import load_dotenv

load_dotenv(override=True)

async def test_input_guardrails():
    """Test input validation"""
    print("=" * 60)
    print("Testing Input Guardrails")
    print("=" * 60)
    
    guardrails = InputGuardrails()
    
    # Test 1: Valid query
    result = guardrails.validate_query("Impact of AI on healthcare")
    print(f"\n✓ Valid query: {result.is_valid}")
    
    # Test 2: Empty query
    result = guardrails.validate_query("")
    print(f"✓ Empty query blocked: {not result.is_valid}")
    
    # Test 3: Too short
    result = guardrails.validate_query("AI")
    print(f"✓ Short query blocked: {not result.is_valid}")
    
    # Test 4: Sensitive topic
    result = guardrails.validate_query("diabetes treatment options")
    print(f"✓ Sensitive topic detected: {result.warning_message is not None}")
    
    # Test 5: Harmful content
    result = guardrails.validate_query("how to hack a website")
    print(f"✓ Harmful content blocked: {not result.is_valid}")


async def test_clarifying_questions():
    """Test clarifying questions generation"""
    print("\n" + "=" * 60)
    print("Testing Clarifying Questions")
    print("=" * 60)
    
    # Test with vague query
    vague_query = "AI"
    print(f"\nQuery: '{vague_query}'")
    questions = await ClarifyingQuestionsTool.generate_questions(vague_query)
    print(f"Should ask questions: {questions.should_ask}")
    print(f"Confidence: {questions.confidence_score:.2f}")
    
    if questions.should_ask:
        for i, q in enumerate(questions.questions, 1):
            print(f"\n{i}. {q.question}")
            print(f"   Reason: {q.reason}")
    
    # Test with clear query
    clear_query = "Detailed analysis of renewable energy adoption rates in European Union countries between 2020-2024"
    print(f"\n\nQuery: '{clear_query}'")
    questions = await ClarifyingQuestionsTool.generate_questions(clear_query)
    print(f"Should ask questions: {questions.should_ask}")
    print(f"Confidence: {questions.confidence_score:.2f}")


async def test_mini_research():
    """Test a mini research run (without email)"""
    print("\n" + "=" * 60)
    print("Testing Mini Research Flow")
    print("=" * 60)
    
    query = "Latest developments in quantum computing"
    print(f"\nQuery: '{query}'")
    print("\nNote: This is a mock test. Full research requires API keys.")
    print("To run full research, set up .env and use the Gradio UI.")


async def main():
    """Run all tests"""
    print("\n🧪 Deep Research System - Quick Test Suite\n")
    
    try:
        await test_input_guardrails()
        await test_clarifying_questions()
        await test_mini_research()
        
        print("\n" + "=" * 60)
        print("✅ All Tests Passed!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Set up your .env file with API keys")
        print("2. Run: python deep_research.py")
        print("3. Try the clarifying questions feature")
        print("4. Run a full research query")
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        print("\nTroubleshooting:")
        print("- Ensure all dependencies are installed: pip install -r requirements.txt")
        print("- Check that all files are in the correct directory")
        print("- Verify .env file exists with API keys")


if __name__ == "__main__":
    asyncio.run(main())
