from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.text import slugify

from .models import Product, Variation, ReviewRating
from .forms import ProductForm, ReviewForm
from category.models import Category
from carts.models import CartItem
from carts.views import _cart_id
from orders.models import OrderProduct

def store(request, category_slug=None):
    categories = None
    products = None
    
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:    
        if 'keyword' in request.GET:
            keyword = request.GET['keyword']
            if keyword:
                products = Product.objects.order_by('-created_date').filter(
                    Q(description__icontains=keyword) | Q(product_name__icontains=keyword), 
                    is_available=True
                )
                product_count = products.count()
                paged_products = products
        else:
            products = Product.objects.all().filter(is_available=True).order_by('id')
            paginator = Paginator(products, 6)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()
            
    context = {
        'products': paged_products,
        'product_count': product_count, 
    }
    return render(request, 'store/store.html', context)

def products_detail(request, category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product)
    except Exception as e:
        raise e
    
    variations = Variation.objects.filter(product=single_product)
    
    if request.user.is_authenticated:
        try:
            orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists()
        except OrderProduct.DoesNotExist:
            orderproduct = None
    else:
        orderproduct = None

    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'variations': variations,
        'orderproduct': orderproduct, 
        'reviews': reviews,           
    }
    return render(request, 'store/product_detail.html', context)

def submit_review(request, product_id):
    product = get_object_or_404(Product, id=product_id) 
    url = product.get_url()
    
    if request.method == 'POST':
        try:
            reviews = ReviewRating.objects.get(user__id=request.user.id, product__id=product_id)
            form = ReviewForm(request.POST, instance=reviews)
            form.save()
            messages.success(request, 'Thank you! Your review has been updated.')
            return redirect(url)
        except ReviewRating.DoesNotExist:
            form = ReviewForm(request.POST)
            if form.is_valid():
                data = ReviewRating()
                data.subject = form.cleaned_data['subject']
                data.rating = form.cleaned_data['rating']
                data.review = form.cleaned_data['review']
                data.ip = request.META.get('REMOTE_ADDR')
                data.product_id = product_id
                data.user_id = request.user.id
                data.save()
                messages.success(request, 'Thank you! Your review has been submitted.')
                return redirect(url)
    return redirect('store')

@login_required(login_url='login')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.save(commit=False)
            data.seller = request.user
            data.slug = slugify(data.product_name)
            
            if Product.objects.filter(slug=data.slug).exists():
                messages.error(request, 'A product with this name already exists.')
                return redirect('add_product')

            data.save()
            return render(request, 'store/product_uploaded.html') 
    else:
        form = ProductForm()
    return render(request, 'store/add_product.html', {'form': form})

# NEW: Edit product view for seller stock/deals
@login_required(login_url='login')
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id, seller=request.user)
    
    if request.method == 'POST':
        product.stock = request.POST['stock']
        product.is_available = 'is_available' in request.POST
        product.is_deals = 'is_deals' in request.POST 
        product.save()
        messages.success(request, 'Product updated successfully.')
        return redirect('dashboard')
        
    context = {'product': product}
    return render(request, 'store/edit_product.html', context)

def handler404(request, exception):
    return render(request, 'errors/404.html', status=404)

def handler500(request):
    return render(request, 'errors/500.html', status=500)