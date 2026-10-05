from django import forms

from .models import ArticleTag, KnowledgeArticle


class ArticleForm(forms.ModelForm):
    tags_input = forms.CharField(
        required=False,
        label="Tagi",
        help_text="Oddziel tagi przecinkami, np. drukarka, sieć, office",
    )

    class Meta:
        model = KnowledgeArticle
        fields = ["title", "summary", "body", "category", "status"]
        widgets = {
            "summary": forms.TextInput(attrs={"placeholder": "Krótki opis — widoczny na liście"}),
            "body": forms.Textarea(attrs={"rows": 12}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields["tags_input"].initial = ", ".join(t.name for t in self.instance.tags.all())

        for f in self.fields.values():
            if isinstance(f.widget, forms.CheckboxInput):
                continue
            css = f.widget.attrs.get("class", "")
            if isinstance(f.widget, forms.Select):
                f.widget.attrs["class"] = (css + " form-select").strip()
            else:
                f.widget.attrs["class"] = (css + " form-control").strip()

    def save(self, commit=True):
        article = super().save(commit=False)
        if commit:
            article.save()
            raw = self.cleaned_data.get("tags_input", "") or ""
            names = [n.strip() for n in raw.split(",") if n.strip()]
            tags = []
            for name in names:
                tag, _ = ArticleTag.objects.get_or_create(name=name)
                tags.append(tag)
            article.tags.set(tags)
        return article
