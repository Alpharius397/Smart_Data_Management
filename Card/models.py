from django.db.models import (  # type: ignore
    SET_NULL,
    CharField,
    Model,
    DateTimeField,
    ForeignKey,
    RESTRICT,
    TextField,
)
from University.models import Branch
from User.models import User


class Card(Model):
    cardID: str = CharField(  # type: ignore
        max_length=200,
        null=False,
        blank=False,
        verbose_name="Card ID",
        primary_key=True,
    )

    data = TextField(
        default="", null=True, blank=False, verbose_name="Card Data (Encrypted)"
    )  # type: ignore

    done_by = ForeignKey(
        to=User, on_delete=SET_NULL, null=True, blank=False, default=None
    )

    last_write = DateTimeField(
        verbose_name="Time of Last Write", null=True, blank=False, default=None
    )

    belongs = ForeignKey(  # type: ignore
        to=Branch, null=False, blank=False, on_delete=RESTRICT
    )

    decryption_key = CharField(  # type: ignore
        max_length=200,
        null=False,
        blank=False,
        verbose_name="Key used to decrypt this",
    )

    class Meta:
        verbose_name = "Card"
        verbose_name_plural = "Cards"

    def __str__(self) -> str:
        return f"{self.cardID}"
