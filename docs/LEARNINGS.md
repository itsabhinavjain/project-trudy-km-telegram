These are Abhinav's learning while building the application. Add this to my central repository later. 
This file should be ignored by claude code 

## Notes 
- I started with the claude planning mode by giving a basic requirement. 
- I think that the best way is to really focus on defining the requirements and specifications well. 
  - Use one of the frameworks 
    - BMAD 
    - Spec Driven etc 


- Run /init after you get the first cut of implementation (This will allow the subsequent runs to be faster)


## Artifacts and Rules 

- Development process related
  - Have states and indempodency while fetching some data especially when you are running a script multiple time
  - Maintain CHANGELOG.md 
  - Define a set of use cases (that can then potentially be added as test cases). It allows you to figure out the corner cases to manage. USECASES.md 
  - What all to specify in the PRD.md file (Fix this well)

```
{
  "role": "system",
  "purpose": "Create a world-class prompt for any AI product workflow by architecting a stable, predictable reasoning environment. The goal is to produce a prompt that behaves consistently even when inputs are vague, incomplete, contradictory, or out-of-scope.",
  "instructions": {
    "1_purpose_definition": "Define the single primary operational purpose of the prompt. It must be unambiguous, decision-focused, and interpretable identically by different operators.",
    "2_responsibility_boundaries": "Explicitly state what this prompt is responsible for and what it is NOT responsible for. This prompt must own exactly one cognitive responsibility. Exclude interpretation, validation, formatting, safety, or multi-step reasoning unless this prompt specifically owns that step.",
    "3_interpretation_logic": "If interpretation is part of this prompt, define which signals matter, which signals must be ignored, how to treat missing or conflicting information, and when to ask for clarification instead of guessing.",
    "4_decision_rules": "Define the hierarchy of decision-making values the model must follow when resolving conflicts. Make tradeoffs explicit (e.g., factual accuracy > completeness > style).",
    "5_constraints": "Define strict constraints specifying what the model must NOT do, including hallucinations, invented facts, smoothing ambiguity, answering outside scope, or generating content unsupported by the input.",
    "6_failure_philosophy": "Define exactly when the model should refuse, ask for clarification, expose uncertainty, or stop processing. Failure behavior must be consistent and product-aligned.",
    "7_output_contract": "Define the precise output format expected: structure, tone, length, fields, units, and prohibited content. The output must be reliable for downstream systems.",
    "8_internal_reasoning_isolation": "Instruct the model to keep internal reasoning hidden and separate from the final output. The prompt must not expose chain-of-thought or deliberations."
  }
}
```

- Python 
  - Specify how you want to manage dependency management etc. Use `pyproject.toml` and `uv` for that.
  - Specify what all packages to use for the project.
    - Use `typer` instead of `argparse` or `click` for the cli tool
  - While creating the cli tool - Add help sections. The help section
  - Specify the flags etc 