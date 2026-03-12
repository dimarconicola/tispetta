# Benefits Opportunity Engine

## README

### What this is
A product and technical plan for a focused platform that discovers, structures, matches, and explains benefits, incentives, grants, tax advantages, and similar opportunities for a specific user or business profile.

The system is not designed as a general legal AI. It is designed as an **opportunity intelligence engine**.

Its core function is simple:
- ingest official and trusted sources
- convert unstructured opportunity information into structured records
- map those records to a profile through deterministic rules
- explain relevance clearly
- notify users when new or changed opportunities may apply

This plan is intentionally constrained. It avoids unnecessary complexity, full legal-reasoning ambitions, and premature AI-heavy architecture.

### Product thesis
Most people and organizations miss benefits and incentives not because the opportunities do not exist, but because discovery is fragmented, eligibility is unclear, and the effort to interpret sources is too high.

The product solves this by turning fragmented public information into a continuously updated, profile-aware opportunity system.

### What the product is not
- not a general legal assistant
- not a universal law search engine
- not a fully autonomous legal advisor
- not a replacement for professionals in ambiguous or high-risk cases
- not a fully agentic black box that makes opaque eligibility decisions

### Product wedge
Start narrow.

Recommended first wedge:
**Italy, startup / freelance / SME incentives and benefits**

Why:
- high user motivation
- direct economic value
- relatively bounded source universe
- good fit for structured opportunity modeling
- lower ambiguity than broad rights-based legal domains

### Product principle
The system should model **opportunities as structured objects**, not law as a giant corpus.

That means the system should reason primarily over:
- who an opportunity is for
- where it applies
- when it applies
- what it is worth
- which conditions matter
- which evidence supports it
- what is still missing to confirm applicability

### Core design principle
Use AI where language is messy.
Use deterministic systems where truth matters.

That means:
- AI for extraction, summarization, query understanding, explanation, anomaly detection
- deterministic rules for eligibility and matching
- versioned source snapshots for auditability
- human review only on exceptions, new rule creation, and critical ambiguities

### Strategic goal
Build a system with very low operational overhead and minimal human-in-the-loop, while preserving relevance, trust, and cost discipline.

---

# 1. High-level product description

## 1.1 Problem
Users miss real economic opportunities because:
- sources are fragmented across many websites and documents
- eligibility language is hard to interpret
- the same opportunity is described differently across pages, FAQs, PDFs, and portals
- users do not know what information matters for matching
- existing search is source-first, not profile-first
- many opportunities are time-sensitive and easy to miss

## 1.2 Solution
A profile-aware opportunity engine that:
- collects opportunities from official and trusted sources
- normalizes and structures them into a canonical data model
- matches them to user profiles through deterministic rules
- explains why something may apply and what information is missing
- alerts users when relevant opportunities appear or change

## 1.3 Target users
### Primary
- freelancers in Italy
- founders and startup operators in Italy
- small business owners and SMEs

### Secondary
- consultants and advisors
- associations or chambers of commerce
- incubators and accelerators
- financial platforms or HR/payroll platforms

## 1.4 User value
For an end user:
- fewer missed opportunities
- less time spent searching and interpreting
- clearer understanding of what applies and why
- deadlines and next steps surfaced proactively

For a B2B partner:
- structured opportunity discovery for their users
- embedded eligibility and alerts
- higher retention and engagement through utility

---

# 2. Product goals and non-goals

## 2.1 Goals
- deliver a high-confidence stream of relevant opportunities
- keep cost per active user low
- minimize manual review through exception-based workflows
- provide clear, explainable relevance and eligibility status
- support a small, focused source set before expanding
- build an internal data and rules foundation that can scale to additional verticals

## 2.2 Non-goals for MVP
- full coverage of all benefits and rights in Italy
- broad legal chat assistant
- automatic application submission
- deep personalization using third-party financial/accounting integrations from day one
- mobile-native app at launch
- fully autonomous legal reasoning

---

# 3. Product requirements document

## 3.1 User stories

