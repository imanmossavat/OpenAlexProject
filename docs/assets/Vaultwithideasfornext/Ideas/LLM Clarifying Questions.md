
---

# LLM for Clarifying User Intent Before Keyword/Expression Generation

## Overview

The crawler relies on keywords and Boolean expressions to filter relevant academic papers. Users often enter vague or incomplete queries, which reduces the quality of crawler results. To fix this, the system will offer **two modes**:

1. **Quick Generate** — Directly convert a query into keywords + Boolean expressions
    
2. **Clarify Intent** — Have an LLM ask clarifying questions first, then generate keywords + expressions
    

This allows both fast usage and high-precision search refinement.

---

# Problem

Users frequently enter broad queries like:

- “AI agriculture”
    
- “robotics medicine”
    
- “exercise rehab”
    

These queries do not specify:

- which subtopics matter
    
- what to include or exclude
    
- which methods are relevant
    
- what the user _really_ wants
    

Direct keyword generation from such ambiguous input often produces noisy or irrelevant crawler results.

---

# Solution: Two LLM Modes

## Mode 1 — Quick Keyword/Expression Generation

**User Flow**

1. User enters a query
    
2. LLM instantly generates:
    
    - keywords
        
    - Boolean expressions
        

### Pros

- Fast
    
- Great for simple or well-defined topics
    

### Cons

- Less accurate when queries are vague
    

---

## Mode 2 — Clarify Intent First

**User Flow**

1. User enters a broad query
    
2. LLM asks clarifying questions
    
3. User answers
    
4. LLM generates:
    
    - refined keywords
        
    - Boolean expressions
        

### Pros

- Much more accurate
    
- Ideal for complex research questions
    
- Helps non-experts express what they want
    

### Cons

- Takes a few extra steps
    

---

# Full Example Workflow

This example shows how the clarifying mode works end-to-end.

---

## 1. User’s Initial Query

> “I want papers about AI in agriculture.”

---

## 2. Clarifier LLM Asks Questions

**LLM:**

- “Are you mainly interested in crop yield prediction, soil analysis, livestock monitoring, or all of them?”
    
- “Should we focus only on machine learning methods, or include robotics and IoT as well?”
    
- “Do you want recent papers or all years?”
    

### User Answers:

> “Crop yield prediction and soil sensing, only machine learning, avoid robotics and IoT, last 5 years.”

---

## 3. Clarifier Intent JSON Output

```json
{
  "include_topics": ["crop yield prediction", "soil sensing"],
  "methods": ["machine learning"],
  "exclude_terms": ["robotics", "iot"],
  "time_range": "last 5 years",
  "domains": ["agriculture", "computer science"],
  "notes": "User wants ML-only papers in agriculture, focusing on crop yield and soil sensing."
}
```

---

## 4. Keyword/Expression Generator Converts That Intent

This produces crawler-ready output.

---

# Example (Correct Crawler-Compatible Output)

### Final Keywords:

- crop yield prediction
    
- soil moisture sensing
    
- soil nutrient estimation
    
- machine learning agriculture
    
- deep learning agriculture
    
- remote sensing agriculture
    
- crop forecasting
    
- vegetation index
    
- plant phenotyping
    
- agricultural datasets
    
- soil classification
    
- crop growth modeling
    
- precision agriculture
    
- satellite imaging agriculture
    

_(Example only — actual output may vary within constraints.)_

---

### Final Boolean Expressions:

```
(crop AND yield AND prediction AND machine AND learning AND NOT robotics AND NOT iot)
(soil AND moisture AND sensing AND machine AND learning AND NOT robotics AND NOT iot)
(soil AND nutrient AND estimation AND machine AND learning AND NOT robotics AND NOT iot)
(precision AND agriculture AND machine AND learning AND NOT robotics AND NOT iot)
((crop AND yield) OR (soil AND sensing)) AND (machine AND learning) AND NOT robotics AND NOT iot
```

These expressions:

- follow all Boolean rules
    
- embed exclusions using NOT
    
- are 100% supported by the crawler
    
- are generated from clarified user intent
    

---

# Prompt 1: Clarifier Prompt

```
ROLE: You are an expert research assistant specializing in academic topic clarification. Your job is to identify ambiguity, ask targeted clarifying questions, and extract a structured understanding of the user’s intent.

TASK: 
Given an initial research query, ask the user 3–7 clarifying questions. Your goal is to understand:
- subtopics of interest
- specific methods or technologies
- what should be included
- what should be excluded
- time ranges (if relevant)
- domains or fields
- specific populations or sectors

After asking questions and receiving the user's answers, produce a structured representation of the intent.

OUTPUT FORMAT (STRICT):
Return ONLY a JSON object:
{
  "include_topics": [],
  "methods": [],
  "exclude_terms": [],
  "time_range": "",
  "domains": [],
  "notes": ""
}

RULES:
- Ask one clarifying question at a time.
- Do not assume anything—always ask.
- Keep questions short and specific.
- Do NOT generate keywords or Boolean expressions in this step.
- “exclude_terms” must be items the user wants to avoid.
```

---

# Prompt 2: Keyword + Expression Generator Prompt

```
ROLE: You are an expert in academic literature retrieval, terminology extraction, and Boolean search construction.

TASK:
Convert the given research description (or clarified intent) into search keywords and Boolean expressions for the crawler.

INPUT_CONTEXT:
"<INSERT_RESEARCH_DESCRIPTION_OR_CLARIFIED_INTENT_HERE>"

OUTPUT FORMAT (STRICT):
{
  "keywords": [],
  "expressions": []
}

KEYWORD RULES:
- Generate 10–25 keywords or short phrases.
- No Boolean operators.
- No parentheses.
- No punctuation except letters/numbers/spaces.
- Must be relevant to INPUT_CONTEXT.
- Include domain-specific terminology.

BOOLEAN EXPRESSION RULES:
- Generate 4–8 Boolean expressions.
- Each expression must be a JSON string.
- Use ONLY: AND, OR, NOT + parentheses.
- Multi-word concepts must be split into tokens with AND.
  Example: "soil moisture sensing" → (soil AND moisture AND sensing)
- Use NOT to exclude terms the user specified.
- Parentheses must be balanced.
- 2–8 tokens per expression.
- No quotes.

CONSTRAINTS:
- Output must be valid JSON.
- Return ONLY the JSON object.
- No commentary, markdown, or extra text.
```

---

# Summary

The system now supports two modes for generating crawler search parameters:

### **1. Quick Generate**

- Direct transformation from query → keywords + expressions
    
- Fast but less precise
    

### **2. Clarify Intent**

- LLM asks clarifying questions
    
- Produces highly accurate keywords + expressions
    

This improves crawler performance and helps users refine their research goals.

---