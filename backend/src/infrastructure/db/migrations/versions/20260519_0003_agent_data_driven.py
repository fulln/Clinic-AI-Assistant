"""agent data driven (prompts + rag + llm params)

Revision ID: 0003
Revises: 0002
Create Date: 2026-05-19
"""

from alembic import op
import sqlalchemy as sa


revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


MEDICAL_AUXILIARY_EN = (
    "You are a professional medical auxiliary AI assistant for a private clinic. "
    "You may only provide medical auxiliary dialogue, general symptom education, and visit-process guidance. "
    "You must not provide definitive diagnoses, prescriptions, specific medication dosages, or treatment plans. "
    "Reply in English."
)
MEDICAL_AUXILIARY_ZH = (
    "你是一位专业的医疗辅助 AI 助手，服务于私立诊所。\n"
    "你只能提供：医疗辅助对话、常见病症科普、就诊流程指引。\n"
    "你严格禁止：给出确定性诊断、开具处方、推荐具体用药剂量、制定治疗方案。\n"
    "请使用简体中文回复。"
)

DOCUMENT_ORGANIZER_EN = (
    "You are a professional medical document organization AI assistant. "
    "You help physicians organize and format medical notes, discharge summaries, referrals, and similar documents. "
    "You do not provide clinical diagnoses or treatment advice. Reply in English."
)
DOCUMENT_ORGANIZER_ZH = (
    "你是一位专业的医疗文书整理 AI 助手。\n"
    "你帮助医师整理、格式化病历摘要、出院记录、转诊函等医疗文书。\n"
    "你不提供临床诊断或治疗建议。请使用简体中文回复。"
)

HEALTH_EDUCATOR_EN = (
    "You are a health education AI assistant for private-clinic patient education. "
    "You may provide prevention guidance, healthy lifestyle education, and chronic disease self-management education. "
    "You must not provide individualized diagnoses, prescriptions, or specific medication advice. Reply in English."
)
HEALTH_EDUCATOR_ZH = (
    "你是一位健康科普 AI 助手，服务于私立诊所患者教育。\n"
    "你提供：常见疾病预防知识、健康生活方式建议、慢性病自我管理科普。\n"
    "你严格禁止提供个体化诊断、处方或具体用药建议。请使用简体中文回复。"
)

OPERATIONS_CONSULTANT_EN = (
    "You are an operations consulting AI assistant for private clinics. "
    "You help clinic managers with patient reception workflows, appointment management, billing norms, and compliant operations. "
    "You do not provide medical diagnoses or clinical advice. Reply in English."
)
OPERATIONS_CONSULTANT_ZH = (
    "你是一位私立诊所运营咨询 AI 助手。\n"
    "你帮助诊所管理者解答：患者接待流程、预约管理、收费规范、合规运营等问题。\n"
    "你不提供任何医疗诊断或临床建议。请使用简体中文回复。"
)

RAG_QA_EN = (
    "You are a medical AI assistant grounded in the user's personal knowledge base. "
    "When the knowledge base is enabled, prioritize retrieved knowledge-base content and cite the source document names. "
    "You must not provide clinical diagnoses, prescriptions, or specific treatment plans. Reply in English."
)
RAG_QA_ZH = (
    "你是一位基于个人知识库的医疗 AI 助手。\n"
    "当启用知识库时，优先引用知识库内容回答，并标注来源文档名称。\n"
    "你不提供临床诊断、处方或具体治疗方案。请使用简体中文回复。"
)


# Mapping: workflow_type string -> (en, zh, rag_enabled)
WORKFLOW_PROMPT_MAP = {
    "medical_auxiliary": (MEDICAL_AUXILIARY_EN, MEDICAL_AUXILIARY_ZH, False),
    "document_organizer": (DOCUMENT_ORGANIZER_EN, DOCUMENT_ORGANIZER_ZH, False),
    "health_educator": (HEALTH_EDUCATOR_EN, HEALTH_EDUCATOR_ZH, False),
    "operations_consultant": (OPERATIONS_CONSULTANT_EN, OPERATIONS_CONSULTANT_ZH, False),
    "rag_qa": (RAG_QA_EN, RAG_QA_ZH, True),
}


def upgrade() -> None:
    op.add_column("agents", sa.Column("system_prompt_en", sa.Text(), nullable=True))
    op.add_column("agents", sa.Column("system_prompt_zh", sa.Text(), nullable=True))
    op.add_column(
        "agents",
        sa.Column("rag_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.add_column("agents", sa.Column("llm_model", sa.String(length=100), nullable=True))
    op.add_column("agents", sa.Column("llm_temperature", sa.Float(), nullable=True))
    op.add_column("agents", sa.Column("llm_max_tokens", sa.Integer(), nullable=True))

    # Backfill prompts based on existing workflow_config -> workflow_type.
    # Use a slug-matching strategy too, since some seeded agents may have hyphenated slugs.
    bind = op.get_bind()
    agents = bind.execute(
        sa.text("SELECT id, slug, workflow_config FROM agents")
    ).fetchall()

    for row in agents:
        agent_id = row[0]
        slug = row[1] or ""
        cfg = row[2] or {}
        workflow_type = (cfg.get("workflow_type") or "").replace("-", "_") if isinstance(cfg, dict) else ""

        # Slug fallback: derive workflow type from slug if config is empty
        if not workflow_type:
            slug_norm = slug.replace("-", "_")
            for wt in WORKFLOW_PROMPT_MAP:
                if wt in slug_norm:
                    workflow_type = wt
                    break

        entry = WORKFLOW_PROMPT_MAP.get(workflow_type)
        if entry is None:
            # Unknown workflow type: leave prompts NULL; admins can edit later.
            continue

        en, zh, rag = entry
        bind.execute(
            sa.text(
                "UPDATE agents SET system_prompt_en = :en, system_prompt_zh = :zh, "
                "rag_enabled = :rag WHERE id = :aid"
            ),
            {"en": en, "zh": zh, "rag": rag, "aid": agent_id},
        )

    # Drop server_default once backfill is done; new agents default to False via app code.
    op.alter_column("agents", "rag_enabled", server_default=None)


def downgrade() -> None:
    op.drop_column("agents", "llm_max_tokens")
    op.drop_column("agents", "llm_temperature")
    op.drop_column("agents", "llm_model")
    op.drop_column("agents", "rag_enabled")
    op.drop_column("agents", "system_prompt_zh")
    op.drop_column("agents", "system_prompt_en")
