import { MagicLinkForm } from '@/components/magic-link-form';

export default function SignInPage() {
  return (
    <section className="split">
      <MagicLinkForm />
      <div className="panel stack">
        <p className="eyebrow">Suggerimento locale</p>
        <h2 style={{ fontSize: '2.4rem' }}>Usa gli account seed per vedere subito il prodotto</h2>
        <ul className="list-reset stack subtle">
          <li>`demo@benefits.local` per il percorso utente</li>
          <li>`admin@benefits.local` per il pannello operatore</li>
          <li>Mailpit: `http://localhost:8025` per controllare le email locali</li>
        </ul>
      </div>
    </section>
  );
}
