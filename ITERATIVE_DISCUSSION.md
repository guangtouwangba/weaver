# Iterative Multi-Agent Discussion Workflow

## Overview

The multi-agent workflow has been refactored to create **iterative discussions** instead of independent parallel analyses. This mimics how people naturally discuss topics through multiple rounds of conversation, where each participant builds on what previous speakers have said.

## Key Changes

### 🔄 **From Parallel to Sequential**

**Before:**
- All agents analyzed papers independently
- Each agent produced separate discussions  
- Results were combined through basic synthesis
- User saw separate agent outputs

**After:**
- Agents participate in sequential discussion rounds
- Each agent builds on previous agents' contributions
- Final unified conclusion synthesizes the entire conversation
- User sees final result with conversation flow for transparency

### 📊 **New Data Structures**

```python
@dataclass
class DiscussionRound:
    """Represents a single round in the iterative discussion"""
    round_number: int
    agent_name: str
    agent_response: str
    timestamp: datetime
    tokens_used: Optional[int] = None

@dataclass
class IterativeDiscussion:
    """Represents an iterative discussion between multiple agents"""
    query: str
    papers: List[Paper]
    rounds: List[DiscussionRound]
    final_conclusion: Optional[str] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
```

### 🎯 **Workflow Process**

1. **Round 1 - Google Engineer**: Analyzes papers and provides initial technical insights
2. **Round 2 - MIT Researcher**: Responds to engineering insights + adds academic perspective  
3. **Round 3 - Industry Expert**: Builds on previous discussion + adds business/market view
4. **Round 4 - Paper Analyst**: Responds to all previous points + adds methodological analysis
5. **Final Synthesis**: AI generates comprehensive conclusion from entire discussion

### 💬 **Context-Aware Prompting**

Each agent (except the first) receives:
- Full research papers
- Previous discussion rounds from other agents
- Instructions to build on previous insights
- Role-specific focus areas

**First Round Prompt Structure:**
```
You are a [Role] participating in a research discussion about: "[Query]"

Your Role: As the first contributor, provide analysis focusing on [focus areas]

Please structure your response:
1. Key Findings
2. Your Perspective  
3. Critical Questions
4. Implications
```

**Subsequent Round Prompt Structure:**
```
You are a [Role] participating in an ongoing research discussion about: "[Query]"

Previous Discussion: [Previous agents' responses]

Your Role: Build on previous insights while adding your perspective on [focus areas]

Please structure your response:
1. Response to Previous Points
2. Your Additional Insights
3. Areas of Agreement/Disagreement  
4. New Directions
```

### 📝 **New Response Format**

The system now emphasizes the **final unified result** while showing the discussion process. **By default, the final conclusion is output in Chinese**:

```
# 研究分析结果

**查询问题**: [User's question]

## 🎯 **最终分析结论**
[用中文提供的综合专家见解的全面结论]

---

## 💬 **专家讨论过程**
*我们的4位研究专家通过4轮分析讨论了您的问题：*

**Round 1 - ⚙️ Google Engineer**
[Brief preview of engineering perspective...]

**Round 2 - 🎓 MIT Researcher** 
[Brief preview of academic perspective...]

**Round 3 - 💼 Industry Expert**
[Brief preview of business perspective...]

**Round 4 - 📊 Paper Analyst**
[Brief preview of methodological perspective...]

---

## 📚 **分析的论文** (X 篇论文)
[List of analyzed papers with relevance scores in Chinese labels]
```

## Benefits

### ✨ **For Users**
- **Single unified answer** instead of multiple separate analyses
- **Comprehensive insights** from conversational agent interaction
- **Transparency** - can see how the discussion evolved
- **Higher quality** - agents build on each other's insights
- **Chinese output by default** - Final conclusions are provided in Chinese for better local accessibility

### 🤖 **For Agents**
- **Context awareness** - each agent knows what others have said
- **Collaborative analysis** - agents can agree, disagree, and build upon points
- **Specialized focus** - each agent contributes their unique expertise
- **Iterative refinement** - later agents can address gaps from earlier rounds

## Technical Implementation

### Key Methods

- `_generate_multi_agent_discussion()` - Main orchestration method (refactored)
- `_create_iterative_discussion_prompt()` - Context-aware prompt generation
- `_get_iterative_agent_response()` - Get agent response for discussion round
- `_generate_final_conclusion()` - Synthesize entire discussion into final result
- `_generate_comprehensive_discussion_response()` - Format final response

### Agent Processing Order

1. **Google Engineer** - Technical implementation and engineering perspective
2. **MIT Researcher** - Academic research and theoretical foundations  
3. **Industry Expert** - Business applications and market implications
4. **Paper Analyst** - Research methodology and analytical rigor

This order ensures a logical flow from technical implementation → research theory → business application → methodological analysis.

## Configuration

The iterative discussion system uses the same configuration as before:

```env
# Enable agent discussions (default: true)
ENABLE_AGENT_DISCUSSIONS=true

# Default selected agents for discussion
DEFAULT_SELECTED_AGENTS=Google Engineer,MIT Researcher,Industry Expert,Paper Analyst
```

## Usage

The system automatically uses the iterative workflow when calling:

```python
result = orchestrator.chat_with_papers(
    query="Your research question",
    n_papers=10,
    min_similarity_threshold=0.6
)

# Access the final conclusion
final_answer = result['agent_discussions']['final_conclusion']

# Access the discussion rounds for transparency
rounds = result['agent_discussions']['discussion_rounds']
```

## Migration Notes

- **Backward compatibility**: Old interface still works
- **Response format**: New format emphasizes final conclusion
- **Performance**: Sequential processing may take slightly longer than parallel, but provides higher quality results
- **API**: No breaking changes to existing API calls

---

*This iterative discussion system transforms multi-agent analysis from independent parallel processing into collaborative conversational intelligence.*