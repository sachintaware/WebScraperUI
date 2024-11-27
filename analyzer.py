from crewai import Agent, Task, Crew
from langchain.tools import Tool

class ContentAnalyzer:
    def __init__(self):
        self.analyzer_agent = Agent(
            role="Analyzer",
            goal="Go through the scraped content and identify websites style, tone of language, theme and vibe. Identify products/services provided by the website/client with USP's. Identify ICP(ideal customer profile) for the website.",
            backstory="You are a web Content analyst who can build product and customer profiles based on website data, blogs and articles available on the website. You can Identify products/services provided by the website/client with USP's and also Identify ICP(ideal customer profile) for the website",
            verbose=True,
            allow_delegation=False
        )

    def analyze_content(self, content, url):
        analysis_task = Task(
            description=f"Analyze the following content from {url} and provide insights about:\n"
                       "1. Website style, tone, and theme\n"
                       "2. Products/Services offered and their USPs\n"
                       "3. Ideal Customer Profile (ICP)",
            expected_output="Provide analysis in JSON format with the following structure: {'Website Style & Tone': 'analysis', 'Products/Services & USPs': 'analysis', 'Ideal Customer Profile (ICP)': 'analysis'}",
            context=[
                f"URL: {url}",
                f"Content: {content}"
            ],
            agent=self.analyzer_agent
        )

        crew = Crew(
            agents=[self.analyzer_agent],
            tasks=[analysis_task],
            verbose=True
        )

        try:
            result = crew.kickoff()
            # Parse the result string into dictionary if it's a string
            if isinstance(result, str):
                try:
                    import json
                    result = json.loads(result)
                except:
                    # If parsing fails, create a structured response
                    return {
                        "Website Style & Tone": result,
                        "Products/Services & USPs": "",
                        "Ideal Customer Profile (ICP)": ""
                    }
            return result
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
