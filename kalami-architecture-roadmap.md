# Kalami: Strategic Architecture Roadmap
## Vocal AI Assistant for Language Learning Through Conversation

**Document Version:** 1.0
**Date:** January 8, 2026
**Author:** Lead Architect

---

## Executive Summary

Kalami is a mobile-first vocal AI assistant designed to accelerate language acquisition through natural, voice-based conversation practice. Unlike traditional language learning apps that focus on gamified drills and written exercises, Kalami prioritizes speaking fluency by enabling real-time, AI-powered conversations that adapt to the learner's proficiency level. The recommended architecture combines React Native for cross-platform mobile development, a hybrid Python/Node.js backend for AI processing and real-time communication, Deepgram for low-latency speech-to-text, ElevenLabs for natural text-to-speech, and Claude/GPT-4 for intelligent conversation generation with pedagogical awareness.

---

## 1. Market Research Findings

### 1.1 Competitive Landscape Analysis

#### Speak (speak.com) - $1B Valuation
- **Strengths:** Deep OpenAI integration, "ML scaffolding" architecture, 1+ billion sentences spoken by users
- **Approach:** Three-step method (listening, talking, feedback), 25+ million personalized lessons generated
- **Limitations:** Limited language support (6 languages), subscription-heavy pricing
- **Technical Insight:** Uses proprietary speech technology combined with latest LLMs

#### Duolingo
- **Strengths:** Gamification mastery, 50+ language support, massive user base, $1B revenue
- **Technology:** Amazon Polly for TTS, server-side speech recognition, GPT-4 integration for Duolingo Max
- **AI Features:** Real-time speech correction (April 2025), Birdbrain AI for adaptive difficulty
- **Limitations:** Voice features feel secondary, conversation practice limited to premium tiers

#### Gliglish
- **Approach:** Pure conversation-focused, web-based interface
- **Positioning:** Budget alternative to Speak

#### Emerging Competitors
- Talkpal, Kippy AI, and numerous AI-powered conversation practice tools
- Most lack sophisticated pronunciation feedback and adaptive curriculum

### 1.2 Market Gaps Identified

1. **Latency Issues:** Most apps have noticeable delays (400-600ms) that break conversational flow
2. **Pronunciation Feedback:** Limited real-time, granular pronunciation correction
3. **Contextual Adaptation:** Few apps truly adapt conversation complexity in real-time
4. **Offline Capability:** Most require constant connectivity
5. **Cultural Context:** Grammar focus without cultural/pragmatic language use
6. **Price Accessibility:** Premium conversation features locked behind expensive subscriptions

---

## 2. Strategic Questions for Product Definition

Before finalizing architecture decisions, the following questions require answers:

### Business & Market
1. **Target Languages:** Which languages will be supported at launch? (Affects TTS/STT model selection and content requirements)
2. **Target Market:** Primary geographic focus? (Affects infrastructure placement, latency optimization)
3. **Monetization Model:** Freemium, subscription, one-time purchase, or hybrid?
4. **User Acquisition Strategy:** Organic growth, paid acquisition, partnerships?

### Technical & Operational
5. **Offline Requirements:** Must conversations work without internet? (Significantly impacts architecture)
6. **Scale Expectations:** Projected concurrent users at 6 months, 1 year, 3 years?
7. **Team Composition:** Available expertise in mobile development, ML/AI, backend systems?
8. **Budget Constraints:** Infrastructure budget ceiling for MVP and growth phases?

### Product & UX
9. **Target Proficiency Levels:** Beginners only, or spanning A1 to C2?
10. **Age Demographics:** Adults only, or including children? (Affects COPPA/privacy requirements)

---

## 3. Recommended Technology Architecture

### 3.1 Mobile Application Layer

#### Framework Selection: React Native with Expo

**Rationale:**
- **Cross-Platform Efficiency:** Single codebase for iOS and Android with 90%+ code sharing
- **Proven Voice Capability:** Discord uses React Native for real-time voice chat at scale
- **Native Audio Access:** Excellent integration with native audio APIs via react-native-audio-api
- **Developer Ecosystem:** Larger talent pool than Flutter, extensive library support
- **Hot Reloading:** Faster development iteration for conversation UI refinements

**Alternative Considered - Flutter:**
- Superior UI rendering (60 FPS animations)
- Better performance in synthetic benchmarks
- Smaller developer community, Dart language barrier
- Discord's success with RN for voice is a stronger proof point

**Key Libraries:**
```
- expo-av: Audio recording and playback
- react-native-audio-api: Low-level audio streaming
- @shopify/react-native-skia: High-performance UI animations
- react-native-reanimated: Smooth conversation UI transitions
- @tanstack/react-query: Server state management
- zustand: Local state management
```

