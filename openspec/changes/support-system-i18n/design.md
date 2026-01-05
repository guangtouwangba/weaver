## Context
The system currently assumes English for both UI and Model outputs. Users from different regions (specifically Chinese users as implied by the request) need a localized experience.

## Goals
- Allow users to switch between English and Chinese (and potentially other languages in the future).
- Ensure "What you see is what you get" regarding language: if UI is Chinese, AI answers in Chinese.

## Decisions
- **Decision**: Use `next-intl` for frontend localization.
  - **Rationale**: It is a standard, robust solution for Next.js App Router.
- **Decision**: Pass `language` explicitly to agents.
  - **Rationale**: While we could rely on "answer in user's language" prompting, explicit instruction reduces hallucinations where the model might default to English (its training dominant language) simply because the context is English. Giving an explicit "Answer in {language}" constraint is safer.

## Migration Plan
- This is a non-breaking additive change. Default behavior (English) is preserved if no locale is specified.
