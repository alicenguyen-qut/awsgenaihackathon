# 🍳 MealBuddy — Your Daily Buddy for Smarter Eating Habits

> Team Number: <Number>

> Team Members: <Number>

> Built and hosted on AWS with Cloudformation for CI/CD deployment · Powered by Amazon Bedrock, Strands Agent & Kiro

---

## 1. Use Case

### The Problem

Chronic disease driven by poor diet is one of the most preventable crises of our time. According to the World Health Organization, unhealthy diets contribute to **11 million deaths globally each year**, making it the single largest risk factor for disease burden worldwide *(GBD Diet Collaborators, The Lancet, 2019)*. In Australia, **66% of adults are overweight or obese**, with poor nutrition cited as a primary driver *(AIHW, 2024)* - and only **4% of Australian adults** meet the recommended daily vegetable intake *(AIHW, 2024)*. Poor diet costs the Australian healthcare system an estimated **$6 billion per year** in direct costs *(AIHW, Australian Burden of Disease Study, 2022)*.

The intent to eat better is not the problem. Research consistently shows that **most people who begin a healthy eating plan struggle to sustain it long-term** - not from lack of motivation, but from the cognitive and logistical burden of maintaining it *(Teixeira et al., IJBNPA, 2015)*. Meal planning takes 2–3 hours per week. A dietitian costs $100–$400 per session. Calorie tracking apps require manual entry for every meal. The tools are fragmented, generic, and exhausting.

### Who Is This For

- **Busy professionals** who want to eat well but have no time to plan
- **Health-conscious individuals** managing dietary restrictions, allergies, or chronic conditions
- **Fitness enthusiasts** tracking macros without the friction of manual logging
- **Budget-conscious households** reducing food waste through smarter weekly planning

### Value Proposition

MealBuddy brings recipe search, meal planning, shopping lists, and nutrition tracking together in a **single personalised conversation**. Set your dietary preferences once. From that point, every interaction is personalised:

- Ask for a high-protein dinner → get a complete recipe with ingredients and steps
- Say "plan my week" → seven days populate automatically via autonomous agent
- Upload a PDF from your nutritionist → MealBuddy reads and applies it
- Ask what's left in your calorie budget → get a real-time answer

**What previously took 2–3 hours of weekly planning takes under 3 minutes.**

### Why This Is Disruptive

Every existing nutrition app is reactive — you open it, input data, it shows you a number. MealBuddy is the first to combine **conversational AI**, **semantic search over personal documents (RAG)**, and **autonomous multi-step action** in a single solution.

It's the difference between a recipe website that shows you options and a planning tool that already knows your allergies, your goals, and what's in your fridge.

Personalised nutrition guidance has always been expensive and time-consuming. MealBuddy makes it accessible to anyone, at the cost of a conversation.

