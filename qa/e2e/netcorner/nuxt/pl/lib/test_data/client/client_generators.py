from __future__ import annotations

import uuid

from qa.e2e.netcorner.nuxt.pl.lib.test_data.client.client_data_models import (
    AuthSessionCase,
    ClientCase,
    ClientData,
    PasswordFlowCase,
)


class ClientDataBuilder:
    def __init__(self) -> None:
        unique = uuid.uuid4().hex[:6]
        self._email = f"client_{unique}@test.pl"  # Mailhog nie lubi domeny netcorner bo Wosina
        self._password = f"a1{uuid.uuid4().hex[:8]}"
        self._password_changed = f"b2{uuid.uuid4().hex[:8]}"
        self._business_offer = False
        self._accept_required_terms = False
        self._accept_marketing = False
        self._nip = ""
        self._phone = ""

    def with_business_offer(self) -> ClientDataBuilder:
        self._business_offer = True
        self._nip = "7770020640"
        self._phone = "791233545"
        return self

    def with_required_terms(self) -> ClientDataBuilder:
        self._accept_required_terms = True
        return self

    def with_marketing(self) -> ClientDataBuilder:
        self._accept_marketing = True
        return self

    def build(self) -> ClientData:
        return ClientData(
            email=self._email,
            password=self._password,
            password_changed=self._password_changed,
            business_offer=self._business_offer,
            accept_required_terms=self._accept_required_terms,
            accept_marketing=self._accept_marketing,
            nip=self._nip,
            phone=self._phone,
        )


def valid_client_cases() -> list[ClientCase]:
    return [
        ClientCase(
            case_id="pl_terms_marketing_business",
            factory=lambda: ClientDataBuilder().with_business_offer().with_required_terms().with_marketing().build(),
        ),
        ClientCase(
            case_id="pl_terms_marketing",
            factory=lambda: ClientDataBuilder().with_required_terms().with_marketing().build(),
        ),
        ClientCase(
            case_id="pl_terms_only",
            factory=lambda: ClientDataBuilder().with_required_terms().build(),
        ),
    ]


def invalid_client_cases() -> list[ClientCase]:
    return [
        ClientCase(
            case_id="pl_marketing_business",
            factory=lambda: ClientDataBuilder().with_business_offer().with_marketing().build(),
        ),
        ClientCase(
            case_id="pl_marketing",
            factory=lambda: ClientDataBuilder().with_marketing().build(),
        ),
        ClientCase(
            case_id="pl_only",
            factory=lambda: ClientDataBuilder().build(),
        ),
    ]


def auth_session_cases() -> list[AuthSessionCase]:
    return [
        AuthSessionCase(case_id="logged_in", authenticated=True),
        AuthSessionCase(case_id="anonymous", authenticated=False),
    ]


def auth_session_cases_basic_orders() -> list[AuthSessionCase]:
    return [
        AuthSessionCase(case_id="logged_in", authenticated=True),
        AuthSessionCase(case_id="anonymous", authenticated=False),
        AuthSessionCase(
            case_id="registered_login_in_cart_overlay",
            authenticated=False,
            register_before_flow=True,
            login_in_cart_overlay=True,
        ),
    ]


def auth_session_not_registered() -> list[AuthSessionCase]:
    return [
        AuthSessionCase(case_id="anonymous", authenticated=False),
    ]


def auth_session_logged() -> list[AuthSessionCase]:
    return [
        AuthSessionCase(case_id="logged_in", authenticated=True),
    ]


def password_change_cases() -> list[PasswordFlowCase]:
    return [
        PasswordFlowCase(
            case_id="pl_password_change",
            factory=lambda: ClientDataBuilder().with_required_terms().build(),
        )
    ]


def password_recovery_cases() -> list[PasswordFlowCase]:
    return [
        PasswordFlowCase(
            case_id="pl_password_recovery",
            factory=lambda: ClientDataBuilder().with_required_terms().build(),
        )
    ]


def prod_registered_client() -> ClientData:
    return ClientData(
        email="nc-test-user@komputronik.pl",
        password="UjK_$CE4pCRB9hjn$_eX",
        password_changed="",
        business_offer=True,
        accept_required_terms=True,
        accept_marketing=True,
        nip="7770020640",
        phone="791233545",
    )
