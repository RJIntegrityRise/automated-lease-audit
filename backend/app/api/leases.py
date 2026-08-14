from typing import Annotated
from uuid import UUID

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)

from app.core.config import get_settings
from app.core.supabase import get_supabase_client
from app.schemas.extraction import ExtractionRunListItem, LeaseExtractionResponse
from app.schemas.lease import (
    LeaseDetailResponse,
    LeaseUploadResponse,
)
from app.services.document_service import (
    InvalidPdfError,
    PdfExtractionResult,
    extract_page_words,
    inspect_pdf_fields,
)

from app.services.ocr_service import (
    OcrError,
    process_pdf_with_ocr,
)


from app.services.lease_service import (
    create_document_record,
    create_extraction_run,
    create_lease_record,
    delete_storage_object,
    get_latest_document,
    get_lease_with_document,
    mark_extraction_run_failed,
    mark_lease_failed,
    save_lease_extraction,
    upload_lease_pdf,
    validate_optional_uuid,
)

from app.services.deterministic_scan_service import (
    run_deterministic_extraction,
)


from app.services.gemini_service import (
    GeminiExtractionError,
    extract_lease_with_gemini,
)

from app.schemas.checklist import (
    LeaseChecklistResult,
)
from app.services.checklist_service import (
    evaluate_checklist,
)



router = APIRouter(
    prefix="/api/leases",
    tags=["Leases"],
)


