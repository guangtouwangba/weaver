from typing import Dict, List, Any, Optional
from .base_agent import BaseResearchAgent, AnalysisResult
from retrieval.arxiv_client import Paper
import logging

logger = logging.getLogger(__name__)

class MITResearcherAgent(BaseResearchAgent):
    """Research agent specialized in MIT-style academic research"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", provider: str = "openai"):
        super().__init__(
            name="MIT Researcher",
            role="Principal Research Scientist at MIT",
            expertise=[
                "Theoretical computer science",
                "Algorithm design and analysis",
                "Mathematical foundations",
                "Novel research methodologies",
                "Academic rigor and validation",
                "Interdisciplinary research"
            ],
            model=model,
            provider=provider,
            api_key=api_key
        )
    
    def analyze_paper(self, paper: Paper, context: Optional[Dict] = None) -> AnalysisResult:
        """Analyze paper from MIT academic research perspective"""
        try:
            system_prompt = f"""{self.get_system_prompt()}

As an MIT researcher, focus specifically on:
- Theoretical contributions and mathematical rigor
- Novel algorithmic approaches
- Experimental methodology and validation
- Reproducibility and scientific soundness
- Connections to fundamental research questions
- Potential for breakthrough discoveries
- Academic significance and impact potential"""

            analysis_prompt = f"""{self.get_analysis_prompt(paper, context)}

From an MIT research perspective, evaluate:

1. **Theoretical Contributions**: What new theoretical insights does this provide?
2. **Mathematical Rigor**: How sound are the mathematical foundations?
3. **Algorithmic Novelty**: Are there new algorithmic contributions?
4. **Experimental Design**: How robust is the experimental methodology?
5. **Reproducibility**: Can the results be independently verified?
6. **Research Impact**: What's the potential academic significance?
7. **Future Directions**: What research questions does this open up?
8. **Interdisciplinary Connections**: How does this connect to other fields?

Provide deep theoretical analysis and identify fundamental research contributions."""

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
            insights = self._extract_theoretical_insights(analysis_text)
            breaking_points = self._extract_research_gaps(analysis_text)
            implementation_ideas = self._extract_research_directions(analysis_text)
            confidence = self._extract_research_confidence(analysis_text)
            
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
                    "focus_areas": ["theory", "algorithms", "methodology"],
                    "research_quality": self._assess_research_quality(analysis_text)
                }
            )
            
            self.add_to_history(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in MIT Researcher analysis: {e}")
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
        """Generate academic research insights from multiple papers"""
        try:
            # Analyze each paper first
            analyses = []
            for paper in papers:
                analysis = self.analyze_paper(paper)
                analyses.append(analysis)
            
            # Generate cross-paper insights
            combined_prompt = f"""Based on your analysis of {len(papers)} papers on "{topic}", 
            provide a comprehensive academic research assessment:

Previous analyses:
{chr(10).join([f"Paper: {analysis.metadata.get('paper_id', 'Unknown')} - {analysis.analysis[:200]}..." for analysis in analyses])}

Generate:
1. **Research Landscape**: Current state of the field and key contributions
2. **Theoretical Gaps**: What fundamental questions remain unanswered?
3. **Methodological Advances**: New research methodologies emerging
4. **Algorithmic Innovations**: Novel algorithmic contributions across papers
5. **Experimental Standards**: Assessment of experimental rigor
6. **Future Research Agenda**: Priority research directions
7. **Interdisciplinary Opportunities**: Connections to other research areas
8. **Academic Impact Potential**: Likelihood of significant scholarly impact

Focus on deep theoretical analysis and fundamental research contributions."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.get_system_prompt()},
                    {"role": "user", "content": combined_prompt}
                ],
                temperature=0.6,
                max_tokens=2000
            )
            
            insights_text = response.choices[0].message.content
            
            return {
                "agent_name": self.name,
                "topic": topic,
                "paper_count": len(papers),
                "comprehensive_analysis": insights_text,
                "individual_analyses": [analysis.__dict__ for analysis in analyses],
                "theoretical_contributions": self._extract_theoretical_contributions(insights_text),
                "research_gaps": self._extract_major_research_gaps(insights_text),
                "future_directions": self._extract_future_research(insights_text),
                "academic_impact_score": self._calculate_academic_impact(analyses)
            }
            
        except Exception as e:
            logger.error(f"Error generating MIT Researcher insights: {e}")
            return {"error": str(e), "agent_name": self.name}
    
    def _extract_theoretical_insights(self, analysis: str) -> List[str]:
        """Extract theoretical insights from analysis text"""
        insights = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['theoretical', 'mathematical', 'algorithm', 'proof', 'theorem']):
                insights.append(line.strip())
        
        return insights[:5]
    
    def _extract_research_gaps(self, analysis: str) -> List[str]:
        """Extract research gaps and limitations"""
        gaps = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['gap', 'limitation', 'unclear', 'missing', 'needs work']):
                gaps.append(line.strip())
        
        return gaps[:3]
    
    def _extract_research_directions(self, analysis: str) -> List[str]:
        """Extract future research directions"""
        directions = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['future', 'extend', 'explore', 'investigate', 'research']):
                directions.append(line.strip())
        
        return directions[:5]
    
    def _extract_research_confidence(self, analysis: str) -> float:
        """Extract confidence in research quality and contributions"""
        analysis_lower = analysis.lower()
        
        # Look for academic quality indicators
        quality_indicators = [
            'rigorous', 'sound methodology', 'strong theoretical',
            'well-designed', 'comprehensive evaluation', 'novel contribution'
        ]
        
        confidence_score = 0.5  # Base score
        
        for indicator in quality_indicators:
            if indicator in analysis_lower:
                confidence_score += 0.1
        
        # Check for negative indicators
        negative_indicators = [
            'weak methodology', 'limited evaluation', 'unclear',
            'insufficient evidence', 'not convincing'
        ]
        
        for indicator in negative_indicators:
            if indicator in analysis_lower:
                confidence_score -= 0.1
        
        return max(0.0, min(1.0, confidence_score))
    
    def _assess_research_quality(self, analysis: str) -> str:
        """Assess overall research quality"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['excellent', 'outstanding', 'breakthrough']):
            return "high"
        elif any(word in analysis_lower for word in ['solid', 'good', 'adequate']):
            return "medium"
        else:
            return "low"
    
    def _extract_theoretical_contributions(self, insights: str) -> List[str]:
        """Extract theoretical contributions from insights text"""
        contributions = []
        lines = insights.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['contribution', 'novel', 'advance', 'breakthrough']):
                contributions.append(line.strip())
        
        return contributions[:5]
    
    def _extract_major_research_gaps(self, insights: str) -> List[str]:
        """Extract major research gaps from insights text"""
        gaps = []
        lines = insights.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['gap', 'open question', 'unresolved', 'challenge']):
                gaps.append(line.strip())
        
        return gaps[:3]
    
    def _extract_future_research(self, insights: str) -> List[str]:
        """Extract future research directions from insights text"""
        directions = []
        lines = insights.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['future', 'next step', 'direction', 'opportunity']):
                directions.append(line.strip())
        
        return directions[:5]
    
    def _calculate_academic_impact(self, analyses: List[AnalysisResult]) -> float:
        """Calculate potential academic impact score"""
        if not analyses:
            return 0.0
        
        total_confidence = sum(analysis.confidence_score for analysis in analyses)
        avg_confidence = total_confidence / len(analyses)
        
        # Factor in research quality
        quality_bonus = 0.0
        for analysis in analyses:
            quality = analysis.metadata.get('research_quality', 'medium')
            if quality == 'high':
                quality_bonus += 0.2
            elif quality == 'medium':
                quality_bonus += 0.1
        
        quality_bonus /= len(analyses)
        
        return min(1.0, avg_confidence + quality_bonus)