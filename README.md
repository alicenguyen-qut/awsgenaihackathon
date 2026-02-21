# 🍳 MealBuddy - Your Daily Buddy for Smarter Eating Habits

> **ANZ Diversity Hackathon 2026 - Team 54 - MealBuddy**

> **Team members:**
- Alice Nguyen – alice.nhnt@gmail.com
- Evelyn Le – evelyn.le.contact@gmail.com

---

## 1. Use Case

### 1.1 The Problem

Chronic disease driven by poor diet is one of the most preventable crises of our time. According to the World Health Organization, unhealthy diets contribute to **11 million deaths globally each year**, making it the single largest risk factor for disease burden worldwide *(GBD Diet Collaborators, The Lancet, 2019)*. In Australia, **66% of adults are overweight or obese**, with poor nutrition cited as a primary driver *(AIHW, 2024)* - and only **4% of Australian adults** meet the recommended daily vegetable intake *(AIHW, 2024)*. Poor diet costs the Australian healthcare system an estimated **$6 billion per year** in direct costs *(AIHW, Australian Burden of Disease Study, 2022)*.

The intent to eat better is not the problem. Research consistently shows that **most people who begin a healthy eating plan struggle to sustain it long-term** - not from lack of motivation, but from the cognitive and logistical burden of maintaining it *(Teixeira et al., IJBNPA, 2015)*. Meal planning takes 2–3 hours per week. A dietitian costs ~200 AUD for a session  *(Vively, 2024)*. Calorie tracking apps require manual entry for every meal. The tools are fragmented, generic, and exhausting.

### 1.2 MealBuddy - The Solution, Vision and Value Proposition

MealBuddy's vision is to address the gap of **fragmented, generic, and inaccessible nutrition tools** - delivering **personalised, proactive nutrition support** by combining recipe search, meal planning, shopping lists, and nutrition tracking in a **single AI-powered conversation**.

| Value Proposition | How MealBuddy Helps |
|---|---|
| **Time savings** | Reduces 2–3 hours of weekly meal planning to under 10 minutes |
| **Personalisation** | Personalises based on users' dietary preferences, goals, and restrictions across every user interaction |
| **Accessibility and cost-saving** | Available 24/7 at affordable cost |
| **Proactive planning** | Autonomously generates a full week of meals - no manual input required |
| **Document intelligence** | Reads and applies user-upload data directly into the meal plan |
| **Real-time tracking** | Instant answers on remaining calorie budget, without manual logging |


### 1.3 Targeted Users

- **Busy professionals** who want to eat well but have no time to plan
- **Health-conscious individuals** managing dietary restrictions, allergies, or chronic conditions
- **Fitness enthusiasts** tracking macros without the friction of manual logging
- **Budget-conscious households** reducing food waste through smarter weekly planning

### 1.4 Market Analysis (Australia)

The scale of the problem translates directly into market opportunity:

- With **66% of Australian adults overweight or obese** and diet-related disease costing **$6 billion/year**, there is clear government and consumer urgency to act *(AIHW, 2022)*
- Personalised nutrition support is inaccessible to most - a dietitian costs ~**AUD 200/session** and wait times are long *(Vively, 2024)* - creating a large underserved population willing to pay for a cheaper, always-available alternative


**Bottom-up market sizing (Australia):**
- Australia has ~20.5 million adults. At 66% overweight or obese, that's ~**13.5 million adults** with a direct health incentive to improve their diet *(AIHW, 2024)* - this is the TAM
- Of these, the digitally active cohort aged 25–54 (the primary health-app demographic) represents roughly **~8 million Australians** *(ABS, 2021 Census)* - this is the SAM
- Capturing just **1–2% of SAM** in year 3 = **80,000–160,000 users** at AUD 10–15/month = **AUD 10–29M ARR**

### 1.5 Competitive & Partnership Landscape

**Competitors:**

