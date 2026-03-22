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
from app.services.corpus import ensure_bootstrap_corpus
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
    extra_required: list[dict] | None = None


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
    {
        'name': 'INPS',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'daily',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.inps.it/',
    },
    {
        'name': 'Mediocredito Centrale',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'weekly',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.mcc.it/',
    },
    {
        'name': 'GSE — Gestore Servizi Energetici',
        'source_type': 'website',
        'authority_level': 'tier_1',
        'crawl_method': 'html',
        'crawl_frequency': 'weekly',
        'trust_level': 'high',
        'region': 'Italy',
        'endpoint_url': 'https://www.gse.it/',
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
    # --- Persona fisica: benefici di base ---
    OpportunitySeed(
        'Assegno Unico Universale',
        'INPS', 'family_benefit', OpportunityType.GRANT.value,
        'assegno mensile per figli a carico',
        ['persona_fisica'], None, None, [], None, None,
        6840.0, 1.0, 365,
        "Assegno mensile erogato da INPS per ogni figlio under 21 a carico, modulato per ISEE.",
        "Spetta automaticamente a ogni famiglia con figli a carico. L'importo scala da 57 a 199 euro al mese per figlio in base all'ISEE. Chi non fa domanda perde i soldi.",
        'https://www.inps.it/assegno-unico',
        'https://www.inps.it/assegno-unico',
        extra_required=[
            {'in': {'field': 'family_composition', 'value': ['coppia_con_figli', 'genitore_solo_con_figli']}},
            {'not_in': {'field': 'figli_a_carico_count', 'value': ['0']}},
        ],
    ),
    OpportunitySeed(
        'Contributo Asilo Nido INPS',
        'INPS', 'family_benefit', OpportunityType.GRANT.value,
        'contributo annuale per rette asilo nido',
        ['persona_fisica'], None, None, [], None, None,
        3600.0, 1.0, 365,
        "Contributo INPS fino a 3.600 euro annui per rette di asilo nido o assistenza domiciliare per bambini sotto i 3 anni.",
        "Modulato per ISEE: 3.600 euro sotto 25.000 euro, 3.000 euro tra 25.000-40.000 euro, 1.500 euro oltre 40.000 euro. Si richiede online su INPS con ricevute di pagamento.",
        'https://www.inps.it/bonus-asilo-nido',
        'https://www.inps.it/bonus-asilo-nido',
        extra_required=[
            {'in': {'field': 'family_composition', 'value': ['coppia_con_figli', 'genitore_solo_con_figli']}},
            {'not_in': {'field': 'figli_a_carico_count', 'value': ['0']}},
            {'in': {'field': 'youngest_child_age_band', 'value': ['under_3']}},
        ],
    ),
    OpportunitySeed(
        "ANF — Assegni al Nucleo Familiare",
        'INPS', 'family_benefit', OpportunityType.GRANT.value,
        'assegno mensile per famiglie numerose con dipendenti',
        ['persona_fisica'], None, None, [], None, None,
        2400.0, 1.0, 365,
        "Assegni al Nucleo Familiare INPS per lavoratori dipendenti con figli a carico. Importo variabile per reddito e numero di componenti.",
        "Dedicato a dipendenti con figli o coniuge a carico. Si richiede tramite il datore di lavoro o direttamente su INPS. Integra il reddito familiare su base mensile.",
        'https://www.inps.it/anf',
        'https://www.inps.it/anf',
        extra_required=[
            {'eq': {'field': 'employment_type', 'value': 'dipendente'}},
            {'not_in': {'field': 'figli_a_carico_count', 'value': ['0']}},
        ],
    ),
    OpportunitySeed(
        "NASpI — Indennita di Disoccupazione",
        'INPS', 'social_benefit', OpportunityType.GRANT.value,
        'indennita per lavoratori dipendenti che perdono involontariamente il lavoro',
        ['persona_fisica'], None, None, [], None, None,
        8400.0, 0.75, 365,
        "Indennita INPS pari al 75% della retribuzione media mensile (max 1.352 euro) per lavoratori dipendenti che perdono involontariamente il lavoro.",
        "Richiede almeno 13 settimane di contribuzione nei 4 anni precedenti. Dura meta dei mesi contributivi. Si riduce del 3% ogni mese a partire dal quinto. Domanda entro 68 giorni.",
        'https://www.inps.it/it/it/inps-comunica/dossier/la-naspi/come-fare-domanda.html',
        'https://www.inps.it/it/it/inps-comunica/dossier/la-naspi/faq---domande-frequenti-sulla-naspi.html',
        extra_required=[
            {'eq': {'field': 'employment_type', 'value': 'disoccupato'}},
        ],
    ),
    OpportunitySeed(
        'Regime Forfettario Agevolato Primo Anno',
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        'imposta sostitutiva al 5% per nuovi autonomi nel primo quinquennio',
        ['persona_fisica'], None, None, [], None, None,
        4250.0, 0.05, 365,
        "Regime fiscale agevolato per autonomi con ricavi sotto 85.000 euro: aliquota flat del 15% (5% per i primi 5 anni di attivita).",
        "Nessun obbligo IVA, esenzione IRAP, contabilita semplificata. Si accede automaticamente aprendo P.IVA senza precedenti attivita fiscalmente rilevanti negli ultimi 3 anni.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/regime-forfetario',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/regime-forfetario',
        extra_required=[
            {'eq': {'field': 'employment_type', 'value': 'autonomo'}},
        ],
    ),
    OpportunitySeed(
        'Detrazione per Figli a Carico',
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        'detrazione IRPEF per figli a carico fino a 24 anni',
        ['persona_fisica'], None, None, [], None, None,
        950.0, 1.0, 365,
        "Detrazione IRPEF di 950 euro per ciascun figlio a carico fino a 21 anni (detrazione piena per under 3 con figli con disabilita).",
        "Si calcola automaticamente nel 730 precompilato. Per figli over 21 non coperti da Assegno Unico, la detrazione continua fino a 24 anni se studenti.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/detrazioni-figli',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/detrazioni-figli',
        extra_required=[
            {'not_in': {'field': 'figli_a_carico_count', 'value': ['0']}},
        ],
    ),
    OpportunitySeed(
        'Bonus Prima Casa Under 36',
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        'esenzione imposte ipotecarie e catastali per under 36 con ISEE sotto 40.000 euro',
        ['persona_fisica'], None, None, [], None, None,
        3000.0, 1.0, 365,
        "Esenzione totale da imposte ipotecaria, catastale e di registro per under 36 che acquistano prima casa con ISEE sotto 40.000 euro.",
        "Anche credito IVA pari all'imposta pagata se acquistato da costruttore con IVA. Si autocertifica al rogito notarile entro i 36 anni. Non prorogabile dopo il compimento dei 36 anni.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/agevolazioni-prima-casa-under36',
        'https://www.agenziaentrate.gov.it/portale/web/guest/agevolazioni-prima-casa-under36',
        extra_required=[
            {'eq': {'field': 'persona_fisica_age_band', 'value': 'under_35'}},
            {'not_in': {'field': 'isee_bracket', 'value': ['over_40k']}},
        ],
    ),
    OpportunitySeed(
        'Detrazione Interessi Mutuo Prima Casa',
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        'detrazione IRPEF 19% sugli interessi passivi del mutuo prima casa fino a 4.000 euro',
        ['persona_fisica'], None, None, [], None, None,
        760.0, 0.19, 365,
        "Detrazione IRPEF del 19% sugli interessi passivi del mutuo per acquisto prima casa, fino a un massimo di 4.000 euro di interessi (detrazione massima 760 euro).",
        "Si indica ogni anno nel 730. Include anche le spese accessorie (perizia, notaio per ipoteca). Valida finche dura il mutuo e la casa rimane prima casa.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/interessi-passivi-mutuo',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/interessi-passivi-mutuo',
        extra_required=[
            {'eq': {'field': 'home_ownership_status', 'value': 'proprietario'}},
        ],
    ),
    OpportunitySeed(
        'Detrazioni Ristrutturazione Casa 50%',
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        'detrazione IRPEF 50% su lavori edilizi fino a 96.000 euro',
        ['persona_fisica'], None, None, [], None, None,
        48000.0, 0.5, 365,
        "Detrazione IRPEF del 50% su lavori di ristrutturazione edilizia fino a 96.000 euro di spesa, recuperata in 10 anni.",
        "Include rifacimento bagni, impianti, pareti, pavimenti, infissi. Richiede bonifico parlante. Compatibile con Ecobonus 65% per interventi energy. Valida per proprietari e locatari.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/ristrutturazioni-edilizie',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/ristrutturazioni-edilizie',
        extra_required=[
            {'in': {'field': 'home_ownership_status', 'value': ['proprietario', 'inquilino_contratto_registrato']}},
        ],
    ),
    OpportunitySeed(
        'Carta Acquisti INPS',
        'INPS', 'social_benefit', OpportunityType.GRANT.value,
        'carta prepagata da 80 euro bimestrali per famiglie in difficolta',
        ['persona_fisica'], None, None, [], None, None,
        480.0, 1.0, 365,
        "Carta prepagata INPS con 80 euro ricaricati ogni 2 mesi per famiglie con ISEE sotto determinata soglia: anziani over 65, famiglie con bambini sotto 3 anni.",
        "Per famiglie con figli under 3 o anziani over 65 con ISEE molto basso. Si richiede presso uffici postali con SPID. Include carburante, farmaci e spesa alimentare.",
        'https://www.inps.it/carta-acquisti',
        'https://www.inps.it/carta-acquisti',
        extra_required=[
            {'eq': {'field': 'isee_bracket', 'value': 'under_15k'}},
        ],
    ),
    # --- Persona fisica: nuovi benefici sociali e fiscali ---
    OpportunitySeed(
        "ADI — Assegno di Inclusione",
        'INPS', 'social_benefit', OpportunityType.GRANT.value,
        "sussidio mensile per famiglie in difficolta economica",
        ['persona_fisica'], None, None, [], None, None,
        6000.0, 1.0, 365,
        "Misura INPS per famiglie con figli minorenni, disabili o anziani over 60 con ISEE sotto 9.360 euro.",
        "Sostituisce il Reddito di Cittadinanza per i nuclei con persone fragili. Importo base 500 euro/mese + 280 euro per affitto. Si richiede su INPS con ISEE aggiornato.",
        'https://www.inps.it/assegno-inclusione',
        'https://www.inps.it/assegno-inclusione',
        extra_required=[
            {'in': {'field': 'family_composition', 'value': ['coppia_con_figli', 'genitore_solo_con_figli']}},
            {'eq': {'field': 'isee_bracket', 'value': 'under_15k'}},
        ],
    ),
    OpportunitySeed(
        "SFL — Supporto Formazione e Lavoro",
        'INPS', 'social_benefit', OpportunityType.GRANT.value,
        "indennita mensile per disoccupati in percorso formativo",
        ['persona_fisica'], None, None, [], None, None,
        4200.0, 1.0, 365,
        "Indennita INPS di 350 euro/mese per persone tra 18 e 59 anni in cerca di lavoro e iscritte a percorsi formativi.",
        "Dedicato a disoccupati occupabili senza figli o disabili a carico che partecipano a corsi GOL o equivalenti. Si attiva tramite centro per l'impiego.",
        'https://www.inps.it/supporto-formazione-lavoro',
        'https://www.inps.it/supporto-formazione-lavoro',
        extra_required=[
            {'eq': {'field': 'employment_type', 'value': 'disoccupato'}},
            {'in': {'field': 'persona_fisica_age_band', 'value': ['under_35', '35_55']}},
        ],
    ),
    OpportunitySeed(
        'Bonus Psicologo',
        'INPS', 'social_benefit', OpportunityType.GRANT.value,
        'contributo per sedute di psicoterapia fino a 1.500 euro',
        ['persona_fisica'], None, None, [], None, None,
        1500.0, 1.0, 365,
        'Contributo INPS per sedute di psicoterapia: fino a 1.500 euro per ISEE sotto 15.000 euro.',
        'Si richiede tramite portale INPS con codice fiscale del terapeuta abilitato. Disponibile fino a esaurimento fondi annuali.',
        'https://www.inps.it/bonus-psicologo',
        'https://www.inps.it/bonus-psicologo',
    ),
    OpportunitySeed(
        'Detrazioni Spese Mediche 730',
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        'detrazione IRPEF 19% su spese sanitarie sopra 129 euro',
        ['persona_fisica'], None, None, [], None, None,
        2400.0, 0.19, 365,
        'Detrazione IRPEF del 19% su spese mediche, farmaci, visite specialistiche, analisi e dispositivi medici.',
        'Si dichiara nel 730 precompilato con spese tracciate. Include spese per familiari a carico. Nessuna soglia ISEE.',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/spese-sanitarie',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/spese-sanitarie',
    ),
    OpportunitySeed(
        'Ecobonus Riqualificazione Energetica 65%',
        'Agenzia delle Entrate', 'sustainability_incentive', OpportunityType.TAX_INCENTIVE.value,
        'detrazione 65% su impianti di riscaldamento e coibentazione',
        ['persona_fisica'], None, None, [], None, None,
        30000.0, 0.65, 365,
        "Detrazione IRPEF del 65% su lavori di riqualificazione energetica: caldaia, isolamento pareti, infissi a risparmio energetico.",
        "Richiede asseverazione energetica e bonifico parlante. Spalmata in 10 anni. Vale per proprietari e conduttori con contratto registrato.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/riqualificazione-energetica',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/riqualificazione-energetica',
        extra_required=[
            {'in': {'field': 'home_ownership_status', 'value': ['proprietario', 'inquilino_contratto_registrato']}},
        ],
    ),
    OpportunitySeed(
        'Bonus Mobili e Grandi Elettrodomestici',
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        "detrazione 50% su mobili e grandi elettrodomestici collegati a ristrutturazione",
        ['persona_fisica'], None, None, [], None, None,
        4000.0, 0.5, 365,
        "Detrazione IRPEF del 50% su mobili e grandi elettrodomestici classe A+ acquistati nell'anno della ristrutturazione, fino a 8.000 euro.",
        "Legato alla detrazione ristrutturazione 50%. Pagamento con bonifico o carta.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/bonus-mobili',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/bonus-mobili',
        extra_required=[
            {'eq': {'field': 'home_ownership_status', 'value': 'proprietario'}},
        ],
    ),
    OpportunitySeed(
        'Detrazione Affitto Inquilini',
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        'detrazione fino a 300 euro per inquilini con contratto registrato',
        ['persona_fisica'], None, None, [], None, None,
        300.0, 1.0, 365,
        'Detrazione IRPEF flat per inquilini con abitazione principale in affitto e reddito sotto 30.987 euro.',
        'Si dichiara nel 730 con il contratto di affitto registrato. Nessuna spesa minima.',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/detrazione-affitto',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/detrazione-affitto',
        extra_required=[
            {'eq': {'field': 'home_ownership_status', 'value': 'inquilino_contratto_registrato'}},
            {'in': {'field': 'isee_bracket', 'value': ['under_15k', '15_25k']}},
        ],
    ),
    OpportunitySeed(
        'Congedo Parentale Indennizzato',
        'INPS', 'family_benefit', OpportunityType.GRANT.value,
        "indennita per astensione dal lavoro dei genitori",
        ['persona_fisica'], None, None, [], None, None,
        3800.0, 0.8, 365,
        "Congedo parentale INPS: il primo mese viene indennizzato all'80% dello stipendio, i successivi al 30% fino ai 12 anni del figlio.",
        "Dal 2024 il secondo mese e stato elevato all'80%. Si richiede online su INPS prima dell'astensione.",
        'https://www.inps.it/congedo-parentale',
        'https://www.inps.it/congedo-parentale',
        extra_required=[
            {'eq': {'field': 'employment_type', 'value': 'dipendente'}},
            {'in': {'field': 'family_composition', 'value': ['coppia_con_figli', 'genitore_solo_con_figli']}},
        ],
    ),
    OpportunitySeed(
        "Legge 104 — Agevolazioni e Permessi Retribuiti",
        'INPS', 'social_benefit', OpportunityType.GRANT.value,
        "permessi retribuiti e agevolazioni per disabilita grave",
        ['persona_fisica'], None, None, [], None, None,
        2400.0, 1.0, 365,
        "La Legge 104 garantisce 3 giorni di permesso retribuito al mese al dipendente che assiste un familiare con disabilita grave.",
        "Richiede il riconoscimento INPS della condizione di handicap grave (art. 3 co. 3). Include detrazioni auto H e agevolazioni fiscali.",
        'https://www.inps.it/it/it/inps-comunica/notizie/dettaglio-news-page.news.2022.11.permessi-legge-n-104-1992-rilascio-funzionalit-rinuncia-ai-benefici-.html',
        'https://www.inps.it/it/it/inps-comunica/notizie/dettaglio-news-page.news.2023.09.permessi-legge-104-e-congedo-familiari-disabili-variazione-domanda.html',
        extra_required=[
            {'in': {'field': 'disability_status', 'value': ['legge_104_in_famiglia', 'invalidita_civile', 'indennita_accompagnamento']}},
        ],
    ),
    OpportunitySeed(
        "Rientro Cervelli — Regime Impatriati",
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        "esenzione fiscale 50-90% per lavoratori rientrati in Italia",
        ['persona_fisica'], None, None, [], None, None,
        15000.0, 0.7, 365,
        "Regime agevolato per lavoratori che trasferiscono la residenza fiscale in Italia dopo almeno 2 anni all'estero.",
        "50% del reddito imponibile esente per 5 anni (90% per Sud o con figli). Estendibile a 10 anni per chi acquista casa. Nessuna domanda: si indica in dichiarazione dei redditi.",
        'https://www.agenziaentrate.gov.it/portale/regime-impatriati',
        'https://www.agenziaentrate.gov.it/portale/regime-impatriati',
    ),
    # --- Freelancer: agevolazioni specifiche per autonomi ---
    OpportunitySeed(
        'Esonero Contributivo INPS Under 35',
        'INPS', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        'riduzione 35% contributi per nuovi iscritti gestione separata under 35',
        ['freelancer'], ['solo'], None, [], False, ['idea', '0-12m', '1-3y'],
        3500.0, 0.35, 365,
        'Riduzione del 35% dei contributi INPS gestione separata per i nuovi iscritti under 35 nei primi 3 anni.',
        "Si attiva in automatico all'apertura P.IVA. Richiede la prima iscrizione alla gestione separata (non iscritti in passato).",
        'https://www.inps.it/esonero-contributivo-autonomi',
        'https://www.inps.it/esonero-contributivo-autonomi',
        extra_required=[
            {'eq': {'field': 'persona_fisica_age_band', 'value': 'under_35'}},
            {'eq': {'field': 'employment_type', 'value': 'autonomo'}},
        ],
    ),
    OpportunitySeed(
        "DIS-COLL — Disoccupazione Collaboratori",
        'INPS', 'unemployment_benefit', OpportunityType.GRANT.value,
        "indennita di disoccupazione per collaboratori e co.co.co.",
        ['freelancer'], None, None, [], None, None,
        8000.0, 0.75, 365,
        "Indennita INPS per co.co.co. e collaboratori che perdono il rapporto di collaborazione involontariamente.",
        "Alternativa alla NASpI per chi lavora con contratto di collaborazione. Dura meta dei mesi di contribuzione negli ultimi 4 anni, max 6 mesi.",
        'https://www.inps.it/dis-coll',
        'https://www.inps.it/dis-coll',
        extra_required=[
            {'eq': {'field': 'employment_type', 'value': 'disoccupato'}},
        ],
    ),
    # --- Business: misure nazionali chiave mancanti ---
    OpportunitySeed(
        "Nuova Sabatini — Finanziamento Beni Strumentali",
        'Ministero delle Imprese e del Made in Italy',
        'subsidized_loan', OpportunityType.SUBSIDIZED_LOAN.value,
        'contributo interessi su finanziamento per beni strumentali e macchinari',
        ['sme', 'startup'], ['micro', 'small', 'medium'],
        ['manifattura', 'digitale', 'servizi', 'agritech'],
        ['digitalizzazione'],
        True, ['0-12m', '1-3y', '3-5y', '5y+'],
        4000000.0, 0.35, 180,
        'Contributo in conto interessi su finanziamenti bancari per acquisto o leasing di macchinari, impianti, attrezzature e hardware/software.',
        "Una delle misure piu utilizzate in Italia per investimenti produttivi. Soglia minima 20.000 euro, massimo 4 milioni. Opera attraverso banche convenzionate.",
        'https://www.mimit.gov.it/it/incentivi/nuova-sabatini',
        'https://www.mimit.gov.it/it/incentivi/nuova-sabatini',
    ),
    OpportunitySeed(
        "Fondo di Garanzia PMI — MCC",
        'Mediocredito Centrale',
        'loan_guarantee', OpportunityType.SUBSIDIZED_LOAN.value,
        "garanzia pubblica fino all'80% su finanziamenti bancari",
        ['sme', 'startup', 'freelancer'], ['solo', 'micro', 'small', 'medium'],
        None, ['crescita'],
        None, ['idea', '0-12m', '1-3y', '3-5y', '5y+'],
        5000000.0, 0.8, 180,
        "Il Fondo di Garanzia MCC garantisce fino all'80% dei finanziamenti bancari per PMI, startup e professionisti.",
        "Strumento di accesso al credito piu impattante per le PMI italiane. La garanzia pubblica riduce il rischio bancario. Richiesta tramite banca o confidi.",
        'https://www.mcc.it/fondo-di-garanzia-pmi',
        'https://www.mcc.it/fondo-di-garanzia-pmi',
    ),
    OpportunitySeed(
        'Piano Transizione 5.0',
        'GSE — Gestore Servizi Energetici',
        'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        "credito d’imposta per investimenti digitali con risparmio energetico certificato",
        ['sme', 'startup'], ['micro', 'small', 'medium'],
        ['manifattura', 'energia', 'digitale', 'agritech'],
        ['sostenibilita', 'digitalizzazione', 'innovazione'],
        True, ['0-12m', '1-3y', '3-5y', '5y+'],
        500000.0, 0.45, 180,
        "Credito d’imposta per beni strumentali 4.0 con riduzione certificata dei consumi energetici di almeno il 3-10%.",
        "Evoluzione di Transizione 4.0: richiede di dimostrare il risparmio energetico. Aliquote: 35% fino a 2,5M, 15% fino a 10M. Gestito tramite GSE con asseverazione.",
        'https://www.gse.it/servizi-per-te/transizione-5-0',
        'https://www.gse.it/servizi-per-te/transizione-5-0',
    ),
    OpportunitySeed(
        "Credito R&S — Ricerca, Sviluppo e Design",
        'Agenzia delle Entrate',
        'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        "credito d’imposta su R&S, innovazione tecnologica e design",
        ['startup', 'sme'], ['micro', 'small', 'medium'],
        ['digitale', 'manifattura', 'agritech', 'energia'],
        ['innovazione'],
        True, ['0-12m', '1-3y', '3-5y', '5y+'],
        200000.0, 0.2, 180,
        "Credito d’imposta su costi per ricerca fondamentale, sviluppo sperimentale, innovazione tecnologica e design.",
        "Aliquote: R&S 20%, innovazione tecnologica 10%, design 10%. Include costi di personale, contratti con universita e centri ricerca, software e materiali.",
        'https://www.agenziaentrate.gov.it/portale/credito-imposta-ricerca',
        'https://www.agenziaentrate.gov.it/portale/credito-imposta-ricerca',
    ),
    OpportunitySeed(
        "Voucher 3I — Brevetti per Imprese Innovative",
        'Ministero delle Imprese e del Made in Italy',
        'grants', OpportunityType.GRANT.value,
        'contributo per deposito brevetti nazionali e internazionali',
        ['startup', 'sme'], ['micro', 'small', 'medium'],
        ['digitale', 'manifattura', 'agritech', 'energia'],
        ['innovazione'],
        True, ['idea', '0-12m', '1-3y', '3-5y', '5y+'],
        25000.0, 1.0, 120,
        'Voucher MIMIT fino a 25.000 euro per coprire costi di deposito e assistenza per brevetti nazionali EPO e PCT.',
        'Gestito da UIBM. Include compenso consulente brevettuale, tasse deposito e traduzione. Rimborso fino al 100% delle spese.',
        'https://www.mimit.gov.it/it/incentivi/voucher-3i-brevetti',
        'https://www.mimit.gov.it/it/incentivi/voucher-3i-brevetti',
    ),
    OpportunitySeed(
        'Bonus Giovani Under 35 Assunzioni',
        'INPS', 'hiring_incentive', OpportunityType.HIRING_INCENTIVE.value,
        'esonero contributivo 100% per 3 anni su assunzioni under 35 a tempo indeterminato',
        ['startup', 'sme'], ['micro', 'small', 'medium'],
        None, ['hiring'],
        True, ['0-12m', '1-3y', '3-5y', '5y+'],
        24000.0, 1.0, 90,
        'Esonero totale dei contributi previdenziali per 36 mesi su assunzioni a tempo indeterminato di under 35 che non hanno mai avuto tale contratto.',
        'Massimale 8.000 euro/anno per lavoratore. Compatibile con altri incentivi. Il dipendente non deve aver avuto precedenti contratti a tempo indeterminato.',
        'https://www.inps.it/bonus-giovani-under35',
        'https://www.inps.it/bonus-giovani-under35',
    ),
    OpportunitySeed(
        'Bonus Donne Assunzioni',
        'INPS', 'hiring_incentive', OpportunityType.HIRING_INCENTIVE.value,
        'esonero contributivo 60-100% per assunzioni donne svantaggiate',
        ['startup', 'sme'], ['micro', 'small', 'medium'],
        None, ['hiring'],
        True, ['0-12m', '1-3y', '3-5y', '5y+'],
        18000.0, 0.6, 90,
        'Riduzione contributi previdenziali del 60% (100% per il Sud) su assunzioni a tempo indeterminato di donne disoccupate da almeno 6 mesi.',
        'Rimborso massimo 8.000 euro/anno per lavoratrice. Include assunzioni a tempo determinato (50% per 12 mesi).',
        'https://www.inps.it/bonus-donne',
        'https://www.inps.it/bonus-donne',
    ),
    OpportunitySeed(
        'Resto al Sud 2.0',
        'Invitalia', 'grants', OpportunityType.GRANT.value,
        'mix contributo a fondo perduto e finanziamento agevolato per nuove imprese al Sud',
        ['startup', 'sme', 'freelancer'], ['solo', 'micro', 'small'],
        ['manifattura', 'servizi', 'digitale', 'turismo', 'agritech'],
        ['avvio'],
        False, ['idea', '0-12m', '1-3y'],
        200000.0, 0.5, 150,
        'Incentivo Invitalia per nuove imprese in Basilicata, Calabria, Campania, Molise, Puglia, Sardegna, Sicilia, Abruzzo.',
        'Mix 50% fondo perduto + 50% tasso zero. Dedicato a under 46 residenti o disposti a trasferirsi nelle regioni del Mezzogiorno.',
        'https://www.invitalia.it/cosa-facciamo/creiamo-nuove-aziende/resto-al-sud',
        'https://www.invitalia.it/cosa-facciamo/creiamo-nuove-aziende/resto-al-sud',
    ),
    OpportunitySeed(
        "Fringe Benefits Dipendenti con Figli 2024",
        'INPS', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        "esenzione contributiva fino a 3.000 euro per dipendenti con figli",
        ['persona_fisica'], None, None, [], None, None,
        3000.0, 1.0, 365,
        "I datori di lavoro possono concedere ai dipendenti con figli a carico fringe benefit esenti fino a 3.000 euro annui (bollette, buoni, rimborsi spese abitazione).",
        "Incluso nel CCNL o accordo aziendale. Si dichiara in CU. Richiede figli fiscalmente a carico.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/fringe-benefit',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/fringe-benefit',
        extra_required=[
            {'eq': {'field': 'employment_type', 'value': 'dipendente'}},
            {'not_in': {'field': 'figli_a_carico_count', 'value': ['0']}},
        ],
    ),
    OpportunitySeed(
        "Detrazione Spese Istruzione Universitaria",
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        "detrazione 19% sulle spese universitarie dei figli",
        ['persona_fisica'], None, None, [], None, None,
        2000.0, 0.19, 365,
        "Detrazione IRPEF del 19% su tasse universitarie, rette di corsi di laurea e master per figli fiscalmente a carico.",
        "Si dichiara nel 730. Include corsi pubblici e privati. Nessun limite di reddito per la detrazione base.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/istruzione',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/dichiarazioni/istruzione',
        extra_required=[
            {'not_in': {'field': 'figli_a_carico_count', 'value': ['0']}},
        ],
    ),
    OpportunitySeed(
        "Patent Box — Agevolazione Fiscale su Redditi da IP",
        'Agenzia delle Entrate', 'tax_incentive', OpportunityType.TAX_INCENTIVE.value,
        "riduzione del 50% sulla tassazione dei redditi derivanti da brevetti e IP",
        ['startup', 'sme'], ['micro', 'small', 'medium'],
        ['digitale', 'manifattura', 'agritech', 'energia'], ['innovazione'],
        True, ['0-12m', '1-3y', '3-5y', '5y+'],
        200000.0, 0.5, 180,
        "Il Patent Box consente una deduzione del 110% sui costi sostenuti per attivita di R&S legate a brevetti, modelli di utilita, software protetto da copyright e know-how.",
        "Richiede documentazione dei costi R&S e nexus approach. Si attiva in dichiarazione dei redditi.",
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/patent-box',
        'https://www.agenziaentrate.gov.it/portale/web/guest/schede/agevolazioni/patent-box',
    ),
    OpportunitySeed(
        "Sabatini Green — Beni Strumentali Ecologici",
        'Ministero delle Imprese e del Made in Italy', 'sustainability_incentive',
        OpportunityType.SUSTAINABILITY.value,
        "finanziamento agevolato per macchinari e impianti a basso impatto ambientale",
        ['sme', 'startup'], ['micro', 'small', 'medium'],
        ['manifattura', 'energia', 'agritech', 'servizi'], ['sostenibilita'],
        True, ['0-12m', '1-3y', '3-5y', '5y+'],
        4000000.0, 0.35, 150,
        "Variante green della Nuova Sabatini con contributo in conto interessi maggiorato per beni strumentali a basso consumo energetico o impatto ambientale ridotto.",
        "Stessi requisiti della Sabatini ordinaria con vincolo green sui beni acquistati. Gestita da banche aderenti alla convenzione MIMIT-ABI.",
        'https://www.mimit.gov.it/it/incentivi/nuova-sabatini',
        'https://www.mimit.gov.it/it/incentivi/nuova-sabatini',
    ),
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
    if seed.extra_required:
        required.extend(seed.extra_required)

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
            {'missing': {'field': 'youngest_child_age_band'}},
            {'missing': {'field': 'home_ownership_status'}},
            {'missing': {'field': 'disability_status'}},
            {'missing': {'field': 'tax_regime_freelancer'}},
        ],
    }


