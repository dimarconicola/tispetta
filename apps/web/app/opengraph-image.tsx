import { ImageResponse } from 'next/og';

export const alt = 'Tispetta';
export const size = {
  width: 1200,
  height: 630,
};
export const contentType = 'image/png';

export default function OpenGraphImage() {
  return new ImageResponse(
    (
      <div
        style={{
          display: 'flex',
          width: '100%',
          height: '100%',
          padding: '64px',
          background:
            'radial-gradient(circle at top left, rgba(211,163,74,0.24), transparent 26%), radial-gradient(circle at 82% 12%, rgba(199,92,47,0.22), transparent 28%), linear-gradient(180deg, #f7f1e6 0%, #efe6d4 100%)',
          color: '#12211c',
          fontFamily: 'Georgia',
        }}
      >
        <div
          style={{
            display: 'flex',
            width: '100%',
            borderRadius: 36,
            border: '1px solid rgba(18,33,28,0.12)',
            background: 'rgba(255,252,245,0.86)',
            boxShadow: '0 24px 70px rgba(30,39,32,0.12)',
            padding: '54px 56px',
            justifyContent: 'space-between',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', maxWidth: 620 }}>
            <div
              style={{
                display: 'flex',
                fontSize: 26,
                letterSpacing: '0.22em',
                textTransform: 'uppercase',
                color: '#c75c2f',
                marginBottom: 24,
              }}
            >
              Italy-first opportunity intelligence
            </div>
            <div style={{ display: 'flex', fontSize: 110, fontWeight: 700, lineHeight: 0.92, marginBottom: 28 }}>
              Tispetta
            </div>
            <div style={{ display: 'flex', fontSize: 42, lineHeight: 1.2, color: '#2c3a33' }}>
              Fonti ufficiali, regole verificabili, opportunita leggibili per startup, freelance e PMI in Italia.
            </div>
          </div>
          <div
            style={{
              display: 'flex',
              width: 290,
              flexDirection: 'column',
              justifyContent: 'space-between',
              alignItems: 'stretch',
            }}
          >
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 18,
                borderRadius: 30,
                background: '#12211c',
                color: '#f5efe2',
                padding: '30px 28px',
              }}
            >
              <div style={{ display: 'flex', fontSize: 22, letterSpacing: '0.18em', textTransform: 'uppercase', color: '#f4c7a4' }}>
                Match spiegati
              </div>
              <div style={{ display: 'flex', fontSize: 62, fontWeight: 700 }}>42</div>
              <div style={{ display: 'flex', fontSize: 28, lineHeight: 1.25 }}>
                opportunita pubbliche gia strutturate dal corpus nazionale ufficiale.
              </div>
            </div>
            <div
              style={{
                display: 'flex',
                alignSelf: 'flex-end',
                padding: '14px 22px',
                borderRadius: 999,
                border: '1px solid rgba(18,33,28,0.14)',
                background: 'rgba(255,255,255,0.72)',
                fontSize: 26,
              }}
            >
              app.tispetta.eu
            </div>
          </div>
        </div>
      </div>
    ),
    size,
  );
}
