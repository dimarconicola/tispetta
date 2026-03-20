import { APP_VERSION_LABEL, BUILD_DEPLOYMENT_ID, BUILD_UPDATED_AT } from '@/lib/env';
import type { ApiHealthSummary } from '@/lib/types';

type BuildFooterProps = {
  variant?: 'app' | 'marketing';
  apiHealth?: ApiHealthSummary | null;
};

function formatUpdatedAt(value: string | undefined, fallbackLabel = 'n/d') {
  if (!value) {
    return {
      label: fallbackLabel,
      title: 'timestamp di build non disponibile in questo ambiente',
    };
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return {
      label: value,
      title: value,
    };
  }

  return {
    label: new Intl.DateTimeFormat('it-IT', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      timeZone: 'Europe/Rome',
    }).format(date),
    title: date.toISOString(),
  };
}

export function BuildFooter({ variant = 'app', apiHealth }: BuildFooterProps) {
  const updated = formatUpdatedAt(BUILD_UPDATED_AT);
  const apiUpdated = formatUpdatedAt(apiHealth?.updated_at ?? undefined, 'n/d');
  const deploymentLabel = BUILD_DEPLOYMENT_ID ? BUILD_DEPLOYMENT_ID.slice(-8) : null;
  const apiVersionLabel = apiHealth?.version?.trim() || 'n/d';
  const apiDeploymentLabel = apiHealth?.deployment_id?.trim() || null;

  return (
    <footer className={`build-footer build-footer-${variant}`}>
      <div className="build-footer__inner">
        <div className="build-footer__lead">
          <span className="build-footer__eyebrow">{variant === 'marketing' ? 'Marketing host' : 'App host'}</span>
          <p className="build-footer__summary">Questa istanza mostra il build live attualmente in produzione.</p>
        </div>
        <div className="build-footer__meta" aria-label="Metadata di versione live">
          <span className="build-footer__item" title={APP_VERSION_LABEL}>
            <span className="build-footer__label">Web</span>
            <strong>v{APP_VERSION_LABEL}</strong>
          </span>
          <span className="build-footer__dot" aria-hidden="true">
            |
          </span>
          <span className="build-footer__item" title={apiVersionLabel}>
            <span className="build-footer__label">API</span>
            <strong>v{apiVersionLabel}</strong>
          </span>
          <span className="build-footer__dot" aria-hidden="true">
            |
          </span>
          <span className="build-footer__item" title={updated.title}>
            <span className="build-footer__label">Web aggiornata</span>
            <strong>{updated.label}</strong>
          </span>
          <span className="build-footer__dot" aria-hidden="true">
            |
          </span>
          <span className="build-footer__item" title={apiUpdated.title}>
            <span className="build-footer__label">API aggiornata</span>
            <strong>{apiUpdated.label}</strong>
          </span>
          {deploymentLabel ? (
            <>
              <span className="build-footer__dot" aria-hidden="true">
                |
              </span>
              <span className="build-footer__item" title={BUILD_DEPLOYMENT_ID ?? undefined}>
                <span className="build-footer__label">Web deploy</span>
                <strong>{deploymentLabel}</strong>
              </span>
            </>
          ) : null}
          {apiDeploymentLabel ? (
            <>
              <span className="build-footer__dot" aria-hidden="true">
                |
              </span>
              <span className="build-footer__item" title={apiHealth?.deployment_id ?? undefined}>
                <span className="build-footer__label">API deploy</span>
                <strong>{apiDeploymentLabel}</strong>
              </span>
            </>
          ) : null}
        </div>
      </div>
    </footer>
  );
}
