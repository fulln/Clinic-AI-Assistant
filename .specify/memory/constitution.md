<!--
SYNC IMPACT REPORT
==================
Version change: 0.0.0 → 1.0.0
Type of bump: MINOR — initial population of all template placeholders; new project constitution established.

Modified principles: N/A (first-time definition; no prior principles to rename)

Added sections:
  - Core Principles (5 principles)
  - Compliance & Regulatory Requirements
  - Development Workflow & Quality Gates
  - Governance

Removed sections: None

Templates requiring updates:
  - .specify/templates/plan-template.md  ✅ Constitution Check gates reflect principles below
  - .specify/templates/spec-template.md  ✅ Scope/requirements align with service boundary principle
  - .specify/templates/tasks-template.md ✅ Task categories align with observability, privacy, safety principles

Follow-up TODOs:
  - TODO(RATIFICATION_DATE): Confirm exact project inception/sign-off date with project owner if
    different from 2026-05-17.
  - TODO(REGULATORY_JURISDICTION): Confirm whether applicable regulations are China's Personal
    Information Protection Law (PIPL) + Regulations on the Administration of Internet Diagnosis and
    Treatment, or additional jurisdictions (e.g., HIPAA for overseas patients).
-->

# 私立诊所 AI 助手平台 Constitution

## Core Principles

### I. Medical Safety First (NON-NEGOTIABLE)

The platform MUST NOT generate clinical diagnoses, prescribe medications, recommend specific
treatment plans, or produce any output that could substitute for a licensed physician's judgment.

- Every AI-generated response in the medical auxiliary dialogue module MUST carry an explicit
  disclaimer: "本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。"
- The system MUST refuse requests that ask it to act as a diagnosing or prescribing entity,
  regardless of how the prompt is phrased.
- Permitted output categories are strictly: auxiliary dialogue support, document drafting/
  organization, operational consulting, and health science popularization. Any feature outside
  these four categories MUST be rejected at specification stage.

**Rationale**: Medical AI systems that blur the line between information and diagnosis create legal
liability and patient safety risk. This principle is the hard outer boundary of the entire product.

### II. Patient Data Privacy & Confidentiality

All patient-identifiable information MUST be handled as strictly confidential at every layer of
the system (transport, storage, processing, logging).

- Personally identifiable information (PII) and protected health information (PHI) MUST be
  encrypted at rest (AES-256 or equivalent) and in transit (TLS 1.2+).
- Logs MUST NOT contain raw patient names, ID numbers, phone numbers, or medical record content.
  Use anonymized or pseudonymized references only.
- Data retention periods MUST be explicitly defined per data category and enforced programmatically.
- Access to patient data MUST follow least-privilege: only the roles that require access for a
  specific function may hold it.

**Rationale**: Clinics operate under strict medical confidentiality obligations (Chinese PIPL,
医疗机构管理条例, and applicable local regulations). A breach is both a legal violation and a
fundamental breach of patient trust.

### III. Strict Service Scope Boundary

The platform MUST only implement the four permitted service categories:

1. **Medical auxiliary dialogue** — conversational support for doctors (e.g., differential
   reminders, literature summaries, patient communication phrasing suggestions).
2. **Document organization** — drafting, formatting, and structuring clinical documents, referrals,
   discharge summaries, and operational reports.
3. **Operations consulting** — scheduling logic, clinic workflow optimization, billing query
   support, and administrative guidance.
4. **Health science popularization** — patient-facing educational content that is general,
   evidence-based, and explicitly non-diagnostic.

Any feature request that falls outside these four categories MUST be rejected at the specification
stage with a documented reason. Scope creep into diagnostic, prescriptive, or triage AI is
explicitly prohibited.

**Rationale**: The platform's regulatory and liability posture depends on remaining a lightweight
assistive tool. Scope expansion without deliberate governance review undermines that posture.

### IV. Human-in-the-Loop for All Clinical-Adjacent Outputs

