from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, Q
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.accounts.mixins import RoleRequiredMixin
from apps.accounts.models import User

from .forms import ArticleForm
from .models import ArticleTag, KnowledgeArticle


class ArticleListView(LoginRequiredMixin, ListView):
    model = KnowledgeArticle
    template_name = "kb/list.html"
    context_object_name = "articles"
    paginate_by = 20

    def get_queryset(self):
        qs = KnowledgeArticle.objects.select_related("category", "author").prefetch_related("tags")
        if not self.request.user.is_technician:
            qs = qs.filter(status=KnowledgeArticle.Status.PUBLISHED)

        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(summary__icontains=q) | Q(body__icontains=q))

        tag_slug = self.request.GET.get("tag")
        if tag_slug:
            qs = qs.filter(tags__slug=tag_slug)

        category_id = self.request.GET.get("category")
        if category_id and category_id.isdigit():
            qs = qs.filter(category_id=int(category_id))

        return qs.distinct()

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["q"] = self.request.GET.get("q", "")
        ctx["current_tag"] = self.request.GET.get("tag", "")
        ctx["current_category"] = self.request.GET.get("category", "")
        ctx["tags"] = ArticleTag.objects.all()

        from apps.tickets.models import Category
        ctx["categories"] = Category.objects.all()
        return ctx


class ArticleDetailView(LoginRequiredMixin, DetailView):
    model = KnowledgeArticle
    template_name = "kb/detail.html"
    context_object_name = "article"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def get_queryset(self):
        qs = KnowledgeArticle.objects.select_related("category", "author").prefetch_related("tags")
        if not self.request.user.is_technician:
            qs = qs.filter(status=KnowledgeArticle.Status.PUBLISHED)
        return qs

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        obj.increase_views()
        obj.refresh_from_db(fields=["views"])
        return obj

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["related"] = (
            KnowledgeArticle.objects.filter(
                status=KnowledgeArticle.Status.PUBLISHED,
                category=self.object.category,
            )
            .exclude(pk=self.object.pk)[:5]
            if self.object.category
            else []
        )
        return ctx


class ArticleCreateView(RoleRequiredMixin, CreateView):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    model = KnowledgeArticle
    form_class = ArticleForm
    template_name = "kb/form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        messages.success(self.request, "Artykuł został utworzony.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("kb:detail", kwargs={"slug": self.object.slug})


class ArticleUpdateView(RoleRequiredMixin, UpdateView):
    allowed_roles = (User.Role.TECHNICIAN, User.Role.ADMIN)
    model = KnowledgeArticle
    form_class = ArticleForm
    template_name = "kb/form.html"
    slug_field = "slug"
    slug_url_kwarg = "slug"

    def form_valid(self, form):
        messages.success(self.request, "Artykuł zaktualizowany.")
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("kb:detail", kwargs={"slug": self.object.slug})