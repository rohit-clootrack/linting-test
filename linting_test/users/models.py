from enum import Enum

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.contrib.postgres.fields import ArrayField, JSONField
from django.core.handlers.wsgi import WSGIRequest
from django.db import models
from django.db.models import CharField, Model
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django_bulk_update.manager import BulkUpdateManager


class User(AbstractUser):
    """
    Default custom user model for Linting-test.
    If adding fields that need to be filled at user signup,
    check forms.SignupForm and forms.SocialSignupForms accordingly.
    """

    #: First and last name do not cover name patterns around the globe
    name = CharField(_("Name of User"), blank=True, max_length=255)
    first_name = None  # type: ignore
    last_name = None  # type: ignore

    def get_absolute_url(self):
        """Get url for user's detail view.

        Returns:
            str: URL for user detail.

        """
        return reverse("users:detail", kwargs={"username": self.username})


class Choices(Enum):
    @classmethod
    def choices(cls):
        return tuple((key.value, key.name) for key in cls)


class FilterName(Choices):
    L1 = "L1"
    L2 = "L2"
    BRAND = "BRAND"
    PRICE_RANGE = "PRICE_RANGE"


class InternalFilterName(Choices):
    FILTER_1 = "FILTER_1"
    FILTER_2 = "FILTER_2"
    FILTER_3 = "FILTER_3"


class FilterType(Choices):
    SINGLE_SELECT = "SINGLE_SELECT "
    MULTI_SELECT = "MULTI_SELECT"
    DATE_RANGE = "DATE_RANGE"
    RANGE = "RANGE"


class TableType(Choices):
    STANDARD_TABLE = "STANDARD_TABLE"
    CUSTOM_TABLE = "CUSTOM_TABLE"


class TableSchemaType(Choices):
    CHAR = "CHAR"
    INT = "INT"
    FLOAT = "FLOAT"
    DATETIME = "DATETIME"


class TablePrepStoreStatus(Choices):
    PUBLISHED = "PUBLISHED"
    QC = "QC"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class PrepStoreParamType(Choices):
    INPUT_PARAM = "INPUT_PARAM"
    OUTPUT_PARAM = "OUTPUT_PARAM"


class TimeStampedModel(Model):
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class TableauProjects(TimeStampedModel):
    # TODO: remove null in client
    name = models.CharField(max_length=256, unique=True, db_index=True)

    objects = BulkUpdateManager()

    class Meta:
        verbose_name_plural = "Tableau Projects"

    def __str__(self):
        return f"{self.name}"


class TableStore(TimeStampedModel):
    name = models.CharField(max_length=128)
    description = models.TextField()
    type = models.CharField(max_length=128, choices=TableType.choices())
    table_source = models.CharField(
        max_length=256, default="", blank=True
    )  # custom input vs analysis input


class TableSchema(TimeStampedModel):
    table = models.ForeignKey(
        TableStore, on_delete=models.CASCADE, related_name="table_schema"
    )
    column_name = models.CharField(max_length=512)
    type = models.CharField(max_length=256, choices=TableSchemaType.choices())
    nullable = models.BooleanField()
    is_filter_column = models.BooleanField(default=True)


class TableauPrepStore(TimeStampedModel):
    name = models.CharField(max_length=512)
    description = models.TextField()
    reference_id = models.CharField(max_length=64)
    status = models.CharField(max_length=256, choices=TablePrepStoreStatus.choices())


class TableauPrepStoreParam(TimeStampedModel):
    prep_flow = models.ForeignKey(
        TableauPrepStore, on_delete=models.CASCADE, related_name="prep_store_param"
    )
    name = models.CharField()
    type = models.CharField(max_length=256, choices=PrepStoreParamType.choices())
    reference_id = models.CharField(max_length=64)


class Template(TimeStampedModel):
    name = models.CharField()
    type = models.CharField()
    filepath = models.URLField()
    project = models.ForeignKey(
        TableauProjects, on_delete=models.CASCADE, related_name="template"
    )
    data_sources = ArrayField(models.CharField(max_length=512))
    summary = models.TextField()
    pre_processing_scripts = ArrayField(
        models.CharField(max_length=256, choices=FilterType.choices(), blank=True)
    )
    input_tables = ArrayField(models.ForeignKey(TableStore, on_delete=models.CASCADE))
    prep_flows = ArrayField(
        models.ForeignKey(TableauPrepStore, on_delete=models.CASCADE)
    )
    master_flow = models.ForeignKey(TableauPrepStore, on_delete=models.CASCADE)


class VizReport(TimeStampedModel):
    project = models.ForeignKey(
        TableauProjects, on_delete=models.CASCADE, related_name="viz_report"
    )
    beagle_report_id = models.IntegerField(null=True, blank=True)
    display_name = models.CharField(max_length=512)
    title = models.CharField(max_length=512)
    url = models.URLField(default="", blank=True)
    is_edit_allowed = models.BooleanField(default=False)
    refresh_in_progress = models.BooleanField(default=False)
    is_refresh_insights_required = models.BooleanField(default=False)
    is_accessible_to_user = models.BooleanField(default=False)
    latest_refresh_time = models.DateTimeField(blank=True, null=True)
    last_processing_time = models.FloatField(null=True, blank=True)


class VizWorkbook(TimeStampedModel):
    report = models.ForeignKey(
        VizReport, on_delete=models.CASCADE, related_name="viz_workbook"
    )
    name = models.CharField(max_length=512)
    template = models.ForeignKey(
        Template, on_delete=models.CASCADE, related_name="viz_workbook"
    )


class VizDashboard(TimeStampedModel):
    workbook = models.ForeignKey(
        VizWorkbook, on_delete=models.CASCADE, related_name="viz_dashboard"
    )
    name = models.CharField(max_length=512)
    url = models.URLField(default="", blank=True)
    sequence_no = models.IntegerField(null=True, blank=True)
    external_filter_config = JSONField(default=dict, blank=True)


class VizDashboardFilter(TimeStampedModel):
    dashboard = models.ForeignKey(
        VizDashboard, on_delete=models.CASCADE, related_name="viz_dashboard_filter"
    )
    display_name = models.CharField(max_length=512)
    filter_column_name = models.CharField(
        max_length=256, choices=FilterName.choices(), blank=True
    )
    internal_filter_name = models.CharField(
        max_length=256, choices=InternalFilterName.choices(), blank=True
    )
    filter_type = models.CharField(
        max_length=256, choices=FilterType.choices(), blank=True
    )
    sequence_no = models.IntegerField(null=True, blank=True)


class VizDashboardParam(TimeStampedModel):
    dashboard = models.ForeignKey(
        VizDashboard, on_delete=models.CASCADE, related_name="viz_dashboard_param"
    )
    internal_name = models.CharField(max_length=512)
    display_name = models.CharField(max_length=512)
    values = ArrayField(models.CharField(max_length=512))
