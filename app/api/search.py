from .gemini import GeminiAPI
from .groq import GroqAPI
from app.services.file_processor import file_processor
import logging
import re
import json
import time
import os
from datetime import datetime

# Set up logging
logger = logging.getLogger(__name__)

def do_search(query, user_id=None):
    """Perform a deep, PhD-level research using advanced LLM capabilities.

    Args:
        query (str): The search query (may include file content)
        user_id (str): User ID for credit consumption

    Returns:
        dict: A dictionary containing the comprehensive research results
    """
    try:
        # Check and consume credits before processing (token-based)
        if user_id:
            from ..services.credit_service import CreditService

            credit_service = CreditService()

            # Determine task type for minimum charge calculation
            if len(query) > 1000 or any(keyword in query.lower() for keyword in ['comprehensive', 'detailed', 'analyze', 'research']):
                task_type = 'research_lab_complex'
            else:
                task_type = 'research_lab_basic'

            # Pre-consume minimum credits (will be adjusted after execution)
            pre_credit_result = credit_service.consume_credits(
                user_id=user_id,
                task_type=task_type,
                input_text=query,
                output_text="",  # Will update after execution
                use_token_based=True
            )

            if not pre_credit_result['success']:
                return {
                    'success': False,
                    'error': pre_credit_result.get('error', 'Insufficient credits'),
                    'credits_needed': pre_credit_result.get('credits_needed'),
                    'credits_available': pre_credit_result.get('credits_available')
                }

        # Process uploaded files if present
        enhanced_query = query
        file_context = ""

        if "--- File:" in query or "--- Image:" in query:
            logger.info("File content detected in research query, processing files...")
            try:
                # Extract the original user query (before file content)
                parts = query.split('\n\n--- File:')
                if len(parts) > 1:
                    original_query = parts[0]
                    file_content = '\n\n--- File:' + '\n\n--- File:'.join(parts[1:])
                else:
                    parts = query.split('\n\n--- Image:')
                    if len(parts) > 1:
                        original_query = parts[0]
                        file_content = '\n\n--- Image:' + '\n\n--- Image:'.join(parts[1:])
                    else:
                        original_query = query
                        file_content = ""

                if file_content:
                    # Use the file processor to enhance the query
                    enhanced_query = file_processor.enhance_prompt_with_files(original_query, file_content)
                    file_context = f" (with {file_content.count('--- File:') + file_content.count('--- Image:')} uploaded file(s))"
                    logger.info(f"Enhanced research query with file analysis: {len(enhanced_query)} characters")
            except Exception as e:
                logger.error(f"Error processing files in research query: {str(e)}")
                # Continue with original query if file processing fails
                enhanced_query = query

        # Initialize APIs
        gemini_api = GeminiAPI()
        groq_api = GroqAPI()

        # Step 1: Generate research questions to explore the topic deeply
        try:
            research_questions = generate_research_questions(enhanced_query, groq_api)
            logger.info(f"Generated {len(research_questions)} research questions")
        except Exception as e:
            logger.error(f"Error generating research questions: {str(e)}")
            # Use default questions if there's an error
            research_questions = [
                f"What is the historical development of {query}?",
                f"What are the theoretical frameworks that explain {query}?",
                f"What are the practical applications or implications of {query}?",
                f"What are the current debates or controversies surrounding {query}?",
                f"How might {query} evolve in the future?"
            ]
            logger.info(f"Using default research questions instead")

        # Step 2: Conduct deep research on each question
        try:
            research_findings = conduct_deep_research(enhanced_query, research_questions, groq_api, gemini_api)
            logger.info(f"Conducted research on {len(research_findings)} questions")
        except Exception as e:
            logger.error(f"Error conducting research: {str(e)}")
            # Create basic findings if there's an error
            research_findings = [
                {
                    "question": research_questions[0] if research_questions else f"What is {query}?",
                    "findings": f"This research explores {query} from multiple perspectives, examining its historical context, theoretical foundations, and practical applications."
                }
            ]
            logger.info(f"Using basic research findings instead")

        # Step 3: Synthesize findings into a comprehensive report
        try:
            final_report = synthesize_research(enhanced_query, research_findings, groq_api)
            logger.info(f"Successfully synthesized research report")
        except Exception as e:
            logger.error(f"Error synthesizing research: {str(e)}")
            # Create a basic report if there's an error
            final_report = f"""
# Research Report on {query}

## Overview

This report provides an academic analysis of {query}, exploring its key aspects and implications.

## Key Findings

- {query} has evolved significantly over time, with important historical developments shaping its current form.
- There are several theoretical frameworks that help explain the nature and significance of {query}.
- {query} has numerous practical applications and implications across different fields and contexts.
- There are ongoing debates and controversies surrounding {query} that reflect different perspectives and approaches.
- The future of {query} is likely to be influenced by emerging trends and developments in related fields.

## Conclusion

Further research on {query} is needed to fully understand its complexity and significance in contemporary contexts.
"""
            logger.info(f"Using basic research report instead")

        # Check if the response contains an error message
        if "Error with Groq API" in final_report or "exceeded your current quota" in final_report:
            logger.warning(f"Error message detected in final report")
            return {"results": "I'm sorry, but I'm currently experiencing high demand and can't process your research request at the moment. Please try again later."}

        # Calculate final token-based credits after research completion
        if user_id:
            try:
                # Calculate actual credits consumed based on tokens
                final_credit_result = credit_service.calculate_token_based_credits(
                    input_text=query,
                    output_text=final_report,
                    task_type=task_type,
                    execution_time_minutes=0,  # Could be enhanced to track actual time
                    tool_calls=len(research_questions),  # Count research questions as tool calls
                    image_count=0
                )

                # Add credit breakdown to response
                result = {
                    "results": final_report,
                    "credits_consumed": pre_credit_result['credits_consumed'],
                    "credit_breakdown": final_credit_result
                }
                return result
            except Exception as e:
                logger.error(f"Error calculating final credits: {str(e)}")
                # Return without credit breakdown if calculation fails
                pass

        return {"results": final_report}
    except Exception as e:
        logger.error(f"Error in research process: {str(e)}")
        return {"results": f"""
# Research Report on {query}

I apologize, but I encountered technical difficulties while researching this topic. Here's what I can provide:

## Overview

{query} is a complex and multifaceted subject that spans multiple disciplines and contexts.

## Basic Information

- {query} has historical roots that have shaped its development over time
- There are various theoretical approaches to understanding {query}
- {query} has practical applications in several fields
- Current research on {query} continues to evolve

## Recommendation

Please try your search again later when our research systems are functioning optimally.
"""}