def positive_profile(seed: OpportunitySeed) -> dict[str, Any]:
    if seed.user_types == ['persona_fisica']:
        return {
            'user_type': 'persona_fisica',
            'region': 'Lombardia',
            'business_exists': False,
            'employment_type': 'dipendente',
            'isee_bracket': 'under_15k',
            'family_composition': 'coppia_con_figli',
            'figli_a_carico_count': '1',
            'persona_fisica_age_band': 'under_35',
            'youngest_child_age_band': 'under_3',
            'home_ownership_status': 'proprietario',
            'disability_status': 'legge_104_in_famiglia',
            'tax_regime_freelancer': 'forfettario',
        }
    if len(seed.user_types) > 0 and seed.user_types[0] == 'freelancer':
        return {
            'user_type': 'freelancer',
            'region': 'Lombardia',
            'business_exists': seed.requires_business if seed.requires_business is not None else False,
            'employment_type': 'autonomo',
            'persona_fisica_age_band': 'under_35',
            'tax_regime_freelancer': 'forfettario',
            'company_size_band': seed.size_constraints[0] if seed.size_constraints else 'solo',
            'company_age_band': seed.company_age_band[0] if seed.company_age_band else '1-3y',
            'sector_code_or_category': seed.sectors[0] if seed.sectors else 'servizi',
            'hiring_intent': 'hiring' in seed.goals,
            'innovation_intent': 'innovazione' in seed.goals,
            'sustainability_intent': 'sostenibilita' in seed.goals,
            'export_intent': 'export' in seed.goals,
        }
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
    if seed.user_types == ['persona_fisica']:
        return {
            'user_type': 'sme',
            'region': 'Lombardia',
            'business_exists': True,
            'company_size_band': 'small',
            'company_age_band': '3-5y',
            'sector_code_or_category': 'servizi',
        }
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
    endpoint = db.execute(select(SourceEndpoint).where(SourceEndpoint.url == spec['endpoint_url'])).scalars().first()
    if source is None and endpoint is not None and endpoint.source is not None:
        return endpoint.source
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
        if endpoint is None:
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
    elif endpoint is None:
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
        sources[spec['name']] = source
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
    demo_user = get_or_create_user(db, 'demo@example.com')
    admin_user = get_or_create_user(db, 'admin@example.com')

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
    ensure_bootstrap_corpus(db)
    seed_catalog(db)
    seed_demo_users(db)