### 3.2 Real-Time Communication Layer

#### WebRTC via LiveKit

**Rationale:**
- WebRTC uses UDP-like transport prioritizing speed over guaranteed delivery
- LiveKit Agents framework handles WebRTC infrastructure complexity
- Sub-300ms round-trip latency achievable
- Built-in support for audio streaming to AI services
- Handles network fluctuations gracefully (packet loss tolerance)

**Architecture Pattern:**
```
Mobile App <--WebRTC--> LiveKit Cloud <--> AI Processing Pipeline
                              |
                              v
                    [Deepgram STT] --> [LLM] --> [ElevenLabs TTS]
```

### 3.3 Speech Processing Pipeline

#### Speech-to-Text: Deepgram Nova-3

**Selection Rationale:**
| Criteria | Deepgram | OpenAI Whisper | Google STT |
|----------|----------|----------------|------------|
| Streaming Latency | <300ms | No native streaming | Higher |
| Cost (per 1000 min) | $4.30 | $6.00 | $16.00 |
| Real-time Capability | Excellent | Requires chunking | Good |
| Multilingual | Strong | Excellent | Excellent |

**Key Decision:** For real-time conversation, Deepgram's streaming capability is non-negotiable. Whisper's superior accuracy matters less when users are waiting for responses.

**Implementation Notes:**
- Use Deepgram's streaming API with interim results
- Implement Voice Activity Detection (VAD) using Silero VAD
- Configure language model hints for language learning context

#### Text-to-Speech: ElevenLabs

**Selection Rationale:**
| Criteria | ElevenLabs | Amazon Polly | Google TTS |
|----------|------------|--------------|------------|
| Voice Naturalness | 75.3% preference | Robotic | Good |
| Latency (TTFA) | 75-135ms | 150ms | Not specified |
| Multilingual | 32 languages | Extensive | 50+ |
| Pronunciation Accuracy | 81.97% | Lower | Good |

**Key Decision:** For language learning, voice naturalness directly impacts learning efficacy. Learners must hear accurate pronunciation and natural intonation. ElevenLabs' quality justifies higher cost.

**Implementation Notes:**
- Use streaming TTS for lower perceived latency
- Pre-generate common phrases for instant playback
- Implement voice caching for repeated content

### 3.4 Conversational AI Engine

#### Primary LLM: Claude Opus/Sonnet (Anthropic)

**Rationale:**
- Superior instruction following for complex pedagogical prompts
- Excellent at maintaining consistent "tutor" persona
- Strong multilingual capabilities
- Better at nuanced language correction feedback
- Constitutional AI alignment reduces inappropriate responses

**Fallback/Comparison:** GPT-4o for specific language pairs where it performs better

#### Conversation Engine Design

```python
# Prompt Architecture (Simplified)
SYSTEM_PROMPT = """
You are Kalami, a patient and encouraging language tutor helping the user
practice {target_language} through natural conversation.

USER PROFILE:
- Native language: {native_language}
- Proficiency level: {cefr_level} (A1-C2)
- Learning goals: {goals}
- Common mistakes: {mistake_patterns}

CONVERSATION RULES:
1. Speak primarily in {target_language} at {complexity_level} complexity
2. When user makes errors, provide gentle corrections using the sandwich method
3. Introduce {new_vocab_count} new vocabulary items naturally
4. Ask follow-up questions to extend conversation
5. Track and reinforce previously taught vocabulary
6. Adjust difficulty based on user's response quality

CORRECTION FORMAT:
- Minor errors: Continue conversation, correct inline naturally
- Major errors: Pause, explain the correction, provide examples
- Pronunciation hints: Use phonetic guides when needed

Current conversation topic: {topic}
Session goal: {session_goal}
"""
```

### 3.5 Backend Architecture

#### Hybrid Architecture: FastAPI (Python) + Node.js

**Python/FastAPI Services (AI-Focused):**
- Conversation generation and management
- Pronunciation analysis and feedback
- Progress tracking and adaptive curriculum
- ML model inference

**Node.js Services (Real-Time Focused):**
- WebSocket connection management
- Real-time event streaming
- Session state management
- API gateway

**Rationale for Hybrid:**
- Python's ML ecosystem is unmatched (NumPy, Torch, Transformers)
- FastAPI matches Node.js performance for async workloads
- Node.js excels at WebSocket and real-time event handling
- Best of both worlds without compromising either domain

#### Service Architecture

