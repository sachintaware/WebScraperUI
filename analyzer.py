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

    def analyze_content(self, content, url):
        analysis_task = Task(
            description=(
                f"Analyze the following content from {url} and provide insights about:\n"
                "1. Website style, tone, and theme\n"
                "2. Products/Services offered and their USPs\n"
                "3. Ideal Customer Profile (ICP)"
            ),
            expected_output="JSON string containing website analysis",
            context=[f"Content to analyze: {content}", f"URL: {url}"],
            agent=self.analyzer_agent
        )

        crew = Crew(
            agents=[self.analyzer_agent],
            tasks=[analysis_task],
            verbose=True
        )

        try:
            result = crew.kickoff()
            
            # Extract the result text
            result_text = result
            if hasattr(result, 'final_answer'):
                result_text = result.final_answer
            elif isinstance(result, dict):
                return result  # Already in correct format
                
            # Try to find and parse JSON in the response
            import json
            import re
            
            # First try direct JSON parsing
            try:
                return json.loads(result_text)
            except json.JSONDecodeError:
                # Look for JSON-like content in the string
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
            
            # If we couldn't parse JSON, create a structured response
            lines = result_text.split('\n')
            formatted_result = {
                "website_analysis": {
                    "style": "",
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
            
            # Try to extract information from the text
            current_section = None
            for line in lines:
                line = line.strip()
                if 'style' in line.lower():
                    formatted_result['website_analysis']['style'] = line.split(':', 1)[1].strip() if ':' in line else line
                elif 'tone' in line.lower():
                    formatted_result['website_analysis']['tone'] = line.split(':', 1)[1].strip() if ':' in line else line
                elif 'theme' in line.lower():
                    formatted_result['website_analysis']['theme'] = line.split(':', 1)[1].strip() if ':' in line else line
                    
            return formatted_result
            
        except Exception as e:
            app.logger.error(f"Analysis error: {str(e)}")
            raise Exception(f"Analysis failed: {str(e)}")
