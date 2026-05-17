from src.domains.conversation.entities import Locale

SUPPORTED_LOCALES = {locale.value for locale in Locale}

DISCLAIMERS = {
    Locale.ZH_CN: "本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。",
    Locale.EN_US: (
        "This content is for auxiliary reference only and does not constitute "
        "medical diagnosis or treatment advice. Please follow a licensed physician's guidance."
    ),
}

REFUSAL_MESSAGES = {
    Locale.ZH_CN: "该请求超出本平台服务范围，请咨询执业医师。",
    Locale.EN_US: "This request is outside the platform's service scope. Please consult a licensed physician.",
}

GENERIC_ERROR_MESSAGES = {
    Locale.ZH_CN: "AI 服务暂时不可用，请稍后重试。",
    Locale.EN_US: "The AI service is temporarily unavailable. Please try again later.",
}

FORBIDDEN_AGENT_MESSAGES = {
    Locale.ZH_CN: "您的角色无权使用此智能体",
    Locale.EN_US: "Your role is not allowed to use this agent.",
}

CONVERSATION_NOT_FOUND_MESSAGES = {
    Locale.ZH_CN: "Conversation not found",
    Locale.EN_US: "Conversation not found",
}

NEW_CONVERSATION_TITLES = {
    Locale.ZH_CN: "新对话",
    Locale.EN_US: "New Conversation",
}

PROGRESS_MESSAGES = {
    "supervisor_start": {
        Locale.ZH_CN: "主控 agent 启动 Orchestra Workflow：读取用户问题和共享上下文",
        Locale.EN_US: "Supervisor agent started the orchestration workflow: reading the user request and shared context.",
    },
    "routing": {
        Locale.ZH_CN: "主控 agent 编排执行计划：{step_labels}",
        Locale.EN_US: "Supervisor agent planned the execution flow: {step_labels}",
    },
    "rag_retrieval": {
        Locale.ZH_CN: "主控 Workflow 正在为「{agent_name}」检索医生知识库",
        Locale.EN_US: 'Supervisor workflow is retrieving the doctor knowledge base for "{agent_name}".',
    },
    "rag_retrieval_done": {
        Locale.ZH_CN: "知识库检索完成，命中 {count} 条相关片段",
        Locale.EN_US: "Knowledge base retrieval completed with {count} matching passages.",
    },
    "child_start": {
        Locale.ZH_CN: "主控 Workflow 调用子 agent {index}/{total}「{agent_name}」执行任务节点：{workflow_type}",
        Locale.EN_US: 'Supervisor workflow invoked child agent {index}/{total} "{agent_name}" for node {workflow_type}.',
    },
    "child_done": {
        Locale.ZH_CN: "子 agent「{agent_name}」任务节点完成，结果已回传主控 Workflow",
        Locale.EN_US: 'Child agent "{agent_name}" finished and returned its result to the supervisor workflow.',
    },
    "supervisor_summary": {
        Locale.ZH_CN: "主控 agent 执行汇总节点：综合子 agent 结果并生成最终回复",
        Locale.EN_US: "Supervisor agent is synthesizing child-agent results into the final reply.",
    },
    "user_selected": {
        Locale.ZH_CN: "用户手动指定",
        Locale.EN_US: "User explicitly selected this agent.",
    },
    "supervisor_route": {
        Locale.ZH_CN: "主控 agent 路由",
        Locale.EN_US: "Supervisor agent routing.",
    },
    "fallback_route": {
        Locale.ZH_CN: "规则兜底路由",
        Locale.EN_US: "Rule-based fallback routing.",
    },
    "rag_request": {
        Locale.ZH_CN: "用户要求基于知识库回答",
        Locale.EN_US: "The user requested a knowledge-base-grounded answer.",
    },
    "document_request": {
        Locale.ZH_CN: "用户同时要求整理成文书/摘要",
        Locale.EN_US: "The user also asked for a document or summary output.",
    },
    "education_request": {
        Locale.ZH_CN: "用户同时要求健康宣教/护理说明",
        Locale.EN_US: "The user also asked for health education or care instructions.",
    },
    "operations_request": {
        Locale.ZH_CN: "用户同时要求运营流程建议",
        Locale.EN_US: "The user also asked for operations workflow guidance.",
    },
}


def parse_locale(value: str | Locale | None) -> Locale:
    if isinstance(value, Locale):
        return value
    if value in SUPPORTED_LOCALES:
        return Locale(value)
    return Locale.ZH_CN


def get_disclaimer(locale: Locale) -> str:
    return DISCLAIMERS[parse_locale(locale)]


def get_refusal_message(locale: Locale) -> str:
    return REFUSAL_MESSAGES[parse_locale(locale)]


def get_generic_error_message(locale: Locale) -> str:
    return GENERIC_ERROR_MESSAGES[parse_locale(locale)]


def get_forbidden_agent_message(locale: Locale) -> str:
    return FORBIDDEN_AGENT_MESSAGES[parse_locale(locale)]


def get_conversation_not_found_message(locale: Locale) -> str:
    return CONVERSATION_NOT_FOUND_MESSAGES[parse_locale(locale)]


def get_new_conversation_title(locale: Locale) -> str:
    return NEW_CONVERSATION_TITLES[parse_locale(locale)]


def get_progress_message(key: str, locale: Locale, **kwargs: object) -> str:
    template = PROGRESS_MESSAGES[key][parse_locale(locale)]
    return template.format(**kwargs)
