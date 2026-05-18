import type { Locale } from '@/domains/conversation/entities';

type Dictionary = {
  currentAgent: string;
  language: string;
  languageOptionZh: string;
  languageOptionEn: string;
  emptyState: string;
  progressTrace: string;
  send: string;
  placeholderReady: string;
  placeholderStreaming: string;
  validationEmpty: string;
  validationTooLong: (length: number) => string;
  networkError: string;
  conversationNotFound: string;
  newConversationTitle: string;
};

const dictionaries: Record<Locale, Dictionary> = {
  'zh-CN': {
    currentAgent: '当前智能体',
    language: '会话语言',
    languageOptionZh: '中文',
    languageOptionEn: 'English',
    emptyState: '开始与 AI 助手对话',
    progressTrace: '多 agent 执行轨迹',
    send: '发送',
    placeholderReady: '输入消息（Enter 发送，Shift+Enter 换行）',
    placeholderStreaming: 'AI 正在回复中...',
    validationEmpty: '消息内容不能为空',
    validationTooLong: (length) => `消息不能超过4000个字符（当前${length}个）`,
    networkError: '网络连接失败，请检查网络后重试',
    conversationNotFound: '未找到当前会话',
    newConversationTitle: '新对话',
  },
  'en-US': {
    currentAgent: 'Current agent',
    language: 'Conversation language',
    languageOptionZh: '中文',
    languageOptionEn: 'English',
    emptyState: 'Start chatting with the AI assistant',
    progressTrace: 'Multi-agent execution trace',
    send: 'Send',
    placeholderReady: 'Type a message (Enter to send, Shift+Enter for a new line)',
    placeholderStreaming: 'AI is responding...',
    validationEmpty: 'Message content cannot be empty.',
    validationTooLong: (length) => `Messages cannot exceed 4000 characters (current: ${length}).`,
    networkError: 'Network connection failed. Please check your connection and try again.',
    conversationNotFound: 'The current conversation could not be found.',
    newConversationTitle: 'New Conversation',
  },
};

export const DEFAULT_LOCALE: Locale = 'zh-CN';

export function normalizeLocale(locale?: string | null): Locale {
  if (!locale) return DEFAULT_LOCALE;
  const normalized = locale.toLowerCase();
  if (normalized.startsWith('en')) return 'en-US';
  if (normalized.startsWith('zh')) return 'zh-CN';
  return DEFAULT_LOCALE;
}

export function detectBrowserLocale(): Locale {
  if (typeof window === 'undefined') return DEFAULT_LOCALE;

  const candidates = [
    ...((navigator.languages ?? []) as string[]),
    navigator.language,
  ].filter(Boolean);

  for (const candidate of candidates) {
    const resolved = normalizeLocale(candidate);
    if (resolved === 'en-US' || resolved === 'zh-CN') {
      return resolved;
    }
  }

  return DEFAULT_LOCALE;
}

export function t(locale: Locale): Dictionary {
  return dictionaries[normalizeLocale(locale)];
}

export function getDisclaimer(locale: Locale): string {
  return locale === 'en-US'
    ? 'This content is for auxiliary reference only and does not constitute medical diagnosis or treatment advice. Please follow a licensed physician\'s guidance.'
    : '本内容仅供辅助参考，不构成医疗诊断或治疗建议，请遵医嘱。';
}

export const localeOptions: Array<{ value: Locale; label: string }> = [
  { value: 'zh-CN', label: '中文' },
  { value: 'en-US', label: 'English' },
];
