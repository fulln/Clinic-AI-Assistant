export type UserRole = 'doctor' | 'staff' | 'admin';

export interface User {
  id: string;
  username: string;
  role: UserRole;
  displayName: string;
}
