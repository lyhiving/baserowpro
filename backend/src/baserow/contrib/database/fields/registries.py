from typing import TYPE_CHECKING, Any, Dict, List, NoReturn, Optional, Tuple, Union
from zipfile import ZipFile

from django.contrib.auth.models import AbstractUser
from django.contrib.postgres.aggregates import StringAgg
from django.contrib.postgres.fields import ArrayField
from django.contrib.postgres.fields import JSONField as PostgresJSONField
from django.core.exceptions import ValidationError
from django.core.files.storage import Storage
from django.db import models as django_models
from django.db.models import (
    BooleanField,
    CharField,
    DurationField,
    Expression,
    JSONField,
    Model,
    OuterRef,
    Q,
    QuerySet,
    Subquery,
    Value,
)
from django.db.models.fields.related import ForeignKey, ManyToManyField
from django.db.models.functions import Cast, Coalesce

from rest_framework.serializers import CharField as SerializerCharField

from baserow.contrib.database.fields.constants import UPSERT_OPTION_DICT_KEY
from baserow.contrib.database.fields.field_sortings import OptionallyAnnotatedOrderBy
from baserow.contrib.database.types import SerializedRowHistoryFieldMetadata
from baserow.core.registries import ImportExportConfig
from baserow.core.registry import (
    APIUrlsInstanceMixin,
    APIUrlsRegistryMixin,
    CustomFieldsInstanceMixin,
    CustomFieldsRegistryMixin,
    Instance,
    MapAPIExceptionsInstanceMixin,
    ModelInstanceMixin,
    ModelRegistryMixin,
    Registry,
)

from .deferred_field_fk_updater import DeferredFieldFkUpdater
from .exceptions import (
    FieldTypeAlreadyRegistered,
    FieldTypeDoesNotExist,
    ReadOnlyFieldHasNoInternalDbValueError,
)
from .fields import DurationFieldUsingPostgresFormatting
from .models import Field, LinkRowField, SelectOption

if TYPE_CHECKING:
    from baserow.contrib.database.fields.dependencies.handler import FieldDependants
    from baserow.contrib.database.fields.dependencies.types import FieldDependencies
    from baserow.contrib.database.fields.dependencies.update_collector import (
        FieldUpdateCollector,
    )
    from baserow.contrib.database.fields.field_cache import FieldCache
    from baserow.contrib.database.table.models import (
        FieldObject,
        GeneratedTableModel,
        Table,
    )

StartingRowType = Union["GeneratedTableModel", List["GeneratedTableModel"]]