```
                                    [Load Balancer]
                                          |
                    +---------------------+---------------------+
                    |                                           |
            [Node.js Gateway]                           [Node.js Gateway]
                    |                                           |
        +-----------+-----------+                   +-----------+-----------+
        |           |           |                   |           |           |
   [WebSocket]  [REST API]  [Webhooks]         [WebSocket]  [REST API]  [Webhooks]
        |           |           |                   |           |           |
        +-----------+-----------+-------------------+-----------+-----------+
                                |
                    [Message Queue - Redis Streams]
                                |
        +-----------------------+-----------------------+
        |                       |                       |
[Conversation Service]  [Progress Service]    [Analytics Service]
    (FastAPI)               (FastAPI)              (FastAPI)
        |                       |                       |
        +-----------------------+-----------------------+
                                |
                    [PostgreSQL Primary]
                            |
                    [Read Replicas]
```

### 3.6 Database Architecture

#### Primary Database: PostgreSQL

**Schema Design:**

```sql
-- Core User Management
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    native_language VARCHAR(10) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Language Learning Profiles (per target language)
CREATE TABLE learning_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    target_language VARCHAR(10) NOT NULL,
    cefr_level VARCHAR(2) DEFAULT 'A1', -- A1, A2, B1, B2, C1, C2
    total_speaking_time_seconds INTEGER DEFAULT 0,
    vocabulary_mastered INTEGER DEFAULT 0,
    streak_days INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, target_language)
);

-- Conversation Sessions
CREATE TABLE conversation_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    learning_profile_id UUID REFERENCES learning_profiles(id),
    topic VARCHAR(255),
    started_at TIMESTAMPTZ DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    duration_seconds INTEGER,
    words_spoken INTEGER,
    new_vocabulary_introduced TEXT[], -- Array of vocabulary IDs
    corrections_made INTEGER DEFAULT 0
);

-- Conversation Messages
CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id UUID REFERENCES conversation_sessions(id),
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    content TEXT NOT NULL,
    audio_url VARCHAR(500),
    pronunciation_score DECIMAL(3,2), -- 0.00 to 1.00
    grammar_errors JSONB, -- Array of error objects
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vocabulary Tracking
CREATE TABLE vocabulary_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    language VARCHAR(10) NOT NULL,
    word VARCHAR(255) NOT NULL,
    translation JSONB NOT NULL, -- Multiple language translations
    pronunciation_guide VARCHAR(255),
    difficulty_level VARCHAR(2), -- A1-C2
    context_examples TEXT[],
    UNIQUE(language, word)
);

-- User Vocabulary Progress (Spaced Repetition)
CREATE TABLE user_vocabulary (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    vocabulary_item_id UUID REFERENCES vocabulary_items(id),
    times_encountered INTEGER DEFAULT 0,
    times_used_correctly INTEGER DEFAULT 0,
    last_reviewed_at TIMESTAMPTZ,
    next_review_at TIMESTAMPTZ,
    ease_factor DECIMAL(3,2) DEFAULT 2.50, -- SM-2 algorithm
    interval_days INTEGER DEFAULT 1,
    UNIQUE(user_id, vocabulary_item_id)
);

-- Pronunciation Analysis Results
CREATE TABLE pronunciation_analyses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES conversation_messages(id),
    overall_score DECIMAL(3,2),
    phoneme_scores JSONB, -- Per-phoneme breakdown
    problem_areas TEXT[],
    improvement_suggestions TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

#### Caching Layer: Redis

**Use Cases:**
- Session state (current conversation context)
- Real-time presence and typing indicators
- Rate limiting
- Vocabulary review queue
- Temporary audio file URLs

### 3.7 Infrastructure Architecture

#### Cloud Provider: AWS (Primary) with Multi-Region Support

**Component Placement:**

```
┌─────────────────────────────────────────────────────────────────┐
│                         AWS Global                               │
├─────────────────────────────────────────────────────────────────┤
│  CloudFront CDN                                                  │
│  ├── Static assets (app bundles, images)                        │
│  └── Audio file caching (common phrases)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────────┐         ┌─────────────────┐                │
│  │   US-EAST-1     │         │   EU-WEST-1     │                │
│  │   (Primary)     │         │   (Expansion)   │                │
│  ├─────────────────┤         ├─────────────────┤                │
│  │ EKS Cluster     │         │ EKS Cluster     │                │
│  │ ├─Node Gateway  │         │ ├─Node Gateway  │                │
│  │ ├─FastAPI Pods  │         │ ├─FastAPI Pods  │                │
│  │ └─LiveKit Agent │         │ └─LiveKit Agent │                │
│  │                 │         │                 │                │
│  │ RDS PostgreSQL  │◄───────►│ RDS Read Replica│                │
│  │ (Multi-AZ)      │         │                 │                │
│  │                 │         │                 │                │
│  │ ElastiCache     │         │ ElastiCache     │                │
│  │ (Redis Cluster) │         │ (Redis Cluster) │                │
│  └─────────────────┘         └─────────────────┘                │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    Shared Services                          ││
│  │  S3 (Audio storage) | SQS (Task queues) | Secrets Manager  ││
│  │  CloudWatch (Monitoring) | X-Ray (Tracing)                  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘

