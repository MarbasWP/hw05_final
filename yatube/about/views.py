from django.views.generic.base import TemplateView


class AuthorStaticPage(TemplateView):
    template_name = 'about/author_page.html'


class TechStaticPage(TemplateView):
    template_name = 'about/tech_page.html'
