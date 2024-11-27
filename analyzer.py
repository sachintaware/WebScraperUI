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
                f"Analyze the following content from {url} and provide insights in JSON format with the following structure:\n"
                "{\n"
                '  "website_analysis": {\n'
                '    "style": "style description",\n'
                '    "tone": "tone description",\n'
                '    "theme": "theme description",\n'
                '    "products_services": [\n'
                '      {\n'
                '        "name": "product name",\n'
                '        "description": "description",\n'
                '        "USPs": ["USP1", "USP2"]\n'
                '      }\n'
                '    ],\n'
                '    "ideal_customer_profile": {\n'
                '      "business_types": ["type1", "type2"],\n'
                '      "size": "size description",\n'
                '      "goals": ["goal1", "goal2"],\n'
                '      "pain_points": ["point1", "point2"]\n'
                '    }\n'
                '  }\n'
                '}'
            ),
            expected_output="Analysis in JSON format",
            context=content,
            agent=self.analyzer_agent
        )

        crew = Crew(
            agents=[self.analyzer_agent],
            tasks=[analysis_task],
            verbose=True
        )

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
