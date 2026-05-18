import type { Locale } from '@/domains/conversation/entities';
import { normalizeLocale } from '@/shared/i18n/conversation';

type SiteDictionary = {
  metaTitle: string;
  metaDescription: string;
  appName: string;
  language: string;
  logout: string;
  cancel: string;
  create: string;
  delete: string;
  loading: string;
  roleDoctor: string;
  roleAdmin: string;
  roleStaff: string;
  landingEyebrow: string;
  landingTitle: string;
  landingBody: string;
  landingPrimaryCta: string;
  landingSecondaryCta: string;
  landingCardOneTitle: string;
  landingCardOneBody: string;
  landingCardTwoTitle: string;
  landingCardTwoBody: string;
  landingCardThreeTitle: string;
  landingCardThreeBody: string;
  landingCardFourTitle: string;
  landingCardFourBody: string;
  landingFlowTitle: string;
  landingFlowOneTitle: string;
  landingFlowOneBody: string;
  landingFlowTwoTitle: string;
  landingFlowTwoBody: string;
  landingFlowThreeTitle: string;
  landingFlowThreeBody: string;
  landingFlowFourTitle: string;
  landingFlowFourBody: string;
  navConversation: string;
  navAgents: string;
  navAgentManagement: string;
  navKnowledgeBase: string;
  authLoginTitle: string;
  authLoginSubtitle: string;
  authUsername: string;
  authUsernamePlaceholder: string;
  authPassword: string;
  authPasswordPlaceholder: string;
  authLogin: string;
  authLoggingIn: string;
  authLoginFailed: string;
  authMarketingEyebrow: string;
  authMarketingTitle: string;
  authMarketingBody: string;
  authFeatureOne: string;
  authFeatureTwo: string;
  authFeatureThree: string;
  authUsernameRequired: string;
  authUsernameMin: string;
  authPasswordRequired: string;
  conversationSelectAgent: string;
  conversationDemoSuffix: string;
  agentsTitle: string;
  agentsSubtitle: string;
  agentsManagementTitle: string;
  agentsManagementSubtitle: string;
  agentsTabAll: string;
  agentsTabFormal: string;
  agentsTabDemo: string;
  agentsStatusDraft: string;
  agentsStatusPublished: string;
  agentsStatusArchived: string;
  agentsLoadFailed: string;
  agentsEmpty: string;
  agentsDemoEnter: string;
  agentsNotFound: string;
  agentsInitConversation: string;
  agentsActions: string;
  agentsPublish: string;
  agentsArchive: string;
  agentsRestoreToDraft: string;
  agentsNoVersion: string;
  agentsAllowedRoles: string;
  agentsManagementForbidden: string;
  agentsActionFailed: string;
  dashboardOverview: string;
  dashboardWorkspaceStatus: string;
  dashboardWorkspaceHealthy: string;
  dashboardSubtitleConversation: string;
  dashboardSubtitleAgents: string;
  dashboardSubtitleAgentManagement: string;
  dashboardSubtitleKnowledgeBase: string;
  dashboardConversationPatternTitle: string;
  dashboardConversationPatternLabel: string;
  dashboardConversationPatternBody: string;
  dashboardConversationPatternIncluded: string;
  dashboardConversationPatternPointOne: string;
  dashboardConversationPatternPointTwo: string;
  dashboardConversationPatternPointThree: string;
  agentsTableName: string;
  agentsTableSlug: string;
  agentsTableType: string;
  agentsTableStatus: string;
  agentsTableVersion: string;
  ragTitle: string;
  ragDoctorOnlyTitle: string;
  ragDoctorOnlySubtitle: string;
  ragCreateTitle: string;
  ragName: string;
  ragNamePlaceholder: string;
  ragDescription: string;
  ragDescriptionPlaceholder: string;
  ragCreateFailed: string;
  ragCreateSubmitting: string;
  ragCreateConfirm: string;
  ragKbList: string;
  ragCreateKb: string;
  ragEmptyKb: string;
  ragDocCount: (count: number) => string;
  ragDeleteKb: string;
  ragEmptyDoc: string;
  ragDeleteDoc: string;
  ragDeleteKbConfirm: string;
  ragDeleteDocConfirm: string;
  ragUploadHintPrefix: string;
  ragUploadHintAction: string;
  ragUploadHintFormats: string;
  ragUploadButton: string;
  ragUploading: string;
  ragStatusUploading: string;
  ragStatusProcessing: string;
  ragStatusReady: string;
  ragStatusFailed: string;
  ragUnsupportedType: (type: string) => string;
  ragFileTooLarge: (sizeMb: string) => string;
};