Every AI output that informs a clinical decision or becomes part of a patient-facing document
MUST pass through a licensed physician review step before being acted upon or delivered.

- The system MUST make the physician review step explicit in the UX — outputs must not be
  auto-sent to patients without acknowledgment by a clinician.
- Document drafts MUST be presented as drafts requiring physician sign-off, never as final records.
- The system MUST log which physician reviewed and approved each clinical-adjacent output.

**Rationale**: Automation without oversight is the primary failure mode for medical AI. Keeping a
mandatory human checkpoint preserves accountability and legal defensibility.

### V. Auditability & Observability

Every system action — user query, AI response, document operation, data access — MUST be
logged with sufficient detail to support a full audit trail.

- Logs MUST capture: timestamp (UTC), actor (user/role ID), action type, resource identifier,
  outcome, and session ID.
- Logs MUST be immutable once written (append-only storage or equivalent).
- System health metrics (latency, error rate, availability) MUST be monitored and alertable.
- Audit logs MUST be retained for a minimum of 5 years per medical record regulations.

**Rationale**: Regulatory compliance and incident investigation both require a reliable, tamper-
evident record of what the system did and who authorized it.

## Compliance & Regulatory Requirements

The platform operates under the following regulatory framework (jurisdiction: Mainland China unless
TODO(REGULATORY_JURISDICTION) is resolved otherwise):

- **中华人民共和国个人信息保护法 (PIPL)** — governs patient PII handling.
- **互联网诊疗管理办法 (试行)** — defines boundaries between AI-assisted services and regulated
  internet medical practice; the platform MUST stay on the assistive side of that boundary.
- **医疗机构病历管理规定** — governs document retention and integrity for medical records.
- **网络安全法** — governs data localization and security obligations.

All features MUST be reviewed against these regulations before specification is finalized. Legal
review is REQUIRED for any feature that generates patient-facing health content or stores patient
records.

## Development Workflow & Quality Gates

- **Specification gate**: Every feature specification MUST include a compliance review section
  confirming the feature stays within the four permitted service categories (Principle III).
- **Privacy gate**: Any feature touching patient data MUST include a data-flow diagram and a
  privacy impact assessment before implementation begins.
- **Review gate**: All pull requests that modify AI prompt logic, data access layers, or patient-
  facing output rendering MUST receive sign-off from both a technical reviewer and a designated
  clinical/compliance reviewer.
- **Testing gate**: Features in the medical auxiliary dialogue and document organization modules
  MUST include integration tests covering the refusal behavior (system rejects diagnostic requests)
  and disclaimer presence.
- **Deployment gate**: No production deployment may proceed without a completed QA checklist
  confirming Principles I–V are satisfied for the release scope.

## Governance

This constitution supersedes all other development guidelines, product roadmaps, and informal
agreements. Where conflicts exist, this constitution takes precedence.

**Amendment procedure**:
1. Propose amendment in writing with: motivation, principle(s) affected, version bump type,
   migration plan for existing features, and compliance impact.
2. Obtain sign-off from the platform owner and (for Principle I or II changes) a designated
   medical/legal reviewer.
3. Update this file, increment the version, set `Last Amended` to amendment date, and update
   the Sync Impact Report comment at the top.
4. Propagate changes to all dependent templates (plan, spec, tasks) within the same commit.

**Versioning policy**:
- MAJOR: Removal or redefinition of a core principle, or narrowing/expanding service scope boundary.
- MINOR: Addition of a new principle or materially new section.
- PATCH: Clarifications, wording fixes, non-semantic refinements.

**Compliance review**: All active feature branches MUST be reviewed against the current constitution
version before merging. Features approved against a superseded version MUST be re-reviewed if the
constitution was amended in a MAJOR or MINOR bump since approval.

**Version**: 1.0.0 | **Ratified**: 2026-05-17 | **Last Amended**: 2026-05-17
