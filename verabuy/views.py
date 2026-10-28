from django.shortcuts import render
from store.models import Product

def home(request):
    products = Product.objects.all().filter(is_available=True)
    deals = Product.objects.filter(is_deals=True, is_available=True)[:4] 
    context = {'products': products, 'deals': deals}
    return render(request, 'home.html', context)