const dictionaries: Record<Locale, SiteDictionary> = {
  'zh-CN': {
    metaTitle: '诊所 AI 助手平台',
    metaDescription: '私立诊所专属 AI 助手',
    appName: '诊所 AI 助手',
    language: '站点语言',
    logout: '退出登录',
    cancel: '取消',
    create: '创建',
    delete: '删除',
    loading: '加载中',
    roleDoctor: '医师',
    roleAdmin: '管理员',
    roleStaff: '员工',
    landingEyebrow: 'Clinic AI SaaS Template',
    landingTitle: '面向私立诊所的标准 SaaS AI 工作台',
    landingBody: '把患者沟通、智能体协作、知识库检索和管理员治理放进一套统一的 SaaS 网站样板里，既适合演示，也适合继续产品化扩展。',
    landingPrimaryCta: '进入登录',
    landingSecondaryCta: '查看工作台',
    landingCardOneTitle: '统一会话入口',
    landingCardOneBody: '用户从一个标准化会话面板进入，由前端统一承接输入、流式回复和安全提示。',
    landingCardTwoTitle: '多智能体协作',
    landingCardTwoBody: '主控流程会根据问题路由到合适 agent，并把执行轨迹和结果汇总成最终回复。',
    landingCardThreeTitle: '知识库增强回答',
    landingCardThreeBody: '医师可上传和维护 RAG 知识库，让回答具备文档上下文和来源基础。',
    landingCardFourTitle: '管理员治理',
    landingCardFourBody: '管理员可以管理 agent 生命周期，处理草稿、发布、归档和恢复流程。',
    landingFlowTitle: '当前系统的工作环节',
    landingFlowOneTitle: '1. 登录与角色识别',
    landingFlowOneBody: '根据医师、管理员或员工身份，进入对应功能入口和权限范围。',
    landingFlowTwoTitle: '2. 发起会话或选择 agent',
    landingFlowTwoBody: '用户进入会话页，选择智能体或直接输入问题，系统同步站点语言与回复语言。',
    landingFlowThreeTitle: '3. 编排回答与知识检索',
    landingFlowThreeBody: '主控 agent 负责路由、调用子 agent、可选地接入知识库，并以流式方式返回内容。',
    landingFlowFourTitle: '4. 运维与治理',
    landingFlowFourBody: '管理员和医师分别维护 agent 生命周期与知识库资产，保证工作台持续可用。',
    navConversation: '对话',
    navAgents: '智能体',
    navAgentManagement: 'Agent 管理',
    navKnowledgeBase: '知识库',
    authLoginTitle: '诊所 AI 助手',
    authLoginSubtitle: '请登录您的账户',
    authUsername: '用户名',
    authUsernamePlaceholder: '请输入用户名',
    authPassword: '密码',
    authPasswordPlaceholder: '请输入密码',
    authLogin: '登录',
    authLoggingIn: '登录中...',
    authLoginFailed: '登录失败，请重试',
    authMarketingEyebrow: 'Clinic AI Workspace',
    authMarketingTitle: '把临床协作、知识检索和 AI 助手集中到一个标准 SaaS 工作台里',
    authMarketingBody: '参考 GitHub 上成熟 SaaS 模板的后台结构，统一交互入口、角色权限和内容面板。',
    authFeatureOne: '面向医师、管理员和员工的角色化工作流',
    authFeatureTwo: '知识库、智能体与会话在一个空间中联动',
    authFeatureThree: '统一的后台导航、卡片、表格和操作反馈',
    authUsernameRequired: '请输入用户名',
    authUsernameMin: '用户名至少3个字符',
    authPasswordRequired: '请输入密码',
    conversationSelectAgent: '选择智能体',
    conversationDemoSuffix: '（演示）',
    agentsTitle: '智能体目录',
    agentsSubtitle: '浏览并使用可用的 AI 智能体',
    agentsManagementTitle: 'Agent 管理',
    agentsManagementSubtitle: '查看全部智能体并执行发布或归档操作',
    agentsTabAll: '全部',
    agentsTabFormal: '正式',
    agentsTabDemo: '演示',
    agentsStatusDraft: '草稿',
    agentsStatusPublished: '已发布',
    agentsStatusArchived: '已归档',
    agentsLoadFailed: '加载智能体失败，请稍后重试。',
    agentsEmpty: '暂无可用智能体',
    agentsDemoEnter: '进入演示',
    agentsNotFound: '智能体不存在。',
    agentsInitConversation: '正在初始化对话…',
    agentsActions: '操作',
    agentsPublish: '发布',
    agentsArchive: '归档',
    agentsRestoreToDraft: '恢复为草稿',
    agentsNoVersion: '未发布',
    agentsAllowedRoles: '允许角色',
    agentsManagementForbidden: '仅管理员可访问 Agent 管理。',
    agentsActionFailed: 'Agent 操作失败，请重试。',
    dashboardOverview: '工作台',
    dashboardWorkspaceStatus: 'Workspace',
    dashboardWorkspaceHealthy: 'Operational',
    dashboardSubtitleConversation: '统一会话、智能体与知识上下文的核心工作区',
    dashboardSubtitleAgents: '浏览可用智能体，并按任务选择最合适的能力入口',
    dashboardSubtitleAgentManagement: '管理草稿、已发布与已归档智能体的完整生命周期',
    dashboardSubtitleKnowledgeBase: '维护医生知识库与上传文档，支撑可追溯的 RAG 回复',
    dashboardConversationPatternTitle: '标准 SaaS 会话工作区',
    dashboardConversationPatternLabel: '会话样板',
    dashboardConversationPatternBody: '会话、智能体路由和知识上下文现在与后台其它模块共享同一套卡片与面板体系。',
    dashboardConversationPatternIncluded: '包含模块',
    dashboardConversationPatternPointOne: '固定后台壳与角色化导航',
    dashboardConversationPatternPointTwo: '统一的卡片、表格和操作反馈样式',
    dashboardConversationPatternPointThree: '围绕工作流组织的会话与知识区',
    agentsTableName: '名称',
    agentsTableSlug: '标识',
    agentsTableType: '类型',
    agentsTableStatus: '状态',
    agentsTableVersion: '版本',
    ragTitle: 'RAG 知识库管理',
    ragDoctorOnlyTitle: '此功能仅限医师使用',
    ragDoctorOnlySubtitle: '请使用医师账号登录后访问。',
    ragCreateTitle: '创建知识库',
    ragName: '名称',
    ragNamePlaceholder: '请输入知识库名称',
    ragDescription: '描述',
    ragDescriptionPlaceholder: '可选描述',
    ragCreateFailed: '创建失败，请重试',
    ragCreateSubmitting: '创建中…',
    ragCreateConfirm: '确认创建',
    ragKbList: '知识库列表',
    ragCreateKb: '创建知识库',
    ragEmptyKb: '暂无知识库，请点击上方按钮创建',
    ragDocCount: (count) => `(${count} 个文档)`,
    ragDeleteKb: '删除知识库',
    ragEmptyDoc: '暂无文档',
    ragDeleteDoc: '删除',
    ragDeleteKbConfirm: '确认删除此知识库？该操作不可撤销。',
    ragDeleteDocConfirm: '确认删除此文档？',
    ragUploadHintPrefix: '拖拽文件至此或',
    ragUploadHintAction: ' 点击选择文件',
    ragUploadHintFormats: '支持 PDF、TXT、DOCX、Markdown，最大 50 MB',
    ragUploadButton: '上传文件',
    ragUploading: '上传中…',
    ragStatusUploading: '上传中',
    ragStatusProcessing: '处理中',
    ragStatusReady: '就绪',
    ragStatusFailed: '失败',
    ragUnsupportedType: (type) => `不支持的文件类型：${type || '未知'}。请上传 PDF、TXT、DOCX 或 Markdown 文件。`,
    ragFileTooLarge: (sizeMb) => `文件过大（${sizeMb} MB），最大允许 50 MB。`,
  },
  'en-US': {
    metaTitle: 'Clinic AI Assistant Platform',
    metaDescription: 'An AI assistant built for private clinics',
    appName: 'Clinic AI Assistant',
    language: 'Site language',
    logout: 'Log out',
    cancel: 'Cancel',
    create: 'Create',
    delete: 'Delete',
    loading: 'Loading',
    roleDoctor: 'Doctor',
    roleAdmin: 'Admin',
    roleStaff: 'Staff',
    landingEyebrow: 'Clinic AI SaaS Template',
    landingTitle: 'A standard SaaS AI workspace for private clinics',
    landingBody: 'Bring patient communication, multi-agent coordination, grounded knowledge retrieval, and admin governance into one coherent SaaS website template built for further productization.',
    landingPrimaryCta: 'Go to login',
    landingSecondaryCta: 'Open workspace',
    landingCardOneTitle: 'Unified conversation entry',
    landingCardOneBody: 'Users start from one standardized conversation surface with streaming replies and consistent safety framing.',
    landingCardTwoTitle: 'Multi-agent coordination',
    landingCardTwoBody: 'A supervisor workflow routes requests to the right agent and synthesizes execution results into one final answer.',
    landingCardThreeTitle: 'Knowledge-grounded answers',
    landingCardThreeBody: 'Doctors can maintain a RAG knowledge base so responses stay anchored to uploaded documents and context.',
    landingCardFourTitle: 'Administrative governance',
    landingCardFourBody: 'Admins manage the full agent lifecycle across draft, publish, archive, and restore transitions.',
    landingFlowTitle: 'Current product workflow',
    landingFlowOneTitle: '1. Sign in and resolve role access',
    landingFlowOneBody: 'Doctors, admins, and staff enter the workspace with role-specific navigation and permissions.',
    landingFlowTwoTitle: '2. Start a conversation or pick an agent',
    landingFlowTwoBody: 'Users enter the conversation workspace, choose an agent when needed, and keep site and response locale aligned.',
    landingFlowThreeTitle: '3. Orchestrate answers and retrieve knowledge',
    landingFlowThreeBody: 'The supervisor agent routes work, invokes child agents, optionally retrieves knowledge, and streams the final answer back.',
    landingFlowFourTitle: '4. Govern the operating system',
    landingFlowFourBody: 'Admins and doctors manage agent lifecycle and knowledge assets so the workspace stays maintainable.',
    navConversation: 'Conversation',
    navAgents: 'Agents',
    navAgentManagement: 'Agent Management',
    navKnowledgeBase: 'Knowledge Base',
    authLoginTitle: 'Clinic AI Assistant',
    authLoginSubtitle: 'Sign in to your account',
    authUsername: 'Username',
    authUsernamePlaceholder: 'Enter your username',
    authPassword: 'Password',
    authPasswordPlaceholder: 'Enter your password',
    authLogin: 'Sign in',
    authLoggingIn: 'Signing in...',
    authLoginFailed: 'Login failed. Please try again.',
    authMarketingEyebrow: 'Clinic AI Workspace',
    authMarketingTitle: 'Bring clinical collaboration, grounded knowledge, and AI assistants into one SaaS-style workspace',
    authMarketingBody: 'Structured after proven GitHub SaaS templates so navigation, permissions, and content surfaces feel consistent.',
    authFeatureOne: 'Role-aware workflows for doctors, admins, and staff',
    authFeatureTwo: 'Knowledge, agents, and conversations linked in one workspace',
    authFeatureThree: 'Unified dashboard patterns for navigation, cards, tables, and actions',
    authUsernameRequired: 'Please enter your username.',
    authUsernameMin: 'Username must be at least 3 characters.',
    authPasswordRequired: 'Please enter your password.',
    conversationSelectAgent: 'Select agent',
    conversationDemoSuffix: '(Demo)',
    agentsTitle: 'Agent Catalog',
    agentsSubtitle: 'Browse and use available AI agents',
    agentsManagementTitle: 'Agent Management',
    agentsManagementSubtitle: 'Review all agents and publish or archive them',
    agentsTabAll: 'All',
    agentsTabFormal: 'Formal',
    agentsTabDemo: 'Demo',
    agentsStatusDraft: 'Draft',
    agentsStatusPublished: 'Published',
    agentsStatusArchived: 'Archived',
    agentsLoadFailed: 'Failed to load agents. Please try again later.',
    agentsEmpty: 'No agents are currently available.',
    agentsDemoEnter: 'Open Demo',
    agentsNotFound: 'Agent not found.',
    agentsInitConversation: 'Initializing conversation…',
    agentsActions: 'Actions',
    agentsPublish: 'Publish',
    agentsArchive: 'Archive',
    agentsRestoreToDraft: 'Restore to draft',
    agentsNoVersion: 'Unpublished',
    agentsAllowedRoles: 'Allowed roles',
    agentsManagementForbidden: 'Only admins can access agent management.',
    agentsActionFailed: 'Agent action failed. Please try again.',
    dashboardOverview: 'Workspace',
    dashboardWorkspaceStatus: 'Workspace',
    dashboardWorkspaceHealthy: 'Operational',
    dashboardSubtitleConversation: 'A unified workspace for conversations, agents, and grounded knowledge context',
    dashboardSubtitleAgents: 'Browse available agents and pick the right capability for each task',
    dashboardSubtitleAgentManagement: 'Manage the full lifecycle of draft, published, and archived agents',
    dashboardSubtitleKnowledgeBase: 'Maintain the doctor knowledge base and uploaded files for grounded RAG replies',
    dashboardConversationPatternTitle: 'Standard SaaS conversation workspace',
    dashboardConversationPatternLabel: 'Conversation Pattern',
    dashboardConversationPatternBody: 'Conversations, agent routing, and grounded knowledge now share the same card and panel system as the rest of the dashboard.',
    dashboardConversationPatternIncluded: 'Included surfaces',
    dashboardConversationPatternPointOne: 'Sticky shell with role-aware navigation',
    dashboardConversationPatternPointTwo: 'Consistent cards, tables, and action feedback',
    dashboardConversationPatternPointThree: 'Workflow-oriented conversation and knowledge surfaces',
    agentsTableName: 'Name',
    agentsTableSlug: 'Slug',
    agentsTableType: 'Type',
    agentsTableStatus: 'Status',
    agentsTableVersion: 'Version',
    ragTitle: 'RAG Knowledge Base Management',
    ragDoctorOnlyTitle: 'This feature is only available to doctors',
    ragDoctorOnlySubtitle: 'Please sign in with a doctor account to continue.',
    ragCreateTitle: 'Create knowledge base',
    ragName: 'Name',
    ragNamePlaceholder: 'Enter a knowledge base name',
    ragDescription: 'Description',
    ragDescriptionPlaceholder: 'Optional description',
    ragCreateFailed: 'Creation failed. Please try again.',
    ragCreateSubmitting: 'Creating…',
    ragCreateConfirm: 'Create',
    ragKbList: 'Knowledge bases',
    ragCreateKb: 'Create knowledge base',
    ragEmptyKb: 'No knowledge bases yet. Create one to get started.',
    ragDocCount: (count) => `(${count} documents)`,
    ragDeleteKb: 'Delete knowledge base',
    ragEmptyDoc: 'No documents yet.',
    ragDeleteDoc: 'Delete',
    ragDeleteKbConfirm: 'Delete this knowledge base? This action cannot be undone.',
    ragDeleteDocConfirm: 'Delete this document?',
    ragUploadHintPrefix: 'Drag files here or',
    ragUploadHintAction: ' click to choose a file',
    ragUploadHintFormats: 'Supports PDF, TXT, DOCX, and Markdown up to 50 MB',
    ragUploadButton: 'Upload file',
    ragUploading: 'Uploading…',
    ragStatusUploading: 'Uploading',
    ragStatusProcessing: 'Processing',
    ragStatusReady: 'Ready',
    ragStatusFailed: 'Failed',
    ragUnsupportedType: (type) => `Unsupported file type: ${type || 'unknown'}. Please upload PDF, TXT, DOCX, or Markdown files.`,
    ragFileTooLarge: (sizeMb) => `File is too large (${sizeMb} MB). The maximum allowed size is 50 MB.`,
  },
};

export function getSiteCopy(locale: Locale): SiteDictionary {
  return dictionaries[normalizeLocale(locale)];
}

export function getRoleLabel(role: 'doctor' | 'admin' | 'staff', locale: Locale): string {
  const copy = getSiteCopy(locale);
  if (role === 'doctor') return copy.roleDoctor;
  if (role === 'admin') return copy.roleAdmin;
  return copy.roleStaff;
}
