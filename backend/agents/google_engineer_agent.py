from typing import Dict, List, Any, Optional
from .base_agent import BaseResearchAgent, AnalysisResult
from retrieval.arxiv_client import Paper
import logging
import json

logger = logging.getLogger(__name__)

class GoogleEngineerAgent(BaseResearchAgent):
    """Research agent specialized in Google-style engineering practices"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", provider: str = "openai"):
        super().__init__(
            name="Google Engineer",
            role="Senior Software Engineer at Google",
            expertise=[
                "Large-scale distributed systems",
                "Machine learning infrastructure", 
                "Performance optimization",
                "Production systems reliability",
                "Scalability engineering",
                "System architecture"
            ],
            model=model,
            provider=provider,
            api_key=api_key
        )
    
    def analyze_paper(self, paper: Paper, context: Optional[Dict] = None) -> AnalysisResult:
        """Analyze paper from Google engineering perspective"""
        try:
            system_prompt = f"""{self.get_system_prompt()}

As a Google engineer, focus specifically on:
- Scalability to billions of users
- Production deployment challenges
- Infrastructure requirements
- Performance bottlenecks
- Reliability and fault tolerance
- Integration with existing Google services
- Engineering team collaboration aspects"""

            analysis_prompt = f"""{self.get_analysis_prompt(paper, context)}

From a Google engineering perspective, evaluate:

1. **Scalability Analysis**: How would this work at Google scale (billions of users)?
2. **Infrastructure Requirements**: What systems/resources would be needed?
3. **Implementation Complexity**: Engineering effort and timeline estimates
4. **Performance Bottlenecks**: Potential speed/efficiency issues
5. **Production Readiness**: What's needed to deploy this safely?
6. **Integration Points**: How would this fit with existing Google products?
7. **Team Dynamics**: What engineering teams would need to collaborate?

Provide specific, actionable engineering insights."""

            response = self.create_chat_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.7,
                max_tokens=1500
            )
            
            analysis_text = response["content"]
            
            # Parse the analysis to extract structured insights
            insights = self._extract_insights(analysis_text)
            breaking_points = self._extract_breaking_points(analysis_text)
            implementation_ideas = self._extract_implementation_ideas(analysis_text)
            confidence = self._extract_confidence_score(analysis_text)
            
            result = AnalysisResult(
                agent_name=self.name,
                analysis=analysis_text,
                key_insights=insights,
                breaking_points=breaking_points,
                implementation_ideas=implementation_ideas,
                confidence_score=confidence,
                metadata={
                    "paper_id": paper.id,
                    "categories": paper.categories,
                    "focus_areas": ["scalability", "infrastructure", "production"]
                }
            )
            
            self.add_to_history(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in Google Engineer analysis: {e}")
            return AnalysisResult(
                agent_name=self.name,
                analysis=f"Error analyzing paper: {e}",
                key_insights=[],
                breaking_points=[],
                implementation_ideas=[],
                confidence_score=0.0,
                metadata={"error": str(e)}
            )
    
    def generate_insights(self, papers: List[Paper], topic: str) -> Dict[str, Any]:
        """Generate engineering insights from multiple papers"""
        try:
            # Analyze each paper first
            analyses = []
            for paper in papers:
                analysis = self.analyze_paper(paper)
                analyses.append(analysis)
            
            # Generate cross-paper insights
            combined_prompt = f"""Based on your analysis of {len(papers)} papers on "{topic}", 
            provide a comprehensive engineering assessment:

Previous analyses:
{chr(10).join([f"Paper: {analysis.metadata.get('paper_id', 'Unknown')} - {analysis.analysis[:200]}..." for analysis in analyses])}

Generate:
1. **System Architecture Recommendations**: How to build this at scale
2. **Implementation Roadmap**: Phased approach for development
3. **Resource Requirements**: Infrastructure and team needs
4. **Risk Assessment**: Technical and operational risks
5. **Performance Metrics**: KPIs to track success
6. **Integration Strategy**: How to connect with existing systems

Focus on actionable engineering recommendations."""

            response = self.create_chat_completion(
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": combined_prompt}
                ],
                temperature=0.6,
                max_tokens=2000
            )
            
            insights_text = response["content"]
            
            return {
                "agent_name": self.name,
                "topic": topic,
                "paper_count": len(papers),
                "comprehensive_analysis": insights_text,
                "individual_analyses": [analysis.__dict__ for analysis in analyses],
                "recommendations": self._extract_recommendations(insights_text),
                "architecture_suggestions": self._extract_architecture_suggestions(insights_text)
            }
            
        except Exception as e:
            logger.error(f"Error generating Google Engineer insights: {e}")
            return {"error": str(e), "agent_name": self.name}
    
    def _extract_insights(self, analysis: str) -> List[str]:
        """Extract key insights from analysis text"""
        insights = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['insight:', 'key:', 'important:', 'critical:']):
                insights.append(line.strip())
        
        return insights[:5]  # Top 5 insights
    
    def _extract_breaking_points(self, analysis: str) -> List[str]:
        """Extract breaking points from analysis"""
        breaking_points = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['bottleneck', 'limitation', 'challenge', 'problem', 'issue']):
                breaking_points.append(line.strip())
        
        return breaking_points[:3]  # Top 3 breaking points
    
    def _extract_implementation_ideas(self, analysis: str) -> List[str]:
        """Extract implementation ideas from analysis"""
        ideas = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['implement', 'build', 'develop', 'create', 'design']):
                ideas.append(line.strip())
        
        return ideas[:5]  # Top 5 implementation ideas
    
    def _extract_confidence_score(self, analysis: str) -> float:
        """Extract confidence score from analysis"""
        # Look for confidence mentions in the text
        analysis_lower = analysis.lower()
        
        if 'high confidence' in analysis_lower or 'very confident' in analysis_lower:
            return 0.9
        elif 'medium confidence' in analysis_lower or 'moderately confident' in analysis_lower:
            return 0.7
        elif 'low confidence' in analysis_lower or 'not confident' in analysis_lower:
            return 0.3
        else:
            return 0.6  # Default moderate confidence
    
    def _extract_recommendations(self, insights: str) -> List[str]:
        """Extract specific recommendations from insights text"""
        recommendations = []
        lines = insights.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['recommend', 'suggest', 'should', 'must', 'need to']):
                recommendations.append(line.strip())
        
        return recommendations[:5]
    
    def _extract_architecture_suggestions(self, insights: str) -> List[str]:
        """Extract architecture suggestions from insights text"""
        suggestions = []
        lines = insights.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['architecture', 'system', 'infrastructure', 'design', 'framework']):
                suggestions.append(line.strip())
        
        return suggestions[:3]