External Services:
├── LiveKit Cloud (WebRTC infrastructure)
├── Deepgram API (Speech-to-Text)
├── ElevenLabs API (Text-to-Speech)
├── Anthropic API (Claude LLM)
└── Auth0/Clerk (Authentication)
```

---

## 4. The "Secret Sauce" - Differentiating Features

### 4.1 Adaptive Conversational Scaffolding (ACS)

**Concept:** Unlike competitors that adjust difficulty between sessions, Kalami adjusts IN REAL-TIME during conversation.

**Implementation:**
```python
class AdaptiveScaffoldingEngine:
    """
    Monitors conversation quality metrics and adjusts AI behavior
    dynamically within a single conversation session.
    """

    def analyze_turn(self, user_response: str, expected_complexity: str):
        metrics = {
            "response_time": self.measure_response_latency(),
            "grammar_accuracy": self.analyze_grammar(user_response),
            "vocabulary_level": self.assess_vocabulary_complexity(user_response),
            "pronunciation_score": self.get_pronunciation_score(),
            "hesitation_markers": self.detect_hesitation_patterns(user_response),
            "comprehension_signals": self.detect_comprehension_issues()
        }

        # Real-time adjustment decisions
        if metrics["hesitation_markers"] > THRESHOLD:
            return self.simplify_next_response()
        elif metrics["grammar_accuracy"] > 0.9 and metrics["vocabulary_level"] == expected_complexity:
            return self.increase_complexity_slightly()
        elif metrics["comprehension_signals"]:
            return self.provide_scaffolding_support()

        return self.maintain_current_level()
```

### 4.2 Phoneme-Level Pronunciation Feedback

**Concept:** Go beyond "good/bad" pronunciation to show exactly which sounds need work.

**Implementation:**
- Integrate with pronunciation assessment APIs (Azure Speech, SpeechSuper)
- Build visual phoneme breakdown showing strength/weakness
- Provide targeted practice exercises for problem phonemes
- Use minimal pairs practice (e.g., "ship" vs "sheep" for /i/ vs /i:/)

### 4.3 Cultural Context Integration

**Concept:** Language isn't just grammar--it's knowing when to use formal vs informal, understanding idioms in context, and navigating cultural nuances.

**Implementation:**
- Include cultural notes in conversation corrections
- Offer alternative phrasings for different contexts (formal/informal, regional variations)
- Scenario-based conversations (job interview vs casual cafe chat)

### 4.4 Spaced Repetition Through Conversation

**Concept:** Instead of flashcard-style review, naturally reintroduce vocabulary in conversations.

**Implementation:**
```python
def generate_conversation_prompt(user_profile, session_context):
    # Get vocabulary due for review
    due_vocabulary = get_vocabulary_due_for_review(user_profile.id)

    # Inject into conversation generation prompt
    return f"""
    ...
    VOCABULARY TO REINFORCE (use naturally in conversation):
    {format_vocabulary_list(due_vocabulary)}

    When user successfully uses these words, mark for longer interval.
    If user struggles, provide contextual help and mark for shorter interval.
    ...
    """
```

---

## 5. Security Architecture

### 5.1 Authentication & Authorization

**Provider:** Auth0 or Clerk (managed authentication)

**Rationale:**
- Reduces security surface area (no password storage)
- Built-in MFA, social login, passwordless options
- SOC 2 Type II compliant
- Mobile SDK support (React Native)

**Token Strategy:**
- Short-lived access tokens (15 minutes)
- Refresh tokens stored in secure storage (iOS Keychain, Android Keystore)
- Token rotation on each refresh

### 5.2 Data Protection

**In Transit:**
- TLS 1.3 for all API communication
- WebRTC encryption (DTLS-SRTP) for audio streams
- Certificate pinning in mobile app

**At Rest:**
- AWS RDS encryption (AES-256)
- S3 bucket encryption for audio files
- Secrets managed via AWS Secrets Manager

**Audio Data Handling:**
- User audio processed in real-time, not stored by default
- Optional storage (with consent) for progress tracking
- Automatic deletion after configurable retention period
- GDPR-compliant data export and deletion

### 5.3 Privacy Considerations

**For Child Users (if applicable):**
- COPPA compliance required if targeting under-13
- Parental consent mechanisms
- No voice data storage for minors
- Limited data collection

**Voice Biometrics:**
- Explicit opt-in for any voice profile features
- Clear disclosure of data use
- Easy deletion mechanism

### 5.4 API Security

```yaml
Security Measures:
  Rate Limiting:
    - 100 requests/minute per user (API)
    - 10 concurrent WebSocket connections per user
    - Adaptive rate limiting based on user tier

  Input Validation:
    - Schema validation on all API inputs
    - Audio file format validation
    - Maximum audio duration limits (5 minutes per clip)

  Monitoring:
    - Real-time anomaly detection
    - Automated blocking of suspicious patterns
    - Audit logging for all data access