def generate_research_questions(query, api):
    """Generate sophisticated research questions to explore the topic deeply.

    Args:
        query (str): The main research topic
        api: The API to use for generation

    Returns:
        list: A list of research questions
    """
    try:
        prompt = f"""
        You are a PhD-level research methodologist with expertise in developing sophisticated research questions.

        TOPIC: {query}

        Generate 5 deep, nuanced research questions that would help explore this topic at an academic level.
        These questions should:
        - Cover different dimensions of the topic (historical, theoretical, practical, ethical, future implications)
        - Be specific enough to guide focused research
        - Encourage critical analysis rather than just factual answers
        - Reveal underlying complexities and tensions in the field

        IMPORTANT: Your response must be ONLY a valid JSON array of strings, with each string being a research question.
        Example format: ["Question 1?", "Question 2?", "Question 3?", "Question 4?", "Question 5?"]
        Do not include any explanations, headers, or additional text before or after the JSON array.
        """

        try:
            # Try with Groq's Llama 3 70B model first
            result = api.generate_text(prompt, model="llama3-70b-8192")
        except Exception as groq_error:
            logger.warning(f"Error with Groq 70B model, falling back to 8B: {str(groq_error)}")
            # Fall back to smaller model if there's an error
            result = api.generate_text(prompt, model="llama3-8b-8192")

        # Clean the result to extract only the JSON part
        result = result.strip()

        # Try to find a JSON array in the response
        json_match = re.search(r'\[\s*".*"\s*(,\s*".*"\s*)*\]', result, re.DOTALL)

        if json_match:
            questions_json = json_match.group(0)
            try:
                questions = json.loads(questions_json)
                return questions[:5]  # Ensure we have at most 5 questions
            except json.JSONDecodeError:
                logger.error(f"Failed to parse JSON: {questions_json}")
                # Don't raise an exception, try to extract questions directly
                logger.info("Attempting to extract questions directly from the response")

        # If no valid JSON array is found or parsing failed, try to extract questions directly
        questions = []

        # First, try to extract questions from the response by looking for patterns
        for line in result.split('\n'):
            # Look for numbered questions or questions with question marks
            if re.search(r'^\d+[\.\)]\s+', line) and '?' in line:
                # Extract the question part
                question = re.sub(r'^\d+[\.\)]\s+', '', line).strip()
                questions.append(question)
            elif '?' in line:
                # Look for any line with a question mark
                # Try to clean up the line by removing quotes and other characters
                line = line.strip()
                if line.startswith('"'):
                    line = line.lstrip('"')
                if line.endswith('"') or line.endswith('",'):
                    line = line.rstrip('",')
                if '?' in line:
                    questions.append(line)

        if questions:
            return questions[:5]  # Return up to 5 extracted questions
        else:
                # If no questions could be extracted, use default questions
                raise Exception("Could not extract questions from response")
    except Exception as e:
        logger.error(f"Error generating research questions: {str(e)}")
        # Return default questions if there's an error
        default_questions = [
            f"What is the historical development of {query}?",
            f"What are the theoretical frameworks that explain {query}?",
            f"What are the practical applications or implications of {query}?",
            f"What are the current debates or controversies surrounding {query}?",
            f"How might {query} evolve in the future?"
        ]
        return default_questions