class FieldType(
    MapAPIExceptionsInstanceMixin,
    APIUrlsInstanceMixin,
    CustomFieldsInstanceMixin,
    ModelInstanceMixin,
    Instance,
):

    """
    This abstract class represents a custom field type that can be added to the
    field type registry. It must be extended so customisation can be done. Each field
    type will have its own model that must extend the Field model, this is needed so
    that the user can set custom settings per field instance they have created.

    Example:
        from baserow.contrib.database.fields.models import Field
        from baserow.contrib.database.fields.registry import (
            FieldType, field_type_registry
        )

        class ExampleFieldModel(Field):
            pass

        class ExampleFieldType(FieldType):
            type = 'a-unique-field-type-name'
            model_class = ExampleFieldModel
            allowed_fields = ['text_default']
            serializer_field_names = ['text_default']
            serializer_field_overrides = {
                'text_default': serializers.CharField()
            }

        field_type_registry.register(ExampleFieldType())
    """

    _can_order_by = True
    """Indicates whether it is possible to order by this field type."""

    can_be_primary_field = True
    """Some field types cannot be the primary field."""

    can_have_select_options = False
    """Indicates whether the field can have select options."""

    can_be_in_form_view = True
    """Indicates whether the field is compatible with the form view."""

    can_get_unique_values = True
    """
    Indicates whether this field can generate a list of unique values using the
    `FieldHandler::get_unique_row_values` method.
    """

    _can_group_by = False
    """Indicates whether it is possible to group by by this field type."""

    read_only = False
    """Indicates whether the field allows inserting/updating row values or if it is
    read only."""

    keep_data_on_duplication = True
    """
    Indicates whether the data must be kept when duplicating the field. We typically
    don't want to do this when the field is read_only, but there are exceptions with
    the read-only UUID field type for example
    """

    field_data_is_derived_from_attrs = False
    """Set this to True if your field can completely reconstruct it's data just from
    it's field attributes. When set to False the fields data will be backed up when
    updated to a different type so an undo is possible. When True is backup isn't needed
    and so isn't done as we can get the data back from simply restoring the attributes.
    """

    needs_refresh_after_import_serialized = False
    """Set this to True your after_import_serialized function can cause the field
    data to change and hence it needs to be refreshed after this function has run
    inside of the import process.
    """

    is_many_to_many_field = False
    """
    Set this to True if the underlying database field is a ManyToManyField. This
    let the RowM2MChangeTracker to track changes to the field when creating/updating
    values without having to query the database.
    """

    update_always = False
    """
    Set to True if the field value should be updated in update operations at
    all times.
    """

    def prepare_value_for_db(self, instance: Field, value: Any) -> Any:
        """
        When a row is created or updated all the values are going to be prepared for the
        database. The value for this field type will run through this method and the
        returned value will be used. It is also possible to raise validation errors if
        the value is incorrect.

        :param instance: The field instance.
        :param value: The value that needs to be inserted or updated.
        :return: The modified value that is going to be saved in the database.
        """

        return value

    def get_search_expression(self, field: Field, queryset: QuerySet) -> Expression:
        """
        When a field/row is created, updated or restored, this `FieldType` method
        must return a django expression that can be cast to string that will be used
        to create this fields search index column.
        """

        return Cast(field.db_column, output_field=CharField())

    def is_searchable(self, field: Field) -> bool:
        """
        If this field needs a tsv search index column made for it then this should
        return True. If True is returned then get_search_expression should also
        be implemented.
        """

        return True

    def get_internal_value_from_db(
        self, row: "GeneratedTableModel", field_name: str
    ) -> Any:
        """
        This method is the counterpart of `prepare_value_for_db`.
        It will return the internal value of the field starting from the database value
        for non read_only fields.
        It isn't meant to be used for reporting, since ReadOnlyFieldType instances will
        not return a value.

        :param row: The row instance.
        :param field_name: The name of the field.
        :return: The value of the field ready to be JSON serializable.
        """

        return getattr(row, field_name)

    def prepare_value_for_db_in_bulk(
        self,
        instance: Field,
        values_by_row: Dict[str, Any],
        continue_on_error: bool = False,
    ) -> Dict[str, Union[Any, Exception]]:
        """
        This method will work for every `prepare_value_for_db` that doesn't
        execute a query. Fields that do should override this method.

        :param instance: The field instance.
        :param values_by_row: The values that needs to be inserted or updated,
            indexed by row id as dict(index, values).
        :param continue_on_error: True if you want to continue on any value validation
            error. In this case the returned value dict can contain exception instead of
            the prepared value.
        :return: The modified values in the same structure as it was passed in.
            If the parameter `continue_on_error` is true, the values of the result dict
            can be the exceptions raised during the values validation.
        """

        for row_index, value in values_by_row.items():
            try:
                values_by_row[row_index] = self.prepare_value_for_db(instance, value)
            except Exception as e:
                if continue_on_error:
                    values_by_row[row_index] = e
                else:
                    raise

        return values_by_row

    def enhance_queryset(self, queryset: QuerySet, field: Field, name: str) -> QuerySet:
        """
        This hook can be used to enhance a queryset when fetching multiple rows of a
        table. This is for example used by the grid view endpoint. Many rows can be
        requested there and if the table has a `link_row` field it can become slow
        because the .all() method of the ManyToMany field is called for every row.
        In case of the `link_row` field we could enhance the queryset by using the
        `prefetch_related` function in order to prevent many queries.

        Note that the enhance_queryset will be called for each field in the table. So
        this hook should only optimise the queryset for the provided field.

        :param queryset: The queryset that can be enhanced.
        :type: QuerySet
        :param field: The related field's instance. The queryset can optionally be
            enhanced based on the properties of the field.
        :type field: Field
        :param name: The name of the field.
        :type name: str
        :return: The enhanced queryset.
        :rtype: QuerySet
        """

        return queryset

    def enhance_queryset_in_bulk(
        self, queryset: QuerySet, field_objects: List[dict]
    ) -> QuerySet:
        """
        This hook is similar to the `enhance_queryset` method, but combined for all
        the fields of the same type. This can for example be used to efficiently
        fetch all select options of N number of single select fields.

        :param queryset: The queryset that can be enhanced.
        :param field_objects: All field objects of the same type in the table that
            must be enhanced.
        :return: The enhanced queryset.
        """

        # By default, the `enhance_queryset` of the field type is called for all the
        # fields. Typically, this will be overridden if the queryset is enhanced in
        # bulk.
        for field_object in field_objects:
            queryset = self.enhance_queryset(
                queryset, field_object["field"], field_object["name"]
            )
        return queryset

    def empty_query(
        self,
        field_name: str,
        model_field: django_models.Field,
        field: Field,
    ) -> Q:
        """
        Returns a Q filter which performs an empty filter over the
        provided field for this specific type of field.

        :param field_name: The name of the field.
        :param model_field: The field's actual django field model instance.
        :param field: The related field's instance.
        :return: A Q filter.
        """

        empty_is_null_model_field_types = (
            ManyToManyField,
            ForeignKey,
            DurationField,
            ArrayField,
            DurationFieldUsingPostgresFormatting,
        )
        # If the model_field is a ManyToMany field we only have to check if it is None.
        if isinstance(model_field, empty_is_null_model_field_types):
            return Q(**{f"{field_name}": None})

        if isinstance(model_field, BooleanField):
            return Q(**{f"{field_name}": False})

        q = Q(**{f"{field_name}__isnull": True})
        q = q | Q(**{f"{field_name}": None})

        empty_is_empty_list_or_object_model_field_types = (JSONField, PostgresJSONField)
        if isinstance(model_field, empty_is_empty_list_or_object_model_field_types):
            q = q | Q(**{f"{field_name}": []}) | Q(**{f"{field_name}": {}})

        # If the model field accepts an empty string as value we are going to add
        # that to the or statement.
        try:
            model_field.get_prep_value("")
            q = q | Q(**{f"{field_name}": ""})
            return q
        except Exception:
            return q

    def contains_query(self, field_name, value, model_field, field):
        """
        Returns a Q or AnnotatedQ filter which performs a contains filter over the
        provided field for this specific type of field.

        :param field_name: The name of the field.
        :type field_name: str
        :param value: The value to check if this field contains or not.
        :type value: str
        :param model_field: The field's actual django field model instance.
        :type model_field: models.Field
        :param field: The related field's instance.
        :type field: Field
        :return: A Q or AnnotatedQ filter.
            given value.
        :rtype: OptionallyAnnotatedQ
        """

        return Q()

    def contains_word_query(self, field_name, value, model_field, field):
        """
        Returns a Q or AnnotatedQ filter which performs a regex filter over the
        provided field for this specific type of field.

        :param field_name: The name of the field.
        :type field_name: str
        :param value: The value to check if this field contains as a whole word or not.
        :type value: str
        :param model_field: The field's actual django field model instance.
        :type model_field: models.Field
        :param field: The related field's instance.
        :type field: Field
        :return: A Q or AnnotatedQ filter.
            given value.
        :rtype: OptionallyAnnotatedQ
        """

        return Q()

    def get_serializer_field(self, instance, **kwargs):
        """
        Should return the serializer field based on the custom model instance
        attributes. It is common that the field is not required so that a user
        doesn't have to update the field each time another field in the same row
        changes.

        :param instance: The field instance for which to get the serializer field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The serializer field that represents the field instance attributes.
        :rtype: serializer.Field
        """

        raise NotImplementedError("Each must have his own get_serializer_field method.")

    def get_response_serializer_field(self, instance, **kwargs):
        """
        The response serializer field can be overridden if the field's value should be
        represented in a different way when the value is included in a response. This
        will for example happen with a user lists all the rows in the grid view,
        but also in the response after creating a row. By default the serializer that
        also handles the validation and input is returned here.

        :param instance: The field instance for which to get the model field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The serializer field that represents the field instance attributes.
        :rtype: serializer.Field
        """

        return self.get_serializer_field(instance, **kwargs)

    def get_serializer_help_text(self, instance):
        """
        If some additional information in the documentation related to the field's type
        is required then that can be returned here. It will be added to the
        `create_database_table_row` part.

        :param instance:
        :type: Struct
        :return: The additional field documentation.
        :rtype: str
        """

        return ""

    def get_model_field(self, instance, **kwargs):
        """
        Should return the model field based on the custom model instance attributes. It
        is common that the field can be blank because people are going to create a row
        without any data in it.

        :param instance: The field instance for which to get the model field for.
        :type instance: Field
        :param kwargs: The kwargs that will be passed to the field.
        :type kwargs: dict
        :return: The model field that represents the field instance attributes.
        :rtype: model.Field
        """

        raise NotImplementedError("Each must have his own get_model_field method.")

    def has_compatible_model_fields(self, instance, instance2) -> bool:
        """
        Returns True if the provided instances have compatible model fields.
        """

        return type(instance) == type(instance2)

    def after_model_generation(self, instance, model, field_name):
        """
        After the model is generated the after_model_generation method of each field
        is also called to make some additional changes when whole model is available.
        This is for example used by the LinkRow field so that the ManyToMany field
        can be added later.

        :param instance: The field instance object.
        :type instance: Field
        :param model: The generated model containing all fields.
        :type model: Model
        :param field_name: The given name of the field in the model.
        :type field_name: str
        """

    def random_value(self, instance, fake, cache):
        """
        Should return a random value that can be used as value for the field. This is
        used by the fill_table management command which will add an N amount of rows
        to the table with random data.

        :param instance: The field instance for which to get the random value for.
        :type instance: Field
        :param fake: An instance of the Faker package.
        :type fake: Faker
        :param cache: A small in memory cache dict that can be used to store data
            that is needed for to generate a random value.
        :type dict: dict
        :return: The randomly generated value.
        :rtype: any
        """

        return None

    def get_alter_column_prepare_old_value(self, connection, from_field, to_field):
        """
        Can return an SQL statement to convert the `p_in` variable to a readable text
        format for the new field.
        This SQL will not be run when converting between two fields of the same
        baserow type which share the same underlying database column type.
        If you require this then implement force_same_type_alter_column.

        Example: return "p_in = lower(p_in);"

        :param connection: The used connection. This can for example be used to check
            the database engine type.
        :type connection: DatabaseWrapper
        :param from_field: The old field instance.
        :type to_field: Field
        :param to_field: The new field instance.
        :type to_field: Field
        :return: The SQL statement converting the value to text for the next field. The
            can for example be used to convert a select option to plain text.
        :rtype: None or str
        """

        return None

    def get_alter_column_prepare_new_value(self, connection, from_field, to_field):
        """
        Can return a SQL statement to convert the `p_in` variable from text to a
        desired format for the new field.
        This SQL will not be run when converting between two fields of the same
        baserow type which share the same underlying database column type.
        If you require this then implement force_same_type_alter_column.

        Example: when a string is converted to a number, to statement could be:
        `REGEXP_REPLACE(p_in, '[^0-9]', '', 'g')` which would remove all non numeric
        characters. The p_in variable is the old value as a string.

        :param connection: The used connection. This can for example be used to check
            the database engine type.
        :type connection: DatabaseWrapper
        :param from_field: The old field instance.
        :type to_field: Field
        :param to_field: The new field instance.
        :type to_field: Field
        :return: The SQL statement converting the old text value into the correct
            format.
        :rtype: None or str
        """

        return None

    def prepare_values(self, values, user):
        """
        The prepare_values hook gives the possibility to change the provided values
        that just before they are going to be used to create or update the instance. For
        example if an ID is provided, it can be converted to a model instance. Or to
        convert a certain date string to a date object.

        :param values: The provided values.
        :type values: dict
        :param user: The user on whose behalf the change is made.
        :type user: User
        :return: The updates values.
        :type: dict
        """

        return values

    def get_request_kwargs_to_backup(
        self, field: Field, kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Returns a dict of attributes that should be backed up when the field is
        updated. These attributes are sent in the request body but are not
        stored in the database field model. This is for example used by the
        DateField to replace the timezone adding/subtracting the corresponding
        timedelta.

        :param field: The field to update.
        :param kwargs: The kwargs that are passed to the update request.
        :return: A dict of attributes that should be backed up.
        """

        return {}

    def export_prepared_values(self, field: Field):
        """
        Returns a serializable dict of prepared values for the fields attributes.
        This method is the counterpart of `prepare_values`. It is called
        by undo/redo ActionHandler to store the values in a way that could be
        restored later on in in the UpdateField handler calling the `update_field`
        method with values.

        :param field: The field
        :return: A dict of prepared values for the provided fields.
        """

        values = {
            "name": field.name,
        }

        values.update({key: getattr(field, key) for key in self.allowed_fields})

        if self.can_have_select_options:
            values["select_options"] = [
                {
                    UPSERT_OPTION_DICT_KEY: select_option.id,
                    "value": select_option.value,
                    "color": select_option.color,
                    "order": select_option.order,
                }
                for select_option in field.select_options.all()
            ]

        return values

    def before_create(
        self, table, primary, allowed_field_values, order, user, field_kwargs
    ):
        """
        This cook is called just before the fields instance is created. Here
        some additional checks can be done based on the provided values.

        :param table: The table where the field is going to be added to.
        :type table: Table
        :param primary: Indicates whether the field is going to be a primary
            field.
        :type primary: bool
        :param allowed_field_values: The new values that are going to be passed
            when creating the field instance.
        :type field_values: dict
        :param order: The order that the field is going to get in the database.
        :type order: int
        :param user: The user on whose behalf the change is made.
        :type user: User
        :param field_kwargs: The kwargs that are going to be passed when
            creating the field instance.
        :type field_kwargs: dict
        """

    def after_create(self, field, model, user, connection, before, field_kwargs):
        """
        This hook is called right after the has been created. The schema change has
        also been done so the provided model could optionally be used.

        :param field: The created field instance.
        :type field: Field
        :param model: The Django model that contains the newly created field.
        :type model: Model
        :param user: The user on whose behalf the change is made.
        :type user: User
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        :param before: The value returned by the before_created method.
        :type before: any
        :param field_kwargs: The kwargs that were passed when creating the field
            instance.
        :type field_kwargs: dict
        """

    def before_update(self, from_field, to_field_values, user, field_kwargs):
        """
        This hook is called just before updating the field instance. It is called on
        the to (new) field type if it changes. Here some additional checks can be
        done based on the provided values.

        :param from_field: The old field instance.
        :type from_field: Field
        :param to_field_values: The values that are going to be updated.
        :type to_field_values: dict
        :param user: The user on whose behalf the change is made.
        :type user: User
        :field_kwargs: The kwargs that are going to be passed when updating the
            field instance.
        :type field_kwargs: dict
        """

    def before_schema_change(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        from_model_field,
        to_model_field,
        user,
        to_field_kwargs,
    ):
        """
        This hook is called just before the database's schema change. In some cases
        some additional cleanup or creation of related instances has to happen if the
        field type changes. That can happen here.

        :param from_field: The old field instance. It is not recommended to call the
            save function as this will undo part of the changes that have been made.
            This is just for comparing values.
        :type from_field: Field
        :param to_field: The updated field instance.
        :type: to_field: Field
        :param from_model: The old generated model containing only the old field.
        :type from_model: Model
        :param to_model: The generated model containing only the new field.
        :type to_model: Model
        :param from_model_field: The old field extracted from the old model.
        :type from_model_field: models.Field
        :param to_model_field: The new field extracted from the new model.
        :type to_model_field: models.Field
        :param user: The user on whose behalf the change is made.
        :type user: User
        :param to_field_kwargs: The kwargs that are going to be passed when updating
            the field instance.
        :type to_field_kwargs: dict
        """

    def after_update(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        user,
        connection,
        altered_column,
        before,
        to_field_kwargs,
    ):
        """
        This hook is called right after a field has been updated. In some cases data
        mutation still has to be done in order to maintain data integrity. For example
        when the only the allowing of negative values has been changed for the number
        field.

        :param from_field: The old field instance. It is not recommended to call the
            save function as this will undo part of the changes that have been made.
            This is just for comparing values.
        :type from_field: Field
        :param to_field: The updated field instance.
        :type: to_field: Field
        :param from_model: The old generated model containing only the old field.
        :type from_model: Model
        :param to_model: The generated model containing only the new field.
        :type to_model: Model
        :param user: The user on whose behalf the change is made.
        :type user: User
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        :param altered_column: Indicates whether the column has been altered in the
            table. Sometimes data has to be updated if the column hasn't been altered.
        :type altered_column: bool
        :param before: The value returned by the before_update method.
        :type before: any
        :param to_field_kwargs: The kwargs that were passed when updating the field
            instance.
        :type to_field_kwargs: dict
        """

    def after_delete(self, field, model, connection):
        """
        This hook is called right after the field has been deleted and the schema
        change has been done.

        :param field: The deleted field instance.
        :type field: Field
        :param model: The Django model that contains the deleted field.
        :type model: Model
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        """

    def get_order(
        self, field, field_name, order_direction
    ) -> OptionallyAnnotatedOrderBy:
        """
        This hook can be called to generate a different order by expression.
        By default the normal field sorting will be applied.
        Optionally a different expression can be generated. This is for example used
        by the single select field generates a mapping achieve the correct sorting
        based on the select option value.
        Additionally an annotation can be returned which will get applied to the
        queryset.
        If you are implementing this method you should also implement the
        get_value_for_filter method.

        :param field: The related field object instance.
        :type field: Field
        :param field_name: The name of the field.
        :type field_name: str
        :param order_direction: The sort order direction.
        :type order_direction: str (Either "ASC" or "DESC")
        :return: Either the expression that is added directly to the
            model.objects.order(), an AnnotatedOrderBy class or None.
        :rtype: Optional[Expression, AnnotatedOrderBy, None]
        """

        field_expr = django_models.F(field_name)

        if order_direction == "ASC":
            field_order_by = field_expr.asc(nulls_first=True)
        else:
            field_order_by = field_expr.desc(nulls_last=True)

        return OptionallyAnnotatedOrderBy(order=field_order_by, can_be_indexed=True)

    def force_same_type_alter_column(self, from_field, to_field):
        """
        Defines whether the sql provided by the get_alter_column_prepare_{old,new}_value
        hooks should be forced to run when converting between two fields of this field
        type which have the same database column type.
        You only need to implement this when you have validation and/or data
        manipulation running as part of your alter_column_prepare SQL which must be
        run even when from_field and to_field are the same Baserow field type and sql
        column type. If your field has the same baserow type but will convert into
        different sql column types then the alter sql will be run automatically and you
        do not need to use this override.

        :param from_field: The old field instance. It is not recommended to call the
            save function as this will undo part of the changes that have been made.
            This is just for comparing values.
        :type from_field: Field
        :param to_field: The updated field instance.
        :type: to_field: Field
        :return: Whether the alter column sql should be forced to run.
        :rtype: bool
        """

        return False

    def serialize_to_input_value(self, field: Field, value: any) -> any:
        """
        Converts the field's value to input value. For example, we can use this method
        to convert the result of random_value() to provide values to row actions
        such as UpdateRowsActionType.

        :param field: The field instance for which the provided value is intended.
        :param value: The field's value that we want to represent as input value.
        :return: Value represented as input value.
        """

        return value

    def export_serialized(
        self, field: Field, include_allowed_fields: bool = True
    ) -> Dict[str, Any]:
        """
        Exports the field to a serialized dict that can be imported by the
        `import_serialized` method. This dict is also JSON serializable.

        :param field: The field instance that must be exported.
        :param include_allowed_fields: Indicates whether or not the allowed fields
            should automatically be added to the serialized object.
        :return: The exported field in as serialized dict.
        """

        serialized = {
            "id": field.id,
            "type": self.type,
            "name": field.name,
            "order": field.order,
            "primary": field.primary,
        }

        if include_allowed_fields:
            for field_name in self.allowed_fields:
                serialized[field_name] = getattr(field, field_name)

        if self.can_have_select_options:
            serialized["select_options"] = [
                {
                    "id": select_option.id,
                    "value": select_option.value,
                    "color": select_option.color,
                    "order": select_option.order,
                }
                for select_option in field.select_options.all()
            ]

        return serialized

    def import_serialized(
        self,
        table: "Table",
        serialized_values: Dict[str, Any],
        import_export_config: ImportExportConfig,
        id_mapping: Dict[str, Any],
        deferred_fk_update_collector: DeferredFieldFkUpdater,
    ) -> Field:
        """
        Imported an exported serialized field dict that was exported via the
        `export_serialized` method.

        :param table: The table where the field should be added to.
        :param serialized_values: The exported serialized field values that need to
            be imported.
        :param id_mapping: The map of exported ids to newly created ids that must be
            updated when a new instance has been created.
        :param import_export_config: provides configuration options for the
            import/export process to customize how it works.
        :param deferred_fk_update_collector: An object than can be used to defer
            setting FK's to other fields until after all fields have been created
            and we know their IDs.
        :return: The newly created field instance.
        """

        if "database_fields" not in id_mapping:
            id_mapping["database_fields"] = {}

        if "database_field_select_options" not in id_mapping:
            id_mapping["database_field_select_options"] = {}

        serialized_copy = serialized_values.copy()
        field_id = serialized_copy.pop("id")
        serialized_copy.pop("type")
        select_options = (
            serialized_copy.pop("select_options")
            if self.can_have_select_options
            else []
        )
        should_create_tsvector_column = not import_export_config.reduce_disk_space_usage
        field = self.model_class(
            table=table,
            tsvector_column_created=should_create_tsvector_column,
            **serialized_copy,
        )
        field.save()

        id_mapping["database_fields"][field_id] = field.id

        if self.can_have_select_options:
            for select_option in select_options:
                select_option_copy = select_option.copy()
                select_option_id = select_option_copy.pop("id")
                select_option_object = SelectOption.objects.create(
                    field=field, **select_option_copy
                )
                id_mapping["database_field_select_options"][
                    select_option_id
                ] = select_option_object.id

        return field

    def after_import_serialized(
        self,
        field: Field,
        field_cache: "FieldCache",
        id_mapping: Dict[str, Any],
    ):
        """
        Called on fields in dependency order after all fields for an application have
        been created for any final tasks that require the field graph to be present.

        :param field: A field instance of this field type.
        :param field_cache: A field cache to be used when fetching fields.
        :param id_mapping:
        """

        from baserow.contrib.database.fields.dependencies.handler import (
            FieldDependencyHandler,
        )

        FieldDependencyHandler.rebuild_dependencies(field, field_cache)

    def after_rows_imported(
        self,
        field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        """
        Called on fields in dependency order after all of its rows have been inserted
        after an import for any row updates required once all rows in all imported
        tables exist.

        :param field: A field instance of this field type.
        :param field_cache: A field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table where the first rows were imported.
        :param update_collector: Any row update statements should be registered into
            this collector.
        """

        for (
            dependant_field,
            dependant_field_type,
            dependency_path,
        ) in field.dependant_fields_with_types(field_cache, via_path_to_starting_table):
            dependant_field_type.after_rows_imported(
                dependant_field, update_collector, field_cache, dependency_path
            )

    def after_rows_created(
        self,
        field: Field,
        rows: List["GeneratedTableModel"],
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
    ):
        """
        Immediately after a row has been created with a field of this type this
        method is called. This is useful fields that need to register some sort of
        update statement with the update_collector to correctly set their value after
        the row has been created.
        """

        pass

    def get_export_serialized_value(
        self,
        row: "GeneratedTableModel",
        field_name: str,
        cache: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> Any:
        """
        Exports the value to a the value of a row to serialized value that is also JSON
        serializable.

        :param row: The row instance that the value must be exported from.
        :param field_name: The name of the field that must be exported.
        :param cache: An in memory dictionary that is shared between all fields while
            exporting the table. This is for example used by the link row field type
            to prefetch all relations.
        :param files_zip: A zip file buffer where the files related to the template
            must be copied into.
        :param storage: The storage where the files can be loaded from.
        :return: The exported value.
        """

        return self.get_internal_value_from_db(row, field_name)

    def set_import_serialized_value(
        self,
        row: "GeneratedTableModel",
        field_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        cache: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> Optional[List[Model]]:
        """
        Sets an imported and serialized value on a row instance.

        :param row: The row instance where the value be set on.
        :param field_name: The name of the field that must be set.
        :param value: The value that must be set.
        :param files_zip: A zip file buffer where files related to the template can
            be extracted from.
        :param id_mapping: The map of exported ids to newly created ids that must be
            updated when a new instance has been created.
        :param cache: An in memory dictionary that is shared between all fields while
            importing the table. This is for example used by the collaborator field type
            to prefetch all relations.
        :param files_zip: A zip file buffer where the files related to the template
            must be copied into.
        :param storage: The storage where the files can be copied to.
        :return: Optionally return with additional model objects that must be
            inserted in bulk. This can be used to efficiently add m2m relationships,
            for example.
        """

        setattr(row, field_name, value)

    def get_export_value(
        self, value: Any, field_object: "FieldObject", rich_value: bool = False
    ) -> Any:
        """
        Should convert this field type's internal baserow value to a form suitable
        for exporting to a standalone file.

        :param value: The internal value to convert to a suitable export format
        :param field_object: The field object for the field to extract
        :param rich_value: whether a rich value can be exported. A rich value is a
           structured data like a dict or a list that can be JSON serializable.
           Otherwise if this value is false, it should return a simple value.
        :return: A value suitable to be serialized and stored in a file format for
            users.
        """

        return value

    def get_human_readable_value(self, value: Any, field_object: "FieldObject") -> str:
        """
        Should convert the value of the provided field to a human readable string for
        display purposes.

        :param value: The value of the field extracted from a row to convert to human
            readable form.
        :param field_object: The field object for the field to extract
        :return A human readable string.
        """

        human_readable_value = self.get_export_value(
            value, field_object, rich_value=False
        )
        if human_readable_value is None:
            return ""
        else:
            return str(human_readable_value)

    # noinspection PyMethodMayBeStatic
    def get_other_fields_to_trash_restore_always_together(
        self, field: Field
    ) -> List[Any]:
        """
        When a field of this type is trashed/restored, or the table it is in
        trashed/restored, this method should return any other trashable fields that
        must always be trashed or restored in tandem with this field.

        For example, a link field has an opposing link field in the other table that
        should also be trashed when it is trashed. And so for link fields this method
        is overridden to return the related field so it is trashed/restored correctly.

        :param field: The specific instance of the field that is being trashed or whose
            table is being trashed.
        :return: A list of related fields that should be trashed or restored
            in tandem with this field or it's table.
        """

        return []

    def to_baserow_formula_type(self, field: Field):
        """
        Should return the Baserow Formula Type to use when referencing a field of this
        type in a formula.

        :param field: The specific instance of the field that a formula type should
            be created for.
        :return: The Baserow Formula Type that represents this field in a formula.
        """

        from baserow.contrib.database.formula import BaserowFormulaInvalidType

        return BaserowFormulaInvalidType(
            f"A field of type {self.type} cannot be referenced in a Baserow formula."
        )

    def from_baserow_formula_type(self, formula_type) -> Field:
        """
        Should return the Baserow Field Type when converting a formula type back
        to a field type.

        :param formula_type: The specific instance of a formula type that a field type
            model should be created for.
        :return: A Baserow Field Type model instance that represents this formula type.
        """

        raise NotImplementedError(
            f"A field of type {self.type} cannot be referenced in a Baserow formula."
        )

    def to_baserow_formula_expression(self, field):
        """
        Should return a Typed Baserow Formula Expression to use when referencing the
        field in a formula.

        :param field: The specific instance of the field that a typed formula
            expression should be created for.
        :return: A typed baserow formula expression which when evaluated represents a
            reference to field.
        """

        from baserow.contrib.database.formula import FormulaHandler

        return FormulaHandler.get_normal_field_reference_expression(
            field, self.to_baserow_formula_type(field)
        )

    def get_field_dependencies(
        self, field_instance: Field, field_cache: "FieldCache"
    ) -> "FieldDependencies":
        """
        Should return a list of field dependencies that field_instance has.

        :param field_instance: The field_instance to get field dependencies for.
        :param field_cache: A cache that can be used to lookup fields.
        """

        return []

    def get_fields_needing_periodic_update(self) -> Optional[QuerySet]:
        """
        Returns a queryset of all fields that need to be periodically updated.
        This method should return all the fields that need to be updated
        periodically.

        :return: A queryset of all the fields that need to be periodically updated.
        """

        return None

    def run_periodic_update(
        self,
        field: Field,
        update_collector: "Optional[FieldUpdateCollector]" = None,
        field_cache: "Optional[FieldCache]" = None,
        via_path_to_starting_table: Optional[List[LinkRowField]] = None,
    ):
        """
        This method is called periodically for all the fields of the same type
        that need to be periodically updated. It should be possible to call this method
        recursively for all the fields that depend on the field passed as argument.

        :param field: The field that needs to be updated.
        :param update_collector: Any update statements should be passed to this
            collector so they are run correctly at the right time. You should not be
            manually updating field values yourself in this method.
        :param field_cache: A field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table where the row was created.
        """

        pass

    def restore_failed(self, field_instance, restore_exception):
        """
        Called when restoring field_instance has caused an exception. Return True if
        the exception should be swallowed and the restore operation should succeed or
        False if it should fail and rollback.

        :param field_instance: The instance of the field which caused
            restore_exception on field restore.
        :type field_instance: Field
        :param restore_exception: The exception that was raised when restoring the
            field.
        :type restore_exception:
        :return: True to swallow the exception and succeed the restore, false to
            re-raise and fail the restore.
        :rtype: bool
        """

        return False

    def row_of_dependency_created(
        self,
        field: Field,
        starting_row: "StartingRowType",
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        """
        Called when a row is created in a dependency field (a field that the field
        instance parameter depends on).
        If as a result row value changes are required by this field type an
        update expression should be provided to the update_collector.
        Ensure super is called if this fields rows also change so dependants of this
        field also get notified.

        :param field: The field whose dependency has had a row created.
        :param starting_row: The row which was created in the dependency field.
        :param update_collector: Any update statements should be passed to this
            collector so they are run correctly at the right time. You should not be
            manually updating row values yourself in this method.
        :param field_cache: A field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table where the row was created.
        """

        self.row_of_dependency_updated(
            field,
            starting_row,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def row_of_dependency_updated(
        self,
        field: Field,
        starting_row: "StartingRowType",
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: List["LinkRowField"],
    ):
        """
        Called when a row or rows are updated in a dependency field (a field that the
        field instance parameter depends on).
        If as a result row value changes are required by this field type an
        update expression should be provided to the update_collector.
        Ensure super is called if this fields rows also change so dependants of this
        field also get notified.

        :param field: The field whose dependency has had a row or rows updated.
        :param starting_row: The very first row which changed triggering this
            eventual update notification, might not be in the same table as field or
            a direct dependency row of field.
        :param update_collector: Any update statements should be passed to this
            collector so they are run correctly at the right time. You should not be
            manually updating row values yourself in this method.
        :param field_cache: An optional field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table where the first row was changed.
        """

    def row_of_dependency_deleted(
        self,
        field: Field,
        starting_row: "StartingRowType",
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        """
        Called when a row is deleted in a dependency field (a field that the
        field instance parameter depends on).
        If as a result row value changes are required by this field type an
        update expression should be provided to the update_collector.
        Ensure super is called if this fields rows also change so dependants of this
        field also get notified.

        :param field: The field whose dependency has had a row deleted.
        :param starting_row: The very row which was deleted.
        :param update_collector: Any update statements should be passed to this
            collector so they are run correctly at the right time. You should not be
            manually updating row values yourself in this method.
        :param field_cache: An optional field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table where the row was deleted.
        """

        self.row_of_dependency_updated(
            field,
            starting_row,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def row_of_dependency_moved(
        self,
        field: Field,
        starting_row: "StartingRowType",
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        """
        Called when a row is moved in a dependency field (a field that the
        field instance parameter depends on).
        If as a result row value changes are required by this field type an
        update expression should be provided to the update_collector.
        Ensure super is called if this fields rows also change so dependants of this
        field also get notified.

        :param field: The field whose dependency has had a row deleted.
        :param starting_row: The row which was moved.
        :param update_collector: Any update statements should be passed to this
            collector so they are run correctly at the right time. You should not be
            manually updating row values yourself in this method.
        :param field_cache: An optional field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table where the row was moved.
        """

        self.row_of_dependency_updated(
            field,
            starting_row,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def field_dependency_created(
        self,
        field: Field,
        created_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        """
        Called when a field is created which the field parameter depends on.
        If as a result row value changes are required by this field type an
        update expression should be provided to the update_collector.
        Ensure super is called if this field also changes so dependants of this
        field also get notified.

        :param field: The field who has had a new dependency field created.
        :param created_field: The dependency field which was created.
        :param update_collector: If this field changes the resulting field should be
            passed to the update_collector. Additionally if this fields row values
            should also change has a result an update statement should be passed to
            this collector which will be run correctly at the right time.
            You should not be manually updating row values yourself in this method.
        :param field_cache: An optional field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table where field was created.
        """

        self.field_dependency_updated(
            field,
            field,
            field,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def field_dependency_updated(
        self,
        field: Field,
        updated_field: Field,
        updated_old_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        """
        Called when a field is updated which the field parameter depends on.
        If as a result row value changes are required by this field type an
        update expression should be provided to the update_collector.
        Ensure super is called if this field also changes so dependants of this
        field also get notified.

        :param field: The field who has had a new dependency field created.
        :param updated_field: The dependency field which was updated.
        :param updated_old_field: The instance of the updated field before the update.
        :param update_collector: If this field changes the resulting field should be
            passed to the update_collector. Additionally if this fields row values
            should also change has a result an update statement should be passed to
            this collector which will be run correctly at the right time.
            You should not be manually updating row values yourself in this method.
        :param field_cache: An optional field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table the first field change occurred.
        """

        from baserow.contrib.database.fields.dependencies.handler import (
            FieldDependencyHandler,
        )

        FieldDependencyHandler.rebuild_dependencies(field, field_cache)

        from baserow.contrib.database.views.handler import ViewHandler

        ViewHandler().field_updated(field)

    def field_dependency_deleted(
        self,
        field: Field,
        deleted_field: Field,
        update_collector: "FieldUpdateCollector",
        field_cache: "FieldCache",
        via_path_to_starting_table: Optional[List[LinkRowField]],
    ):
        """
        Called when a field is deleted which the field parameter depends on.
        If as a result row value changes are required by this field type an
        update expression should be provided to the update_collector.
        Ensure super is called if this field also changes so dependants of this
        field also get notified.

        :param field: The field who has had a new dependency field created.
        :param deleted_field: The dependency field which was deleted.
        :param update_collector: If this field changes the resulting field should be
            passed to the update_collector. Additionally if this fields row values
            should also change has a result an update statement should be passed to
            this collector which will be run correctly at the right time.
            You should not be manually updating row values yourself in this method.
        :param field_cache: An optional field cache to be used when fetching fields.
        :param via_path_to_starting_table: A list of link row fields if any leading
            back to the starting table the field was deleted.
        """

        self.field_dependency_updated(
            field,
            field,
            field,
            update_collector,
            field_cache,
            via_path_to_starting_table,
        )

    def check_can_order_by(self, field: Field) -> bool:
        """
        Override this method if this field type can sometimes be ordered or sometimes
        cannot be ordered depending on the individual field state. By default will just
        return the bool property _can_order_by so if your field type doesn't depend
        on the field state and is always just True or False just set _can_order_by
        to the desired value.

        :param field: The field to check to see if it can be ordered by or not.
        :return: True if a view can be ordered by this field, False otherwise.
        """

        return self._can_order_by

    def check_can_group_by(self, field: Field) -> bool:
        """
        Override this method if this field type can sometimes be grouped or sometimes
        cannot be grouped depending on the individual field state. By default will just
        return the bool property _can_group_by so if your field type doesn't depend
        on the field state and is always just True or False just set _can_group_by
        to the desired value.

        :param field: The field to check to see if it can be grouped by or not.
        :return: True if a view can be grouped by this field, False otherwise.
        """

        return self._can_group_by

    def get_group_by_field_unique_value_string(
        self, field: Field, field_name: str, value: Any
    ) -> Any:
        """
        Should return a unique hashable value that can be set as key of a dict. In
        almost all cases, it's fine to just return the actual value, but for example
        with a more complex structure like a ManyToOneDescription, something
        compatible can be returned.

        :param field: The field for which to generate the unique value.
        :param field_name: The name of that field in the table.
        :param value: The unique value that must be converted.
        :return: The converted unique value.
        """

        return value

    def get_group_by_field_filters_and_annotations(
        self, field: Field, field_name: str, base_queryset: QuerySet, value: Any
    ) -> Tuple[Dict, Dict]:
        """
        The filters that must be applied to match the provided value to the queryset
        when grouping. By default, a `field_name=value` lookup will suffice for most
        use cases, but for some other a more complicated lookup must be done.

        :param field: The field that must be looked up.
        :param field_name: The name of the field in the table that must be looked up.
        :param base_queryset: The base queryset of the items the grouped rows.
        :param value: The unique value that must be looked up.
        :return: A tuple containing the filters and annotations as dict.
        """

        return {field_name: value}, {}

    def get_group_by_serializer_field(self, instance: Field, **kwargs: dict):
        """
        Returns the serializer that is used in the `serialize_group_by_meta_data`. By
        default, we're returning the normal serializer, because that will be fine in
        most casus, but if a different value is returned in the
        `get_group_by_field_unique_value_string` method, then we might need a
        different serializer field.

        :param instance: The field instance for which to get the serializer field for.
        :param kwargs: The kwargs that will be passed to the field.
        :return: The serializer field that represents the field instance attributes.
        :rtype: serializer.Field
        """

        return self.get_response_serializer_field(instance, **kwargs)

    def before_field_options_update(
        self,
        field: Field,
        to_create: Optional[List[int]] = None,
        to_update: Optional[List[dict]] = None,
        to_delete: Optional[List[int]] = None,
    ):
        """
        Called from `FieldHandler.update_field_select_options()` just before
        the select options of a field are updated in database.

        :param field: The field instance whose options are updated.
        :param to_create: A list of dict containing data for each new option
            added to the field.
        :param to_update: A list of option ids that already exists and are going
            to be associated with this field.
        :param to_delete: A list of option ids that are removed from the field
            option list.
        """

    def should_backup_field_data_for_same_type_update(
        self, old_field: Field, new_field_attrs: Dict[str, Any]
    ) -> bool:
        """
        When a field is updated we backup it's data beforehand so we can undo the
        update. This method is called when the update is not changing the type of
        the field and decides if given the new_field_attrs whether or not to backup.

        By default returns False as we assume when a fields type does not change
        and only it's attributes are changing a backup is not required. If this is
        not the case for your field type you should override this method and
        return True when the attributes changing results in data loss (and hence a
        backup is needed).

        :param old_field: The original field instance.
        :param new_field_attrs: The user supplied new field values.
        :return: True if the field data should be backed up even if the type has
            not changed, False otherwise.
        """

        return False

    def get_dependants_which_will_break_when_field_type_changes(
        self, field: Field, to_field_type: "FieldType", field_cache: "FieldCache"
    ) -> "FieldDependants":
        """
        If this field has dependants which will have their FieldDependency deleted
        because of a field type change to `to_field_type` this function should query for
        and return these FieldDependencies. This hook is called immediately before
        the field type change and the results will later have the
        `field_dependency_updated` hook called on them.

        :param field: The field which is being converted to "to_field_type"
        :param to_field_type: The new field type field is being converted to..
        :param field_cache: A field cache that can be used to lookup and cache fields.
        :return: A list of field dependency tuples.
        """

        return []

    def get_value_for_filter(self, row: "GeneratedTableModel", field: Field) -> any:
        """
        Returns the value of a field in a row that can be used for SQL filtering.
        Usually this is just a string or int value stored in the row but for
        some field types this is not the case. For example a multiple select field will
        return a list of values which need to be converted to a string for filtering.
        If you are implementing this method you should also implement the get_order
        method.

        :param row: The row which contains the field value.
        :param field: The instance of the field to get the value for.
        :return: The value of the field in the row in a filterable format.
        """

        return getattr(row, field.db_column)

    def can_represent_date(self, field):
        """Indicates whether the field can be used to represent date or datetime."""

        return False

    def get_permission_error_when_user_changes_field_to_depend_on_forbidden_field(
        self, user: AbstractUser, changed_field: Field, forbidden_field: Field
    ) -> Exception:
        """
        Called when the field has been created or changed in a way that resulted in
        it depending on another field in a way that was forbidden for the user
        who triggered the change.

        :param user: The user.
        :param changed_field: The changed field.
        :param forbidden_field: The forbidden field.
        """

        return PermissionError(user)

    def serialize_metadata_for_row_history(
        self,
        field: Field,
        row: "GeneratedTableModel",
        metadata: Optional[SerializedRowHistoryFieldMetadata] = None,
    ) -> SerializedRowHistoryFieldMetadata:
        """
        Returns a dictionary of metadata that should be stored in the row history
        table for this field type. This is necessary for fields that have a
        non-trivial value representation to be able to reconstruct the value from
        the history table.

        :param field: The field instance that the value belongs to.
        :param row: The row which the metadata are for.
        :param metadata: When provided, the new metadata will be merged with
            the provided ones. That way this method can be called twice for old
            and new values of the row while keeping single metadata representing
            both.
        :return: A dictionary of metadata that should be stored in the row history
            table for this field type.
        """

        return {
            "id": field.id,
            "type": self.type,
        }

    def are_row_values_equal(self, value1: any, value2: any) -> bool:
        """
        Determines if two field values are the same.

        :param value1: The first field value to compare.
        :param value2: The second field value to compare.
        :return: Boolean indicating whether value1 and value2 are in
            fact the same.
        """

        return value1 == value2


class ReadOnlyFieldType(FieldType):
    read_only = True
    keep_data_on_duplication = False

    def get_internal_value_from_db(
        self, row: "GeneratedTableModel", field_name: str
    ) -> NoReturn:
        """
        Called when a read only field is trying to get its internal db value.
        """

        if not self.keep_data_on_duplication:
            raise ReadOnlyFieldHasNoInternalDbValueError

        return super().get_internal_value_from_db(row, field_name)

    def prepare_value_for_db(self, instance: Field, value: Any) -> NoReturn:
        """
        Since this is a read only field, no value should be prepared for database,
        so we raise a ValidationError here.
        """

        raise ValidationError(
            f"Field of type {self.type} is read only and should not be set manually."
        )

    def get_export_serialized_value(
        self,
        row: "GeneratedTableModel",
        field_name: str,
        cache: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ) -> None:
        # Since this is a read only field, no value should be prepared for export,
        # except when we explicitly want to keep the data on duplication like for
        # example with the UUID field type.
        if self.keep_data_on_duplication:
            return super().get_export_serialized_value(
                row, field_name, cache, files_zip, storage
            )

    def set_import_serialized_value(
        self,
        row: "GeneratedTableModel",
        field_name: str,
        value: Any,
        id_mapping: Dict[str, Any],
        cache: Dict[str, Any],
        files_zip: Optional[ZipFile] = None,
        storage: Optional[Storage] = None,
    ):
        # Since this is a read only field, no value be set with export, except when we
        # explicitly want to keep the data on duplication like for example with the
        # UUID field type.
        if self.keep_data_on_duplication:
            return super().set_import_serialized_value(
                row, field_name, value, id_mapping, cache, files_zip, storage
            )


class ManyToManyGroupByMixin:
    """
    Mixin that can be added to a field type that uses a ManyToMany relationship. It
    introduces methods that make it compatible with the group by functionality. Note
    that the field type must set the `_can_group_by` property to `True`.
    """

    def get_group_by_field_unique_value_string(
        self, field: Field, field_name: str, value: Any
    ) -> Any:
        return ",".join([str(v.id) for v in value.all()])

    def get_group_by_field_filters_and_annotations(
        self, field, field_name, base_queryset, value
    ):
        filters = {
            field_name: value,
        }
        annotations = {
            field_name: Subquery(
                base_queryset.filter(id=OuterRef("id"))
                .annotate(
                    res=Coalesce(
                        StringAgg(
                            Cast(
                                f"{field_name}__id",
                                output_field=CharField(),
                            ),
                            ",",
                        ),
                        Value(""),
                    )
                )
                .values("res")
            )
        }
        return filters, annotations

    def get_group_by_serializer_field(self, field, **kwargs):
        return SerializerCharField(
            **{
                "required": False,
                "allow_null": True,
                "allow_blank": True,
                **kwargs,
            }
        )


class FieldTypeRegistry(
    APIUrlsRegistryMixin,
    CustomFieldsRegistryMixin,
    ModelRegistryMixin[Field, FieldType],
    Registry[FieldType],
):
    """
    With the field type registry it is possible to register new field types.  A field
    type is an abstraction made specifically for Baserow. If added to the registry a
    user can create new fields based on this type.
    """

    name = "field"
    does_not_exist_exception_class = FieldTypeDoesNotExist
    already_registered_exception_class = FieldTypeAlreadyRegistered


class FieldConverter(Instance):
    """
    By default when changing a field the lenient schema editor is used to alter the
    field to make the schema changes. If for whatever reason this does not suffice
    then a converter can be used to change field and the related data. This is for
    example used by the link_row field because it is not possible to change a
    ManyToManyField to another field.

    Example:
        from baserow.contrib.database.fields.field_types import (
            TextFieldType, DateFieldType
        )
        from baserow.contrib.database.fields.registries import (
            FieldConverter, field_converter_registry
        )

        class TextToDateFieldConverter(FieldConverter):
            type = 'text-to-date'

            def is_applicable(self, from_model, from_field, to_field):
                return (
                    isinstance(from_field, TextFieldType) and
                    isinstance(to_field, DateFieldType)
                )

            def alter_field(self, from_field, to_field, from_model, to_model,
                            from_model_field, to_model_field, user, connection):
                # This is just for example purposes, but it will delete the old text
                # field and create a new date field. You can be very creative
                # here in how you want to convert field and the data. It is for example
                # possible to load all the old data in memory, convert it and then
                # update the new data. Performance should always be kept in mind
                # though.
                with safe_django_schema_editor() as schema_editor:
                    schema_editor.remove_field(from_model, from_model_field)
                    schema_editor.add_field(to_model, to_model_field)


        field_converter_registry.register(TextToDateFieldConverter())
    """

    def is_applicable(self, from_model, from_field, to_field):
        """
        Decides whether the converter is applicable for the alteration of the provided
        fields. Before conversion all converters are checked to see if they are
        applicable. The first one that is will be used.

        :param from_model: The old model containing only the old field.
        :type from_model: Model
        :param from_field: The old field instance. It should only be used for type and
            property comparison with the to_field because else things might break.
        :type from_field: Field
        :param to_field: The new field instance. It should only be used for type and
            property comparison with the from_field because else things might
            break.
        :type to_field: Field
        :return: If True then the alter_field method of this converter will be used
            to alter the field instead of the lenient schema editor.
        :rtype: bool
        """

        raise NotImplementedError(
            "Each field converter must have an is_applicable " "method."
        )

    def alter_field(
        self,
        from_field,
        to_field,
        from_model,
        to_model,
        from_model_field,
        to_model_field,
        user,
        connection,
    ):
        """
        Should perform the schema change and changes related to the field change. It
        must bring the field's schema into the desired state.

        :param from_field: The old field's instance. This should be used for getting
            the type and properties. Making changes can override things.
        :type from_field: Field
        :param to_field: The new field's instance. This should be used for getting the
            type and properties. It already is in a correct state.
        :type to_field: Field
        :param from_model: The old generated model containing only the old field.
        :type from_model: Model
        :param to_model: The generated model containing only the new field.
        :type to_model: Model
        :param from_model_field: The old field extracted from the old model.
        :type from_model_field: models.Field
        :param to_model_field: The new field extracted from the new model.
        :type to_model_field: models.Field
        :param user: The user on whose behalf the change is made.
        :type user: User
        :param connection: The connection used to make the database schema change.
        :type connection: DatabaseWrapper
        """

        raise NotImplementedError(
            "Each field converter must have an alter_field " "method."
        )


class FieldConverterRegistry(Registry):
    """
    The registry that holds all the available field converters. A field converter can
    be used to convert a field to another type in a custom way. It can also be used the
    data related to the field needs a specific conversion. It should be used when the
    default lenient schema editor does not work.
    """

    name = "field_converter"

    def find_applicable_converter(self, *args, **kwargs):
        """
        Finds the first applicable converter that is in the register based on the
        provided arguments. Note that is might be possible for other converters to be
        applicable also. This only returns the first match, not the best match. Might
        be an idea to implement something with a priority system once we have lots of
        converters.

        :return: The applicable field converter or None if no converter has been found.
        :rtype: None or FieldConverter
        """

        for converter in self.registry.values():
            if converter.is_applicable(*args, **kwargs):
                return converter
        return None


# A default field type registry is created here, this is the one that is used
# throughout the whole Baserow application to add a new field type.
field_type_registry: FieldTypeRegistry = FieldTypeRegistry()
field_converter_registry: FieldConverterRegistry = FieldConverterRegistry()