### Discovery and onboarding
- As a new user, I want to describe my profile so the system can identify relevant opportunities.
- As a user, I want the onboarding to adapt to my type so I do not answer unnecessary questions.
- As a user, I want to save my profile and return later without re-entering core information.

### Opportunity matching
- As a user, I want to see opportunities likely relevant to me.
- As a user, I want to understand whether an opportunity is confirmed, likely, uncertain, or not relevant.
- As a user, I want to see what information is missing to assess a benefit more accurately.

### Explanation
- As a user, I want each opportunity page to explain why it may apply.
- As a user, I want to see the original sources and date of last verification.
- As a user, I want concise summaries rather than raw legal or bureaucratic text.

### Alerts
- As a user, I want notifications when a new opportunity relevant to me appears.
- As a user, I want notifications when a deadline is approaching.
- As a user, I want notifications when a previously matched opportunity changes status.

### Search and exploration
- As a user, I want to browse opportunities by category, geography, and audience.
- As a user, I want to ask simple natural-language questions and get grounded answers.

### Internal operations
- As an operator, I want the system to automatically ingest and update source content.
- As an operator, I want low-confidence records to be routed for review.
- As an operator, I want a history of source changes and rule changes.
- As an operator, I want every user-facing claim traceable to structured evidence.

## 3.2 MVP features

### User-facing
- adaptive onboarding questionnaire
- persistent user profile
- homepage with matched opportunities
- detail page for each opportunity
- status labels: confirmed / likely / unclear / not eligible
- missing-information prompts
- email notifications
- basic saved opportunities list
- basic search and filters

### Admin-facing
- source registry
- ingestion job dashboard
- opportunity review queue
- diff view for changed sources
- rule versioning and test results
- publish / unpublish controls

### System-facing
- scheduled source ingestion
- source snapshot storage
- canonical opportunity extraction
- deterministic matching engine
- confidence scoring
- explanation generation grounded on evidence

## 3.3 Out of scope for MVP
- in-app claim submission
- direct filing or document automation
- mobile app
- multi-country support
- advanced advisor workflow
- third-party integrations beyond email and basic analytics

---

# 4. Product experience

## 4.1 Onboarding flow
The onboarding should not be a giant static questionnaire. It should be progressive and adaptive.

### Step 1: user type
- freelancer
- company founder / startup
- SME owner
- advisor

### Step 2: core profile
Examples:
- age range
- region
- city or province
- employment or company status
- company size
- sector / ATECO if relevant
- revenue band
- incorporation status
- startup age
- hiring plans
- ownership / gender / youth / innovation criteria where relevant

### Step 3: optional enrichment
- goals: hiring, digitization, export, R&D, training, sustainability, new business, etc.
- funding stage
- legal structure
- existing grants received

### Step 4: first results
Immediately show:
- likely relevant opportunities
- missing info to refine matching
- estimated value or category of value where available
- deadlines

## 4.2 Homepage
The homepage should answer only these questions:
- what could be relevant to me now
- what changed recently
- what is urgent
- what information should I add to improve results

Sections:
- top opportunities for you
- expiring soon
- newly discovered for your profile
- refine your profile
- saved opportunities

## 4.3 Opportunity detail page
Required fields:
- title
- brief summary
- eligibility status
- why this matches
- what is missing
- value / incentive type
- geography
- deadline
- source authority
- last checked date
- next steps
- official links and evidence snippets

## 4.4 Notifications
Start with email only.

Trigger types:
- new relevant opportunity
- deadline approaching
- source changed for a saved/matched opportunity
- profile completion prompt when that materially improves matching

---

# 5. Core product logic

## 5.1 Opportunity object
Every opportunity should be represented as a canonical structured object.

Suggested schema:
- opportunity_id
- title
- normalized_title
- short_description
- long_description
- opportunity_type
- category
- subcategory
- issuer_name
- issuer_type
- country
- region
- geography_scope
- target_entities
- target_sectors
- company_stage
- company_size_constraints
- demographic_constraints
- legal_constraints
- eligibility_inputs_required
- exclusions
- benefit_type
- benefit_value_type
- estimated_value_min
- estimated_value_max
- funding_rate
- deadline_type
- deadline_date
- application_window_start
- application_window_end
- application_mode
- required_documents
- official_links
- source_documents
- evidence_snippets
- version_number
- record_status
- extraction_confidence
- verification_status
- last_checked_at
- changed_at

