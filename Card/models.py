from django.db.models import (
    SET_NULL,
    CharField,
    Model,
    ForeignKey,
    OneToOneField,
)  # type: ignore
from django.core.validators import MinValueValidator, RegexValidator  # type: ignore
from User.models import User, RoleType
from Upload.models import UploadTable, DataTable

MongoID = RegexValidator(r"^[0-9a-f]{24}$", message="Invalid MongoID")


class Card(Model):
    cardID: str = CharField(  # type: ignore
        max_length=200,
        null=False,
        blank=False,
        verbose_name="Card ID",
        primary_key=True,
    )

    data: DataTable = OneToOneField(  # type: ignore
        to=DataTable, on_delete=SET_NULL, default=None, null=True, blank=False
    )

    user: User = ForeignKey(  # type: ignore
        to=User,
        on_delete=SET_NULL,
        default=None,
        null=True,
        blank=False,
        limit_choices_to={"role__role": RoleType.ADMIN},
    )

    class Meta:
        verbose_name = "Card"
        verbose_name_plural = "Cards"

    def __str__(self) -> str:
        dataID: int | None = self.data if (self.data is None) else self.data.id
        return f"{self.cardID} => {dataID}"

    @staticmethod
    def attemptSave(cardID: str, mongoID: str, rowIndex: int, user: User) -> bool:
        try:
            Card(cardID=cardID, mongoID=mongoID, rowIndex=rowIndex, user=user).save()
            return True
        except Exception:
            return False

    def save(self, *args, **kwargs):
        self.clean_fields()
        super().save(*args, **kwargs)
