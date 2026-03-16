from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import Dictionary, Word


class TimestampedAdmin(admin.ModelAdmin):
    def get_fieldsets(self, request, obj=None):
        fieldsets = list(super().get_fieldsets(request, obj))
        fieldsets.append(
            (
                "Metadata",
                {
                    "fields": ("created_at", "updated_at"),
                    "classes": ("collapse",),
                },
            ),
        )
        return fieldsets


@admin.register(Dictionary)
class DictionaryAdmin(TimestampedAdmin):
    list_display = [
        "name",
        "slug",
        "word_count",
    ]
    search_fields = ["name", "prompt"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at", "word_count"]

    @admin.display(description=Word._meta.verbose_name_plural)
    def word_count(self, obj: Dictionary):
        count = obj.words.count()
        url = (
            reverse("admin:dailyword_word_changelist")
            + f"?dictionary__id__exact={obj.pk}"
        )
        return format_html('<a href="{}">{}</a>', url, count)


@admin.register(Word)
class WordAdmin(TimestampedAdmin):
    list_display = [
        "word",
        "dictionary",
        "part_of_speech",
    ]
    list_filter = [
        "dictionary",
        "part_of_speech",
    ]
    search_fields = [
        "word",
        "definition",
        "example_sentence",
    ]
    readonly_fields = ["created_at", "updated_at"]
    autocomplete_fields = ["dictionary"]

    fieldsets = (
        (
            None,
            {
                "fields": (
                    "dictionary",
                    "word",
                )
            },
        ),
        (
            "Definition",
            {
                "fields": (
                    "definition",
                    "example_sentence",
                    "pronunciation",
                    "part_of_speech",
                )
            },
        ),
    )