def conduct_deep_research(main_query, research_questions, groq_api, gemini_api):
    """Conduct deep research on each question.

    Args:
        main_query (str): The main research topic
        research_questions (list): List of research questions
        groq_api: The Groq API instance
        gemini_api: The Gemini API instance

    Returns:
        list: Research findings for each question
    """
    findings = []

    # Limit to 3 questions to avoid payload too large errors
    research_questions = research_questions[:3]

    # Track API usage to avoid rate limiting
    groq_usage_count = 0
    max_groq_calls = 3  # Limit Groq API calls to avoid rate limiting

    for question in research_questions:
        try:
            # Use Groq for deep academic research
            prompt = f"""
            You are a PhD-level researcher with expertise in {main_query}.

            RESEARCH QUESTION: {question}

            Provide a detailed, academic-quality response that:
            1. Addresses the question with depth and nuance
            2. Incorporates relevant theories, models, and frameworks
            3. Discusses empirical evidence and research findings
            4. Acknowledges different perspectives and scholarly debates
            5. Cites specific researchers, studies, and publications (with years)
            6. Uses precise academic language and terminology

            Format your response in academic prose with clear paragraphs. Include in-text citations in the format (Author, Year).
            Limit your response to approximately 1000 words.
            """

            result = ""

            # Try with Groq first if we haven't exceeded the limit
            if groq_usage_count < max_groq_calls:
                try:
                    # Try with Groq's Llama 3 8B model first (more reliable, less likely to hit rate limits)
                    result = groq_api.generate_text(prompt, model="llama3-8b-8192", max_tokens=2000)
                    groq_usage_count += 1

                    # Add a delay after successful Groq call to avoid rate limiting
                    time.sleep(1.5)
                except Exception as groq_error:
                    logger.warning(f"Groq API error, falling back to Gemini: {str(groq_error)}")
                    # Fall back to Gemini if Groq fails
                    try:
                        result = gemini_api.generate_text(prompt)
                    except Exception as gemini_error:
                        logger.error(f"Gemini API error: {str(gemini_error)}")
                        result = f"This research question could not be fully explored due to technical limitations. The question was: {question}"
            else:
                # If we've exceeded Groq usage, use Gemini directly
                try:
                    result = gemini_api.generate_text(prompt)
                except Exception as gemini_error:
                    logger.error(f"Gemini API error: {str(gemini_error)}")
                    result = f"This research question could not be fully explored due to technical limitations. The question was: {question}"

            findings.append({
                "question": question,
                "findings": result
            })

        except Exception as e:
            logger.error(f"Error researching question '{question}': {str(e)}")
            findings.append({
                "question": question,
                "findings": f"Unable to research this question due to technical limitations. The question was: {question}"
            })

    # If we have fewer than 3 findings, add some default ones
    if len(findings) < 3:
        default_findings = [
            {
                "question": f"What are the key concepts related to {main_query}?",
                "findings": f"This research question explores the fundamental concepts and terminology associated with {main_query}. Understanding these key concepts is essential for developing a comprehensive understanding of the topic."
            },
            {
                "question": f"What are the practical applications of {main_query}?",
                "findings": f"This research question examines how {main_query} is applied in real-world contexts. Practical applications demonstrate the relevance and utility of theoretical knowledge in addressing concrete problems and challenges."
            },
            {
                "question": f"What are the future directions for research on {main_query}?",
                "findings": f"This research question investigates emerging trends and potential future developments in the study of {main_query}. Identifying future directions helps scholars anticipate how the field might evolve and where new insights might be gained."
            }
        ]

        # Add default findings until we have at least 3
        for i in range(3 - len(findings)):
            if i < len(default_findings):
                findings.append(default_findings[i])

    return findings