## 5.2 Profile object
Suggested fields for MVP:
- user_id
- user_type
- country
- region
- age_range
- business_exists
- legal_entity_type
- company_age_band
- company_size_band
- revenue_band
- sector_code_or_category
- founder_attributes where relevant and consented
- hiring_intent
- innovation_intent
- sustainability_intent
- export_intent
- profile_completeness_score
- updated_at

## 5.3 Match result object
Each match should store:
- match_id
- user_id
- opportunity_id
- match_status
- match_score
- rule_evaluation_trace
- missing_fields
- explanation_summary
- user_visible_reasoning
- last_evaluated_at

## 5.4 Eligibility statuses
Keep these simple.
- confirmed: enough structured data satisfies the rules
- likely: most conditions satisfied, some ambiguity remains
- unclear: insufficient profile or source clarity
- not eligible: one or more hard disqualifiers triggered

---

# 6. Technical architecture

## 6.1 Design principle
Do not make the LLM the system of record.

The system of record should be:
- structured source snapshots
- canonical opportunity records
- deterministic rules
- versioned match results

## 6.2 High-level architecture

### A. Source registry
A small curated list of allowed sources.

Fields:
- source_id
- source_name
- source_type
- authority_level
- crawl_method
- crawl_frequency
- trust_level
- region
- status

### B. Ingestion layer
Purpose:
- fetch pages and documents
- store snapshots
- detect changes
- send content for normalization

Functions:
- scheduled crawl
- retry handling
- failure logging
- checksum and diff tracking

### C. Normalization layer
Purpose:
- convert raw HTML/PDF into normalized content
- extract metadata
- classify page/document type

Outputs:
- clean text
- metadata
- candidate document type
- structural sections

### D. Opportunity extraction layer
Purpose:
- convert normalized content into candidate structured opportunity objects

Outputs:
- structured record candidate
- field-level confidence
- evidence snippets
- unresolved ambiguities

### E. Rules engine
Purpose:
- evaluate profile against structured opportunity rules
- return eligibility state and trace

Properties:
- deterministic
- versioned
- testable
- explainable

### F. Matching engine
Purpose:
- select candidate opportunities for a profile
- run rules only on relevant subsets

### G. Explanation layer
Purpose:
- generate concise, grounded user-facing explanations

### H. Notification layer
Purpose:
- send event-triggered alerts via email

### I. Admin console
Purpose:
- review exceptions
- inspect source changes
- publish/unpublish records
- manage rules and tests

---

# 7. AI and automation strategy

## 7.1 Principle
Use AI as an efficiency layer, not as the final authority.

## 7.2 Where AI is appropriate
- document classification
- field extraction from messy text
- source change summarization
- query interpretation
- concise explanation generation
- anomaly detection in source changes
- draft rule suggestions for operator review

## 7.3 Where AI should not be the final authority
- final eligibility truth
- canonical rule publication without checks
- hard yes/no answers where source ambiguity exists
- unsupported legal interpretation

## 7.4 Minimal-human operating model
The correct goal is not zero humans. It is **human-on-exception**.

That means the system should auto-process most routine tasks and escalate only when needed.

Escalation conditions:
- low extraction confidence
- source conflict
- new opportunity type
- unresolved field ambiguity
- rule conflict or missing rule coverage
- high-value or high-risk opportunity
- user dispute or flagged error

## 7.5 Agent model
Use specialized workers, not one general black-box agent.

Suggested workers:
- source monitor
- fetcher
- normalizer
- extractor
- verifier
- rule-draft assistant
- matcher
- explainer
- QA sentinel

---

# 8. Cost-conscious architecture

