from django import forms

from .models import Asset, AssetCategory, License, Location


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = [
            "name",
            "type",
            "category",
            "manufacturer",
            "model_name",
            "serial_number",
            "status",
            "location",
            "assigned_to",
            "purchase_date",
            "warranty_until",
            "purchase_price",
            "notes",
        ]
        widgets = {
            "purchase_date": forms.DateInput(attrs={"type": "date"}),
            "warranty_until": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = AssetCategory.objects.all()
        self.fields["category"].empty_label = "— brak —"
        self.fields["location"].queryset = Location.objects.all()
        self.fields["location"].empty_label = "— brak —"
        self.fields["assigned_to"].empty_label = "— nieprzypisany —"

        for f in self.fields.values():
            if isinstance(f.widget, forms.CheckboxInput):
                continue
            css = f.widget.attrs.get("class", "")
            if isinstance(f.widget, forms.Select):
                f.widget.attrs["class"] = (css + " form-select").strip()
            else:
                f.widget.attrs["class"] = (css + " form-control").strip()


class AssetAssignForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=None,
        required=False,
        label="Użytkownik",
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 2}),
        required=False,
        label="Komentarz",
    )

    def __init__(self, *args, **kwargs):
        from apps.accounts.models import User

        super().__init__(*args, **kwargs)
        self.fields["user"].queryset = User.objects.filter(is_active=True).order_by("username")
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            if isinstance(f.widget, forms.Select):
                f.widget.attrs["class"] = (css + " form-select").strip()
            else:
                f.widget.attrs["class"] = (css + " form-control").strip()


class LicenseForm(forms.ModelForm):
    class Meta:
        model = License
        fields = [
            "name",
            "vendor",
            "seats_total",
            "seats_used",
            "expires_at",
            "key_reference",
            "notes",
        ]
        widgets = {
            "expires_at": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control").strip()
