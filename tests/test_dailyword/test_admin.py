import pytest
from django.contrib.admin.sites import AdminSite

from dailyword.admin import DictionaryAdmin
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
        word="Example Word",
        definition="A thing characteristic of its kind",
        example_sentence="This is an example sentence.",
        pronunciation="/igzaempel/",
        part_of_speech="noun",
    )


class TestDictionaryAdmin:
    def test_word_count_link(self, admin_site, dictionary, word):
        admin = DictionaryAdmin(Dictionary, admin_site)
        result = admin.word_count(dictionary)
        assert f"?dictionary__id__exact={dictionary.pk}" in result
        assert ">1</a>" in result

        Word.objects.create(
            dictionary=dictionary,
            word="Another",
            definition="Another word",
        )
        result = admin.word_count(dictionary)
        assert ">2</a>" in result

    def test_word_count_empty(self, admin_site, dictionary):
        admin = DictionaryAdmin(Dictionary, admin_site)
        result = admin.word_count(dictionary)
        assert ">0</a>" in result

    def test_todays_word_link(self, admin_site, dictionary, word):
        admin = DictionaryAdmin(Dictionary, admin_site)
        result = admin.todays_image(dictionary)
        assert "<a" in result
        assert f"/admin/dailyword/word/{word.pk}/change/" in result
        assert "Example Word" in result
        assert "<img" in result
        assert f"/{dictionary.slug}/512x256/" in result

    def test_todays_word_link_empty(self, admin_site, dictionary):
        admin = DictionaryAdmin(Dictionary, admin_site)
        result = admin.todays_image(dictionary)
        assert result == "-"


class TestAdminIntegration:
    def test_dictionary_list_page(self, admin_client, dictionary):
        response = admin_client.get("/admin/dailyword/dictionary/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Dictionary" in content

    def test_dictionary_change_page(self, admin_client, dictionary):
        response = admin_client.get(
            f"/admin/dailyword/dictionary/{dictionary.id}/change/"
        )
        assert response.status_code == 200
        content = response.content.decode()
        assert "Test Dictionary" in content
        assert f"?dictionary__id__exact={dictionary.pk}" in content
        assert ">0</a>" in content

    def test_dictionary_change_page_shows_today_section(
        self, admin_client, dictionary, word
    ):
        response = admin_client.get(
            f"/admin/dailyword/dictionary/{dictionary.id}/change/"
        )
        content = response.content.decode()
        assert f"/admin/dailyword/word/{word.pk}/change/" in content
        assert "<img" in content
        assert f"/{dictionary.slug}/512x256" in content

    def test_word_list_page(self, admin_client, word):
        response = admin_client.get("/admin/dailyword/word/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Example Word" in content

    def test_word_change_page(self, admin_client, word):
        response = admin_client.get(f"/admin/dailyword/word/{word.id}/change/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Example Word" in content