## 8.1 Cost minimization principles
- use deterministic filters before any model inference
- use a constrained source set
- use structured schemas everywhere
- run expensive models only on shortlisted candidates
- do not embed or vectorize everything by default
- store reusable intermediate outputs
- re-evaluate matches only when profile or source changes

## 8.2 Suggested cost stack

### Default path
- source fetch
- parse
- classify
- structured extraction
- deterministic rule evaluation
- user-facing explanation

### Cheap by default
- metadata filters
- PostgreSQL full-text search
- rule evaluation
- template-based summaries where possible

### Optional later
- vector search for harder discovery queries
- reranker on top-k candidates
- specialized legal embedding models only if offline evaluation proves value

## 8.3 LLM usage policy
Only use LLM calls for:
- messy extraction where deterministic parsing fails
- document type classification in ambiguous cases
- explanation generation grounded on structured fields
- user query normalization or routing

Do not use LLM calls for:
- every search request by default
- final eligibility truth
- large-scale blind corpus processing when simpler methods suffice

---

# 9. Data and rules design

## 9.1 Taxonomy
Keep the taxonomy small and useful.

Top-level categories for MVP:
- grants and non-repayable funding
- subsidized loans
- tax incentives
- hiring incentives
- training and skills incentives
- digitization incentives
- sustainability / energy incentives
- export / internationalization incentives

Cross-cutting dimensions:
- geography
- audience type
- company size
- sector
- lifecycle stage
- time sensitivity

## 9.2 Rule design
Rules should be explicit and versioned.

A rule should answer:
- which profile fields matter
- which are required
- which are disqualifiers
- which are unknown but tolerable

Example rule shape:
- required conditions
- disqualifiers
- optional boosters
- missing-data conditions
- evidence references

## 9.3 Testing
Every opportunity with rules should have:
- at least one positive test case
- at least one negative test case
- at least one incomplete-profile test case

This is mandatory.

---

# 10. Source strategy

## 10.1 Start with a trusted source set
Do not scrape everything.

Start with:
- national government portals
- Invitalia
- EU funding sources relevant to SMEs/startups
- selected regional portals
- selected chamber of commerce sources

## 10.2 Source tiers
### Tier 1
Official public sources. These are the highest-trust sources.

### Tier 2
Semi-official or institutional intermediaries. Useful but not primary truth.

### Tier 3
Editorial or advisory sources. Use for discovery support only, not as the final truth source.

## 10.3 Refresh logic
Different source types should refresh differently:
- deadlines and active calls: high frequency
- evergreen incentive pages: medium frequency
- policy pages and guides: lower frequency

---

# 11. Security, trust, and compliance

## 11.1 Trust requirements
Every user-facing claim should be traceable to:
- source URL or document
- snapshot version
- extraction timestamp
- rule version

## 11.2 User messaging discipline
Never overclaim.

Use controlled language:
- may apply to you
- likely relevant
- missing information needed
- appears not applicable based on current profile

Avoid authoritative statements when confidence is limited.

## 11.3 Privacy
Minimize stored user data.
Only ask for data that improves matching.
Track consent where sensitive or special categories might arise.

## 11.4 Auditability
Store:
- source snapshots
- extraction versions
- rule versions
- match traces
- notification history

---

# 12. Recommended stack

## 12.1 Backend
- Python
- FastAPI
- PostgreSQL
- Redis
- background worker system such as Celery or Dramatiq
- object storage compatible with S3 for snapshots

## 12.2 Search
For MVP:
- PostgreSQL full-text search

Later if needed:
- OpenSearch or Elasticsearch
- pgvector for selective semantic retrieval

## 12.3 Frontend
- Next.js web app
- server-rendered pages where useful for speed and simplicity
- component system kept lean

## 12.4 Ingestion
- Playwright for complex sites
- standard HTTP and HTML parsing for simpler sites
- PDF parsing pipeline
- diffing and checksum utilities

## 12.5 AI integration
- provider-agnostic LLM wrapper
- task-specific prompts with strict JSON outputs
- confidence scoring and fallback logic
- offline evaluation harness for extraction quality

---

# 13. Phased roadmap

## Phase 1: foundation
Duration: 2 to 4 weeks

