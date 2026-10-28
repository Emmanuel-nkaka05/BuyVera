from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from orders.models import Order, OrderProduct
from store.models import Product

@login_required(login_url='login')
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id, is_ordered=True)
    orders_count = orders.count()
    my_products = Product.objects.filter(seller=request.user).order_by('-created_date')

    context = {
        'orders_count': orders_count,
        'my_products': my_products,
    }
    return render(request, 'dashboard/dashboard.html', context)

@login_required(login_url='login')
def my_orders(request):
    orders = Order.objects.filter(user=request.user, is_ordered=True).order_by('-created_at')
    context = {'orders': orders}
    return render(request, 'dashboard/my_orders.html', context)

# NEW: Receipt View
@login_required(login_url='login')
def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    order_products = OrderProduct.objects.filter(order=order)
    
    context = {
        'order': order,
        'order_products': order_products,
    }
    return render(request, 'dashboard/order_detail.html', context)