from datetime import date

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
    readonly_fields = [
        "created_at",
        "updated_at",
        "word_count",
        "todays_image",
    ]
    fields = (
        "name",
        "slug",
        "prompt",
        "word_count",
        "todays_image",
    )

    @admin.display(description=Word._meta.verbose_name_plural)
    def word_count(self, obj: Dictionary):
        count = obj.words.count()
        url = (
            reverse("admin:dailyword_word_changelist")
            + f"?dictionary__id__exact={obj.pk}"
        )
        return format_html('<a href="{}">{}</a>', url, count)

    @admin.display(description="Today's Word")
    def todays_image(self, obj: Dictionary):
        if not obj.pk or not (word := obj.get_word_for_date(date.today())):
            return "-"

        word_url = reverse("admin:dailyword_word_change", args=[word.pk])
        image_url = reverse(
            "dailyword:day-image",
            kwargs={
                "dictionary_slug": obj.slug,
                "width": 512,
                "height": 256,
            },
        )
        return format_html(
            '<a href="{}"><img src="{}" style="max-width:100%;border:1px solid var(--header-bg)" alt="{}"></a>',
            word_url,
            image_url,
            word.word,
        )


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
