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
            f"Analyze the following content from {url} and provide insights about:\n"
            "1. Website style, tone, and theme\n"
            "2. Products/Services offered and their USPs\n"
            "3. Ideal Customer Profile (ICP)",
            expected_output=
            "JSON string with website analysis including style, tone, products, and ICP",
            context=None,
            agent=self.analyzer_agent)

        try:
            analysis_task.description += f"\n\nURL: {url}\nContent: {content}"

            crew = Crew(agents=[self.analyzer_agent],
                        tasks=[analysis_task],
                        verbose=True)

            result = crew.kickoff()
            # The result is a CrewOutput object, we need to access its final answer
            if hasattr(result, 'final_answer'):
                try:
                    import json
                    return json.loads(result.final_answer)
                except:
                    return {
                        "Website Style & Tone": str(result.final_answer),
                        "Products/Services & USPs": "",
                        "Ideal Customer Profile (ICP)": ""
                    }
            return {"error": "No analysis results available"}
        except Exception as e:
            raise Exception(f"Analysis failed: {str(e)}")
