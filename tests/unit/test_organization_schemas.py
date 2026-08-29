import pytest
from pydantic import ValidationError

from audittrail_api.organizations.schemas import OrganizationCreate


def test_slug_is_normalized() -> None:
    payload = OrganizationCreate(name="Example Company", slug="Example-Company")

    assert payload.slug == "example-company"


@pytest.mark.parametrize("slug", ["two words", "leading-", "a--b"])
def test_invalid_slug_is_rejected(slug: str) -> None:
    with pytest.raises(ValidationError):
        OrganizationCreate(name="Example Company", slug=slug)