```

---

## 6. Scalability Strategy

### 6.1 Initial Architecture (MVP: 0-10K users)

```
Simple Setup:
├── Single region (US-EAST-1)
├── EKS cluster with 3 nodes
├── RDS PostgreSQL (db.t3.medium, single AZ)
├── ElastiCache (cache.t3.small)
├── LiveKit Cloud (managed)
└── Estimated cost: $500-1,000/month
```

### 6.2 Growth Phase (10K-100K users)

**Scaling Triggers:**
- API latency P95 > 200ms
- Database CPU > 70%
- WebSocket connection limit approaching

**Actions:**
- Enable RDS Multi-AZ
- Add read replicas
- Implement connection pooling (PgBouncer)
- Horizontal pod autoscaling
- Add EU region for European users

### 6.3 Scale Phase (100K+ users)

**Architecture Evolution:**
- Database sharding by user_id
- Regional deployments (US, EU, APAC)
- Edge caching for common audio
- Reserved capacity with AI providers
- Consider self-hosted LLM for cost optimization

### 6.4 Performance Targets

| Metric | MVP Target | Scale Target |
|--------|------------|--------------|
| Voice Response Latency | <800ms | <500ms |
| API Response (P95) | <200ms | <100ms |
| App Cold Start | <3s | <2s |
| Concurrent Users/Instance | 500 | 1000 |
| Uptime SLA | 99.5% | 99.9% |

---

## 7. Implementation Roadmap

### Phase 1: MVP (Months 1-3)

**Goal:** Validate core voice conversation experience with limited features

#### Sprint 1-2: Foundation
```
Deliverables:
├── React Native app shell with navigation
├── Audio recording and playback functionality
├── Basic authentication flow (Auth0)
├── Backend API skeleton (FastAPI)
└── Database schema implementation

Coder Agent Prompt:
"Set up a React Native Expo project with TypeScript. Implement audio
recording using expo-av with the following requirements:
- Record audio in WAV format at 16kHz sample rate
- Show real-time audio waveform visualization
- Implement start/stop recording with haptic feedback
- Store recordings temporarily in app cache
Include unit tests for audio utility functions."
```

#### Sprint 3-4: Voice Pipeline
```
Deliverables:
├── Deepgram integration for real-time STT
├── ElevenLabs integration for TTS
├── Basic conversation flow with Claude
├── WebSocket communication layer
└── Simple conversation UI

Coder Agent Prompt:
"Build a FastAPI service that integrates with Deepgram's streaming
speech-to-text API. Requirements:
- Accept WebSocket audio streams from mobile clients
- Forward audio chunks to Deepgram in real-time
- Return interim and final transcription results
- Handle connection lifecycle (connect, disconnect, errors)
- Implement exponential backoff for API failures
Include integration tests using recorded audio samples."
```

#### Sprint 5-6: MVP Polish
```
Deliverables:
├── End-to-end conversation flow
├── Basic progress tracking
├── Onboarding flow with language selection
├── Error handling and offline states
├── Basic analytics integration
└── TestFlight/Internal testing release

Coder Agent Prompt:
"Create the conversation UI in React Native with the following features:
- Chat bubble interface showing both user and AI messages
- Real-time transcription display while user speaks
- Visual feedback during AI 'thinking' and speaking
- Smooth animations for new messages (react-native-reanimated)
- Accessibility support (VoiceOver/TalkBack compatible)
Use Zustand for local state and React Query for server state."
```

### Phase 2: Enhancement (Months 4-6)

**Goal:** Add learning-specific features and improve retention

```
Features:
├── Pronunciation feedback with phoneme analysis
├── Vocabulary tracking with spaced repetition
├── Multiple conversation topics/scenarios
├── Progress dashboard and statistics
├── Push notification reminders
├── Streak and achievement system
└── Basic subscription implementation (RevenueCat)

Key Technical Work:
├── Integrate pronunciation assessment API
├── Implement SM-2 spaced repetition algorithm
├── Build vocabulary injection system
├── Add offline mode for review features
└── Implement analytics pipeline
```

### Phase 3: Growth (Months 7-12)

**Goal:** Scale, monetize, and differentiate

```
Features:
├── Adaptive Conversational Scaffolding
├── Cultural context integration
├── Role-play scenarios (job interviews, travel, etc.)
├── Pronunciation practice mini-games
├── Social features (leaderboards, challenges)
├── Additional language support (5-10 languages)
└── Family/team plans

