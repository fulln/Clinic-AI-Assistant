export class AuthDomainService {
  static validateUsername(username: string): string | null {
    if (!username.trim()) return '请输入用户名';
    if (username.trim().length < 3) return '用户名至少3个字符';
    return null;
  }

  static validatePassword(password: string): string | null {
    if (!password) return '请输入密码';
    return null;
  }
}
