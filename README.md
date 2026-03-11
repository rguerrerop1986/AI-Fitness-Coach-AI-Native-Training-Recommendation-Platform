# AI Fitness Coach – AI-Native Training Recommendation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![AI / LLM](https://img.shields.io/badge/AI-LLM%20System-green.svg)]()
[![Status](https://img.shields.io/badge/status-active-success.svg)]()

---

AI-powered coaching platform that generates **adaptive workout and nutrition recommendations** using Large Language Models (LLMs), contextual user data, and historical training signals.

The system combines **LLM reasoning**, **contextual prompts**, a **memory layer**, a **recommendation engine**, **retrieval-based training knowledge**, and an **evaluation layer** to generate personalized daily training and nutrition plans.

This project demonstrates how modern AI systems can integrate **data pipelines, LLM reasoning, and intelligent orchestration** to build adaptive fitness applications.

---

## Project Overview

Traditional fitness programs rely on static training plans. The AI Fitness Coach replaces this approach with a **dynamic AI-driven recommendation engine**.

The system evaluates multiple user signals each day, including:

- Sleep quality
- Adherence to diet
- Motivation levels
- Historical workouts
- Body metrics
- Recovery indicators

Using this contextual information, the platform generates **personalized daily workout recommendations** through LLM reasoning.

The result is a coaching system capable of adapting training intensity, recovery strategies, and workout selection dynamically.

---

## AI System Architecture

The platform is designed as an **AI-native system** combining contextual state, memory, retrieval, and LLM reasoning.

```
User Check-in
       ↓
Context Builder
       ↓
User State Engine
       ↓
Memory Layer
       ↓
Training Knowledge Base (RAG)
       ↓
Coach Agent
       ↓
Prompt Engine
       ↓
LLM Reasoning Layer
       ↓
Evaluation Layer
       ↓
Persisted Training Plan
```

Architecture diagram:

![AI Architecture](docs/ai-architecture.png)

---

## Core System Components

### Context Builder

Aggregates all contextual information used by the AI system.

Inputs include:

- User profile
- Body measurements
- Training history
- Daily check-in signals
- Previous recommendations

The Context Builder generates the **AI context package** used by downstream components.

---

### User State Engine

Transforms raw inputs into structured readiness indicators.

Examples of derived signals:

- Recovery score
- Fatigue score
- Adherence score
- Training load
- Readiness classification

These indicators help determine whether the user should perform:

- Intense training
- Moderate workout
- Recovery session

---

### Memory Layer

Stores historical information used to personalize recommendations over time.

Examples of stored data:

- Previous workouts
- Adherence trends
- Historical recommendations
- Performance improvements
- Long-term training patterns

The memory layer enables the system to behave like a **coach with historical awareness**.

---

### Training Knowledge Base (RAG)

The system includes a retrieval-based knowledge layer containing structured training information.

Examples of knowledge sources:

- Exercise catalog
- Training guidelines
- Recovery rules
- Intensity recommendations
- Workout video catalog

This allows the AI to retrieve reliable training rules before generating a recommendation.

---

### Coach Agent

The **Coach Agent** acts as the decision-making orchestrator.

Responsibilities include:

- Analyzing user readiness
- Selecting the training strategy
- Retrieving relevant exercises
- Determining workout intensity
- Preparing context for the LLM

This component enables the system to behave more like an **AI planning system** rather than a simple chatbot.

---

### Prompt Engine

Builds structured prompts combining:

- Contextual user state
- Retrieved training knowledge
- Historical training signals
- Exercise availability

The Prompt Engine ensures the model receives **structured and reliable context**.

---

### LLM Reasoning Layer

The LLM generates the final training recommendation.

Example outputs include:

- Daily workout plan
- Exercise selection
- Training duration
- Intensity level
- Coaching message

Example structured output:

```json
{
  "workout_plan": "Full Body Moderate Training",
  "duration_minutes": 45,
  "intensity": "moderate",
  "exercises": [
    "bodyweight squats",
    "push-ups",
    "plank",
    "jump rope"
  ],
  "coach_message": "You reported moderate recovery today. Focus on controlled movement and maintain consistent pacing."
}
```

---

### Evaluation Layer

Before persisting recommendations, the system validates the output.

Validation includes:

- Safety checks
- Intensity boundaries
- Exercise availability
- Recovery constraints
- Overtraining prevention

This prevents unsafe or unrealistic recommendations.

---

## Key Features

### AI-Powered Training Recommendations

- LLM-generated workout plans
- Fatigue-aware training adjustments
- Contextual prompts using user history

### Adaptive Training Programs

Recommendations adapt daily based on user feedback and readiness.

### Coach Dashboard

Coaches can:

- Manage clients
- Track progress
- Assign training plans
- Review AI recommendations

### Client Portal

Clients can:

- View assigned workouts
- Track performance
- Monitor progress
- Complete daily readiness check-ins and receive contextual diet + training plans

### Progress Tracking

Includes:

- Weekly check-ins
- Body measurements
- Training adherence monitoring

---

## Tech Stack

| Layer | Technologies |
|-------|--------------|
| **Backend** | Python 3.12, Django 5, Django REST Framework |
| **AI / Recommendation Engine** | LLMs, Prompt Engineering, Context Engineering, Retrieval-Augmented Context |
| **Data Layer** | PostgreSQL, structured training history, contextual user state storage |
| **Frontend** | React, TypeScript, Vite, TailwindCSS |
| **Infrastructure** | Docker, docker-compose, Poetry |

---

## System Design

The system follows a layered architecture:

```
Frontend (React)
       ↓
Backend API (Django REST)
       ↓
Recommendation Engine
       ↓
LLM Service
       ↓
PostgreSQL Database
```

---

## Repository Structure

```
├── README.md
├── LICENSE
├── .gitignore
├── docs/
│   ├── ai-architecture.png    # Architecture diagram
│   └── ai-architecture.md     # Architecture documentation
├── backend/                    # Django API + AI recommendation engine
├── frontend/                   # React client portal & coach dashboard
└── docker-compose.yml
```

---

## Quick Start

### Requirements

- Docker
- Docker Compose
- Node.js 18+

### Run the Application

```bash
git clone <repository-url>
cd fitness-coach-app

docker-compose up --build
```

### Access the Services

| Service | URL |
|---------|-----|
| Backend API | http://localhost:8000 |
| Frontend | http://localhost:5174 |
| API Documentation | http://localhost:8000/api/docs/ |

### Example AI Workflow

Daily recommendation generation:

```
User submits check-in
       ↓
Context Builder aggregates data
       ↓
User State Engine evaluates readiness
       ↓
Coach Agent selects strategy
       ↓
Prompt Engine builds structured prompt
       ↓
LLM generates recommendation
       ↓
Evaluation Layer validates output
       ↓
Training plan persisted
```

---

## Future Improvements

Planned enhancements include:

- Retrieval-augmented training knowledge base
- AI-driven recovery analysis
- Automated nutrition planning
- AI workout performance evaluation
- Agent-based coaching assistants
- Personalized long-term training periodization

---

## Author

**Raúl Guerrero**

AI Engineer focused on Generative AI systems, machine learning, and intelligent software architectures.

- [LinkedIn](https://www.linkedin.com/in/raulguerrerop)
