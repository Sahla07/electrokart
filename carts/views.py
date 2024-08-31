from django.shortcuts import render, redirect, get_object_or_404
from store.models import Product, Wishlist,Variation
from .models import Cart, CartItem
from orders.models import Coupon
from django.contrib import messages
from accounts.forms import AddressForm,Address
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
import json
from django.views.decorators.csrf import csrf_exempt

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart
def add_cart(request, product_id):
    current_user = request.user
    product = None
    try:
        product = Product.objects.get(id=product_id)  # get the product
    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)

    product_variation = []
    if request.method == "POST":
        for item in request.POST:
            key = item
            value = request.POST[key]
            try:
                variations = Variation.objects.filter(product=product, variation_category__iexact=key, variation_value__iexact=value)
                if variations.exists():
                    product_variation.extend(variations)
            except Variation.DoesNotExist:
                pass

    is_cart_item_exists = CartItem.objects.filter(product=product, user_id=current_user.id).exists()
    if current_user.is_authenticated:
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, user=current_user)
            ex_var_list = []
            id_list = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id_list.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, quantity=1, user=current_user)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, user=current_user)
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()
    else:
        product_variation = []
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]
                try:
                    variations = Variation.objects.filter(product=product, variation_category__iexact=key, variation_value__iexact=value)
                    if variations.exists():
                        product_variation.extend(variations)
                except Variation.DoesNotExist:
                    pass

        cart = None
        try:
            cart = Cart.objects.get(cart_id=_cart_id(request))
        except Cart.DoesNotExist:
            cart = Cart.objects.create(cart_id=_cart_id(request))
            cart.save()

        is_cart_item_exists = CartItem.objects.filter(product=product, cart=cart).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product, cart=cart)
            ex_var_list = []
            id_list = []
            for item in cart_item:
                existing_variation = item.variations.all()
                ex_var_list.append(list(existing_variation))
                id_list.append(item.id)

            if product_variation in ex_var_list:
                index = ex_var_list.index(product_variation)
                item_id = id_list[index]
                item = CartItem.objects.get(product=product, id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product, quantity=1, cart=cart)
                if len(product_variation) > 0:
                    item.variations.clear()
                    item.variations.add(*product_variation)
                item.save()
        else:
            cart_item = CartItem.objects.create(product=product, quantity=1, cart=cart)
            if len(product_variation) > 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_variation)
            cart_item.save()

    return redirect('cart')



@csrf_exempt
def update_cart_quantity(request):
    if request.method == 'POST':
        import json
        data = json.loads(request.body)
        cart_id = data.get('cart_id')
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        try:
            cart_item = CartItem.objects.get(id=cart_id, product_id=product_id)
            if quantity <= cart_item.product.stock:
                cart_item.quantity = quantity
                cart_item.save()
                return JsonResponse({'status': 'success'})
            else:
                return JsonResponse({'status': 'error', 'message': 'Insufficient stock'})
        except CartItem.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Cart item not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})
def remove_cart(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else:
            cart_item.delete()
    except:
        pass
    return redirect('cart')

def remove_cart_item(request, product_id, cart_item_id):
    product = get_object_or_404(Product, id=product_id)
    try:
        if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product, user=request.user, id=cart_item_id)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product, cart=cart, id=cart_item_id)
        cart_item.delete()
    except:
        pass
    return redirect('cart')

def cart(request, total=0, quantity=0, cart_items=None):
    tax = 0
    grand_total = 0
    wishlist_items = None

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
            wishlist_items = Wishlist.objects.filter(user=request.user)
        else:
            cart_queryset = Cart.objects.filter(cart_id=_cart_id(request))
            if cart_queryset.exists():
                cart = cart_queryset.first()  # Assuming there should be only one cart with the given cart_id
                cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            else:
                cart_items = []  # Handle the case where the cart does not exist

        for cart_item in cart_items:
            total += cart_item.sub_total()
            quantity += cart_item.quantity
        # Calculate tax and grand total
        if total:
            tax = (2 * total) / 100
            grand_total = total + tax
    except ZeroDivisionError:
        # Handle division by zero error
        pass
    except ObjectDoesNotExist:
        # Handle the case where objects do not exist, such as when the cart is empty
        pass

    context = {
        'total': total,
        'quantity': quantity,
        'cart_items': cart_items,
        'tax': tax,
        'grand_total': grand_total,
        'wishlist_items': wishlist_items,
    }

    return render(request, 'store/cart.html', context)

@login_required(login_url='accounts:loginn')
def checkout(request, total=0, quantity=0, cart_items=None):

    try:
        tax = 0  # Initialize tax variable outside of try block
        grand_total = 0  # Initialize tax variable outside of try block
        addresses = Address.objects.filter(user=request.user)
        coupon = None  # Initialize coupon variable
        final_total = 0  # Initialize final_total variable
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)        
        for cart_item in cart_items:
            total += cart_item.sub_total()
            quantity += cart_item.quantity
        tax = (2 * total)/100
        grand_total = total + tax

        

    except ObjectDoesNotExist:
        pass
    

    context = {
        'total' : total,
        'quantity' : quantity,
        'cart_items': cart_items,
        'tax' : tax,
        'grand_total' : grand_total,
        'addresses': addresses,
    }
    return render(request, 'store/checkout.html',context)


@login_required(login_url='accounts:loginn')
def add_address(request):
    if request.method == 'POST':
        address_form = AddressForm(request.POST)
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully')
            return redirect('accounts:edit_profile')
    else:
        address_form = AddressForm()

    context = {
        'address_form': address_form,
    }
    return render(request, 'accounts/add_address.html', context)

@login_required(login_url='accounts:loginn')
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == 'POST':
        address_form = AddressForm(request.POST, instance=address)
        if address_form.is_valid():
            address_form.save()
            messages.success(request, 'Address updated successfully')
            return redirect('accounts:edit_profile')
    else:
        address_form = AddressForm(instance=address)

    context = {
        'address_form': address_form
    }
    return render(request, 'accounts/edit_address.html', context)

@login_required(login_url='accounts:loginn')
def delete_address(request, address_id):
    address = Address.objects.get(pk=address_id)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully')
    return redirect('accounts:edit_profile')


def apply_coupon(request):
    if request.method == 'POST' and request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Extract the coupon code from the request body
        body_unicode = request.body.decode('utf-8')
        body_data = json.loads(body_unicode)
        coupon_code = body_data.get('coupon_code')
        current_datetime = timezone.now()

        try:
            coupon = Coupon.objects.get(code=coupon_code)
            if coupon.valid_from <= current_datetime <= coupon.valid_to:
                # Coupon is valid, you can return success and additional coupon information
                print('good')
                return JsonResponse({'success': True, 'discount': coupon.discount}, status=200)
                
            else:
                # Coupon is expired
                print('expir')
                return JsonResponse({'success': False, 'error': 'Coupon is expired'}, status=400)
        except Coupon.DoesNotExist:
            # Coupon does not exist
            print('error')
            return JsonResponse({'success': False, 'error': 'Invalid coupon code'}, status=400)
    else:
        # Method not allowed or request is not AJAX
        print('big error')
        return JsonResponse({'success': False, 'error': 'Invalid request'}, status=400)



