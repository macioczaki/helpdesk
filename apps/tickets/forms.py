from django import forms

from apps.accounts.models import User

from .models import Category, Ticket, TicketComment


class TicketCreateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority"]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 6}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.all()
        self.fields["category"].empty_label = "— brak —"

        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control").strip()
            if isinstance(f.widget, forms.Select):
                f.widget.attrs["class"] = (css + " form-select").strip()


class TicketUpdateForm(forms.ModelForm):
    class Meta:
        model = Ticket
        fields = ["title", "description", "category", "priority", "status", "assigned_to"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["category"].queryset = Category.objects.all()
        self.fields["assigned_to"].queryset = User.objects.filter(
            role__in=[User.Role.TECHNICIAN, User.Role.ADMIN]
        )
        self.fields["assigned_to"].empty_label = "— nieprzypisane —"

        if user and not user.is_technician:
            for field in ("status", "assigned_to"):
                self.fields.pop(field)

        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control").strip()
            if isinstance(f.widget, forms.Select):
                f.widget.attrs["class"] = (css + " form-select").strip()

class CommentForm(forms.ModelForm):
    class Meta:
        model = TicketComment
        fields = ["body", "is_internal"]
        widgets = {"body": forms.Textarea(attrs={"rows": 3, "placeholder": "Treść komentarza..."})}

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        if not (user and user.is_technician):
            self.fields.pop("is_internal")
        for f in self.fields.values():
            css = f.widget.attrs.get("class", "")
            f.widget.attrs["class"] = (css + " form-control").strip()