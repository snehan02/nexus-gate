# Logic to choose models
def get_optimal_model(prompt: str, priority: str = "standard") -> str:
    # 1. Check for 'High Priority' flag
    if priority == "high":
        return "anthropic/claude-3-5-sonnet"

    # 2. Heuristic Triage: Analyze complexity
    # In 2026, we look for code blocks or reasoning keywords
    reasoning_keywords = ["analyze", "evaluate", "solve", "step-by-step", "code"]
    
    if any(k in prompt.lower() for k in reasoning_keywords) or len(prompt) > 500:
        return "openai/gpt-4o"  # High reasoning
    
    return "openai/gpt-4o-mini" # Simple, fast, and cheap