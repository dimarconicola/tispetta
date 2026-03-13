'use client';

import { useState, useTransition } from 'react';

import type { RuleTestResult } from '@/lib/types';

const API_URL = '/api/proxy';

export function RuleTestRunner({ ruleId }: { ruleId: string }) {
  const [result, setResult] = useState<RuleTestResult | null>(null);
  const [isPending, startTransition] = useTransition();

  return (
    <div className="stack">
      <button
        type="button"
        className="button-secondary"
        disabled={isPending}
        onClick={() => {
          startTransition(async () => {
            const response = await fetch(`${API_URL}/v1/admin/rules/${ruleId}/test`, {
              method: 'POST',
              credentials: 'include',
            });
            if (response.ok) {
              setResult((await response.json()) as RuleTestResult);
            }
          });
        }}
      >
        {isPending ? 'Esecuzione test...' : 'Esegui fixture'}
      </button>
      {result ? (
        <div className="banner">
          <strong>{result.passed ? 'Tutti i test superati' : 'Fixture con errori'}</strong>
          <ul className="list-reset stack" style={{ marginTop: '0.8rem' }}>
            {result.results.map((item) => (
              <li key={item.case_id}>
                {item.name}: atteso {item.expected_status}, ottenuto {item.actual_status}
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
