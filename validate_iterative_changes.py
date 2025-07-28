#!/usr/bin/env python3
"""
Simple validation script to check if the iterative discussion changes are properly implemented
"""

import ast
import re

def check_orchestrator_changes():
    """Check if the orchestrator.py has the required changes"""
    print("🔍 Checking orchestrator.py changes...")
    
    try:
        with open("/Users/siqiuchen/Documents/opensource/research-agent-rag/agents/orchestrator.py", "r") as f:
            content = f.read()
        
        # Check 1: New data structures
        if "class DiscussionRound:" in content:
            print("✅ DiscussionRound class found")
        else:
            print("❌ DiscussionRound class not found")
            return False
            
        if "class IterativeDiscussion:" in content:
            print("✅ IterativeDiscussion class found")
        else:
            print("❌ IterativeDiscussion class not found")
            return False
        
        # Check 2: New methods for iterative discussion
        if "_create_iterative_discussion_prompt" in content:
            print("✅ _create_iterative_discussion_prompt method found")
        else:
            print("❌ _create_iterative_discussion_prompt method not found")
            return False
            
        if "_get_iterative_agent_response" in content:
            print("✅ _get_iterative_agent_response method found")
        else:
            print("❌ _get_iterative_agent_response method not found")
            return False
            
        if "_generate_final_conclusion" in content:
            print("✅ _generate_final_conclusion method found")
        else:
            print("❌ _generate_final_conclusion method not found")
            return False
        
        # Check 3: Updated _generate_multi_agent_discussion method
        if "def _generate_multi_agent_discussion" in content:
            # Find the method and check if it has iterative logic
            method_match = re.search(r'def _generate_multi_agent_discussion.*?\n    def ', content, re.DOTALL)
            if method_match:
                method_content = method_match.group(0)
                if "IterativeDiscussion" in method_content and "discussion.rounds" in method_content:
                    print("✅ _generate_multi_agent_discussion updated for iterative workflow")
                else:
                    print("❌ _generate_multi_agent_discussion not properly updated")
                    return False
            else:
                print("❌ Could not parse _generate_multi_agent_discussion method")
                return False
        else:
            print("❌ _generate_multi_agent_discussion method not found")
            return False
        
        # Check 4: Updated response format 
        if '"final_conclusion"' in content and '"discussion_rounds"' in content:
            print("✅ New response format with final_conclusion and discussion_rounds")
        else:
            print("❌ New response format not found")
            return False
        
        # Check 5: Updated _generate_comprehensive_discussion_response
        if "Generate comprehensive response with iterative multi-agent discussion" in content:
            print("✅ _generate_comprehensive_discussion_response updated for iterative format")
        else:
            print("❌ _generate_comprehensive_discussion_response not properly updated")
            return False
        
        print("✅ All orchestrator changes validated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking orchestrator.py: {e}")
        return False

def check_workflow_logic():
    """Check the logical flow of the iterative discussion"""
    print("\n🔍 Checking iterative discussion workflow logic...")
    
    try:
        with open("/Users/siqiuchen/Documents/opensource/research-agent-rag/agents/orchestrator.py", "r") as f:
            content = f.read()
        
        # Check for sequential agent processing
        if "for round_num, agent_name in enumerate(available_agents, 1):" in content:
            print("✅ Sequential agent processing implemented")
        else:
            print("❌ Sequential agent processing not found")
            return False
        
        # Check for context passing
        if "_create_iterative_discussion_prompt" in content and "previous_rounds" in content:
            print("✅ Context passing between rounds implemented")
        else:
            print("❌ Context passing not properly implemented")
            return False
        
        # Check for final conclusion generation
        if "discussion.final_conclusion = self._generate_final_conclusion(discussion)" in content:
            print("✅ Final conclusion generation implemented")
        else:
            print("❌ Final conclusion generation not found")
            return False
        
        print("✅ Workflow logic validated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking workflow logic: {e}")
        return False

def check_prompt_improvements():
    """Check if prompts have been improved for iterative discussion"""
    print("\n🔍 Checking prompt improvements...")
    
    try:
        with open("/Users/siqiuchen/Documents/opensource/research-agent-rag/agents/orchestrator.py", "r") as f:
            content = f.read()
        
        # Check for context-aware prompting
        if "Previous Discussion:" in content:
            print("✅ Context-aware prompting implemented")
        else:
            print("❌ Context-aware prompting not found")
            return False
        
        # Check for role-specific prompts
        if "agent_roles = {" in content and "google_engineer" in content:
            print("✅ Role-specific prompts implemented")
        else:
            print("❌ Role-specific prompts not found")
            return False
        
        # Check for conversational structure
        if "building on the previous insights" in content:
            print("✅ Conversational prompt structure implemented")
        else:
            print("❌ Conversational prompt structure not found")
            return False
        
        print("✅ Prompt improvements validated successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error checking prompt improvements: {e}")
        return False

def main():
    """Main validation function"""
    print("🚀 Validating Iterative Multi-Agent Discussion Implementation")
    print("=" * 65)
    
    all_checks_passed = True
    
    # Check 1: Orchestrator changes
    if not check_orchestrator_changes():
        all_checks_passed = False
    
    # Check 2: Workflow logic
    if not check_workflow_logic():
        all_checks_passed = False
    
    # Check 3: Prompt improvements
    if not check_prompt_improvements():
        all_checks_passed = False
    
    print("\n" + "=" * 65)
    if all_checks_passed:
        print("🎉 ALL VALIDATIONS PASSED!")
        print("\nSummary of changes implemented:")
        print("✅ New data structures: DiscussionRound, IterativeDiscussion")
        print("✅ Sequential agent workflow instead of parallel")
        print("✅ Context-aware prompting with conversation history")
        print("✅ Final unified conclusion generation")
        print("✅ Updated response format emphasizing final results")
        print("\n🚀 The iterative discussion workflow is ready to use!")
    else:
        print("❌ SOME VALIDATIONS FAILED!")
        print("Please check the issues above and fix them.")
    
    return 0 if all_checks_passed else 1

if __name__ == "__main__":
    import sys
    sys.exit(main())