| Competitor | What They Do | Key Gap MealBuddy Fills |
|---|---|---|
| **MyFitnessPal** | Calorie & macro tracking via manual food logging | Reactive, no planning, no personalisation, no conversation |
| **Cronometer** | Detailed micronutrient tracking | Complex UI, no conversational AI, no autonomous meal planning |
| **ChatGPT / general LLMs** | Ad-hoc nutrition Q&A | No persistent profile, no meal plan memory, no document RAG, no structured tracking |

**MealBuddy's competitive moat:** Few existing solutions combine a persistent user profile, conversational AI, document ingestion (RAG), and autonomous multi-step action in a single nutrition product. Every existing app is reactive - open it, input data, it shows a number. MealBuddy is designed to *plan with users*, not just *record after them* - making personalised nutrition support accessible to anyone, at the cost of a conversation.

**Potential business partnership opportunities:** Meal kit services like HelloFresh and Marley Spoon are a natural integration opportunity - MealBuddy could recommend their kits when users want a no-prep option, or auto-populate a shopping list that links to their catalogue. Partnerships with grocery retailers (e.g. Woolworths, Coles) could take this further - enabling users to purchase ingredients directly from within the app, turning a meal plan into a completed grocery order in one step.

*Sources: [AIHW Overweight and Obesity (2024)](https://www.aihw.gov.au/reports/overweight-obesity/overweight-and-obesity/contents/overweight-and-obesity); [AIHW Food & Nutrition (2024)](https://www.aihw.gov.au/reports/food-nutrition/nutrition); [Vively, How Much Does It Cost to See a Dietitian in Australia (2024)](https://www.vively.com.au/post/how-much-does-it-cost-to-see-a-dietitian-in-australia); [AIHW Australian Burden of Disease Study (2022)](https://www.aihw.gov.au/reports/burden-of-disease/australian-burden-of-disease-study-2022); [GBD Diet Collaborators, The Lancet (2019)](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(19)30041-8/fulltext); [Teixeira et al., IJBNPA (2015)](https://ijbnpa.biomedcentral.com/articles/10.1186/1479-5868-12-S1-S4)*

---

## 2. Architecture Diagrams

### 2.1 Hackathon Demo Architecture

The below architecture was chosen to validate the full product concept end-to-end within the constraints of a hackathon - fast to deploy, zero infrastructure overhead, and cheap enough to run without budget concerns. 

```
User
 │
 ▼
Flask UI (HTML/CSS/JS)
 │
 ▼
AWS Elastic Beanstalk  (t3.micro EC2)
 │
 ├──► Amazon Bedrock
 │     ├── Claude 3 Haiku          (Conversational AI + Strands Multi-Agent)
 │     └── Titan Embeddings V2     (Semantic recipe & document search)
 │
 └──► Amazon S3
       ├── embeddings/             (Pre-indexed recipe embeddings)
       ├── recipes/                (Recipe raw data)
       ├── sessions/               (User profiles, chat history, meal plans)
       └── uploads/                (User-uploaded documents + embeddings)
```

**Multi-Agent Architecture (Strands)**

```
User Message
     │
     ▼
Coordinator Agent
     │
     ├──► 🥗 Planner Agent      → meal planning, shopping list, favourites
     ├──► 📊 Nutrition Agent    → calorie tracking, macro stats, snack suggestions
     └──► 📄 Document Agent     → RAG over uploaded PDFs, dietary restrictions
```
**Hackathon Architecture Diagram**

<img src="architecture_diagrams/architecture_hackathon.png" width="800">


**AWS Services Selected with a focus on demonstrating PoC and being cost-optimised for Hackathon Demo**

| Service | What it is used for | Why chosen |
|---|---|---|
| Elastic Beanstalk (t3.micro) | Web app hosting | Rapidly deploys and manages application without much infrastructure provisioning  |
| Amazon S3 | Data storage | Data storage in cloud at near-zero cost at demo scale |
| Amazon Bedrock - Claude 3 Haiku | LLM + multi-agent reasoning | Fast and cost-saving Bedrock model powering 3 specialist Strands agents |
| Amazon Bedrock - Titan Embeddings V2 | Semantic search | Fully managed, no GPU infra, optimises for cost and retrieval performance without sacrificing accuracy |
| Strands Agents (open source) | Multi-agent orchestration | Coordinator routes to specialist agents (Planner, Nutrition, Document) for focused, reliable responses |
| NumPy cosine similarity | RAG retrieval | Embedding search - quick, easy and no-cost to implement |
| CloudFormation | IaC / CI-CD | Deploys entire stack (Beanstalk app, S3, IAM) in one template - reusable and faster deployment compared to ClicksOp |

---

### 2.2 Future Enhancement Architecture

The hackathon stack proves the concept. The below future architecture introduces infrastructure-as-code, containerised scaling, secure identity boundaries, vector persistence, and full-stack observability to support real-world concurrency, durability, scalability, and intelligent agent workflows.

```
Users (Web Browser)
 │
 ▼
Amazon CloudFront  (Edge CDN + WAF + DDoS Protection)
 │
 ▼
Application Load Balancer
 │
 ▼
AWS ECS Fargate (Containerised Compute, Auto Scaling)
 │
 ├──► AWS Bedrock AgentCore
 │      ├── Identity
 │      ├── Tools
 │      ├── Memory
 │      ├── Runtime
 │      └── GenAI Observability (OpenTelemetry of LLM traces and monitoring)
 │
 ├──► Amazon Bedrock
 │      ├── Claude Sonnet / Opus (Reasoning LLMs)
 │      └── Titan Embeddings V2 (Embedding)
 │
 ├──► Amazon OpenSearch Serverless  (Vector Knowledge Base)
 │
 ├──► Amazon DynamoDB  (User metadata, sessions)
 │
 ├──► Amazon S3  (Object storage & artifacts)
 │
 ├──► Redis Cache  (RAG + LLM response caching)
 │
 └──► Amazon CloudWatch (Logging + Monitoring)

Infrastructure:
 ├── AWS CloudFormation (IaC deployment)
 ├── Amazon ECR (Container registry)
 └── IAM Roles (Least-privilege access control)
```
**Future Architecture Diagram**

<img src="architecture_diagrams/architecture_future.png" width="800">


| Layer | Service | What it is used for | Why chosen |
|---|---|---|---|
| **Compute & Infrastructure** | ECS Fargate | Containerised compute | Horizontally auto-scaled, no server management, high concurrency |
| | CloudFormation (IaC) | CI/CD deployment | Reusable, automated stack deployment |
| | Amazon ECR + IAM Roles | Container registry + access control | Least-privilege access |
| **Intelligent Agent** | AWS Bedrock AgentCore | Agent orchestration | Identity boundaries, tool control, memory persistence, GenAI observability |
| | Claude Sonnet / Opus | LLM reasoning | Complex multi-step planning, structured outputs, advanced document analysis |
| | Titan Embeddings V2 | Semantic search & embeddings | Production-grade RAG, knowledge base ingestion |
| **Databases & Storage** | OpenSearch Serverless | Vector knowledge base | Persistent, scalable vector index for production RAG |
| | DynamoDB | User metadata & sessions | Single-digit ms reads, TTL-based expiry |
| | Amazon S3 | Object storage | Durable storage for uploads, assets, static content |
| | Redis Cache | Response & RAG caching | Reduces Bedrock latency and cost under load |
| **Edge, Security & Observability** | CloudFront + WAF | CDN + security | DDoS protection, rate limiting, geo-restriction |
| | CloudWatch | Logging + Monitoring | Logging and monitoring across deployed AWS services |

---

## 3. Video Demo

[![MealBuddy Demo](https://img.shields.io/badge/▶_Watch_Demo-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/watch?v=PLACEHOLDER)


---

## 4. Live Link

🌐 **[mealbuddy.ap-southeast-2.elasticbeanstalk.com](http://mealbuddy.ap-southeast-2.elasticbeanstalk.com)**

---

## 5. Other Documentatuion

📋 [Webapp Features](FEATURES.md) 

🛠️ [Developer Guide](DEVELOPER-GUIDE.md)


*Built by MealBuddy team and hosted on AWS with Cloudformation for CI/CD deployment · Powered by Amazon Bedrock, Strands Multi-Agent & Kiro*