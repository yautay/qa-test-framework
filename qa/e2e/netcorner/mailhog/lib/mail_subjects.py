from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class MailSubjectPattern:
    key: str
    regex: str
    description: str

    def compiled(self) -> re.Pattern[str]:
        return re.compile(self.regex)


class MailSubjects:
    PASSWORD_RESET = MailSubjectPattern(
        key="password_reset",
        regex=r"^Odzyskanie hasła - Komputronik\.pl$",
        description="Mail odzyskiwania hasła",
    )

    LOGIN = MailSubjectPattern(
        key="login",
        regex=r"^Logowanie$",
        description="Mail logowania",
    )

    NEW_USER_REGISTERED = MailSubjectPattern(
        key="new_user_registered",
        regex=r"^Zarejestrował się nowy użytkownik\.?$",
        description="Mail o nowej rejestracji",
    )

    ORDER_PROBLEM = MailSubjectPattern(
        key="order_problem",
        regex=r"^Komputronik\.pl - Problem z zamówieniem$",
        description="Mail o problemie z zamówieniem",
    )

    @staticmethod
    def order_shop_number(shop_host: str, order_number: str | None = None) -> MailSubjectPattern:
        escaped_shop_host = re.escape(str(shop_host or "").strip())
        if not escaped_shop_host:
            raise ValueError("shop_host is required")

        escaped_order_number = re.escape(order_number) if order_number else r"[A-Z]*\d+/\d{4}"
        return MailSubjectPattern(
            key=f"order_shop_{shop_host}",
            regex=rf"^Zamówienie sklepu\s+{escaped_shop_host}\s+numer:\s*{escaped_order_number}$",
            description=f"Mail zamówienia dla sklepu {shop_host}",
        )

    @staticmethod
    def order_summary_komputronik(order_number: str | None = None) -> MailSubjectPattern:
        escaped_order_number = re.escape(order_number) if order_number else r"\d+/\d{4}"
        return MailSubjectPattern(
            key="order_summary_komputronik",
            regex=rf"^(?:★\s*)?Zamówienie\s+{escaped_order_number}\s*-\s*Komputronik\.pl$",
            description="Mail podsumowania zamówienia Komputronik.pl",
        )
