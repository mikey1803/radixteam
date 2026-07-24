# Profile Builder Module (STUB — Role 3)

Already functional: real save/load CRUD against the shared
`CandidateProfile` contract, backed by local JSON storage. What's missing
is the React form UI (see `frontend/src/pages/ProfileBuilder.tsx` stub) and
pre-filling from Resume Parsing's output.

**Role 3 owner:** wire the frontend form to these endpoints, and consider
pulling a resume_id's extracted skills to pre-fill the form (talk to
whoever owns Resume Parsing).
