import pytest
from django.core.exceptions import ValidationError
from django.test.utils import override_settings
from faker import Faker

from baserow.contrib.database.fields.field_types import (
    PhoneNumberFieldType,
)
from baserow.contrib.database.fields.handler import FieldHandler
from baserow.contrib.database.fields.models import (
    LongTextField,
    URLField,
    EmailField,
    PhoneNumberField,
    SelectOption,
)
from baserow.contrib.database.fields.registries import field_type_registry
from baserow.contrib.database.rows.handler import RowHandler
from baserow.test_utils.helpers import setup_interesting_test_table


@pytest.mark.django_db
def test_import_export_text_field(data_fixture):
    id_mapping = {}

    text_field = data_fixture.create_text_field(
        name="Text name", text_default="Text default"
    )
    text_field_type = field_type_registry.get_by_model(text_field)
    text_serialized = text_field_type.export_serialized(text_field)
    text_field_imported = text_field_type.import_serialized(
        text_field.table, text_serialized, id_mapping
    )
    assert text_field.id != text_field_imported.id
    assert text_field.name == text_field_imported.name
    assert text_field.order == text_field_imported.order
    assert text_field.primary == text_field_imported.primary
    assert text_field.text_default == text_field_imported.text_default
    assert id_mapping["database_fields"][text_field.id] == text_field_imported.id


