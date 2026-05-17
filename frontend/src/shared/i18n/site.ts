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
  navConversation: string;
  navAgents: string;
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
  authUsernameRequired: string;
  authUsernameMin: string;
  authPasswordRequired: string;
  conversationSelectAgent: string;
  conversationDemoSuffix: string;
  agentsTitle: string;
  agentsSubtitle: string;
  agentsTabAll: string;
  agentsTabFormal: string;
  agentsTabDemo: string;
  agentsLoadFailed: string;
  agentsEmpty: string;
  agentsDemoEnter: string;
  agentsNotFound: string;
  agentsInitConversation: string;
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
    navConversation: '对话',
    navAgents: '智能体',
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
    authUsernameRequired: '请输入用户名',
    authUsernameMin: '用户名至少3个字符',
    authPasswordRequired: '请输入密码',
    conversationSelectAgent: '选择智能体',
    conversationDemoSuffix: '（演示）',
    agentsTitle: '智能体目录',
    agentsSubtitle: '浏览并使用可用的 AI 智能体',
    agentsTabAll: '全部',
    agentsTabFormal: '正式',
    agentsTabDemo: '演示',
    agentsLoadFailed: '加载智能体失败，请稍后重试。',
    agentsEmpty: '暂无可用智能体',
    agentsDemoEnter: '进入演示',
    agentsNotFound: '智能体不存在。',
    agentsInitConversation: '正在初始化对话…',
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
    navConversation: 'Conversation',
    navAgents: 'Agents',
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
    authUsernameRequired: 'Please enter your username.',
    authUsernameMin: 'Username must be at least 3 characters.',
    authPasswordRequired: 'Please enter your password.',
    conversationSelectAgent: 'Select agent',
    conversationDemoSuffix: '(Demo)',
    agentsTitle: 'Agent Catalog',
    agentsSubtitle: 'Browse and use available AI agents',
    agentsTabAll: 'All',
    agentsTabFormal: 'Formal',
    agentsTabDemo: 'Demo',
    agentsLoadFailed: 'Failed to load agents. Please try again later.',
    agentsEmpty: 'No agents are currently available.',
    agentsDemoEnter: 'Open Demo',
    agentsNotFound: 'Agent not found.',
    agentsInitConversation: 'Initializing conversation…',
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
