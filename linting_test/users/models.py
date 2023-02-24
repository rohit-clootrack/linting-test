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


class ReportModel(TimeStampedModel):
    name = models.CharField(max_length=256, db_index=True, unique=True)


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


class TimeStampedModel(Model):
    created_on = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        abstract = True


class Choices(Enum):
    @classmethod
    def choices(cls):
        return tuple((key.value, key.name) for key in cls)


class FilterColumnName(Choices):
    L1 = "L1"
    L2 = "L2"
    BRAND = "BRAND"
    PRICE_RANGE = "PRICE_RANGE"


class FilterSelectionType(Choices):
    SINGLE_SELECT = "SINGLE_SELECT "
    MULTI_SELECT = "MULTI_SELECT"
    DATE_RANGE = "DATE_RANGE"
    RANGE = "RANGE"


class FilterType(Choices):
    DEFAULT = "DEFAULT"
    CUSTOM = "CUSTOM"


class TableType(Choices):
    STANDARD_TABLE = "STANDARD_TABLE"
    CUSTOM_TABLE = "CUSTOM_TABLE"


class DataSourceOrigin(Choices):
    CLUSTERING = "CLUSTERING"
    ANALYSIS_MODULE_1 = "ANALYSIS_MODULE_1"
    ANALYSIS_MODULE_2 = "ANALYSIS_MODULE_2"


class TableSchemaDataType(Choices):
    CHAR = "CHAR"
    INT = "INT"
    FLOAT = "FLOAT"
    DATETIME = "DATETIME"


class TablePrepStoreStatus(Choices):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    QC = "QC"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class TemplateStoreStatus(Choices):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    QC = "QC"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class PrepStoreParamType(Choices):
    INPUT_PARAM = "INPUT_PARAM"
    OUTPUT_PARAM = "OUTPUT_PARAM"


class TemplateType(Choices):
    CUSTOM = "CUSTOM"
    STANDARD = "STANDARD"


# TODO: insert correct preprocessing names
class PreProcessingScript(Choices):
    XYZ = "XYZ"
    ABC = "ABC"


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
    data_source_origin = models.CharField(
        max_length=256, default="", blank=True, choices=DataSourceOrigin.choices()
    )
    deleted = models.BooleanField(default=False)


class TableSchema(TimeStampedModel):
    table = models.ForeignKey(
        TableStore, on_delete=models.CASCADE, related_name="table_schemas"
    )
    column_name = models.CharField(max_length=512)
    type = models.CharField(max_length=64, choices=TableSchemaDataType.choices())
    nullable = models.BooleanField(default=False)
    is_filter_column = models.BooleanField(default=True)


class TableauPrepStore(TimeStampedModel):
    name = models.CharField(max_length=512)
    description = models.TextField()
    filepath = models.URLField()
    flow_id = models.CharField(max_length=64)
    status = models.CharField(max_length=64, choices=TablePrepStoreStatus.choices())


class TableauPrepStoreParam(TimeStampedModel):
    prep_store = models.ForeignKey(
        TableauPrepStore, on_delete=models.CASCADE, related_name="prep_store_params"
    )
    name = models.CharField(max_length=512)
    type = models.CharField(max_length=64, choices=PrepStoreParamType.choices())
    flow_param_id = models.CharField(max_length=64)


class TemplateStore(TimeStampedModel):
    project_name = models.CharField(max_length=512, blank=True, default="")
    name = models.CharField(max_length=512)
    type = models.CharField(max_length=64, choices=TemplateType.choices())
    filepath = models.URLField()
    summary = models.TextField()
    deleted = models.BooleanField(default=False)
    pre_processing_scripts = ArrayField(
        models.CharField(
            max_length=128, choices=PreProcessingScript.choices(), blank=True
        )
    )
    input_tables = models.ManyToManyField(
        TableStore, related_name="input_table_template_stores"
    )
    prep_flows = models.ManyToManyField(
        TableauPrepStore, related_name="prep_flow_template_stores"
    )
    master_flow = models.ForeignKey(
        TableauPrepStore,
        on_delete=models.SET_NULL,
        null=True,
        related_name="master_flow_template_stores",
    )
    status = models.CharField(
        max_length=64, choices=TemplateStoreStatus.choices(), blank=True
    )
    qc_reports = models.ManyToManyField(
        ReportModel, related_name="qc_reports_template_stores"
    )
    qc_approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="qc_approved_by_template_stores",
    )
    last_modified_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="last_modified_by_template_stores",
    )


class VizDashboard(TimeStampedModel):
    template = models.ForeignKey(
        TemplateStore, on_delete=models.CASCADE, related_name="viz_dashboards"
    )
    name = models.CharField(max_length=512)
    description = models.TextField()
    allow_parameters = models.BooleanField()


class VizDashboardFilter(TimeStampedModel):
    dashboard = models.ForeignKey(
        VizDashboard, on_delete=models.CASCADE, related_name="viz_dashboard_filters"
    )
    display_name = models.CharField(max_length=512)
    filter_column_name = models.CharField(
        max_length=64, choices=FilterColumnName.choices(), blank=True
    )
    internal_filter_name = models.CharField(max_length=64, blank=True)
    filter_type = models.CharField(
        max_length=64, choices=FilterType.choices(), blank=True
    )
    filter_selection_type = models.CharField(
        max_length=64, choices=FilterSelectionType.choices(), blank=True
    )


class VizDashboardParam(TimeStampedModel):
    dashboard = models.ForeignKey(
        VizDashboard, on_delete=models.CASCADE, related_name="viz_dashboard_params"
    )
    internal_name = models.CharField(max_length=512)
    display_name = models.CharField(max_length=512)
    values = ArrayField(models.CharField(max_length=512))
