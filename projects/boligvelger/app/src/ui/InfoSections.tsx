import type { SiteConfig } from '../lib/types';

export function InfoSections({ site }: { site: SiteConfig }) {
  return (
    <>
      <section className="info">
        <h2>Om prosjektet</h2>
        <p>{site.ingress}</p>
      </section>
      <section className="info alt">
        <h2>Beliggenhet</h2>
        <p>Rolig boliggate ved Majorstuveien med kort gangavstand til Bogstadveien,
           Majorstuen stasjon og byens beste utvalg av kaféer og service.</p>
      </section>
      <section className="info">
        <h2>Kontakt</h2>
        <p>{site.kontakt.navn}<br />{site.kontakt.tittel}<br />
          <a href={`tel:${site.kontakt.telefon.replace(/ /g, '')}`}>{site.kontakt.telefon}</a> ·{' '}
          <a href={`mailto:${site.kontakt.epost}`}>{site.kontakt.epost}</a></p>
      </section>
    </>
  );
}
