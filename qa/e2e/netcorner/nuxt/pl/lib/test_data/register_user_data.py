from dataclasses import dataclass
import uuid
from collections.abc import Callable


@dataclass
class RegisterUserData:
    email: str
    password: str
    repeated_password: str
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
        self._email = f"client_{unique}@test.pl"  #  Mailhog nie lubi domeny netcorner bo Wosina
        self._password = unique
        self._repeated_password = unique
        self._business_offer = False
        self._accept_required_terms = False
        self._accept_marketing = False
        self._nip = ""
        self._phone = ""

    def with_wrong_repeated_password(self) -> "RegisterUserDataBuilder":
        self._repeated_password = uuid.uuid4().hex[:8]
        return self

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
            repeated_password=self._repeated_password,
            business_offer=self._business_offer,
            accept_required_terms=self._accept_required_terms,
            accept_marketing=self._accept_marketing,
            nip=self._nip,
            phone=self._phone,
        )


def valid_clients() -> list[RegisterUserData]:
    return [case.factory() for case in valid_client_cases()]


def valid_client_cases() -> list[RegisterUserCase]:
    return [
        RegisterUserCase(
            case_id="b2b_terms_marketing",
            factory=lambda: (
                RegisterUserDataBuilder().with_business_offer().with_required_terms().with_marketing().build()
            ),
        ),
        RegisterUserCase(
            case_id="b2c_terms_marketing",
            factory=lambda: RegisterUserDataBuilder().with_required_terms().with_marketing().build(),
        ),
        RegisterUserCase(
            case_id="b2c_terms_only",
            factory=lambda: RegisterUserDataBuilder().with_required_terms().build(),
        ),
    ]


def invalid_clients() -> list[RegisterUserData]:
    return [
        RegisterUserDataBuilder().with_business_offer().with_marketing().build(),
        RegisterUserDataBuilder().with_marketing().build(),
        RegisterUserDataBuilder().with_business_offer().build(),
        RegisterUserDataBuilder().with_wrong_repeated_password().build(),
    ]


def registered_client() -> RegisterUserData:
    return RegisterUserData(
        email="nc-test-user@komputronik.pl",
        password="UjK_$CE4pCRB9hjn$_eX",
        repeated_password="UjK_$CE4pCRB9hjn$_eX",
        business_offer=True,
        accept_required_terms=True,
        accept_marketing=True,
        nip="7770020640",
        phone="791233545",
    )
