from dataclasses import dataclass
import uuid
from collections.abc import Callable


@dataclass
class RegisterUserData:
    email: str
    password: str
    password_changed: str
    business_offer: bool = False
    accept_required_terms: bool = False
    accept_marketing: bool = False
    nip: str = ""
    phone: str = ""


@dataclass(frozen=True)
class RegisterUserCase:
    case_id: str
    factory: Callable[[], "RegisterUserData"]


class RegisterUserDataBuilder:
    def __init__(self) -> None:
        unique = uuid.uuid4().hex[:6]
        self._email = f"client_{unique}@test.pl"  # Mailhog nie lubi domeny netcorner bo Wosina
        self._password = uuid.uuid4().hex[:6]
        self._password_changed = uuid.uuid4().hex[:6]
        self._business_offer = False
        self._accept_required_terms = False
        self._accept_marketing = False
        self._nip = ""
        self._phone = ""

    def with_business_offer(self) -> "RegisterUserDataBuilder":
        self._business_offer = True
        self._nip = "7770020640"
        self._phone = "791233545"
        return self

    def with_required_terms(self) -> "RegisterUserDataBuilder":
        self._accept_required_terms = True
        return self

    def with_marketing(self) -> "RegisterUserDataBuilder":
        self._accept_marketing = True
        return self

    def build(self) -> RegisterUserData:
        return RegisterUserData(
            email=self._email,
            password=self._password,
            password_changed=self._password_changed,
            business_offer=self._business_offer,
            accept_required_terms=self._accept_required_terms,
            accept_marketing=self._accept_marketing,
            nip=self._nip,
            phone=self._phone,
        )


def valid_client_cases() -> list[RegisterUserCase]:
    return [
        RegisterUserCase(
            case_id="pl_terms_marketing_business",
            factory=lambda: (
                RegisterUserDataBuilder().with_business_offer().with_required_terms().with_marketing().build()
            ),
        ),
        RegisterUserCase(
            case_id="pl_terms_marketing",
            factory=lambda: RegisterUserDataBuilder().with_required_terms().with_marketing().build(),
        ),
        RegisterUserCase(
            case_id="pl_terms_only",
            factory=lambda: RegisterUserDataBuilder().with_required_terms().build(),
        ),
    ]


def invalid_client_cases() -> list[RegisterUserCase]:
    return [
        RegisterUserCase(
            case_id="pl_marketing_business",
            factory=lambda: (
                RegisterUserDataBuilder().with_business_offer().with_marketing().build()
            ),
        ),
        RegisterUserCase(
            case_id="pl_marketing",
            factory=lambda: RegisterUserDataBuilder().with_marketing().build(),
        ),
        RegisterUserCase(
            case_id="pl_only",
            factory=lambda: RegisterUserDataBuilder().build(),
        ),
    ]


def prod_registered_client() -> RegisterUserData:
    return RegisterUserData(
        email="nc-test-user@komputronik.pl",
        password="UjK_$CE4pCRB9hjn$_eX",
        password_changed="",
        business_offer=True,
        accept_required_terms=True,
        accept_marketing=True,
        nip="7770020640",
        phone="791233545",
    )