*Sources: [GBD Diet Collaborators, The Lancet (2019)](https://www.thelancet.com/journals/lancet/article/PIIS0140-6736(19)30041-8/fulltext); [AIHW Overweight and Obesity (2024)](https://www.aihw.gov.au/reports/overweight-obesity/overweight-and-obesity/contents/overweight-and-obesity); [AIHW Food & Nutrition (2024)](https://www.aihw.gov.au/reports/food-nutrition/food-nutrition); [AIHW Australian Burden of Disease Study (2022)](https://www.aihw.gov.au/reports/burden-of-disease/australian-burden-of-disease-study-2022); [Teixeira et al., IJBNPA (2015)](https://ijbnpa.biomedcentral.com/articles/10.1186/1479-5868-12-S1-S4)*

---

## 2. Architecture

### Hackathon Demo Architecture

The architecture was deliberately chosen to validate the full product concept end-to-end within the constraints of a hackathon — fast to deploy, zero infrastructure overhead, and cheap enough to run for days without budget concerns. Every service selected has a direct functional justification, not just cost.


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
 │     ├── Claude 3 Haiku          (Conversational AI + Strands Agent)
 │     └── Titan Embeddings V2     (Semantic recipe & document search)
 │
 └──► Amazon S3
       ├── embeddings/             (Pre-indexed recipe embeddings)
       ├── recipes/                (Recipe raw data)
       ├── sessions/               (User profiles, chat history, meal plans)
       └── uploads/                (User-uploaded documents + embeddings)
```
![Hackathon Architecture](architecture_diagrams/architecture_hackathon.png)

**AWS Services Selected — Cost-Optimised for Hackathon Demo**

| Service | Role | Why chosen |
|---|---|---|
| Elastic Beanstalk (t3.micro) | Web app host | One-command deploy, no VPC/ALB config, free tier eligible |
| Amazon S3 | All data storage | Replaces RDS + vector DB; near-zero cost at demo scale |
| Amazon Bedrock — Claude 3 Haiku | LLM + agent reasoning | Fastest & cheapest Bedrock model; sufficient for conversational tasks |
| Amazon Bedrock — Titan Embeddings V2 | Semantic search | Fully managed, no GPU infra; pay-per-call |
| Strands Agents (open source) | Agentic tool orchestration | No extra AWS service needed; runs in-process on the EC2 |
| NumPy cosine similarity (in-memory) | RAG retrieval | Eliminates need for OpenSearch or Pinecone; embeddings loaded from S3 |
| CloudFormation | IaC / CI-CD | Entire stack (Beanstalk app, S3, IAM) in one template |

**Infrastructure:** All resources deployed via CloudFormation (Elastic Beanstalk app, S3 bucket, IAM role with Bedrock + S3 permissions).

---

### Future Production Architecture

The hackathon stack proves the concept. Scaling to real users requires replacing the cost-optimised shortcuts with managed services built for concurrency, durability, and observability.

![Future Architecture](architecture_diagrams/architecture_future.png)

```
Users
 │
 ▼
Amazon CloudFront  (CDN + WAF)
 │
 ▼
Application Load Balancer
 │
 ▼
AWS Fargate (ECS)           ◄── Auto Scaling
 │
 ├──► Amazon Bedrock
 │     ├── Claude 3 Sonnet / Opus   (upgraded model tier)
 │     └── Titan Embeddings V2
 │
 ├──► Amazon OpenSearch Serverless  (vector store — replaces NumPy)
 │
 ├──► Amazon DynamoDB               (user profiles, sessions, meal plans)
 │
 ├──► Amazon S3                     (uploads, recipe assets)
 │
 ├──► Amazon Cognito                (auth — replaces session UUID)
 │
 └──► Amazon CloudWatch + X-Ray     (observability)
```

**Key upgrades and rationale**

- **Fargate (ECS)** replaces Beanstalk t3.micro — horizontal auto-scaling with no server management; handles concurrent users without cold-start latency
- **OpenSearch Serverless** replaces NumPy in-memory search — persistent, scalable vector index; no full embedding reload on each request
- **DynamoDB** replaces S3 JSON files for sessions — single-digit millisecond reads, TTL for session expiry, no file I/O
- **CloudFront + WAF** — edge caching for static assets, DDoS protection, geo-restriction
- **Cognito** — managed auth with MFA, social login, and JWT; replaces anonymous UUID sessions
- **CloudWatch + X-Ray** — distributed tracing across Bedrock calls, tool invocations, and S3 ops; essential for debugging agentic workflows at scale
- **Claude 3 Sonnet/Opus** — higher reasoning quality for complex multi-day meal planning and document analysis as user base grows

> See [DEVELOPER-GUIDE.md](DEVELOPER-GUIDE.md) for full setup, deployment, and API documentation.

---

## 3. Video Demo

[![MealBuddy Demo](https://img.shields.io/badge/▶_Watch_Demo-3_mins-red?style=for-the-badge&logo=youtube)](https://www.youtube.com/watch?v=PLACEHOLDER)


---

## 4. Live Link

🌐 **[mealbuddy.ap-southeast-2.elasticbeanstalk.com](http://mealbuddy.ap-southeast-2.elasticbeanstalk.com)**

---

📋 [Features](FEATURES.md) · 🛠️ [Developer Guide](DEVELOPER-GUIDE.md)