@router.post(
    "/upload",
    response_model=LeaseUploadResponse,
    status_code=status.HTTP_201_CREATED,
)
async def upload_lease(
    file: Annotated[UploadFile, File(...)],
    property_id: Annotated[str | None, Form()] = None,
    unit_number: Annotated[str | None, Form()] = None,
    internal_lease_id: Annotated[str | None, Form()] = None,
) -> LeaseUploadResponse:
    """Upload a lease PDF and extract its page-level text."""

    settings = get_settings()
    client = get_supabase_client()

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only application/pdf files are allowed.",
        )

    filename = file.filename or "lease.pdf"

    try:
        file_bytes = await file.read()
    finally:
        await file.close()

    if not file_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The uploaded PDF is empty.",
        )

    if len(file_bytes) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=(
                "The file exceeds the configured "
                "32 MB upload limit."
            ),
        )

    try:
        document_metadata = inspect_pdf_fields(
            pdf_bytes=file_bytes,
        )
        page_layout = extract_page_words(
            pdf_bytes=file_bytes,
        )

        document_metadata["page_layout"] = (
            page_layout
        )
    except InvalidPdfError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    try:
        validated_property_id = validate_optional_uuid(
            property_id,
            "property_id",
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc



    try:
        ocr_result = process_pdf_with_ocr(
            pdf_bytes=file_bytes,
        )
    

        page_texts = [
            f"--- Page {page.page_number} ---\n"
            f"{page.combined_text}"
            for page in ocr_result.pages
        ]

        full_text = "\n\n".join(page_texts)

        extraction = PdfExtractionResult(
            page_count=len(ocr_result.pages),
            full_text=full_text,
            page_texts=page_texts,
        )

    except (InvalidPdfError, OcrError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc




    

    lease_id: str | None = None
    storage_path: str | None = None

    try:
        lease = create_lease_record(
            client=client,
            user_id=settings.dev_user_id,
            property_id=validated_property_id,
            unit_number=unit_number,
            internal_lease_id=internal_lease_id,
        )

        lease_id = lease["id"]

        storage_path = upload_lease_pdf(
            client=client,
            settings=settings,
            user_id=settings.dev_user_id,
            lease_id=lease_id,
            filename=filename,
            file_bytes=file_bytes,
        )

        document = create_document_record(
            client=client,
            lease_id=lease_id,
            user_id=settings.dev_user_id,
            storage_path=storage_path,
            original_filename=filename,
            file_size_bytes=len(file_bytes),
            extraction=extraction,
            document_metadata=document_metadata,
            ocr_metadata=ocr_result.model_dump(
                mode="json"
            ),
            ocr_used=ocr_result.ocr_page_count > 0,
            ocr_page_count=ocr_result.ocr_page_count,
        )

        return LeaseUploadResponse(
            lease_id=lease["id"],
            document_id=document["id"],
            original_filename=filename,
            storage_path=storage_path,
            file_size_bytes=len(file_bytes),
            page_count=extraction.page_count,
            extracted_character_count=len(
                extraction.full_text
            ),
            status=lease["status"],
        )

    except Exception as exc:
        if storage_path:
            delete_storage_object(
                client=client,
                bucket=settings.supabase_storage_bucket,
                storage_path=storage_path,
            )

        if lease_id:
            mark_lease_failed(
                client=client,
                lease_id=lease_id,
                error_message=str(exc),
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lease upload failed: {exc}",
        ) from exc


@router.get(
    "/{lease_id}",
    response_model=LeaseDetailResponse,
)
def get_lease(
    lease_id: UUID,
) -> LeaseDetailResponse:
    """Return lease metadata, extracted text and a signed PDF URL."""

    settings = get_settings()
    client = get_supabase_client()

    try:
        lease = get_lease_with_document(
            client=client,
            settings=settings,
            lease_id=str(lease_id),
        )

        return LeaseDetailResponse.model_validate(lease)

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Unable to retrieve lease: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.post(
    "/{lease_id}/extract",
    response_model=LeaseExtractionResponse,
)
def extract_lease_data(
    lease_id: UUID,
) -> LeaseExtractionResponse:
    """Create an independent Gemini extraction run."""

    settings = get_settings()
    client = get_supabase_client()
    lease_id_string = str(lease_id)

    extraction_run_id: str | None = None

    try:
        document = get_latest_document(
            client=client,
            lease_id=lease_id_string,
        )

        extraction_run = create_extraction_run(
            client=client,
            lease_id=lease_id_string,
            document_id=document["id"],
            provider="gemini",
            model_name=settings.gemini_model,
        )

        extraction_run_id = extraction_run["id"]

        extraction = extract_lease_with_gemini(
            extracted_text=document["extracted_text"],
        )

        save_lease_extraction(
            client=client,
            lease_id=lease_id_string,
            extraction_run_id=extraction_run_id,
            extraction=extraction,
        )

        return LeaseExtractionResponse(
            extraction_run_id=extraction_run_id,
            lease_id=lease_id_string,
            document_id=document["id"],
            status="completed",
            model=settings.gemini_model,
            extracted_data=extraction,
            evidence_count=len(extraction.evidence),
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except (GeminiExtractionError, ValueError) as exc:
        if extraction_run_id:
            mark_extraction_run_failed(
                client=client,
                extraction_run_id=extraction_run_id,
                error_message=str(exc),
            )

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        if extraction_run_id:
            mark_extraction_run_failed(
                client=client,
                extraction_run_id=extraction_run_id,
                error_message=str(exc),
            )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Gemini extraction failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc



@router.get(
    "/{lease_id}/extractions",
    response_model=list[ExtractionRunListItem],
)
def list_extraction_runs(
    lease_id: UUID,
) -> list[ExtractionRunListItem]:
    client = get_supabase_client()

    response = (
        client.table("extraction_runs")
        .select(
            (
                "id,"
                "lease_id,"
                "document_id,"
                "status,"
                "provider,"
                "model_name,"
                "overall_confidence,"
                "processing_error,"
                "created_at,"
                "completed_at"
            )
        )
        .eq("lease_id", str(lease_id))
        .order("created_at", desc=True)
        .execute()
    )

    return [
        ExtractionRunListItem.model_validate(item)
        for item in response.data or []
    ]

@router.post(
    "/{lease_id}/scan",
)
def scan_lease_without_ai(
    lease_id: UUID,
) -> dict:
    """Run an independent deterministic lease scan."""

    client = get_supabase_client()

    try:
        result = run_deterministic_extraction(
            client=client,
            lease_id=str(lease_id),
        )

        return {
            "extraction_run_id": result["id"],
            "lease_id": result["lease_id"],
            "document_id": result["document_id"],
            "status": result["status"],
            "extraction_method": result[
                "extraction_method"
            ],
            "scanner_version": result[
                "scanner_version"
            ],
            "structured_data": result[
                "structured_data"
            ],
        }

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Deterministic scan failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.get(
    "/{lease_id}/checklist",
    response_model=LeaseChecklistResult,
)
def get_lease_checklist(
    lease_id: UUID,
    extraction_run_id: UUID,
) -> LeaseChecklistResult:
    """
    Evaluate the configured lease checklist against
    one specific independent scan.
    """

    client = get_supabase_client()

    try:
        run_response = (
            client.table("extraction_runs")
            .select("id,lease_id")
            .eq("id", str(extraction_run_id))
            .eq("lease_id", str(lease_id))
            .limit(1)
            .execute()
        )

        if not run_response.data:
            raise LookupError(
                "Extraction run not found for this lease."
            )

        return evaluate_checklist(
            client=client,
            extraction_run_id=str(
                extraction_run_id
            ),
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=(
                "Checklist evaluation failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc