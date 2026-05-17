import type { Agent } from './entities';

export class AgentDomainService {
  static filterByRole(agents: Agent[], role: string): Agent[] {
    return agents.filter(a => a.allowedRoles.includes(role) || role === 'admin');
  }

  static isDemo(agent: Agent): boolean {
    return agent.agentType === 'demo';
  }
}