@pytest.mark.django_db
def test_import_export_formula_field(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    first_table = data_fixture.create_database_table(user=user)
    second_table = data_fixture.create_database_table(user=user)
    id_mapping = {}

    text_field = data_fixture.create_text_field(
        table=first_table, name="Text name", text_default="Text default"
    )
    formula_field = data_fixture.create_formula_field(
        table=first_table,
        name="formula field",
        formula=f"field('{text_field.name}')",
        formula_type="text",
    )
    formula_field_type = field_type_registry.get_by_model(formula_field)
    formula_serialized = formula_field_type.export_serialized(formula_field)
    assert formula_serialized["formula"] == "field('Text name')"

    text_field_in_diff_table = data_fixture.create_text_field(
        table=second_table, name="Text name", text_default="Text default"
    )
    formula_field_imported = formula_field_type.import_serialized(
        text_field_in_diff_table.table,
        formula_serialized,
        id_mapping,
    )
    assert formula_field.id != formula_field_imported.id
    assert formula_field.name == formula_field_imported.name
    assert formula_field.order == formula_field_imported.order
    assert formula_field.primary == formula_field_imported.primary
    assert formula_field_imported.formula == f"field('Text name')"
    assert id_mapping["database_fields"][formula_field.id] == formula_field_imported.id


@pytest.mark.django_db
def test_long_text_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    field = data_fixture.create_text_field(table=table, order=1, name="name")

    handler = FieldHandler()
    handler.create_field(
        user=user, table=table, type_name="long_text", name="description"
    )
    field = handler.update_field(user=user, field=field, new_type_name="long_text")

    assert len(LongTextField.objects.all()) == 2

    fake = Faker()
    text = fake.text()
    model = table.get_model(attribute_names=True)
    row = model.objects.create(description=text, name="Test")

    assert row.description == text
    assert row.name == "Test"

    handler.delete_field(user=user, field=field)
    assert len(LongTextField.objects.all()) == 1


@pytest.mark.django_db
def test_valid_url(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)
    field = data_fixture.create_text_field(table=table, order=1, name="name")
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_handler.create_field(user=user, table=table, type_name="url", name="URL")
    assert len(URLField.objects.all()) == 1

    model = table.get_model(attribute_names=True)

    valid_urls = [
        "baserow.io",
        "ftp://baserow.io",
        "git://example.com/",
        "ws://baserow.io",
        "http://baserow.io",
        "https://baserow.io",
        "https://www.baserow.io",
        "HTTP://BASEROW.IO",
        "https://test.nl/test",
        "https://test.nl/test",
        "http://localhost",
        "//localhost",
        "https://test.nl/test?with=a-query&that=has-more",
        "https://test.nl/test",
        "http://-.~_!$&'()*+,;=%40:80%2f@example.com",
        "http://उदाहरण.परीक्षा",
        "http://foo.com/(something)?after=parens",
        "http://142.42.1.1/",
        "http://userid:password@example.com:65535/",
        "http://su--b.valid-----hyphens.com/",
        "//baserow.io/test",
        "127.0.0.1",
        "https://test.nl#test",
        "http://baserow.io/hrscywv4p/image/upload/c_fill,g_faces:center,"
        "h_128,w_128/yflwk7vffgwyyenftkr7.png",
        "https://gitlab.com/bramw/baserow/-/issues?row=nice/route",
        "https://web.archive.org/web/20210313191012/https://baserow.io/",
        "mailto:bram@baserow.io?test=test",
    ]
    invalid_urls = [
        "test",
        "test.",
        "localhost",
        "\nwww.test.nl",
        "www\n.test.nl",
        "www .test.nl",
        " www.test.nl",
    ]

    for invalid_url in invalid_urls:
        with pytest.raises(ValidationError):
            row_handler.create_row(
                user=user, table=table, values={"url": invalid_url}, model=model
            )

    for url in valid_urls:
        row_handler.create_row(
            user=user,
            table=table,
            values={"url": url, "name": url},
            model=model,
        )
    for bad_url in invalid_urls:
        row_handler.create_row(
            user=user,
            table=table,
            values={"url": "", "name": bad_url},
            model=model,
        )

    # Convert the text field to a url field so we can check how the conversion of
    # values went.
    field_handler.update_field(user=user, field=field, new_type_name="url")
    rows = model.objects.all()
    i = 0
    for url in valid_urls:
        assert rows[i].url == url
        assert rows[i].name == url
        i += 1

    for _ in invalid_urls:
        assert rows[i].url == ""
        assert rows[i].name == ""
        i += 1


@pytest.mark.django_db
def test_valid_email(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)
    field = data_fixture.create_text_field(table=table, order=1, name="name")
    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_handler.create_field(user=user, table=table, type_name="email", name="email")

    model = table.get_model(attribute_names=True)

    invalid_emails = [
        "test@" + "a" * 246 + ".com",
        "@a",
        "a@",
        "not-an-email",
        "bram.test.nl",
        "invalid_email",
        "invalid@invalid@com",
        "\nhello@gmail.com",
        "asdds asdd@gmail.com",
    ]

    for invalid_email in invalid_emails:
        with pytest.raises(ValidationError):
            row_handler.create_row(
                user=user, table=table, values={"email": invalid_email}, model=model
            )

    valid_emails = [
        "test@" + "a" * 245 + ".com",
        "a@a",
        "用户@例子.广告",
        "अजय@डाटा.भारत",
        "квіточка@пошта.укр",
        "χρήστης@παράδειγμα.ελ",
        "Dörte@Sörensen.example.com",
        "коля@пример.рф",
        "bram@localhost",
        "bram@localhost.nl",
        "first_part_underscores_ok@hyphens-ok.com",
        "wierd@[1.1.1.1]",
        "bram.test.test@sub.domain.nl",
        "BRAM.test.test@sub.DOMAIN.nl",
    ]
    for email in valid_emails:
        row_handler.create_row(
            user=user,
            table=table,
            values={"email": email, "name": email},
            model=model,
        )
    for bad_email in invalid_emails:
        row_handler.create_row(
            user=user,
            table=table,
            values={"email": "", "name": bad_email},
            model=model,
        )

    # Convert the text field to a email field so we can check how the conversion of
    # values went.
    field_handler.update_field(user=user, field=field, new_type_name="email")
    rows = model.objects.all()
    i = 0
    for email in valid_emails:
        assert rows[i].email == email
        assert rows[i].name == email
        i += 1

    for _ in invalid_emails:
        assert rows[i].email == ""
        assert rows[i].name == ""
        i += 1


@pytest.mark.django_db
def test_email_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)
    field = data_fixture.create_text_field(table=table, order=1, name="name")

    field_handler = FieldHandler()
    row_handler = RowHandler()

    field_2 = field_handler.create_field(
        user=user, table=table, type_name="email", name="email"
    )
    number = field_handler.create_field(
        user=user, table=table, type_name="number", name="number"
    )

    assert len(EmailField.objects.all()) == 1
    model = table.get_model(attribute_names=True)

    row_handler.create_row(
        user=user,
        table=table,
        values={
            "name": "a.very.STRANGE@email.address.coM",
            "email": "test@test.nl",
            "number": 5,
        },
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"name": "someuser", "email": "some@user.com", "number": 10},
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"name": "http://www.baserow.io", "email": "bram@test.nl"},
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"name": "NOT AN EMAIL", "email": "something@example.com"},
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={"name": "testing@nowhere.org", "email": ""},
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "email": None,
        },
        model=model,
    )

    # Convert the text field to a url field so we can check how the conversion of
    # values went.
    field_handler.update_field(user=user, field=field, new_type_name="email")
    field_handler.update_field(user=user, field=number, new_type_name="email")

    model = table.get_model(attribute_names=True)
    rows = model.objects.all()

    assert rows[0].name == "a.very.STRANGE@email.address.coM"
    assert rows[0].email == "test@test.nl"
    assert rows[0].number == ""

    assert rows[1].name == ""
    assert rows[1].email == "some@user.com"
    assert rows[1].number == ""

    assert rows[2].name == ""
    assert rows[2].email == "bram@test.nl"
    assert rows[2].number == ""

    assert rows[3].name == ""
    assert rows[3].email == "something@example.com"
    assert rows[3].number == ""

    assert rows[4].name == "testing@nowhere.org"
    assert rows[4].email == ""
    assert rows[4].number == ""

    assert rows[5].name == ""
    assert rows[5].email == ""
    assert rows[5].number == ""

    field_handler.delete_field(user=user, field=field_2)
    assert len(EmailField.objects.all()) == 2


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_phone_number_field_type(data_fixture):
    user = data_fixture.create_user()
    table = data_fixture.create_database_table(user=user)
    data_fixture.create_database_table(user=user, database=table.database)

    field_handler = FieldHandler()
    row_handler = RowHandler()

    text_field = field_handler.create_field(
        user=user, table=table, order=1, type_name="text", name="name"
    )
    phone_number_field = field_handler.create_field(
        user=user, table=table, type_name="phone_number", name="phonenumber"
    )
    email_field = field_handler.create_field(
        user=user, table=table, type_name="email", name="email"
    )
    number_field = data_fixture.create_number_field(
        table=table, order=1, number_negative=True, name="number"
    )

    assert len(PhoneNumberField.objects.all()) == 1
    model = table.get_model(attribute_names=True)

    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user,
            table=table,
            values={"phonenumber": "invalid phone number"},
            model=model,
        )

    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user,
            table=table,
            values={"phonenumber": "Phone: 2312321 2349432 "},
            model=model,
        )
    with pytest.raises(ValidationError):
        row_handler.create_row(
            user=user,
            table=table,
            values={
                "phonenumber": "1" * (PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH + 1)
            },
            model=model,
        )

    max_length_phone_number = "1" * PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "name": "+45(1424) 322314 324234",
            "phonenumber": max_length_phone_number,
            "number": 1234534532,
            "email": "a_valid_email_to_be_blanked_after_conversion@email.com",
        },
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "name": "some text which should be blanked out after conversion",
            "phonenumber": "1234567890 NnXx,+._*()#=;/ -",
            "number": 0,
        },
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "name": max_length_phone_number,
            "phonenumber": "",
            "number": -10230450,
        },
        model=model,
    )
    row_handler.create_row(
        user=user,
        table=table,
        values={
            "phonenumber": None,
            "name": "1" * (PhoneNumberFieldType.MAX_PHONE_NUMBER_LENGTH + 1),
        },
        model=model,
    )
    row_handler.create_row(user=user, table=table, values={}, model=model)

    # No actual database type change occurs here as a phone number field is also a text
    # field. Instead the after_update hook is being used to clear out invalid
    # phone numbers.
    field_handler.update_field(
        user=user, field=text_field, new_type_name="phone_number"
    )

    field_handler.update_field(
        user=user, field=number_field, new_type_name="phone_number"
    )
    field_handler.update_field(
        user=user, field=email_field, new_type_name="phone_number"
    )

    model = table.get_model(attribute_names=True)
    rows = model.objects.all()

    assert rows[0].name == "+45(1424) 322314 324234"
    assert rows[0].phonenumber == max_length_phone_number
    assert rows[0].number == "1234534532"
    assert rows[0].email == ""

    assert rows[1].name == ""
    assert rows[1].phonenumber == "1234567890 NnXx,+._*()#=;/ -"
    assert rows[1].number == "0"

    assert rows[2].name == max_length_phone_number
    assert rows[2].phonenumber == ""
    assert rows[2].number == "-10230450"

    assert rows[3].name == ""
    assert rows[3].phonenumber == ""
    assert rows[3].number == ""

    field_handler.delete_field(user=user, field=phone_number_field)
    assert len(PhoneNumberField.objects.all()) == 3


