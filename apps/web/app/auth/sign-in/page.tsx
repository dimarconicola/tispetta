import type { Metadata } from 'next';

import { MagicLinkForm } from '@/components/magic-link-form';

export const metadata: Metadata = {
  title: 'Accedi',
  description: 'Accedi a Tispetta con un magic link inviato alla tua email.',
  robots: {
    index: false,
    follow: false,
  },
};

export default function SignInPage() {
  const isLocalEnvironment = process.env.NODE_ENV !== 'production';

  return (
    <section className="split">
      <MagicLinkForm />
      <div className="panel stack">
        {isLocalEnvironment ? (
          <>
            <p className="eyebrow">Suggerimento locale</p>
            <h2 style={{ fontSize: '2.4rem' }}>Usa gli account seed per vedere subito il prodotto</h2>
            <ul className="list-reset stack subtle">
              <li>`demo@example.com` per il percorso utente</li>
              <li>`admin@example.com` per il pannello operatore</li>
              <li>Mailpit: `http://localhost:8025` per controllare le email locali</li>
            </ul>
          </>
        ) : (
          <>
            <p className="eyebrow">Produzione</p>
            <h2 style={{ fontSize: '2.4rem' }}>Il link arriva via email e scade in 30 minuti</h2>
            <div className="stack subtle">
              <p>Ogni accesso crea una sessione nuova sul dominio sicuro di Tispetta.</p>
              <p>Se non trovi il messaggio, controlla spam e promozioni prima di richiedere un secondo invio.</p>
            </div>
          </>
        )}
      </div>
    </section>
  );
}
