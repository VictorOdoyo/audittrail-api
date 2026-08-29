from uuid import uuid4

from audittrail_api.identity.models import Membership, User


def test_user_and_membership_capture_identity_boundary() -> None:
    user = User(
        email="auditor@example.com",
        display_name="Example Auditor",
        password_hash="stored-hash",
    )
    membership = Membership(
        organization_id=uuid4(),
        user_id=uuid4(),
        role="auditor",
    )

    assert user.is_active is None
    assert membership.role == "auditor"
