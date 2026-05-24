# BCT Hack Brief — Structured Notes

Source: [BCT Hack Brief.pdf](BCT%20Hack%20Brief.pdf)

## Competition Structure

**Two Task. One Ambition.**

### Task A — User Modeling

Build an agent that understands users deeply enough to simulate their reviews, including tone, rating behavior, and contextual nuance.

Requirements:

- Simulate star ratings and written reviews for unseen items
- Leverage user history, item metadata, and contextual signals
- Evaluate on review quality, rating accuracy, and behavioural fidelity

### Task B — Recommendation

Build an agent that delivers personalized recommendations beyond collaborative filtering, using contextual and conversational retrieval.

Requirements:

- Rank and recommend items tailored to individual user context
- Handle cold-start, cross-domain, and multiturn scenarios
- Design agentic workflows that reason before recommending

## Submission Requirements

Each task must be submitted as a **containerized application** with either a web application or an API endpoint.

### Task 1 Submission

- Input: user persona + product details
- Output: reviews and ratings
- Acceptable form: API endpoint or web app inside a container

### Task 2 Submission

- Input: user persona
- Output: personalized recommendations
- Acceptable form: API endpoint or web app inside a container

Examples of product domains mentioned in the brief:

- Movies
- Food
- Drinks

## Deliverables

### 1. Containerized Application

- Task A and Task B must be runnable in a containerized form
- Judges will attempt to run the submission
- Endpoint or web app is acceptable

### 2. Solution Paper (4–8 pages)

Include:

- Approach
- Architecture decisions
- Experiments run
- Ablation studies
- What could be done with more time

This is the primary talent signal and is read first.

### 3. Code Repository

A clean, documented, reproducible repository submitted via GitHub or equivalent.

Judges reward:

- Clear README
- Modular design
- Well-commented agentic workflow logic

## Scoring Summary

### Task A

- Review Text Quality (ROUGE / BERTScore)
- Rating Accuracy (RMSE)
- Behavioural Fidelity (human evaluation)
- Solution Paper
- Code Reproducibility

### Task B

- Ranking Quality (NDCG@10 / Hit Rate) — 30 pts
- Cold-Start & Cross-Domain — 25 pts
- Contextual Relevance (human eval) — 20 pts
- Solution Paper — 15 pts
- Code Reproducibility — 10 pts

Additional marks are available for systems that are contextualized to behave and sound like Nigerians.

## Timeline

- **4 May 2026** — Hackathon launch
- **24 May 2026** — Submission deadline, all three deliverables due before midnight
- **25–29 May 2026** — Judging panel review
- **29 May–1 June 2026** — Top 4 teams notified
- **1–8 June 2026** — Presentation deck submission
- **10 June 2026** — Winner announcement and prize ceremony

## Prizes

- 1st: ₦1,500,000
- 2nd: ₦1,000,000
- 3rd: ₦750,000
- 4th: ₦200,000
- 5th–9th: ₦100,000
- 10th: ₦50,000

## Eligibility

Eligible:

- Undergraduate students
- Postgraduate students
- PhD students
- Teams of 1–4 members, all must be eligible students

Not eligible:

- Sharing solutions or code across competing teams
- Teams submitting only one task

Allowed with disclosure:

- Public pre-trained models and open-source frameworks
- Additional datasets

## Implications for ARCHE

ARCHE should present itself as:

- A containerized API and/or webapp
- A two-task system with shared agentic reasoning
- A solution that supports both review simulation and recommendation
- A system with explainability and cold-start handling

## ARCHE Application Alignment

The implementation already matches the brief in the following way:

### Task A — User Modeling

- **Brief input:** user persona + product details
- **ARCHE input:** `user_persona` or `user_token` + `user_history` + `item`
- **ARCHE endpoint:** `POST /v1/simulate-review`
- **ARCHE output:** predicted rating, generated review, confidence, reasoning

How the mapping works:

- User persona is represented by the user token plus historical behavior and contextual signals
- Product details are represented by the unseen item payload (`name`, `category`, `price_tier`, attributes)
- The review generation layer uses the shared simulation engine so the review is grounded in behavior instead of generic text

### Task B — Recommendation

- **Brief input:** user persona
- **ARCHE input:** `user_persona` or `user_token` plus optional context
- **ARCHE endpoint:** `POST /v1/recommend`
- **ARCHE output:** ranked recommendations with confidence, reasoning, and recommendation type

How the mapping works:

- The orchestrator reasons over user history, context, and memory before ranking
- The recommendation flow already handles cold-start, cross-domain style blending, and multi-step explanation
- The webapp uses this endpoint for the interactive demo and the `explain` endpoint for deeper reasoning traces

### Why this aligns with the brief

- Both required tasks are implemented
- Both tasks are available as container-ready API endpoints
- The system is explainable and judge-friendly
- The same shared brain powers Task A and Task B, which is exactly the agentic workflow the brief asks for

### Recommended endpoint framing

- `POST /v1/simulate-review` for Task A
- `POST /v1/recommend` for Task B
- `POST /v1/explain` for traceability

### Recommended webapp framing

- Webapp showcases the same endpoints through an interactive demo
- Recommendation cards can call the explanation endpoint
- The UI should make the agentic reasoning visible to judges
