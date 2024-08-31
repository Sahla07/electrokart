from .models import Category

def menu_links(request):
    links = Category.objects.filter(is_active=True)
    return dict(links=links)