Deliverables:
- source registry
- opportunity schema
- profile schema
- rule format
- first admin workflows
- first 25 to 50 manually curated opportunity records

## Phase 2: ingestion and matching MVP
Duration: 4 to 6 weeks

Deliverables:
- source ingestion jobs
- snapshot storage
- normalization pipeline
- extraction pipeline
- deterministic rules engine
- basic user onboarding
- homepage and opportunity detail page
- email notifications

## Phase 3: exception-based operations
Duration: 2 to 4 weeks

Deliverables:
- confidence scoring
- review queues
- diff console
- rule testing UI or internal workflow
- better explanation generation

## Phase 4: optimization
Duration: 3 to 6 weeks

Deliverables:
- source change summaries
- improved matching prioritization
- better profile refinement prompts
- search improvements
- analytics for conversion and precision

## Phase 5: selective intelligence expansion
Deliverables:
- optional vector search
- optional reranking
- optional advisor workflow
- selective integrations with external systems

---

# 14. Success metrics

## User value metrics
- percentage of users receiving at least one relevant opportunity
- number of saved or acted-on opportunities
- profile completion rate
- notification open and return rate
- user-reported relevance

## System quality metrics
- extraction accuracy by field
- rule pass/fail correctness on test cases
- precision of top matched opportunities
- percent of opportunities requiring manual intervention
- source freshness lag

## Cost metrics
- AI cost per active user
- ingestion cost per source
- review time per escalated record
- percentage of fully automated publish flows

---

# 15. MVP release definition

The MVP is complete when all of the following are true:
- users can create a profile and receive relevant opportunity matches
- opportunities are sourced from a controlled list of trusted sources
- every displayed opportunity is represented as a structured object
- eligibility status is derived from deterministic rules, not raw chat inference
- email notifications work for new opportunities and deadlines
- low-confidence or ambiguous cases are held for review rather than auto-published
- operators can inspect source diffs and rule history

---

# 16. Recommended team shape

Minimal practical setup:
- 1 product / founder lead
- 1 full-stack engineer
- 1 backend / data engineer
- 1 part-time domain/review operator

A single strong engineer could build an early version, but quality will improve materially with dedicated backend/data ownership.

---

# 17. Risks and mitigations

## Risk: scope explosion
Mitigation:
- choose one vertical and one country
- keep taxonomy bounded
- reject broad legal use cases early

## Risk: low trust due to wrong matches
Mitigation:
- deterministic rules
- controlled language
- confidence gating
- evidence display

## Risk: source instability
Mitigation:
- snapshot everything
- maintain source registry
- use robust retry and diff logic

## Risk: hidden operational burden
Mitigation:
- review by exception only
- strict schemas
- field-level confidence
- limited source set first

## Risk: AI cost creep
Mitigation:
- deterministic-first architecture
- cached intermediate outputs
- small-model or no-model default path
- expensive inference only for hard cases

---

# 18. Build recommendation

Build this as a narrow, structured, explainable opportunity engine.

Do not build a general legal AI.
Do not make chat the core product.
Do not rely on agent autonomy for final eligibility truth.

The strongest first version is:
- web-first
- Italy-only
- startup/freelance/SME wedge
- trusted-source ingestion
- structured opportunity catalog
- deterministic matching
- explanation and notifications
- exception-based human oversight

That version is buildable, sustainable, and extensible.

---

# 19. Short implementation brief

If this were turned into an immediate execution brief, the first sequence would be:

1. define vertical and trusted sources
2. finalize opportunity schema and taxonomy
3. define profile schema and onboarding fields
4. implement source registry and snapshot ingestion
5. create first curated opportunity dataset
6. implement rules engine and test cases
7. build user onboarding and homepage
8. build opportunity detail page and explanation layer
9. launch email alerts
10. add review-by-exception admin tooling

---

# 20. Final product statement

This product should behave like a continuously updating layer of opportunity intelligence between fragmented public information and the real profile of a user or business.

Its value comes from structure, matching, clarity, and timing.

Not from pretending to understand all law.

