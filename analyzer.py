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
            description=
            (f"Analyze the following content from {url} and provide insights about:\n"
             "1. Website style, tone, and theme\n"
             "2. Products/Services offered and their USPs\n"
             "3. Ideal Customer Profile (ICP)"),
            expected_output=
            ("Analyze the content and provide a structured analysis in the following format:\n"
             "{\n"
             '  "website_analysis": {\n'
             '    "style": "style description",\n'
             '    "tone": "tone description",\n'
             '    "theme": "theme description",\n'
             '    "products_services": [\n'
             '      {\n'
             '        "name": "product name",\n'
             '        "description": "product description",\n'
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
             '}'),
            context=[
                Task(description=f"Content to analyze: {content}",
                     expected_output="A brief statement about the content.",
                     agent=self.analyzer_agent),
                Task(description=f"URL: {url}",
                     expected_output="A brief statement about the URL.",
                     agent=self.analyzer_agent)
            ],
            agent=self.analyzer_agent)

        crew = Crew(agents=[self.analyzer_agent],
                    tasks=[analysis_task],
                    verbose=True)

        try:
            result = crew.kickoff()

            # Handle string result from CrewAI
            if isinstance(result, str):
                try:
                    # Try to extract JSON from the string response
                    import json
                    import re

                    # Look for JSON-like content in the string
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        result_json = json.loads(json_match.group())
                    else:
                        # Create structured response from plain text
                        result_json = {
                            "website_analysis": {
                                "style": result,
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
                    return result_json
                except json.JSONDecodeError:
                    raise Exception("Failed to parse analysis result")

            # Handle object result
            if hasattr(result, 'final_answer'):
                return json.loads(result.final_answer)

            raise Exception("Unexpected analysis result format")

        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