@pytest.mark.django_db
def test_human_readable_values(data_fixture):
    table, user, row, blank_row = setup_interesting_test_table(data_fixture)
    model = table.get_model()
    results = {}
    blank_results = {}
    for field in model._field_objects.values():
        value = field["type"].get_human_readable_value(
            getattr(row, field["name"]), field
        )
        results[field["field"].name] = value
        blank_value = field["type"].get_human_readable_value(
            getattr(blank_row, field["name"]), field
        )
        blank_results[field["field"].name] = blank_value

    assert blank_results == {
        "boolean": "False",
        "date_eu": "",
        "date_us": "",
        "datetime_eu": "",
        "datetime_us": "",
        "last_modified_date_eu": "02/01/2021",
        "last_modified_date_us": "01/02/2021",
        "last_modified_datetime_eu": "02/01/2021 13:00",
        "last_modified_datetime_us": "01/02/2021 13:00",
        "created_on_date_eu": "02/01/2021",
        "created_on_date_us": "01/02/2021",
        "created_on_datetime_eu": "02/01/2021 13:00",
        "created_on_datetime_us": "01/02/2021 13:00",
        "decimal_link_row": "",
        "email": "",
        "file": "",
        "file_link_row": "",
        "link_row": "",
        "long_text": "",
        "negative_decimal": "",
        "negative_int": "",
        "phone_number": "",
        "positive_decimal": "",
        "positive_int": "",
        "single_select": "",
        "multiple_select": "",
        "text": "",
        "url": "",
        "formula": "test FORMULA",
        "lookup": "",
    }
    assert results == {
        "boolean": "True",
        "date_eu": "01/02/2020",
        "date_us": "02/01/2020",
        "datetime_eu": "01/02/2020 01:23",
        "datetime_us": "02/01/2020 01:23",
        "last_modified_date_eu": "02/01/2021",
        "last_modified_date_us": "01/02/2021",
        "last_modified_datetime_eu": "02/01/2021 13:00",
        "last_modified_datetime_us": "01/02/2021 13:00",
        "created_on_date_eu": "02/01/2021",
        "created_on_date_us": "01/02/2021",
        "created_on_datetime_eu": "02/01/2021 13:00",
        "created_on_datetime_us": "01/02/2021 13:00",
        "decimal_link_row": "1.234, -123.456, unnamed row 3",
        "email": "test@example.com",
        "file": "a.txt, b.jpg",
        "file_link_row": "name.txt, unnamed row 2",
        "link_row": "linked_row_1, linked_row_2, unnamed row 3",
        "long_text": "long_text",
        "negative_decimal": "-1.2",
        "negative_int": "-1",
        "phone_number": "+4412345678",
        "positive_decimal": "1.2",
        "positive_int": "1",
        "single_select": "A",
        "multiple_select": "D, C, E",
        "text": "text",
        "url": "https://www.google.com",
        "formula": "test FORMULA",
        "lookup": "linked_row_1, linked_row_2, ",
    }


