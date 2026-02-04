import pytest
from django.contrib.admin.sites import AdminSite

from dailyword.admin import DictionaryAdmin, WordInline
from dailyword.models import Dictionary, Word


@pytest.fixture
def admin_site():
    return AdminSite()


@pytest.fixture
def dictionary(db):
    return Dictionary.objects.create(
        name="Test Dictionary",
        prompt="test prompt",
    )


@pytest.fixture
def word(dictionary):
    return Word.objects.create(
        dictionary=dictionary,
        word="Example",
        definition="A thing characteristic of its kind",
        example_sentence="This is an example sentence.",
        pronunciation="/igzaempel/",
        part_of_speech="noun",
    )


class TestDictionaryAdmin:
    def test_list_display(self, admin_site):
        admin = DictionaryAdmin(Dictionary, admin_site)
        assert "name" in admin.list_display
        assert "slug" in admin.list_display
        assert "word_count" in admin.list_display
        assert "created_at" in admin.list_display
        assert "updated_at" in admin.list_display

    def test_word_count(self, admin_site, dictionary, word):
        admin = DictionaryAdmin(Dictionary, admin_site)
        assert admin.word_count(dictionary) == 1

        # Add another word
        Word.objects.create(
            dictionary=dictionary,
            word="Another",
            definition="Another word",
        )
        assert admin.word_count(dictionary) == 2

    def test_word_count_empty(self, admin_site, dictionary):
        admin = DictionaryAdmin(Dictionary, admin_site)
        assert admin.word_count(dictionary) == 0

    def test_search_fields(self, admin_site):
        admin = DictionaryAdmin(Dictionary, admin_site)
        assert "name" in admin.search_fields
        assert "prompt" in admin.search_fields

    def test_prepopulated_fields(self, admin_site):
        admin = DictionaryAdmin(Dictionary, admin_site)
        assert "slug" in admin.prepopulated_fields
        assert admin.prepopulated_fields["slug"] == ("name",)

    def test_readonly_fields(self, admin_site):
        admin = DictionaryAdmin(Dictionary, admin_site)
        assert "created_at" in admin.readonly_fields
        assert "updated_at" in admin.readonly_fields

    def test_has_word_inline(self, admin_site):
        admin = DictionaryAdmin(Dictionary, admin_site)
        assert WordInline in admin.inlines


class TestWordInline:
    def test_model(self, admin_site):
        inline = WordInline(Dictionary, admin_site)
        assert inline.model == Word

    def test_extra(self, admin_site):
        inline = WordInline(Dictionary, admin_site)
        assert inline.extra == 0

    def test_fields(self, admin_site):
        inline = WordInline(Dictionary, admin_site)
        assert "word" in inline.fields
        assert "definition" in inline.fields
        assert "example_sentence" in inline.fields
        assert "pronunciation" in inline.fields
        assert "part_of_speech" in inline.fields


class TestAdminIntegration:
    def test_dictionary_admin_registered(self, admin_client):
        response = admin_client.get("/admin/dailyword/dictionary/")
        assert response.status_code == 200

    def test_add_dictionary_page(self, admin_client):
        response = admin_client.get("/admin/dailyword/dictionary/add/")
        assert response.status_code == 200

    def test_dictionary_change_page(self, admin_client, dictionary):
        response = admin_client.get(
            f"/admin/dailyword/dictionary/{dictionary.id}/change/"
        )
        assert response.status_code == 200

    def test_word_inline_visible_on_dictionary_change(self, admin_client, dictionary):
        response = admin_client.get(
            f"/admin/dailyword/dictionary/{dictionary.id}/change/"
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "word" in content.lower()
