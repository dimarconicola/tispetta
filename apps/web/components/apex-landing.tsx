'use client';

import { motion } from 'motion/react';
import { ArrowRight } from 'lucide-react';
import Image from 'next/image';

type ApexLandingProps = {
  appBaseUrl: string;
};

export function ApexLanding({ appBaseUrl }: ApexLandingProps) {
  const catalogUrl = `${appBaseUrl}/search`;
  const startUrl = `${appBaseUrl}/start`;

  return (
    <div className="landing-page w-full bg-[var(--color-gray-950-ink)]">
      <nav className="absolute inset-x-0 top-0 z-50 text-[var(--color-gray-50-ivory)]">
        <div className="mx-auto flex h-24 max-w-7xl items-center justify-between px-6">
          <div className="text-lg font-medium tracking-tight">Tispetta</div>
          <div className="hidden items-center gap-8 text-sm font-medium md:flex">
            <a href="#metodo" className="transition-colors hover:text-[var(--color-gray-400)]">Metodo</a>
            <a href="#copertura" className="transition-colors hover:text-[var(--color-gray-400)]">Copertura</a>
            <a href="#storie" className="transition-colors hover:text-[var(--color-gray-400)]">Storie</a>
          </div>
          <div className="flex items-center gap-6">
            <a href={catalogUrl} className="hidden text-sm font-medium transition-colors hover:text-[var(--color-gray-400)] md:block">
              Catalogo
            </a>
            <a
              href={startUrl}
              className="rounded-sm bg-[#fafaf9] px-4 py-2 text-sm font-medium text-[#0f0e0d] transition-opacity hover:opacity-90"
            >
              Inizia guidato
            </a>
          </div>
        </div>
      </nav>

      <section className="theme-black relative flex min-h-screen flex-col items-center justify-end overflow-hidden bg-[var(--background-primary)] px-0 pb-24 pt-32 text-[var(--text-primary)] md:pb-32">
        <div className="absolute inset-0 z-0 bg-[var(--color-gray-950-ink)]">
          <video
            autoPlay
            loop
            muted
            playsInline
            poster="https://images.pexels.com/photos/3205567/pexels-photo-3205567.jpeg"
            className="absolute inset-0 h-full w-full object-cover mix-blend-lighten opacity-60"
          >
            <source src="https://www.pexels.com/download/video/3198252/" type="video/mp4" />
          </video>
          <div className="absolute inset-0 bg-gradient-to-t from-[var(--background-primary)] via-[var(--background-primary)]/60 to-transparent" />
        </div>

        <div className="relative z-10 mx-auto w-full max-w-7xl px-6">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
            className="text-5xl font-medium leading-[1.05] tracking-tight md:text-6xl lg:text-[5.5rem]"
          >
            Incentivi italiani.
            <br />
            <span className="text-[var(--text-muted)]">Letti come un prodotto.</span>
          </motion.h1>

          <div className="mt-12 flex flex-col justify-between gap-10 md:mt-16 md:flex-row md:items-end">
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
              className="max-w-md text-base font-light leading-relaxed text-[var(--text-secondary)] md:text-lg"
            >
              Tispetta legge norme, decreti e circolari e le trasforma in opportunita strutturate, criteri espliciti e match spiegabili.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
              className="flex shrink-0 flex-col items-center gap-3 sm:flex-row"
            >
              <a
                href={startUrl}
                className="flex w-full items-center justify-center rounded-sm bg-[#fafaf9] px-5 py-2.5 text-sm font-medium text-[#0f0e0d] transition-opacity hover:opacity-90 sm:w-auto"
              >
                Inizia dal profilo guidato
              </a>
              <a
                href={catalogUrl}
                className="flex w-full items-center justify-center gap-2 rounded-sm border border-[var(--border-secondary)] px-5 py-2.5 text-sm font-medium text-[var(--text-primary)] transition-colors hover:bg-[var(--background-secondary)] sm:w-auto"
              >
                Esplora il catalogo <ArrowRight className="h-4 w-4" />
              </a>
            </motion.div>
          </div>
        </div>
      </section>

      <section id="metodo" className="theme-light bg-[var(--background-primary)] py-24 text-[var(--text-primary)] md:py-32">
        <div className="mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 gap-16 lg:grid-cols-2 lg:gap-24">
            <div>
              <h2 className="text-4xl font-medium leading-[1.05] tracking-tight md:text-5xl lg:sticky lg:top-32 lg:text-6xl">
                Non un motore di ricerca di bandi.
              </h2>
            </div>

            <div className="flex flex-col gap-12">
              <p className="mb-4 text-lg font-light leading-relaxed text-[var(--text-secondary)] md:text-xl">
                Il punto non e trovare piu pagine. Il punto e capire prima cosa e vivo, cosa richiede stato societario, cosa dipende da un progetto e cosa resta ambiguo.
              </p>

              {[
                {
                  title: 'Analisi Normativa',
                  desc: 'Decodifichiamo il linguaggio burocratico in criteri binari e requisiti chiari.',
                },
                {
                  title: 'Matching Intelligente',
                  desc: 'Incrociamo il tuo profilo con migliaia di agevolazioni per trovare solo quelle rilevanti.',
                },
                {
                  title: 'Dati Strutturati',
                  desc: 'Ogni opportunita e scomposta in scadenze, importi e requisiti verificabili.',
                },
              ].map((feature, index) => (
                <div key={feature.title} className="flex flex-col gap-3 border-t border-[var(--border-primary)] pt-6">
                  <div className="text-xs font-medium text-[var(--text-muted)]">0{index + 1}</div>
                  <h3 className="text-xl font-medium tracking-tight md:text-2xl">{feature.title}</h3>
                  <p className="text-base font-light leading-relaxed text-[var(--text-secondary)]">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section id="storie" className="theme-black relative overflow-hidden bg-[var(--background-primary)] py-24 text-[var(--text-primary)] md:py-32">
        <div className="absolute inset-0 z-0 bg-[var(--color-gray-950-ink)]">
          <video
            autoPlay
            loop
            muted
            playsInline
            poster="https://images.pexels.com/photos/3205567/pexels-photo-3205567.jpeg"
            className="absolute inset-0 h-full w-full object-cover grayscale mix-blend-lighten opacity-40"
          >
            <source src="https://assets.codepen.io/3364143/7btrrd.mp4" type="video/mp4" />
            <source src="https://assets.mixkit.co/videos/preview/mixkit-ink-swirling-in-water-2226-large.mp4" type="video/mp4" />
          </video>
          <div className="absolute inset-0 bg-[var(--background-primary)]/70" />
        </div>

        <div className="relative z-10 mx-auto max-w-7xl px-6">
          <div className="grid grid-cols-1 items-center gap-16 lg:grid-cols-2 lg:gap-24">
            <div className="order-2 lg:order-1">
              <h2 className="mb-8 text-xs font-medium uppercase tracking-widest text-[var(--text-muted)]">Real impact for real clients</h2>
              <h3 className="mb-10 text-2xl font-medium leading-[1.2] tracking-tight md:text-3xl lg:text-4xl">
                &quot;Tispetta ha trasformato il modo in cui identifichiamo gli incentivi. Quello che prima richiedeva settimane di studio normativo, ora e immediato e strutturato.&quot;
              </h3>
              <div className="mb-12 flex flex-col gap-1">
                <span className="text-base font-medium">Marco Rossi</span>
                <span className="text-sm font-light text-[var(--text-secondary)]">CFO, Nexus Industries</span>
              </div>
              <div className="grid grid-cols-2 gap-8 border-t border-[var(--border-primary)] pt-8">
                <div>
                  <div className="mb-2 text-3xl font-medium tracking-tight md:text-4xl">300%</div>
                  <div className="text-xs font-light text-[var(--text-secondary)]">Aumento incentivi rilevati</div>
                </div>
                <div>
                  <div className="mb-2 text-3xl font-medium tracking-tight md:text-4xl">40h</div>
                  <div className="text-xs font-light text-[var(--text-secondary)]">Risparmiate al mese</div>
                </div>
              </div>
            </div>
            <div className="order-1 lg:order-2">
              <Image
                src="https://images.pexels.com/photos/3205567/pexels-photo-3205567.jpeg"
                alt="Couple portrait"
                width={960}
                height={1200}
                unoptimized
                className="aspect-[4/5] w-full rounded-sm object-cover grayscale opacity-80"
              />
            </div>
          </div>
        </div>
      </section>

      <section className="theme-light bg-[var(--background-primary)] py-24 text-[var(--text-primary)] md:py-32">
        <div className="mx-auto max-w-7xl px-6">
          <div className="mb-16 grid grid-cols-1 gap-16 lg:grid-cols-2 lg:gap-24">
            <div>
              <h2 className="text-4xl font-medium leading-[1.05] tracking-tight md:text-5xl lg:text-6xl">
                Dal sito entri in un percorso guidato, non in un form generico.
              </h2>
            </div>
            <div className="flex items-end">
              <p className="text-lg font-light leading-relaxed text-[var(--text-secondary)] md:text-xl">
                Parti sempre da te. Chiudi il profilo personale, vedi subito i primi match e aggiungi l&apos;attivita solo se esiste davvero.
              </p>
            </div>
          </div>

          <div className="group relative flex aspect-video w-full cursor-pointer items-center justify-center overflow-hidden rounded-sm bg-[var(--color-gray-900)]">
            <video
              autoPlay
              loop
              muted
              playsInline
              poster="https://images.pexels.com/photos/3205567/pexels-photo-3205567.jpeg"
              className="absolute inset-0 h-full w-full object-cover opacity-50 transition-opacity duration-700 group-hover:opacity-40"
              src="https://www.pexels.com/download/video/4065921/"
            />
            <div className="z-10 flex h-16 w-16 items-center justify-center rounded-full border border-[var(--color-gray-50-ivory)]/20 bg-[var(--color-gray-50-ivory)]/10 backdrop-blur-md transition-transform duration-500 group-hover:scale-110">
              <div className="ml-1 h-0 w-0 border-y-[8px] border-y-transparent border-l-[12px] border-l-[var(--color-gray-50-ivory)]" />
            </div>
          </div>
        </div>
      </section>

      <section id="copertura" className="theme-black relative overflow-hidden border-t border-[var(--border-primary)] bg-[var(--background-primary)] py-24 text-[var(--text-primary)] md:py-32">
        <div className="absolute inset-0 z-0 bg-[var(--color-gray-950-ink)]">
          <video
            autoPlay
            loop
            muted
            playsInline
            poster="https://images.pexels.com/photos/3205567/pexels-photo-3205567.jpeg"
            className="absolute inset-0 h-full w-full object-cover grayscale mix-blend-lighten opacity-40"
          >
            <source src="https://assets.codepen.io/3364143/7btrrd.mp4" type="video/mp4" />
            <source src="https://assets.mixkit.co/videos/preview/mixkit-ink-swirling-in-water-2226-large.mp4" type="video/mp4" />
          </video>
          <div className="absolute inset-0 bg-[var(--background-primary)]/70" />
        </div>

        <div className="relative z-10 mx-auto max-w-7xl px-6">
          <div className="mb-16">
            <h2 className="max-w-3xl text-4xl font-medium leading-[1.05] tracking-tight md:text-5xl lg:text-6xl">
              Copertura totale del panorama italiano.
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-px bg-[var(--border-primary)] md:grid-cols-3">
            {[
              { value: '100%', label: 'Regioni coperte' },
              { value: '24/7', label: 'Aggiornamento dati' },
              { value: '5k+', label: 'Agevolazioni analizzate' },
            ].map((stat) => (
              <div key={stat.label} className="flex flex-col items-center justify-center bg-[var(--background-primary)] px-8 py-12 text-center">
                <div className="mb-3 text-5xl font-medium tracking-tight md:text-6xl">{stat.value}</div>
                <div className="text-sm font-light text-[var(--text-secondary)]">{stat.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      <footer className="theme-black border-t border-[var(--border-primary)] bg-[var(--background-primary)] py-10 text-[var(--text-primary)]">
        <div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-6 px-6 md:flex-row">
          <div className="text-lg font-medium tracking-tight">Tispetta</div>
          <div className="flex flex-wrap items-center gap-6 text-xs font-light text-[var(--text-muted)]">
            <a href="#" className="transition-colors hover:text-[var(--text-primary)]">Privacy Policy</a>
            <a href="#" className="transition-colors hover:text-[var(--text-primary)]">Terms of Service</a>
            <span>© {new Date().getFullYear()} Tispetta. All rights reserved.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
