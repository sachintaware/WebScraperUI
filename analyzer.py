from crewai import Agent, Task, Crew
from langchain.tools import Tool


class ContentAnalyzer:

    def __init__(self):
        self.analyzer_agent = Agent(
            role="Analyzer",
            goal=
            "Go through the scraped content and identify websites style, tone of language, theme and vibe. Identify products/services provided by the website/client with USP's. Identify ICP(ideal customer profile) for the website.",
            backstory=
            "You are a web Content analyst who can build product and customer profiles based on website data, blogs and articles available on the website. You can Identify products/services provided by the website/client with USP's and also Identify ICP(ideal customer profile) for the website",
            verbose=True,
            allow_delegation=False)

    def generate_content(self, context):
        content_generator = Agent(
            role="Content Generator",
            goal="Generate engaging and relevant content based on website analysis",
            backstory="You are an expert content writer who can create various types of content while maintaining consistent style and tone",
            verbose=True,
            allow_delegation=False
        )

        generation_task = Task(
            description=(
                f"Generate {context['content_type']} content based on the following analysis:\n\n"
                f"Style and Tone:\n{context['style_tone']}\n\n"
                f"Products/Services:\n{context['products_services']}\n\n"
                f"Target Audience:\n{context['icp']}\n\n"
                "Ensure the content matches the website's style and tone while "
                "addressing the target audience's needs and pain points."
            ),
            expected_output="Generated content in plain text format",
            agent=content_generator
        )

        crew = Crew(
            agents=[content_generator],
            tasks=[generation_task],
            verbose=True
        )

        try:
            result = crew.kickoff()
            return str(result)
        except Exception as e:
            raise Exception(f"Content generation failed: {str(e)}")

    def analyze_content(self, content, url):
        analysis_task = Task(
            description=(
                f"Analyze the following content from {url} and provide insights about:\n"
                "1. Website style, tone, and theme\n"
                "2. Products/Services offered and their USPs\n"
                "3. Ideal Customer Profile (ICP)\n\n"
                "Content to analyze:\n"
                f"{content}\n\n"  # Include content directly in description
                "Format the response in the following JSON structure:\n"
                '{"website_analysis": {'
                '"style": "Professional and Direct",'
                '"tone": "Persuasive and Informative",'
                '"theme": "Main theme of the website",'
                '"products_services": ['
                '{"name": "Product/Service Name",'
                '"description": "Description of the service",'
                '"USPs": ["USP1", "USP2", "USP3"]}'
                '],'
                '"ideal_customer_profile": {'
                '"business_types": ["Type1", "Type2"],'
                '"size": "Size description",'
                '"goals": ["Goal1", "Goal2"],'
                '"pain_points": ["Point1", "Point2"]'
                '}}}'),
            expected_output=
            "JSON string containing website analysis in the specified format",
            agent=self.analyzer_agent)

        crew = Crew(agents=[self.analyzer_agent],
                    tasks=[analysis_task],
                    verbose=True)

        try:
            result = crew.kickoff()

            # Handle different result formats
            if isinstance(result, dict):
                return result

            result_text = str(result)
            if hasattr(result, 'final_answer'):
                result_text = str(result.final_answer)

            # Try to extract JSON from the response
            import json
            import re

            # Look for JSON-like content in the string
            json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass

            # If no JSON found, create a structured response from the text
            return {
                "website_analysis": {
                    "style": result_text,
                    "tone": "",
                    "theme": "",
                    "products_services": [],
                    "ideal_customer_profile": {
                        "business_types": [],
                        "size": "",
                        "goals": [],
                        "pain_points": []
                    }
                }
            }
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