Technical Work:
├── Multi-region deployment
├── Performance optimization (sub-500ms latency)
├── Advanced analytics and ML pipeline
├── A/B testing infrastructure
└── Self-hosted LLM evaluation for cost reduction
```

---

## 8. Risk Analysis & Mitigation

### 8.1 Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| High latency degrades UX | Medium | High | Pre-load common responses, optimize streaming pipeline, edge deployment |
| AI generates inappropriate content | Low | High | Content filtering, Claude's constitutional AI, human review system |
| Third-party API outages | Medium | High | Fallback providers (Whisper for STT, Amazon Polly for TTS) |
| Audio quality issues on devices | Medium | Medium | Adaptive audio settings, quality detection, user feedback loop |
| Cost overrun from AI APIs | High | Medium | Usage monitoring, caching strategies, volume discounts, hybrid approach |

### 8.2 Business Risks

| Risk | Mitigation |
|------|------------|
| Speak/Duolingo competitive response | Focus on unique ACS feature, pronunciation depth, price positioning |
| User retention challenges | Gamification, streak mechanics, personalized curriculum |
| Regulatory changes (AI, privacy) | Privacy-first design, minimal data collection, configurable retention |

---

## 9. Cost Estimation

### MVP Monthly Costs (0-1K users)

| Component | Provider | Estimated Cost |
|-----------|----------|----------------|
| Cloud Infrastructure | AWS | $300-500 |
| Speech-to-Text | Deepgram | $200-400 |
| Text-to-Speech | ElevenLabs | $200-400 |
| LLM API | Anthropic | $300-600 |
| Authentication | Auth0 | $0 (free tier) |
| WebRTC | LiveKit Cloud | $100-200 |
| **Total** | | **$1,100-2,100/month** |

### Growth Phase (10K users, estimated)

| Component | Estimated Cost |
|-----------|----------------|
| Infrastructure | $2,000-4,000 |
| Speech APIs | $3,000-5,000 |
| LLM APIs | $5,000-10,000 |
| Other Services | $1,000-2,000 |
| **Total** | **$11,000-21,000/month** |

### Cost Optimization Strategies

1. **Aggressive Caching:** Pre-generate common phrases and greetings
2. **Conversation Length Limits:** Cap free tier conversation duration
3. **Efficient Prompting:** Minimize token usage through prompt optimization
4. **Volume Discounts:** Negotiate enterprise pricing at scale
5. **Hybrid LLM:** Use smaller models for simple responses, larger for complex

---

## 10. Success Metrics

### Product Metrics
- **Daily Active Users (DAU)**: Target 30% of registered users
- **Session Length**: Target 10+ minutes average
- **Sessions per Week**: Target 4+ for active learners
- **Retention (D7/D30)**: Target 40%/20%

### Learning Metrics
- **Words Spoken per Session**: Track growth over time
- **Pronunciation Score Improvement**: Week-over-week gains
- **Vocabulary Retention Rate**: Spaced repetition effectiveness
- **CEFR Level Progression**: Time to advance levels

### Technical Metrics
- **Voice Response Latency**: P50 < 500ms, P95 < 800ms
- **Transcription Accuracy**: > 90% WER for target languages
- **App Crash Rate**: < 0.5%
- **API Availability**: > 99.5%

---

## 11. System Architecture Diagram (Text Representation)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER DEVICE                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    REACT NATIVE APPLICATION                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │   │
│  │  │   Audio     │  │ Conversation│  │  Progress   │  │   Auth     │ │   │
│  │  │  Capture    │  │     UI      │  │  Tracking   │  │   Flow     │ │   │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └─────┬──────┘ │   │
│  │         │                │                │                │        │   │
│  │         └────────────────┼────────────────┼────────────────┘        │   │
│  │                          │                │                          │   │
│  │                    ┌─────┴─────┐    ┌─────┴─────┐                   │   │
│  │                    │  WebRTC   │    │   REST    │                   │   │
│  │                    │  Client   │    │  Client   │                   │   │
│  │                    └─────┬─────┘    └─────┬─────┘                   │   │
│  └──────────────────────────┼────────────────┼─────────────────────────┘   │
└─────────────────────────────┼────────────────┼──────────────────────────────┘
                              │                │
                    ══════════╪════════════════╪══════════════
                         INTERNET/HTTPS
                    ══════════╪════════════════╪══════════════
                              │                │
┌─────────────────────────────┼────────────────┼──────────────────────────────┐
│                         CLOUD INFRASTRUCTURE                                 │
│                              │                │                              │
│  ┌───────────────────────────┼────────────────┼────────────────────────────┐│
│  │                      API GATEWAY (Node.js)                              ││
│  │  ┌────────────────────────┴────────────────┴──────────────────────────┐ ││
│  │  │  Authentication │ Rate Limiting │ Request Routing │ Load Balancing │ ││
│  │  └────────────────────────────────────────────────────────────────────┘ ││
│  └─────────────────────────────┬──────────────────────────────────────────┘│
│                                │                                            │
│         ┌──────────────────────┼──────────────────────┐                    │
│         │                      │                      │                    │
│         ▼                      ▼                      ▼                    │
│  ┌─────────────┐        ┌─────────────┐        ┌─────────────┐            │
│  │  LiveKit    │        │ Conversation│        │  Progress   │            │
│  │  Agents     │        │   Service   │        │   Service   │            │
│  │  (WebRTC)   │        │  (FastAPI)  │        │  (FastAPI)  │            │
│  └──────┬──────┘        └──────┬──────┘        └──────┬──────┘            │
│         │                      │                      │                    │
│         │              ┌───────┴───────┐              │                    │
│         │              │               │              │                    │
│         ▼              ▼               ▼              ▼                    │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                       MESSAGE QUEUE (Redis Streams)              │      │
│  └─────────────────────────────────────────────────────────────────┘      │
│         │              │               │              │                    │
│         │              │               │              │                    │
│  ┌──────┴──────┐       │               │       ┌──────┴──────┐            │
│  │             │       │               │       │             │            │
│  ▼             ▼       ▼               ▼       ▼             ▼            │
│ ┌───────────────────────────────────────────────────────────────┐        │
│ │                    EXTERNAL AI SERVICES                        │        │
│ │  ┌──────────┐    ┌──────────┐    ┌──────────┐                │        │
│ │  │ Deepgram │    │  Claude  │    │ElevenLabs│                │        │
│ │  │   STT    │───►│   LLM    │───►│   TTS    │                │        │
│ │  └──────────┘    └──────────┘    └──────────┘                │        │
│ └───────────────────────────────────────────────────────────────┘        │
│                                                                            │
│  ┌─────────────────────────────────────────────────────────────────┐      │
│  │                       DATA LAYER                                 │      │
│  │  ┌─────────────────┐    ┌─────────────────┐    ┌──────────────┐│      │
│  │  │   PostgreSQL    │    │  Redis Cache    │    │  S3 Storage  ││      │
│  │  │  (Primary DB)   │    │  (Sessions)     │    │   (Audio)    ││      │
│  │  └─────────────────┘    └─────────────────┘    └──────────────┘│      │
│  └─────────────────────────────────────────────────────────────────┘      │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## 12. Voice Conversation Flow (Sequence)

```
User                App                 Backend              AI Services
 │                   │                     │                      │
 │  Start Speaking   │                     │                      │
 │──────────────────►│                     │                      │
 │                   │                     │                      │
 │                   │ Audio Stream (WebRTC)                      │
 │                   │────────────────────►│                      │
 │                   │                     │                      │
 │                   │                     │ Audio Chunks         │
 │                   │                     │─────────────────────►│ Deepgram
 │                   │                     │                      │
 │                   │                     │ Interim Transcription│
 │                   │                     │◄─────────────────────│
 │                   │                     │                      │
 │                   │ Show Interim Text   │                      │
 │                   │◄────────────────────│                      │
 │                   │                     │                      │
 │  Stop Speaking    │                     │                      │
 │──────────────────►│                     │                      │
 │                   │                     │                      │
 │                   │ End Audio Stream    │                      │
 │                   │────────────────────►│                      │
 │                   │                     │                      │
 │                   │                     │ Final Transcription  │
 │                   │                     │◄─────────────────────│ Deepgram
 │                   │                     │                      │
 │                   │                     │ Generate Response    │
 │                   │                     │─────────────────────►│ Claude
 │                   │                     │                      │
 │                   │                     │ Response + Feedback  │
 │                   │                     │◄─────────────────────│
 │                   │                     │                      │
 │                   │                     │ Convert to Speech    │
 │                   │                     │─────────────────────►│ ElevenLabs
 │                   │                     │                      │
 │                   │                     │ Audio Stream         │
 │                   │                     │◄─────────────────────│
 │                   │                     │                      │
 │                   │ Play AI Response    │                      │
 │◄──────────────────│◄────────────────────│                      │
 │                   │                     │                      │
 │                   │ Show Corrections    │                      │
 │◄──────────────────│◄────────────────────│                      │
 │                   │                     │                      │

