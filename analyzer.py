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
            expected_output=(
                "Analyze the content and provide a structured analysis in the following format:\n"
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
                '}'
            ),
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
            
            if hasattr(result, 'final_answer'):
                try:
                    import json
                    # Parse the result and ensure it matches the expected format
                    parsed_result = json.loads(result.final_answer)
                    
                    # Return the parsed result directly, it should already be in the correct format
                    # due to the expected_output template
                    return parsed_result
                    
                except json.JSONDecodeError:
                    # If JSON parsing fails, return a properly structured error response
                    return {
                        "website_analysis": {
                            "style": "Error parsing response",
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
            
            # Return empty structure if no result
            return {
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
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
