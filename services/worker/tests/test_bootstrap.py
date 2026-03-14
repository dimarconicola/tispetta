from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import (
    Base,
    DocumentRole,
    MeasureFamily,
    MeasureFamilyDocument,
    NormalizedDocument,
    Source,
    SourceEndpoint,
    SourceSnapshot,
)
from worker.services.bootstrap import choose_relationship_type


def test_choose_relationship_type_tolerates_multiple_primary_operational_links() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    with Session(engine) as db:
        source = Source(
            source_name="Example Source",
            source_type="website",
            authority_level="tier_1",
            crawl_method="html",
            crawl_frequency="daily",
            trust_level="high",
            region="Italy",
        )
        db.add(source)
        db.flush()
        endpoint = SourceEndpoint(
            source_id=source.id,
            name="Example Endpoint",
            url="https://example.com/family-test",
            document_type="measure_family_document",
        )
        db.add(endpoint)
        db.flush()
        first_snapshot = SourceSnapshot(
            source_endpoint_id=endpoint.id,
            checksum="checksum-1",
        )
        second_snapshot = SourceSnapshot(
            source_endpoint_id=endpoint.id,
            checksum="checksum-2",
        )
        db.add_all([first_snapshot, second_snapshot])
        db.flush()
        family = MeasureFamily(
            slug="family-test",
            title="Family Test",
            operator_name="Operator",
            source_domain="example.com",
        )
        first_document = NormalizedDocument(
            source_snapshot_id=first_snapshot.id,
            title="First",
            clean_text="bonus incentivi",
            metadata_json={},
            structural_sections=[],
            document_role=DocumentRole.OPERATOR_MEASURE_PAGE.value,
            lifecycle_status="open_application",
        )
        second_document = NormalizedDocument(
            source_snapshot_id=second_snapshot.id,
            title="Second",
            clean_text="bonus incentivi",
            metadata_json={},
            structural_sections=[],
            document_role=DocumentRole.OPERATOR_MEASURE_PAGE.value,
            lifecycle_status="open_application",
        )
        db.add_all([family, first_document, second_document])
        db.flush()
        db.add_all(
            [
                MeasureFamilyDocument(
                    measure_family_id=family.id,
                    normalized_document_id=first_document.id,
                    relationship_type="primary_operational",
                    is_primary_operational_doc=True,
                ),
                MeasureFamilyDocument(
                    measure_family_id=family.id,
                    normalized_document_id=second_document.id,
                    relationship_type="primary_operational",
                    is_primary_operational_doc=True,
                ),
            ]
        )
        db.commit()

        relationship_type = choose_relationship_type(
            db,
            family,
            DocumentRole.OPERATOR_MEASURE_PAGE.value,
        )

    assert relationship_type == "supporting_document"
