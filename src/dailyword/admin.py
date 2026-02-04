from django.contrib import admin

from .models import Dictionary, Word


class WordInline(admin.StackedInline):
    model = Word
    extra = 0
    fields = [
        "word",
        "definition",
        "example_sentence",
        "pronunciation",
        "part_of_speech",
    ]


@admin.register(Dictionary)
class DictionaryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "word_count", "created_at", "updated_at"]
    search_fields = ["name", "prompt"]
    prepopulated_fields = {"slug": ("name",)}
    readonly_fields = ["created_at", "updated_at"]
    inlines = [WordInline]

    @admin.display(description="Words")
    def word_count(self, obj):
        return obj.words.count()
