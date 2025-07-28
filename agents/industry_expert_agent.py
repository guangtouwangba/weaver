from typing import Dict, List, Any, Optional
from .base_agent import BaseResearchAgent, AnalysisResult
from retrieval.arxiv_client import Paper
import logging

logger = logging.getLogger(__name__)

class IndustryExpertAgent(BaseResearchAgent):
    """Research agent specialized in industry applications and commercialization"""
    
    def __init__(self, api_key: str, model: str = "gpt-4o-mini", provider: str = "openai"):
        super().__init__(
            name="Industry Expert",
            role="Senior Technology Director with industry experience",
            expertise=[
                "Technology commercialization",
                "Market analysis and adoption",
                "Business model validation",
                "Product development lifecycle",
                "Competitive landscape analysis",
                "Technology transfer and licensing"
            ],
            model=model,
            provider=provider,
            api_key=api_key
        )
    
    def analyze_paper(self, paper: Paper, context: Optional[Dict] = None) -> AnalysisResult:
        """Analyze paper from industry commercialization perspective"""
        try:
            system_prompt = f"""{self.get_system_prompt()}

As an industry expert, focus specifically on:
- Commercial viability and market potential
- Technology readiness and maturity level
- Competitive advantages and differentiation
- Business model implications
- Adoption barriers and market challenges
- Revenue generation opportunities
- Intellectual property considerations
- Time-to-market and development costs"""

            analysis_prompt = f"""{self.get_analysis_prompt(paper, context)}

From an industry perspective, evaluate:

1. **Market Potential**: What is the addressable market for this technology?
2. **Commercial Viability**: How ready is this for commercialization?
3. **Competitive Landscape**: How does this compare to existing solutions?
4. **Business Model**: What revenue models could this enable?
5. **Adoption Barriers**: What would prevent market adoption?
6. **Technology Readiness**: What's needed to make this production-ready?
7. **Investment Appeal**: Would this attract venture capital or corporate investment?
8. **Regulatory Considerations**: Are there compliance or regulatory hurdles?

Provide concrete business and market insights with actionable recommendations."""

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
            insights = self._extract_market_insights(analysis_text)
            breaking_points = self._extract_adoption_barriers(analysis_text)
            implementation_ideas = self._extract_commercialization_ideas(analysis_text)
            confidence = self._extract_commercial_confidence(analysis_text)
            
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
                    "focus_areas": ["commercialization", "market_analysis", "business_model"],
                    "market_readiness": self._assess_market_readiness(analysis_text),
                    "technology_readiness_level": self._assess_trl(analysis_text)
                }
            )
            
            self.add_to_history(result)
            return result
            
        except Exception as e:
            logger.error(f"Error in Industry Expert analysis: {e}")
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
        """Generate industry and commercialization insights from multiple papers"""
        try:
            # Analyze each paper first
            analyses = []
            for paper in papers:
                analysis = self.analyze_paper(paper)
                analyses.append(analysis)
            
            # Generate cross-paper insights
            combined_prompt = f"""Based on your analysis of {len(papers)} papers on "{topic}", 
            provide a comprehensive industry and market assessment:

Previous analyses:
{chr(10).join([f"Paper: {analysis.metadata.get('paper_id', 'Unknown')} - {analysis.analysis[:200]}..." for analysis in analyses])}

Generate:
1. **Market Landscape**: Current industry state and emerging opportunities
2. **Technology Trends**: Key technological developments and their market impact
3. **Commercial Roadmap**: Path from research to market-ready products
4. **Investment Opportunities**: Areas most attractive to investors
5. **Competitive Analysis**: How different approaches compare commercially
6. **Risk Assessment**: Market and technology risks to consider
7. **Business Model Innovation**: New revenue models enabled by this research
8. **Go-to-Market Strategy**: Recommended market entry approaches

Focus on actionable business insights and commercialization strategies."""

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
                "market_opportunities": self._extract_market_opportunities(insights_text),
                "business_models": self._extract_business_models(insights_text),
                "investment_potential": self._calculate_investment_score(analyses),
                "commercialization_timeline": self._estimate_timeline(analyses)
            }
            
        except Exception as e:
            logger.error(f"Error generating Industry Expert insights: {e}")
            return {"error": str(e), "agent_name": self.name}
    
    def _extract_market_insights(self, analysis: str) -> List[str]:
        """Extract market-related insights from analysis text"""
        insights = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['market', 'commercial', 'business', 'revenue', 'customer']):
                insights.append(line.strip())
        
        return insights[:5]
    
    def _extract_adoption_barriers(self, analysis: str) -> List[str]:
        """Extract barriers to market adoption"""
        barriers = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['barrier', 'challenge', 'obstacle', 'difficulty', 'risk']):
                barriers.append(line.strip())
        
        return barriers[:3]
    
    def _extract_commercialization_ideas(self, analysis: str) -> List[str]:
        """Extract commercialization and business ideas"""
        ideas = []
        lines = analysis.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['opportunity', 'potential', 'application', 'use case', 'monetize']):
                ideas.append(line.strip())
        
        return ideas[:5]
    
    def _extract_commercial_confidence(self, analysis: str) -> float:
        """Extract confidence in commercial viability"""
        analysis_lower = analysis.lower()
        
        # Positive commercial indicators
        positive_indicators = [
            'strong market potential', 'clear value proposition', 'competitive advantage',
            'ready for market', 'high demand', 'profitable'
        ]
        
        # Negative commercial indicators
        negative_indicators = [
            'limited market', 'unclear value', 'high barriers',
            'not ready', 'expensive', 'regulatory issues'
        ]
        
        confidence = 0.5  # Base score
        
        for indicator in positive_indicators:
            if indicator in analysis_lower:
                confidence += 0.1
        
        for indicator in negative_indicators:
            if indicator in analysis_lower:
                confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def _assess_market_readiness(self, analysis: str) -> str:
        """Assess market readiness level"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['market ready', 'production ready', 'commercializable']):
            return "high"
        elif any(word in analysis_lower for word in ['prototype', 'pilot', 'testing']):
            return "medium"
        else:
            return "low"
    
    def _assess_trl(self, analysis: str) -> int:
        """Assess Technology Readiness Level (1-9)"""
        analysis_lower = analysis.lower()
        
        if any(word in analysis_lower for word in ['production', 'deployed', 'commercial']):
            return 9
        elif any(word in analysis_lower for word in ['pilot', 'demonstration']):
            return 7
        elif any(word in analysis_lower for word in ['prototype', 'testing']):
            return 5
        elif any(word in analysis_lower for word in ['proof of concept', 'validation']):
            return 3
        else:
            return 2  # Research stage
    
    def _extract_market_opportunities(self, insights: str) -> List[str]:
        """Extract market opportunities from insights text"""
        opportunities = []
        lines = insights.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['opportunity', 'market', 'potential', 'growth']):
                opportunities.append(line.strip())
        
        return opportunities[:5]
    
    def _extract_business_models(self, insights: str) -> List[str]:
        """Extract business model suggestions from insights text"""
        models = []
        lines = insights.split('\n')
        
        for line in lines:
            if any(keyword in line.lower() for keyword in ['business model', 'revenue', 'monetization', 'pricing']):
                models.append(line.strip())
        
        return models[:3]
    
    def _calculate_investment_score(self, analyses: List[AnalysisResult]) -> float:
        """Calculate investment attractiveness score"""
        if not analyses:
            return 0.0
        
        total_score = 0.0
        for analysis in analyses:
            # Base confidence score
            score = analysis.confidence_score
            
            # Bonus for high market readiness
            market_readiness = analysis.metadata.get('market_readiness', 'low')
            if market_readiness == 'high':
                score += 0.2
            elif market_readiness == 'medium':
                score += 0.1
            
            # Bonus for high TRL
            trl = analysis.metadata.get('technology_readiness_level', 2)
            if trl >= 7:
                score += 0.2
            elif trl >= 5:
                score += 0.1
            
            total_score += score
        
        return min(1.0, total_score / len(analyses))
    
    def _estimate_timeline(self, analyses: List[AnalysisResult]) -> Dict[str, str]:
        """Estimate commercialization timeline"""
        if not analyses:
            return {}
        
        avg_trl = sum(analysis.metadata.get('technology_readiness_level', 2) for analysis in analyses) / len(analyses)
        
        if avg_trl >= 7:
            return {
                "prototype_to_market": "6-12 months",
                "full_commercialization": "1-2 years",
                "market_maturity": "3-5 years"
            }
        elif avg_trl >= 5:
            return {
                "prototype_to_market": "1-2 years",
                "full_commercialization": "2-4 years",
                "market_maturity": "5-7 years"
            }
        else:
            return {
                "prototype_to_market": "2-4 years",
                "full_commercialization": "4-7 years",
                "market_maturity": "7-10 years"
            }