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
            description=f"Analyze the following content from {url} and provide insights about:\n"
                       "1. Website style, tone, and theme\n"
                       "2. Products/Services offered and their USPs\n"
                       "3. Ideal Customer Profile (ICP)",
            expected_output="Analyze and return website content analysis",
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
            
            # Format the result into the expected structure
            formatted_result = {
                'style_tone': '',
                'products_services': '',
                'icp': ''
            }
            
            if isinstance(result, str):
                # Parse the analysis into sections
                sections = result.split('\n\n')
                for section in sections:
                    if 'style' in section.lower() or 'tone' in section.lower():
                        formatted_result['style_tone'] = section
                    elif 'product' in section.lower() or 'service' in section.lower():
                        formatted_result['products_services'] = section
                    elif 'customer' in section.lower() or 'icp' in section.lower():
                        formatted_result['icp'] = section
            
            return formatted_result
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
