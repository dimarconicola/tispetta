'use client';

import { useState, useTransition } from 'react';

import type { AdminDocument } from '@/lib/types';

const API_URL = '/api/proxy';

export function DocumentReviewForm({ document: item }: { document: AdminDocument }) {
  const [message, setMessage] = useState<string | null>(null);
  const [isPending, startTransition] = useTransition();

  return (
    <div className="stack" style={{ minWidth: '18rem' }}>
      <label className="field">
        <span>Ruolo documento</span>
        <input id={`role-${item.id}`} defaultValue={item.document_role} placeholder="operator_measure_page" />
      </label>
      <label className="field">
        <span>Lifecycle</span>
        <input id={`lifecycle-${item.id}`} defaultValue={item.lifecycle_status} placeholder="open_application" />
      </label>
      <label className="field">
        <span>Famiglia misura</span>
        <input id={`family-${item.id}`} defaultValue={item.family_slug === 'unlinked' ? '' : item.family_slug} placeholder="smart_start_italia" />
      </label>
      <label className="field">
        <span>Relazione</span>
        <input id={`relationship-${item.id}`} defaultValue={item.relationship_type} placeholder="primary_operational" />
      </label>
      <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input id={`legal-${item.id}`} type="checkbox" defaultChecked={item.is_primary_legal_basis} />
        <span>Base legale primaria</span>
      </label>
      <label style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input id={`operational-${item.id}`} type="checkbox" defaultChecked={item.is_primary_operational_doc} />
        <span>Doc operativo primario</span>
      </label>
      <div style={{ display: 'flex', gap: '0.8rem', flexWrap: 'wrap' }}>
        <button
          className="button"
          type="button"
          disabled={isPending}
          onClick={() => {
            startTransition(async () => {
              setMessage(null);
              const response = await fetch(`${API_URL}/v1/admin/documents/${item.id}/review`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                  document_role: (window.document.getElementById(`role-${item.id}`) as HTMLInputElement | null)?.value ?? item.document_role,
                  lifecycle_status: (window.document.getElementById(`lifecycle-${item.id}`) as HTMLInputElement | null)?.value ?? item.lifecycle_status,
                  family_slug: (window.document.getElementById(`family-${item.id}`) as HTMLInputElement | null)?.value || null,
                  relationship_type: (window.document.getElementById(`relationship-${item.id}`) as HTMLInputElement | null)?.value || null,
                  is_primary_legal_basis: (window.document.getElementById(`legal-${item.id}`) as HTMLInputElement | null)?.checked ?? false,
                  is_primary_operational_doc: (window.document.getElementById(`operational-${item.id}`) as HTMLInputElement | null)?.checked ?? false,
                }),
              });
              setMessage(response.ok ? 'Revisione salvata.' : 'Salvataggio non riuscito.');
            });
          }}
        >
          {isPending ? 'Salvataggio...' : 'Salva revisione'}
        </button>
        <button
          className="button-secondary"
          type="button"
          disabled={isPending}
          onClick={() => {
            startTransition(async () => {
              setMessage(null);
              const response = await fetch(`${API_URL}/v1/admin/documents/${item.id}/review`, {
                method: 'POST',
                credentials: 'include',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ mark_irrelevant: true }),
              });
              setMessage(response.ok ? 'Documento segnato come irrilevante.' : 'Azione non riuscita.');
            });
          }}
        >
          Segna irrilevante
        </button>
      </div>
      {message ? <small className="subtle">{message}</small> : null}
    </div>
  );
}
