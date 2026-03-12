from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.matching.service import evaluate_profile_against_catalog
from app.models import (
    IngestionRun,
    Opportunity,
    OpportunityRule,
    OpportunityType,
    OpportunityVersion,
    Profile,
    RecordStatus,
    ReviewItem,
    ReviewItemType,
    RuleTestCase,
    Source,
    SourceEndpoint,
    User,
    VerificationStatus,
)
from app.services.auth import get_or_create_user
from app.services.profile import get_or_create_profile, update_profile
from app.schemas.profile import ProfilePayload


@dataclass(frozen=True)
class OpportunitySeed:
    title: str
    issuer_name: str
    category: str
    opportunity_type: str
    benefit_type: str
    user_types: list[str]
    size_constraints: list[str] | None
    sectors: list[str] | None
    goals: list[str]
    requires_business: bool | None = True
    company_age_band: list[str] | None = None
    value: float | None = None
    funding_rate: float | None = None
    deadline_days: int = 90
    short_description: str = ''
    long_description: str = ''
    official_link: str = ''
    source_document: str = ''


SOURCE_SPECS = [
    {
        'name': 'Invitalia',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'daily',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.invitalia.it/',
    },
    {
        'name': 'Ministero delle Imprese e del Made in Italy',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'daily',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.mimit.gov.it/',
    },
    {
        'name': 'SIMEST',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'daily',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.simest.it/',
    },
    {
        'name': 'Unioncamere',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'weekly',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.unioncamere.gov.it/',
    },
    {
        'name': 'Agenzia delle Entrate',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'daily',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.agenziaentrate.gov.it/',
    },
    {
        'name': 'Ministero dell’Ambiente e della Sicurezza Energetica',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'daily',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.mase.gov.it/',
    },
]


