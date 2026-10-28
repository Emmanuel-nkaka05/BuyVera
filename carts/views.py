import datetime
import random 
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required

from store.models import Product, Variation # <--- Added Variation
from .models import Cart, CartItem
from orders.models import Order, OrderProduct, Payment
from orders.forms import OrderForm 

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart
    
def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    
    # Get or create the cart
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id=_cart_id(request)
        )
    cart.save()
    
    # Get or create the cart item
    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        cart_item.quantity += 1 
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            quantity=1,
            cart=cart,
            user=request.user if request.user.is_authenticated else None
        )    
        cart_item.save()
        
        # --- ADD VARIATIONS ---
        if 'color' in request.POST:
            color = request.POST['color']
            if color:
                variation = Variation.objects.get(product=product, variation_category='color', variation_value=color)
                cart_item.variations.add(variation)
                
        if 'size' in request.POST:
            size = request.POST['size']
            if size:
                variation = Variation.objects.get(product=product, variation_category='size', variation_value=size)
                cart_item.variations.add(variation)
                
    return redirect('cart')

def remove_cart(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    if cart_item.quantity > 1:
        cart_item.quantity -= 1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart')

def remove_cart_item(request, product_id):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart=cart)
    cart_item.delete()
    return redirect('cart')
    
def cart(request, total=0, quantity=0):
    tax = 0
    grand_total = 0
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for item in cart_items:
            total += (item.product.price * item.quantity)
            quantity += item.quantity
            
        tax = (2 * total) / 100
        grand_total = total + tax     
    except Cart.DoesNotExist: 
        cart_items = []
        total = 0
        quantity = 0
        
    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }      
    return render(request, 'store/cart.html', context)

@login_required(login_url='login')
def checkout(request, total=0, quantity=0):
    tax = 0
    grand_total = 0
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, is_active=True)
        
        for item in cart_items:
            total += (item.product.price * item.quantity)
            quantity += item.quantity
            
        tax = (2 * total) / 100
        grand_total = total + tax
        
    except Cart.DoesNotExist:
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
    }
    return render(request, 'store/checkout.html', context)

@login_required(login_url='login')
def place_order(request, total=0, quantity=0):
    current_user = request.user
    cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request))
    
    if cart_items.count() <= 0:
        return redirect('store')

    tax = 0
    grand_total = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    tax = (2 * total) / 100
    grand_total = total + tax

    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            data.user = current_user
            data.first_name = form.cleaned_data['first_name']
            data.last_name = form.cleaned_data['last_name']
            data.phone = form.cleaned_data['phone']
            data.email = form.cleaned_data['email']
            data.address_line_1 = form.cleaned_data['address_line_1']
            data.address_line_2 = form.cleaned_data['address_line_2']
            data.country = form.cleaned_data['country']
            data.state = form.cleaned_data['state']
            data.city = form.cleaned_data['city']
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            data.save()

            # Generate order number
            yr = int(datetime.date.today().strftime('%Y'))
            dt = int(datetime.date.today().strftime('%d'))
            mt = int(datetime.date.today().strftime('%m'))
            d = datetime.date(yr, mt, dt)
            current_date = d.strftime("%Y%m%d")
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)
            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
            }
            return render(request, 'orders/payments.html', context)
    else:
        return redirect('checkout')

@login_required(login_url='login')
def payments(request):
    current_user = request.user
    order = Order.objects.filter(user=current_user, is_ordered=False).order_by('-created_at').first()
    
    if order:
        # 1. Create Payment
        payment = Payment(
            user=current_user,
            payment_id='MOCK-' + str(random.randint(100000, 999999)),
            payment_method='Mock Payment',
            amount_paid=order.order_total,
            status='Completed',
        )
        payment.save()

        # 2. Attach payment to order
        order.payment = payment
        order.is_ordered = True
        order.save()

        # 3. Move cart items to OrderProduct & Reduce Stock
        cart_items = CartItem.objects.filter(cart__cart_id=_cart_id(request))

        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.payment = payment
            orderproduct.user_id = current_user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()

            # REDUCE PRODUCT STOCK
            product = Product.objects.get(id=item.product_id)
            product.stock -= item.quantity
            product.save()

        # 4. Clear the cart
        CartItem.objects.filter(cart__cart_id=_cart_id(request)).delete()

        return render(request, 'orders/order_complete.html', {'order': order})
    else:
        return redirect('store')