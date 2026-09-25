# OcéENS

OcéENS is EPF's course-feedback platform. Teaching teams create surveys; students respond; authorized staff export, visualize, and summarize the results.

## Language and product vocabulary

The application interface is primarily in French, while source code, issues, and project documentation use English. Keep the product's French terms *sondage* (a course-feedback survey) and *synthèse* (an LLM-generated summary of free-text responses) in English documentation when referring to those application concepts. Translate surrounding explanations into English; this is the intended boundary between product vocabulary and documentation language.

## Authentication

**Development login** (`AUTH_MODE=dev`) signs in as a selected user without an identity provider or proof of identity. It is intended only for local development and must never be exposed as a production authentication method.

Avoid describing this feature as impersonation, spoofing, or fake login. Those terms imply a security capability or intent beyond this explicitly local development mode.
