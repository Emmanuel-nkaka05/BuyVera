from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator
from django.utils.text import slugify
from django.contrib.auth.decorators import login_required
from .models import Product, Variation, ReviewRating
from .forms import ProductForm, ReviewForm
from category.models import Category
from carts.models import CartItem  # <--- FIXED TYPO
from carts.views import _cart_id
from orders.models import OrderProduct

def store(request, category_slug=None):
    categories = None
    products = None
    is_deals_page = False
    is_price_filter = False
    
    base_query = Product.objects.select_related('seller').filter(is_available=True)
    
    if category_slug != None:
        categories = get_object_or_404(Category, slug=category_slug)
        products = base_query.filter(category=categories)
        paginator = Paginator(products, 6)
        page = request.GET.get('page')
        paged_products = paginator.get_page(page)
        product_count = products.count()
    else:    
        if 'keyword' in request.GET:
            keyword = request.GET['keyword']
            if keyword:
                products = base_query.order_by('-created_date').filter(
                    Q(description__icontains=keyword) | Q(product_name__icontains=keyword)
                )
                product_count = products.count()
                paged_products = products
        
        elif 'deals' in request.GET:
            is_deals_page = True
            products = base_query.filter(is_deals=True).order_by('id')
            product_count = products.count()
            paged_products = products
            
        elif 'min_price' in request.GET and 'max_price' in request.GET:
            is_price_filter = True
            min_price = request.GET['min_price']
            max_price = request.GET['max_price']
            
            if not min_price:
                min_price = 0
            if not max_price:
                max_price = 9999999
            
            products = base_query.filter(price__gte=min_price, price__lte=max_price).order_by('id')
            paginator = Paginator(products, 6)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()
            
        else:
            products = base_query.order_by('id')
            paginator = Paginator(products, 6)
            page = request.GET.get('page')
            paged_products = paginator.get_page(page)
            product_count = products.count()
            
    context = {
        'products': paged_products,
        'product_count': product_count, 
        'is_deals_page': is_deals_page,
        'is_price_filter': is_price_filter,
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
    if not request.user.is_seller and not request.user.is_superadmin:
        messages.error(request, 'You must be a registered seller to upload products.')
        return redirect('dashboard')

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

@login_required(login_url='login')
def edit_product(request, product_id):
    if not request.user.is_seller and not request.user.is_superadmin:
        messages.error(request, 'Access Denied.')
        return redirect('dashboard')
        
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