def synthesize_research(query, research_findings, api):
    """Synthesize all research findings into a comprehensive report.

    Args:
        query (str): The main research topic
        research_findings (list): List of findings for each question
        api: The API to use for synthesis

    Returns:
        str: The final synthesized research report
    """
    try:
        # Prepare the findings for the prompt - limit the size to avoid payload too large errors
        findings_text = ""
        for i, finding in enumerate(research_findings):
            # Truncate findings if they're too long (max 1000 chars per finding)
            finding_text = finding['findings']
            if len(finding_text) > 1000:
                finding_text = finding_text[:997] + "..."

            findings_text += f"QUESTION {i+1}: {finding['question']}\n\n"
            findings_text += f"FINDINGS {i+1}:\n{finding_text}\n\n"

            # If we already have 3 questions processed, stop to avoid payload too large
            if i >= 2:
                break

        prompt = f"""
        You are a PhD-level academic researcher with expertise in synthesizing complex research into comprehensive reports.

        TOPIC: {query}

        Below are findings from research questions related to this topic:

        {findings_text}

        Synthesize these findings into a cohesive, academic-quality research report that:

        1. Begins with an executive summary that highlights key insights
        2. Organizes the content into logical sections with clear headings
        3. Integrates the findings from different questions into a unified narrative
        4. Identifies patterns, connections, and contradictions across the research
        5. Maintains academic rigor with proper citations (Author, Year)
        6. Concludes with implications for theory, practice, and future research

        Format the report with Markdown for headings, lists, and emphasis. Use academic language appropriate for a PhD-level audience.
        """

        try:
            # Try with Groq's Llama 3 70B model first
            result = api.generate_text(prompt, model="llama3-70b-8192", max_tokens=4000)
        except Exception as groq_error:
            logger.warning(f"Error with Groq 70B model, falling back to 8B: {str(groq_error)}")
            # Fall back to smaller model if there's an error
            result = api.generate_text(prompt, model="llama3-8b-8192", max_tokens=4000)

        return result
    except Exception as e:
        logger.error(f"Error synthesizing research: {str(e)}")
        return """
# Research Report

I apologize, but I encountered an error while synthesizing the research findings. This could be due to:

1. The complexity of the topic requiring more processing capacity
2. Temporary API limitations or rate limits
3. The size of the research data exceeding system constraints

## Recommendations

- Try a more specific research query
- Break your research into smaller, focused topics
- Try again in a few minutes when API capacity may be available

Your query has been processed and the system collected valuable information, but the final synthesis step encountered technical limitations.
"""

def save_research_feedback(feedback_type, query, results):
    """Save user feedback on research results to improve future research.

    Args:
        feedback_type (str): The type of feedback ('like' or 'dislike')
        query (str): The research query
        results (str): The research results

    Returns:
        dict: A status message
    """
    try:
        # Create feedback directory if it doesn't exist
        # Use environment variable for data directory if available, otherwise use relative path
        base_dir = os.environ.get('DATA_DIR', os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        feedback_dir = os.path.join(base_dir, 'data', 'feedback')
        os.makedirs(feedback_dir, exist_ok=True)

        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{feedback_type}.json"
        filepath = os.path.join(feedback_dir, filename)

        # Prepare feedback data
        feedback_data = {
            "timestamp": datetime.now().isoformat(),
            "feedback_type": feedback_type,
            "query": query,
            "results_snippet": results[:500] + "..." if len(results) > 500 else results  # Store a snippet to save space
        }

        # Save feedback to file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(feedback_data, f, indent=2)

        logger.info(f"Saved {feedback_type} feedback for query: {query}")
        return {"status": "success", "message": f"Feedback saved successfully"}

    except Exception as e:
        logger.error(f"Error saving feedback: {str(e)}")
        return {"status": "error", "message": f"Error saving feedback: {str(e)}"}
