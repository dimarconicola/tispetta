import { redirect } from 'next/navigation';

import { RuleTestRunner } from '@/components/rule-test-runner';
import { getAdminRules, getSessionUser } from '@/lib/server-api';

export default async function AdminRulesPage() {
  const user = await getSessionUser().catch(() => null);
  if (!user) redirect('/auth/sign-in');
  if (user.role !== 'admin') redirect('/');

  const rules = await getAdminRules().catch(() => []);

  return (
    <div className="stack">
      <section className="panel stack">
        <p className="eyebrow">Admin</p>
        <h1 style={{ fontSize: '3rem' }}>Regole e fixture</h1>
        <p className="subtle">Ogni opportunita pubblica deve avere almeno una regola attiva e fixture passanti.</p>
      </section>
      <div className="grid cards-2">
        {rules.map((rule) => (
          <article className="card stack" key={rule.id}>
            <div>
              <p className="eyebrow">v{rule.version_number}</p>
              <h2 style={{ fontSize: '1.8rem' }}>{rule.opportunity_title}</h2>
            </div>
            <p className="subtle">{rule.note ?? 'Nessuna nota operativa.'}</p>
            <div className="meta-list">
              <span>Attiva: {rule.is_active ? 'si' : 'no'}</span>
              <span>Fixture: {rule.fixture_count}</span>
            </div>
            <RuleTestRunner ruleId={rule.id} />
          </article>
        ))}
      </div>
    </div>
  );
}