@pytest.mark.django_db
def test_import_export_lookup_field(data_fixture, api_client):
    user, token = data_fixture.create_user_and_token()
    table_a, table_b, link_field = data_fixture.create_two_linked_tables(user=user)
    id_mapping = {}

    target_field = data_fixture.create_text_field(name="target", table=table_b)
    table_a_model = table_a.get_model(attribute_names=True)
    table_b_model = table_b.get_model(attribute_names=True)
    row_1 = table_b_model.objects.create(primary="1", target="target 1")
    row_2 = table_b_model.objects.create(primary="2", target="target 2")

    row_a = table_a_model.objects.create(primary="a")
    row_a.link.add(row_1.id)
    row_a.link.add(row_2.id)
    row_a.save()

    lookup = FieldHandler().create_field(
        user,
        table_a,
        "lookup",
        name="lookup",
        through_field_name="link",
        target_field_name="target",
    )
    lookup_field_type = field_type_registry.get_by_model(lookup)
    lookup_serialized = lookup_field_type.export_serialized(lookup)
    assert lookup_serialized["target_field_id"] == target_field.id
    assert lookup_serialized["target_field_name"] == target_field.name
    assert lookup_serialized["through_field_id"] == link_field.id
    assert lookup_serialized["through_field_name"] == link_field.name

    lookup.name = "rename to prevent import clash"
    lookup.save()

    lookup_field_imported = lookup_field_type.import_serialized(
        table_a,
        lookup_serialized,
        id_mapping,
    )
    assert lookup.id != lookup_field_imported.id
    assert lookup_field_imported.name == "lookup"
    assert lookup_field_imported.order == lookup.order
    assert lookup_field_imported.primary == lookup.primary
    assert lookup_field_imported.formula == lookup.formula
    assert lookup_field_imported.through_field == lookup.through_field
    assert lookup_field_imported.target_field == lookup.target_field
    assert lookup_field_imported.through_field_name == lookup.through_field_name
    assert lookup_field_imported.target_field_name == lookup.target_field_name

    assert id_mapping["database_fields"][lookup.id] == lookup_field_imported.id