OPPORTUNITY_SEEDS: list[OpportunitySeed] = [
    OpportunitySeed('Voucher Transizione Digitale PMI', 'Ministero delle Imprese e del Made in Italy', 'digitization_incentive', OpportunityType.DIGITIZATION.value, 'voucher software e processi digitali', ['sme', 'startup'], ['micro', 'small', 'medium'], ['digitale', 'servizi', 'manifattura'], ['digitalizzazione'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 50000, 0.5, 120, 'Supporto per software, servizi cloud e integrazione dei processi aziendali.', 'Misura dedicata a PMI e startup con progetti di modernizzazione digitale e miglioramento dei processi.', 'https://www.mimit.gov.it/', 'https://www.mimit.gov.it/it/incentivi'),
    OpportunitySeed('Credito d’Imposta Formazione 4.0', 'Agenzia delle Entrate', 'training_incentive', OpportunityType.TRAINING.value, 'credito d’imposta sulla formazione', ['sme', 'startup'], ['micro', 'small', 'medium'], ['digitale', 'manifattura', 'servizi'], ['formazione', 'innovazione'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 35000, 0.45, 180, 'Agevolazione fiscale per percorsi di aggiornamento sulle tecnologie abilitanti.', 'Rivolta a imprese che investono in formazione qualificata per processi 4.0 e riqualificazione del personale.', 'https://www.agenziaentrate.gov.it/', 'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni'),
    OpportunitySeed('Fondo Nuove Competenze Startup Team', 'Invitalia', 'training_incentive', OpportunityType.TRAINING.value, 'contributo per piani di upskilling', ['startup', 'sme'], ['micro', 'small', 'medium'], ['digitale', 'servizi'], ['formazione', 'innovazione'], True, ['0-12m', '1-3y'], 40000, 0.7, 75, 'Contributo per piani di reskilling orientati alla crescita digitale del team.', 'La misura sostiene la formazione di team startup e PMI su competenze digitali, prodotto e crescita.', 'https://www.invitalia.it/', 'https://www.invitalia.it/cosa-facciamo/nuove-imprese'),
    OpportunitySeed('Incentivo Assunzioni Giovani Innovazione', 'Ministero delle Imprese e del Made in Italy', 'hiring_incentive', OpportunityType.HIRING_INCENTIVE.value, 'esonero contributivo assunzioni', ['startup', 'sme'], ['micro', 'small', 'medium'], None, ['hiring'], True, ['0-12m', '1-3y', '3-5y'], 24000, 0.6, 45, 'Riduzione del costo del lavoro per nuove assunzioni qualificate in ambiti innovativi.', 'Utile per imprese che vogliono ampliare il team tecnico o commerciale con nuove competenze.', 'https://www.mimit.gov.it/', 'https://www.mimit.gov.it/it/incentivi/assunzioni'),
    OpportunitySeed('Smart & Start Italia Seed', 'Invitalia', 'grants', OpportunityType.GRANT.value, 'finanziamento agevolato startup innovative', ['startup'], ['micro', 'small'], ['digitale', 'agritech', 'energia', 'servizi'], ['innovazione'], False, ['idea', '0-12m', '1-3y'], 1000000, 0.8, 150, 'Sostegno a startup innovative con piani di investimento e crescita.', 'Pensato per team imprenditoriali innovativi con progetti scalabili o ad alto contenuto tecnologico.', 'https://www.invitalia.it/', 'https://www.invitalia.it/cosa-facciamo/creiamo-nuove-aziende/smart-start-italia'),
    OpportunitySeed('ON - Oltre Nuove Imprese a Tasso Zero', 'Invitalia', 'subsidized_loan', OpportunityType.SUBSIDIZED_LOAN.value, 'mutuo agevolato per nuove imprese', ['startup', 'sme'], ['micro', 'small'], ['servizi', 'turismo', 'manifattura', 'retail'], ['avvio'], False, ['idea', '0-12m'], 300000, 0.9, 110, 'Finanziamento a tasso zero per nuove iniziative imprenditoriali.', 'Supporta progetti in fase di avvio, con particolare attenzione a imprese giovani e femminili.', 'https://www.invitalia.it/', 'https://www.invitalia.it/cosa-facciamo/creiamo-nuove-aziende/oltre-nuove-imprese-a-tasso-zero'),
    OpportunitySeed('Fondo Impresa Femminile Digitale', 'Invitalia', 'grants', OpportunityType.GRANT.value, 'contributo a fondo perduto per imprese femminili', ['startup', 'sme', 'freelancer'], ['solo', 'micro', 'small'], ['digitale', 'servizi', 'retail'], ['digitalizzazione', 'avvio'], False, ['idea', '0-12m', '1-3y'], 100000, 0.8, 95, 'Sostegno a imprese o iniziative guidate da donne con focus su digitale e crescita.', 'La misura puo essere utilizzata per avvio, consolidamento e trasformazione digitale.', 'https://www.invitalia.it/', 'https://www.invitalia.it/cosa-facciamo/imprenditorialita-femminile'),
    OpportunitySeed('Bando Efficienza Energetica PMI', 'Ministero dell’Ambiente e della Sicurezza Energetica', 'sustainability_incentive', OpportunityType.SUSTAINABILITY.value, 'contributo per efficientamento', ['sme', 'startup'], ['micro', 'small', 'medium'], ['manifattura', 'energia', 'servizi'], ['sostenibilita'], True, ['1-3y', '3-5y', '5y+'], 250000, 0.65, 130, 'Aiuti per impianti, consumi e retrofit energetico.', 'Pensato per imprese che riducono costi energetici e emissioni attraverso investimenti qualificati.', 'https://www.mase.gov.it/', 'https://www.mase.gov.it/energia/incentivi'),
    OpportunitySeed('SIMEST Fiere Internazionali', 'SIMEST', 'export_incentive', OpportunityType.EXPORT.value, 'finanziamento per fiere ed eventi internazionali', ['sme', 'startup'], ['micro', 'small', 'medium'], None, ['export'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 150000, 0.7, 60, 'Supporto per partecipare a fiere, missioni e eventi internazionali.', 'Adatto a imprese che stanno aprendo o consolidando canali esteri.', 'https://www.simest.it/', 'https://www.simest.it/agevolazioni/partecipazione-fiere'),
    OpportunitySeed('Voucher Export Digitale', 'Unioncamere', 'export_incentive', OpportunityType.EXPORT.value, 'voucher per marketing estero e canali digitali', ['sme', 'startup'], ['micro', 'small'], ['digitale', 'manifattura', 'turismo', 'retail'], ['export', 'digitalizzazione'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 20000, 0.5, 80, 'Voucher per consulenza, market entry e presenza digitale sui mercati esteri.', 'La misura aiuta imprese piccole a testare canali export senza struttura internazionale interna.', 'https://www.unioncamere.gov.it/', 'https://www.unioncamere.gov.it/internazionalizzazione'),
    OpportunitySeed('Credito Ricerca e Sviluppo Startup', 'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value, 'credito d’imposta su ricerca e sviluppo', ['startup', 'sme'], ['micro', 'small', 'medium'], ['digitale', 'agritech', 'energia', 'manifattura'], ['innovazione'], True, ['0-12m', '1-3y', '3-5y'], 180000, 0.3, 180, 'Credito fiscale per investimenti in attivita di R&D, prototipazione e sperimentazione.', 'Indicato per startup e PMI innovative che stanno costruendo un nuovo prodotto o processo.', 'https://www.agenziaentrate.gov.it/', 'https://www.agenziaentrate.gov.it/portale/credito-imposta-ricerca'),
    OpportunitySeed('Fondo Brevetti+ Innovazione', 'Ministero delle Imprese e del Made in Italy', 'grants', OpportunityType.GRANT.value, 'contributo per valorizzazione brevetti', ['startup', 'sme'], ['micro', 'small', 'medium'], ['digitale', 'manifattura', 'agritech', 'energia'], ['innovazione'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 140000, 0.8, 100, 'Aiuto per valorizzare, proteggere e industrializzare asset brevettuali.', 'Pensato per imprese con proprieta intellettuale e percorso chiaro di valorizzazione sul mercato.', 'https://www.mimit.gov.it/', 'https://www.mimit.gov.it/it/incentivi/brevetti'),
    OpportunitySeed('Transizione Ecologica Microimprese', 'Ministero dell’Ambiente e della Sicurezza Energetica', 'sustainability_incentive', OpportunityType.SUSTAINABILITY.value, 'voucher per audit e piccoli investimenti green', ['sme', 'freelancer'], ['solo', 'micro'], ['servizi', 'retail', 'turismo'], ['sostenibilita'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 12000, 0.5, 70, 'Supporto per audit energetici, strumenti di monitoraggio e piccole migliorie green.', 'Mirato a attivita di piccola dimensione che cercano interventi rapidi a basso CAPEX.', 'https://www.mase.gov.it/', 'https://www.mase.gov.it/energia/incentivi-imprese'),
    OpportunitySeed('Nuove Imprese Cultura e Turismo', 'Invitalia', 'grants', OpportunityType.GRANT.value, 'mix contributo e finanziamento per turismo e cultura', ['startup', 'sme', 'freelancer'], ['solo', 'micro', 'small'], ['turismo', 'servizi', 'retail'], ['avvio', 'digitalizzazione'], False, ['idea', '0-12m', '1-3y'], 180000, 0.85, 120, 'Misura per lanciare nuove iniziative nel turismo, hospitality e valorizzazione culturale.', 'Utile a team e microimprese che lavorano su prodotti turistici, esperienziali o culturali.', 'https://www.invitalia.it/', 'https://www.invitalia.it/cosa-facciamo/turismo'),
    OpportunitySeed('Sostegno Investimenti Sud PMI', 'Invitalia', 'grants', OpportunityType.GRANT.value, 'contributo per investimenti nel Mezzogiorno', ['startup', 'sme'], ['micro', 'small', 'medium'], ['manifattura', 'digitale', 'turismo', 'energia'], ['crescita'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 500000, 0.65, 115, 'Agevolazione per piani di sviluppo e consolidamento nelle regioni del Sud.', 'Si adatta a investimenti in capacità produttiva, tecnologia e crescita commerciale.', 'https://www.invitalia.it/', 'https://www.invitalia.it/cosa-facciamo/rafforziamo-le-imprese'),
    OpportunitySeed('Voucher Consulenza Innovazione', 'Ministero delle Imprese e del Made in Italy', 'digitization_incentive', OpportunityType.DIGITIZATION.value, 'voucher innovation manager', ['sme', 'startup'], ['micro', 'small', 'medium'], ['digitale', 'manifattura', 'servizi'], ['innovazione', 'digitalizzazione'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 40000, 0.5, 85, 'Supporto per consulenze specialistiche su trasformazione digitale e innovazione.', 'Ideale per imprese che non hanno ancora leadership digitale interna strutturata.', 'https://www.mimit.gov.it/', 'https://www.mimit.gov.it/it/incentivi/voucher-innovation-manager'),
    OpportunitySeed('Fondo Internazionalizzazione Micro PMI', 'SIMEST', 'export_incentive', OpportunityType.EXPORT.value, 'finanziamento agevolato internazionalizzazione', ['sme'], ['micro', 'small'], ['manifattura', 'servizi', 'retail'], ['export'], True, ['1-3y', '3-5y', '5y+'], 250000, 0.8, 95, 'Supporta l’apertura di canali commerciali esteri, temporary export manager e presidio mercati.', 'Pensato per imprese piccole che stanno passando da export opportunistico a export strutturato.', 'https://www.simest.it/', 'https://www.simest.it/agevolazioni/internazionalizzazione'),
    OpportunitySeed('Bonus Assunzioni Sud', 'Ministero delle Imprese e del Made in Italy', 'hiring_incentive', OpportunityType.HIRING_INCENTIVE.value, 'incentivo all’assunzione in aree prioritarie', ['startup', 'sme'], ['micro', 'small', 'medium'], None, ['hiring'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 30000, 0.65, 50, 'Riduzione del costo lavoro per imprese che assumono in aree del Mezzogiorno.', 'Ha maggiore rilevanza per imprese in espansione con nuovi fabbisogni operativi o commerciali.', 'https://www.mimit.gov.it/', 'https://www.mimit.gov.it/it/incentivi/mezzogiorno'),
    OpportunitySeed('Bando E-commerce per Artigiani', 'Unioncamere', 'digitization_incentive', OpportunityType.DIGITIZATION.value, 'voucher e-commerce e marketplace', ['sme', 'freelancer'], ['solo', 'micro', 'small'], ['retail', 'manifattura', 'turismo'], ['digitalizzazione'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 15000, 0.5, 65, 'Aiuti per e-commerce, fotografie prodotto, integrazione marketplace e CRM base.', 'Adatto a imprese artigiane e microattivita con vendita B2C o D2C.', 'https://www.unioncamere.gov.it/', 'https://www.unioncamere.gov.it/digitale'),
    OpportunitySeed('Fondo Competenze Green', 'Ministero dell’Ambiente e della Sicurezza Energetica', 'training_incentive', OpportunityType.TRAINING.value, 'contributo per formazione green e sostenibilita', ['sme', 'startup'], ['micro', 'small', 'medium'], ['energia', 'manifattura', 'servizi'], ['sostenibilita', 'formazione'], True, ['1-3y', '3-5y', '5y+'], 30000, 0.65, 100, 'Aiuto per aggiornare competenze su energy management, reporting ESG e riduzione sprechi.', 'Particolarmente rilevante per imprese che devono adeguare team e processi a nuovi requisiti green.', 'https://www.mase.gov.it/', 'https://www.mase.gov.it/formazione-green'),
    OpportunitySeed('Incentivi Autoimprenditorialita Freelance Tech', 'Invitalia', 'grants', OpportunityType.GRANT.value, 'contributo per avvio attivita professionale digitale', ['freelancer'], ['solo'], ['digitale', 'servizi'], ['avvio', 'digitalizzazione'], False, ['idea', '0-12m'], 10000, 0.75, 55, 'Sostegno leggero per l’avvio di attivita freelance in ambito tech e servizi digitali.', 'Pensato per profili individuali che stanno formalizzando una nuova attivita professionale.', 'https://www.invitalia.it/', 'https://www.invitalia.it/cosa-facciamo/autoimprenditorialita'),
    OpportunitySeed('Fondo Startup Deep Tech', 'Invitalia', 'grants', OpportunityType.GRANT.value, 'finanziamento per startup deep tech', ['startup'], ['micro', 'small'], ['digitale', 'energia', 'agritech', 'manifattura'], ['innovazione'], False, ['idea', '0-12m', '1-3y'], 1200000, 0.85, 140, 'Sostegno per progetti ad alta intensita tecnologica con percorsi di validazione e industrializzazione.', 'Rivolto a team con asset tecnologici forti e bisogno di capitale paziente.', 'https://www.invitalia.it/', 'https://www.invitalia.it/cosa-facciamo/startup'),
    OpportunitySeed('Contributo Transizione AI per PMI', 'Ministero delle Imprese e del Made in Italy', 'digitization_incentive', OpportunityType.DIGITIZATION.value, 'contributo per adozione AI', ['sme', 'startup'], ['micro', 'small', 'medium'], ['digitale', 'servizi', 'manifattura'], ['innovazione', 'digitalizzazione'], True, ['1-3y', '3-5y', '5y+'], 90000, 0.55, 125, 'Contributo per sperimentare soluzioni di AI su processi, supporto clienti e operations.', 'Indicato per imprese con use case applicativi chiari e volontà di industrializzare rapidamente.', 'https://www.mimit.gov.it/', 'https://www.mimit.gov.it/it/incentivi/ai'),
    OpportunitySeed('Voucher Cybersecurity PMI', 'Ministero delle Imprese e del Made in Italy', 'digitization_incentive', OpportunityType.DIGITIZATION.value, 'voucher audit e protezione cyber', ['sme', 'startup'], ['micro', 'small', 'medium'], ['digitale', 'servizi', 'manifattura', 'retail'], ['digitalizzazione'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 30000, 0.5, 75, 'Agevolazione per audit cyber, formazione e messa in sicurezza infrastrutturale.', 'Pensato per PMI che hanno accelerato il digitale ma hanno lacune su sicurezza e compliance.', 'https://www.mimit.gov.it/', 'https://www.mimit.gov.it/it/incentivi/cybersecurity'),
    OpportunitySeed('Export Lab Innovatori Italiani', 'SIMEST', 'export_incentive', OpportunityType.EXPORT.value, 'contributo consulenziale per mercati esteri', ['startup', 'sme', 'freelancer'], ['solo', 'micro', 'small', 'medium'], ['digitale', 'servizi', 'manifattura'], ['export'], True, ['0-12m', '1-3y', '3-5y', '5y+'], 18000, 0.55, 88, 'Percorso di accompagnamento e contributo per test commerciali e marketing internazionale.', 'Adatto a chi ha già una proposta vendibile e cerca i primi segnali di domanda fuori dall’Italia.', 'https://www.simest.it/', 'https://www.simest.it/export-lab'),
    OpportunitySeed('Bonus Startup Ricerca Collaborativa', 'Ministero delle Imprese e del Made in Italy', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value, 'credito d’imposta per progetti con universita e centri ricerca', ['startup'], ['micro', 'small'], ['digitale', 'energia', 'agritech'], ['innovazione'], True, ['0-12m', '1-3y'], 220000, 0.4, 135, 'Credito e contributo per collaborazioni di ricerca applicata.', 'Particolarmente utile per startup che devono validare tecnologia con partner istituzionali.', 'https://www.mimit.gov.it/', 'https://www.mimit.gov.it/it/incentivi/ricerca-collaborativa'),
]


def slugify(value: str) -> str:
    cleaned = (
        value.lower()
        .replace('&', ' e ')
        .replace('’', '')
        .replace("'", '')
        .replace(' - ', ' ')
    )
    for char in [',', '.', '/', '(', ')']:
        cleaned = cleaned.replace(char, ' ')
    return '-'.join(part for part in cleaned.split() if part)


def build_rule(seed: OpportunitySeed) -> dict[str, Any]:
    required: list[dict[str, Any]] = [{'in': {'field': 'user_type', 'value': seed.user_types}}]
    if seed.size_constraints:
        required.append({'in': {'field': 'company_size_band', 'value': seed.size_constraints}})
    if seed.sectors:
        required.append({'in': {'field': 'sector_code_or_category', 'value': seed.sectors}})
    if seed.requires_business is not None:
        required.append({'eq': {'field': 'business_exists', 'value': seed.requires_business}})
    if seed.company_age_band:
        required.append({'in': {'field': 'company_age_band', 'value': seed.company_age_band}})

    boosters: list[dict[str, Any]] = []
    if 'hiring' in seed.goals:
        boosters.append({'eq': {'field': 'hiring_intent', 'value': True}})
    if 'innovazione' in seed.goals:
        boosters.append({'eq': {'field': 'innovation_intent', 'value': True}})
    if 'digitalizzazione' in seed.goals:
        boosters.append({'in': {'field': 'sector_code_or_category', 'value': ['digitale', 'servizi', 'retail', 'manifattura']}})
    if 'sostenibilita' in seed.goals:
        boosters.append({'eq': {'field': 'sustainability_intent', 'value': True}})
    if 'export' in seed.goals:
        boosters.append({'eq': {'field': 'export_intent', 'value': True}})

    return {
        'required': required,
        'disqualifiers': [{'eq': {'field': 'user_type', 'value': 'advisor'}}],
        'boosters': boosters,
        'tolerated_missing': [
            {'missing': {'field': 'company_size_band'}},
            {'missing': {'field': 'company_age_band'}},
            {'missing': {'field': 'sector_code_or_category'}},
        ],
    }


def positive_profile(seed: OpportunitySeed) -> dict[str, Any]:
    return {
        'user_type': seed.user_types[0],
        'region': 'Lombardia',
        'business_exists': seed.requires_business if seed.requires_business is not None else False,
        'company_size_band': seed.size_constraints[0] if seed.size_constraints else 'micro',
        'company_age_band': seed.company_age_band[0] if seed.company_age_band else '1-3y',
        'sector_code_or_category': seed.sectors[0] if seed.sectors else 'servizi',
        'hiring_intent': 'hiring' in seed.goals,
        'innovation_intent': 'innovazione' in seed.goals,
        'sustainability_intent': 'sostenibilita' in seed.goals,
        'export_intent': 'export' in seed.goals,
    }


def negative_profile(seed: OpportunitySeed) -> dict[str, Any]:
    fallback_user_type = 'freelancer' if seed.user_types[0] != 'freelancer' else 'sme'
    payload = positive_profile(seed)
    payload['user_type'] = fallback_user_type
    return payload


def incomplete_profile(seed: OpportunitySeed) -> dict[str, Any]:
    payload = positive_profile(seed)
    payload['company_size_band'] = None
    payload['sector_code_or_category'] = None
    return payload


def get_or_create_source(db: Session, spec: dict[str, str]) -> Source:
    source = db.execute(select(Source).where(Source.source_name == spec['name'])).scalar_one_or_none()
    if source is None:
        source = Source(
            source_name=spec['name'],
            source_type=spec['source_type'],
            authority_level=spec['authority_level'],
            crawl_method=spec['crawl_method'],
            crawl_frequency=spec['crawl_frequency'],
            trust_level=spec['trust_level'],
            region=spec['region'],
            status='active',
        )
        db.add(source)
        db.flush()
        db.add(
            SourceEndpoint(
                source_id=source.id,
                name=f"{spec['name']} primary endpoint",
                url=spec['endpoint_url'],
                document_type='opportunity_page',
            )
        )
        db.commit()
        db.refresh(source)
    return source


def seed_sources(db: Session) -> dict[str, Source]:
    sources: dict[str, Source] = {}
    for spec in SOURCE_SPECS:
        source = get_or_create_source(db, spec)
        sources[source.source_name] = source
    return sources


def seed_catalog(db: Session) -> None:
    sources = seed_sources(db)
    for index, seed in enumerate(OPPORTUNITY_SEEDS, start=1):
        slug = slugify(seed.title)
        existing = db.execute(select(Opportunity).where(Opportunity.slug == slug)).scalar_one_or_none()
        if existing is not None:
            continue
        deadline = datetime.now(UTC) + timedelta(days=seed.deadline_days)
        opportunity = Opportunity(
            slug=slug,
            title=seed.title,
            short_description=seed.short_description,
            category=seed.category,
            geography_scope='Italy',
            benefit_type=seed.benefit_type,
            deadline_date=deadline,
            estimated_value_max=seed.value,
            record_status=RecordStatus.PUBLISHED.value,
            verification_status=VerificationStatus.REVIEWED.value,
        )
        db.add(opportunity)
        db.flush()
        source = sources[seed.issuer_name]
        source_endpoint = source.endpoints[0]
        version = OpportunityVersion(
            opportunity_id=opportunity.id,
            source_snapshot_id=None,
            version_number=1,
            title=seed.title,
            normalized_title=slug,
            short_description=seed.short_description,
            long_description=seed.long_description,
            opportunity_type=seed.opportunity_type,
            category=seed.category,
            subcategory=None,
            issuer_name=seed.issuer_name,
            issuer_type='public_agency',
            country='IT',
            region=None,
            geography_scope='Italy',
            target_entities=seed.user_types,
            target_sectors=seed.sectors,
            company_stage=seed.company_age_band,
            company_size_constraints=seed.size_constraints,
            demographic_constraints=None,
            legal_constraints={'business_required': seed.requires_business},
            eligibility_inputs_required=['user_type', 'business_exists', 'sector_code_or_category'],
            exclusions=['advisor'],
            benefit_type=seed.benefit_type,
            benefit_value_type='mixed' if seed.funding_rate else 'voucher',
            estimated_value_min=seed.value * 0.4 if seed.value else None,
            estimated_value_max=seed.value,
            funding_rate=seed.funding_rate,
            deadline_type='fixed',
            deadline_date=deadline,
            application_window_start=datetime.now(UTC) - timedelta(days=10),
            application_window_end=deadline,
            application_mode='online_portal',
            required_documents=['Business plan', 'Dichiarazioni fiscali', 'Documento identita'],
            official_links=[seed.official_link],
            source_documents=[seed.source_document, source_endpoint.url],
            evidence_snippets=[
                {
                    'source': seed.source_document,
                    'field': 'eligibility',
                    'quote': seed.short_description,
                },
                {
                    'source': source_endpoint.url,
                    'field': 'deadline',
                    'quote': f'Finestra attiva con scadenza prevista entro {seed.deadline_days} giorni.',
                },
            ],
            extraction_confidence=0.98,
            verification_status=VerificationStatus.REVIEWED.value,
            record_status=RecordStatus.PUBLISHED.value,
            changed_fields=['initial_seed'],
        )
        db.add(version)
        db.flush()
        opportunity.current_version_id = version.id
        rule = OpportunityRule(
            opportunity_version_id=version.id,
            version_number=1,
            note=f'Regola seed per {seed.title}',
            rule_json=build_rule(seed),
            evidence_references=[seed.source_document],
            is_active=True,
        )
        db.add(rule)
        db.flush()
        db.add_all(
            [
                RuleTestCase(rule_id=rule.id, name=f'{seed.title} - positive', scenario_type='positive', profile_payload=positive_profile(seed), expected_status='confirmed'),
                RuleTestCase(rule_id=rule.id, name=f'{seed.title} - negative', scenario_type='negative', profile_payload=negative_profile(seed), expected_status='not_eligible'),
                RuleTestCase(rule_id=rule.id, name=f'{seed.title} - incomplete', scenario_type='incomplete', profile_payload=incomplete_profile(seed), expected_status='likely'),
            ]
        )

        if index <= 3:
            db.add(
                ReviewItem(
                    item_type=ReviewItemType.PUBLISH_PENDING.value,
                    related_entity_type='opportunity',
                    related_entity_id=opportunity.id,
                    title=f'Controllo editoriale iniziale: {seed.title}',
                    description='Elemento seed disponibile per la revisione operativa iniziale.',
                    payload={'seed': True},
                )
            )
    db.commit()

    source = next(iter(sources.values()))
    endpoint = source.endpoints[0]
    if db.execute(select(IngestionRun).where(IngestionRun.source_endpoint_id == endpoint.id)).scalar_one_or_none() is None:
        db.add(IngestionRun(source_endpoint_id=endpoint.id, stage='complete', status='success', diagnostics={'seed': True}))
        db.commit()


def seed_demo_users(db: Session) -> None:
    demo_user = get_or_create_user(db, 'demo@benefits.local')
    admin_user = get_or_create_user(db, 'admin@benefits.local')

    user_profile = get_or_create_profile(db, demo_user)
    admin_profile = get_or_create_profile(db, admin_user)
    db.commit()

    update_profile(
        db,
        demo_user,
        ProfilePayload(
            user_type='startup',
            region='Lombardia',
            business_exists=True,
            company_size_band='micro',
            company_age_band='1-3y',
            sector_code_or_category='digitale',
            hiring_intent=True,
            innovation_intent=True,
            sustainability_intent=False,
            export_intent=True,
            startup_stage='seed',
            goals=['innovazione', 'export'],
        ),
    )
    update_profile(
        db,
        admin_user,
        ProfilePayload(
            user_type='sme',
            region='Lazio',
            business_exists=True,
            company_size_band='small',
            company_age_band='3-5y',
            sector_code_or_category='servizi',
            hiring_intent=True,
            innovation_intent=False,
            sustainability_intent=True,
            export_intent=False,
        ),
    )

    db.refresh(user_profile)
    db.refresh(admin_profile)
    evaluate_profile_against_catalog(db, demo_user.profile)
    evaluate_profile_against_catalog(db, admin_user.profile)


def seed_all(db: Session) -> None:
    seed_catalog(db)
    seed_demo_users(db)
