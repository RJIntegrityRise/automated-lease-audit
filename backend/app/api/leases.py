from typing import Annotated

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
from app.schemas.lease import LeaseUploadResponse
from app.services.document_service import (
    InvalidPdfError,
    extract_pdf_text,
)
from app.services.lease_service import (
    create_document_record,
    create_lease_record,
    delete_storage_object,
    mark_lease_failed,
    upload_lease_pdf,
    validate_optional_uuid,
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
        extraction = extract_pdf_text(file_bytes)
    except InvalidPdfError as exc:
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