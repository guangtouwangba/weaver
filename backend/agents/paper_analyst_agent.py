from typing import Dict, List, Any, Optional
from .base_agent import BaseResearchAgent, AnalysisResult
from retrieval.arxiv_client import Paper
import logging

logger = logging.getLogger(__name__)

class PaperAnalystAgent(BaseResearchAgent):
    """Research agent specialized in deep paper analysis and breaking point identification"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", provider: str = "openai"):
        super().__init__(
            name="Paper Analyst",
            role="Research Paper Analysis Specialist",
            expertise=[
                "Critical paper evaluation",
                "Methodology assessment",
                "Breaking point identification",
                "Research gap analysis",
                "Citation and impact analysis",
                "Cross-paper synthesis"
            ],
            model=model,
            provider=provider,
            api_key=api_key
        )
    
    def analyze_paper(self, paper: Paper, context: Optional[Dict] = None) -> AnalysisResult:
        """Analyze paper focusing on breaking points and critical assessment"""
        try:
            system_prompt = f"""{self.get_system_prompt()}

As a paper analysis specialist, focus specifically on:
- Critical evaluation of methodology and claims
- Identification of weak points and limitations
- Analysis of experimental design and validation
- Assessment of novelty and contribution significance
- Comparison with related work and state-of-the-art
- Evaluation of reproducibility and generalizability
- Identification of potential improvements and extensions"""

            analysis_prompt = f"""{self.get_analysis_prompt(paper, context)}

Conduct a deep critical analysis focusing on:

1. **Methodology Assessment**: 
   - How sound is the experimental design?
   - Are the evaluation metrics appropriate?
   - What are the methodological strengths and weaknesses?

2. **Breaking Points Analysis**:
   - Where does the approach fail or show limitations?
   - What assumptions might not hold in practice?
   - What are the computational or scalability bottlenecks?

3. **Contribution Evaluation**:
   - How novel is this work compared to existing research?
   - What is the significance of the contribution?
   - How does it advance the field?

4. **Reproducibility Assessment**:
   - How reproducible are the results?
   - What information is missing for replication?
   - Are the results generalizable?

5. **Critical Gaps**:
   - What important aspects are not addressed?
   - What follow-up work is needed?
   - Where could the approach be improved?

Provide a thorough, critical analysis with specific identified breaking points."""

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
            insights = self._extract_critical_insights(analysis_text)
            breaking_points = self._extract_detailed_breaking_points(analysis_text)
            implementation_ideas = self._extract_improvement_ideas(analysis_text)
            confidence = self._extract_analytical_confidence(analysis_text)
            
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
                    "focus_areas": ["critical_analysis", "breaking_points", "methodology"],
                    "novelty_score": self._assess_novelty(analysis_text),
                    "reproducibility_score": self._assess_reproducibility(analysis_text),
                    "methodology_score": self._assess_methodology(analysis_text)
                }
            )
            
            self.add_to_history(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in Paper Analyst analysis: {e}")
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
        """Generate comprehensive analytical insights from multiple papers"""
        try:
            # Analyze each paper first
            analyses = []
            for paper in papers:
                analysis = self.analyze_paper(paper)
                analyses.append(analysis)
            
            # Generate cross-paper insights
            combined_prompt = f"""Based on your critical analysis of {len(papers)} papers on "{topic}", 
            provide a comprehensive analytical assessment:

Previous analyses:
{chr(10).join([f"Paper: {analysis.metadata.get('paper_id', 'Unknown')} - {analysis.analysis[:200]}..." for analysis in analyses])}

Generate:
1. **Field Overview**: Current state and progression of research in this area
2. **Common Breaking Points**: Recurring limitations across papers
3. **Methodological Patterns**: Common approaches and their effectiveness
4. **Research Quality Assessment**: Overall quality and rigor of the field
5. **Innovation Gaps**: What novel approaches are missing?
6. **Reproducibility Landscape**: How reproducible is research in this area?
7. **Future Research Priorities**: Most critical areas needing attention
8. **Synthesis Opportunities**: How different approaches could be combined

Focus on critical analysis and identification of systematic issues and opportunities."""

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
                "common_breaking_points": self._extract_common_issues(analyses),
                "methodology_assessment": self._assess_field_methodology(analyses),
                "research_quality_score": self._calculate_field_quality(analyses),
                "innovation_opportunities": self._identify_innovation_gaps(insights_text)
            }
            
        except Exception as e:
            logger.error(f"Error generating Paper Analyst insights: {e}")
            return {"error": str(e), "agent_name": self.name}
    
    def _extract_critical_insights(self, analysis: str) -> List[str]:
        """Extract critical insights from analysis text"""
        insights = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['insight:', 'critical:', 'important:', 'key finding:', 'significant:']):
                insights.append(line.strip())
        
        return insights[:5]
    
    def _extract_detailed_breaking_points(self, analysis: str) -> List[str]:
        """Extract detailed breaking points and limitations"""
        breaking_points = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in [
                'limitation', 'weakness', 'fails when', 'breaks down', 'cannot handle',
                'bottleneck', 'issue', 'problem', 'flaw', 'inadequate'
            ]):
                breaking_points.append(line.strip())
        
        return breaking_points[:5]  # Top 5 breaking points
    
    def _extract_improvement_ideas(self, analysis: str) -> List[str]:
        """Extract improvement and extension ideas"""
        ideas = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in [
                'improve', 'enhance', 'extend', 'address', 'fix',
                'better approach', 'alternative', 'modification'
            ]):
                ideas.append(line.strip())
        
        return ideas[:5]
    
    def _extract_analytical_confidence(self, analysis: str) -> float:
        """Extract confidence in the analytical assessment"""
        analysis_lower = analysis.lower()
        
        # Indicators of high analytical confidence
        high_confidence_indicators = [
            'clear evidence', 'well-documented', 'thorough analysis',
            'comprehensive evaluation', 'strong methodology'
        ]
        
        # Indicators of low analytical confidence
        low_confidence_indicators = [
            'unclear', 'insufficient information', 'limited analysis',
            'needs more investigation', 'uncertain'
        ]
        
        confidence = 0.5  # Base score
        
        for indicator in high_confidence_indicators:
            if indicator in analysis_lower:
                confidence += 0.1
        
        for indicator in low_confidence_indicators:
            if indicator in analysis_lower:
                confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _assess_novelty(self, analysis: str) -> float:
        """Assess the novelty of the paper"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['novel', 'innovative', 'new approach', 'breakthrough']):
            return 0.8
        elif any(word in analysis_lower for word in ['incremental', 'modest improvement']):
            return 0.4
        else:
            return 0.6  # Default moderate novelty
    
    def _assess_reproducibility(self, analysis: str) -> float:
        """Assess reproducibility of the paper"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['reproducible', 'code available', 'detailed methodology']):
            return 0.9
        elif any(word in analysis_lower for word in ['partially reproducible', 'some details missing']):
            return 0.6
        elif any(word in analysis_lower for word in ['not reproducible', 'insufficient details']):
            return 0.2
        else:
            return 0.5  # Default moderate reproducibility
    
    def _assess_methodology(self, analysis: str) -> float:
        """Assess methodology quality"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['sound methodology', 'rigorous', 'well-designed']):
            return 0.9
        elif any(word in analysis_lower for word in ['adequate methodology', 'reasonable approach']):
            return 0.6
        elif any(word in analysis_lower for word in ['weak methodology', 'flawed approach']):
            return 0.3
        else:
            return 0.5  # Default moderate methodology
    
    def _extract_common_issues(self, analyses: List[AnalysisResult]) -> List[str]:
        """Extract common issues across multiple papers"""
        all_breaking_points = []
        for analysis in analyses:
            all_breaking_points.extend(analysis.breaking_points)
        
        # Find common themes (simplified approach)
        common_themes = []
        for point in all_breaking_points:
            if any(keyword in point.lower() for keyword in ['scalability', 'evaluation', 'generalization']):
                common_themes.append(point)
        
        return list(set(common_themes))[:5]
    
    def _assess_field_methodology(self, analyses: List[AnalysisResult]) -> Dict[str, Any]:
        """Assess overall methodology quality of the field"""
        if not analyses:
            return {}
        
        avg_methodology = sum(
            analysis.metadata.get('methodology_score', 0.5) 
            for analysis in analyses
        ) / len(analyses)
        
        avg_reproducibility = sum(
            analysis.metadata.get('reproducibility_score', 0.5) 
            for analysis in analyses
        ) / len(analyses)
        
        return {
            "average_methodology_score": avg_methodology,
            "average_reproducibility_score": avg_reproducibility,
            "field_methodology_assessment": "strong" if avg_methodology > 0.7 else "moderate" if avg_methodology > 0.4 else "weak"
        }
    
    def _calculate_field_quality(self, analyses: List[AnalysisResult]) -> float:
        """Calculate overall research quality score for the field"""
        if not analyses:
            return 0.0
        
        quality_factors = []
        for analysis in analyses:
            novelty = analysis.metadata.get('novelty_score', 0.5)
            reproducibility = analysis.metadata.get('reproducibility_score', 0.5)
            methodology = analysis.metadata.get('methodology_score', 0.5)
            confidence = analysis.confidence_score
            
            # Weighted average
            quality = (novelty * 0.25 + reproducibility * 0.25 + methodology * 0.25 + confidence * 0.25)
            quality_factors.append(quality)
        
        return sum(quality_factors) / len(quality_factors)
    
    def _identify_innovation_gaps(self, insights: str) -> List[str]:
        """Identify innovation opportunities from insights text"""
        gaps = []
        lines = insights.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in [
                'gap', 'opportunity', 'missing', 'lacking', 'needs development',
                'unexplored', 'potential area'
            ]):
                gaps.append(line.strip())
        
        return gaps[:5]