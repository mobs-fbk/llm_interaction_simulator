from .prompts_constants import *

def add_template(prompt:str, keys:list[str]):
    for key in keys:
        prompt += f"\n\n## {key}\n{{{key}}}"
    return prompt

def get_full_SM(initial_SP:str, context:dict[str, str]) -> str:
    full_SP = initial_SP
    full_SP = add_template(full_SP, context.keys())
    full_SP = full_SP.format(**context)
    return full_SP

def get_guard_SM():
    context = {
        "Personality": GUARD_PERSONALITY,
        "Study": STUDY,
        "Environment": GUARD_ENV,
        "Goal": GUARD_GOAL,
        "Risks": GUARD_RISKS,
        "Researcher Oversight": RESEARCH_OVERSIGHT
    }
    full_SM = get_full_SM(GUARD_SP + COMMUNICATION_RULES, context)
    return full_SM

def get_prisoner_SM():
    context = {
        "Personality": PRISONER_PERSONALITY,
        "Study": STUDY,
        "Environment": PRISONER_ENV,
        "Goal": PRISONER_GOAL,
        "Risks": PRISONER_RISKS,
        "Researcher Oversight": RESEARCH_OVERSIGHT
    }
    full_SM = get_full_SM(PRISONER_SP + COMMUNICATION_RULES, context)
    return full_SM

def get_summarizer_SM():
    context = {
        "Goal": SUMMARIZER_GOAL,
        "Key elements": KEY_ELEMENTS,
        "Rules": RULES,
        }
    full_SM = get_full_SM(SUMMERIZER_SP, context)
    return full_SM