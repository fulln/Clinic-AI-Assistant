export class ConversationDomainService {
  static validateMessageContent(content: string): string | null {
    if (!content.trim()) return '消息内容不能为空';
    if (content.length > 4000) return `消息不能超过4000个字符（当前${content.length}个）`;
    return null;
  }
}