@pytest.mark.django_db
def test_fast_serialize_of_all_fields(data_fixture):
    table, user, row, blank_row = setup_interesting_test_table(data_fixture)
    model = table.get_model()
    results = {}
    for field in model._field_objects.values():
        value = field["type"].fast_serialize(
            field["field"], getattr(row, field["name"])
        )
        results[field["field"].name] = value

    assert results == {
        "text": "text",
        "long_text": "long_text",
        "url": "https://www.google.com",
        "email": "test@example.com",
        "negative_int": "-1",
        "positive_int": "1",
        "negative_decimal": "-1.2",
        "positive_decimal": "1.2",
        "boolean": True,
        "datetime_us": "2020-02-01T01:23:00Z",
        "date_us": "2020-02-01",
        "datetime_eu": "2020-02-01T01:23:00Z",
        "date_eu": "2020-02-01",
        "last_modified_datetime_us": "2021-01-02T12:00:00Z",
        "last_modified_date_us": "2021-01-02",
        "last_modified_datetime_eu": "2021-01-02T12:00:00Z",
        "last_modified_date_eu": "2021-01-02",
        "created_on_datetime_us": "2021-01-02T12:00:00Z",
        "created_on_date_us": "2021-01-02",
        "created_on_datetime_eu": "2021-01-02T12:00:00Z",
        "created_on_date_eu": "2021-01-02",
        "link_row": [
            {"id": 1, "value": "linked_row_1"},
            {"id": 2, "value": "linked_row_2"},
            {"id": 3, "value": ""},
        ],
        "decimal_link_row": [
            {"id": 1, "value": "1.234"},
            {"id": 2, "value": "-123.456"},
            {"id": 3, "value": ""},
        ],
        "file_link_row": [{"id": 1, "value": "name.txt"}, {"id": 2, "value": ""}],
        "file": [
            {
                "name": "hashed_name.txt",
                "size": 0,
                "is_image": False,
                "mime_type": "text/plain",
                "image_width": 0,
                "uploaded_at": "2020-02-01 01:23",
                "image_height": 0,
                "visible_name": "a.txt",
                "url": "http://localhost:8000/media/user_files/hashed_name.txt",
                "thumbnails": None,
            },
            {
                "name": "other_name.jpg",
                "size": 0,
                "is_image": True,
                "mime_type": "image/jpeg",
                "image_width": 0,
                "uploaded_at": "2020-02-01 01:23",
                "image_height": 0,
                "visible_name": "b.jpg",
                "url": "http://localhost:8000/media/user_files/other_name.jpg",
                "thumbnails": {
                    "tiny": {
                        "url": "http://localhost:8000/media/thumbnails/tiny/other_name"
                        ".jpg",
                        "width": 21,
                        "height": 21,
                    }
                },
            },
        ],
        "single_select": {
            "id": SelectOption.objects.get(value="A").id,
            "value": "A",
            "color": "red",
        },
        "multiple_select": [
            {
                "id": SelectOption.objects.get(value="D").id,
                "value": "D",
                "color": "yellow",
            },
            {
                "id": SelectOption.objects.get(value="C").id,
                "value": "C",
                "color": "orange",
            },
            {
                "id": SelectOption.objects.get(value="E").id,
                "value": "E",
                "color": "green",
            },
        ],
        "phone_number": "+4412345678",
        "formula": "test FORMULA",
        "lookup": [
            {"id": 1, "value": "linked_row_1"},
            {"id": 2, "value": "linked_row_2"},
            {"id": 3, "value": None},
        ],
    }