Total Target Latency: < 800ms (from user stop speaking to AI audio start)
```

---

## 13. Next Steps

### Immediate Actions Required

1. **Answer Strategic Questions** (Section 2) - Critical for finalizing architecture decisions
2. **Validate Target Languages** - Affects STT/TTS provider selection and content strategy
3. **Define MVP Scope** - Confirm feature set for Phase 1
4. **Establish Budget** - Finalize infrastructure and API spending limits
5. **Assemble Team** - Identify developers for mobile, backend, and ML workstreams

### Recommended Team Composition (MVP)

- 1 Mobile Developer (React Native senior)
- 1 Backend Developer (Python/FastAPI senior)
- 1 Full-Stack Developer (Node.js + general support)
- 0.5 ML/AI Engineer (prompt engineering, model optimization)
- 0.5 DevOps Engineer (infrastructure, CI/CD)
- 1 Product Designer (UX for conversation flows)

---

## Research Sources

### Competitive Analysis
- [Speak - Official Website](https://www.speak.com/)
- [OpenAI Partnership with Speak](https://openai.com/index/speak-connor-zwick/)
- [Speak Series C at $1B Valuation - TechCrunch](https://techcrunch.com/2024/12/10/openai-backed-speak-raises-78m-at-1b-valuation-to-help-users-learn-languages-by-talking-out-loud/)
- [Duolingo AI Strategy - Chief AI Officer Blog](https://chiefaiofficer.com/blog/duolingos-ai-strategy-fuels-51-user-growth-and-1b-revenue/)
- [Duolingo with Amazon Polly - AWS](https://aws.amazon.com/blogs/machine-learning/powering-language-learning-on-duolingo-with-amazon-polly/)
- [Duolingo AI Speech Correction - Silicon Review](https://thesiliconreview.com/2025/04/duolingo-ai-speech-correction)

### Technical Architecture
- [WebRTC for Voice AI Architectures](https://webrtc.ventures/2025/10/why-webrtc-is-the-best-transport-for-real-time-voice-ai-architectures/)
- [Voice Agent Latency Optimization](https://webrtc.ventures/2025/06/reducing-voice-agent-latency-with-parallel-slms-and-llms/)
- [LiveKit Platform](https://livekit.io/)
- [Real-Time vs Turn-Based Voice Architecture](https://softcery.com/lab/ai-voice-agents-real-time-vs-turn-based-tts-stt-architecture)
- [Building Voice AI Applications Guide](https://webrtc.ventures/2025/07/how-to-build-voice-ai-applications-a-complete-developer-guide/)

### Speech Technology
- [Deepgram vs OpenAI vs Google STT Comparison](https://deepgram.com/learn/deepgram-vs-openai-vs-google-stt-accuracy-latency-price-compared)
- [Best Speech-to-Text Models 2025](https://nextlevel.ai/best-speech-to-text-models/)
- [Whisper vs Deepgram 2025](https://deepgram.com/learn/whisper-vs-deepgram)
- [ElevenLabs vs Amazon Polly](https://elevenlabs.io/blog/elevenlabs-vs-amazon-polly)
- [Best TTS APIs 2025 - Speechmatics](https://www.speechmatics.com/company/articles-and-news/best-tts-apis-in-2025-top-12-text-to-speech-services-for-developers)
- [STT and TTS Selection Guide](https://softcery.com/lab/how-to-choose-stt-tts-for-ai-voice-agents-in-2025-a-comprehensive-guide)

### Edge Computing & Latency
- [Edge AI for Voice - Chanl AI](https://www.chanl.ai/blog/edge-ai-breakthrough-privacy-latency)
- [Edge Computing for Voice AI - TringTring](https://tringtring.ai/blog/technology-trends/edge-computing-for-voice-ai-reducing-latency-and-improving-privacy/)
- [Edge vs Cloud Voice AI 2025](https://www.fluid.ai/blog/edge-vs-cloud-where-should-your-voice-ai-be)

### Mobile Development
- [Flutter vs React Native 2025](https://www.thedroidsonroids.com/blog/flutter-vs-react-native-comparison)
- [Cross-Platform Performance Benchmarks](https://www.synergyboat.com/blog/flutter-vs-react-native-vs-native-performance-benchmark-2025)

### Backend Architecture
- [Best Backend Technologies 2025](https://www.ditstek.com/blog/best-backend-technology-for-mobile-app)
- [FastAPI vs Django for AI Apps](https://capsquery.com/blog/fastapi-vs-django-in-2025-which-is-best-for-ai-driven-web-apps/)
- [Node.js vs Python Backend 2025](https://kanhasoft.com/blog/node-js-vs-python-which-is-best-for-backend-development-in-2025/)

### Open Source References
- [Vocode Core - Voice LLM Agents](https://github.com/vocodedev/vocode-core)
- [Discute - Language Learning App](https://github.com/5uru/Discute)
- [Voice Chat AI](https://github.com/bigsk1/voice-chat-ai)

---

*Document prepared by Lead Architect for Kalami project initialization.*
