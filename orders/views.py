from django.shortcuts import render, redirect, get_object_or_404
from carts.models import CartItem
from store.models import Product
from django.contrib import messages
from django.http import JsonResponse
from accounts.models import Address, Wallet
from .models import Order, OrderProduct, Payment, Coupon
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from datetime import datetime
from decimal import Decimal
import json
from django.utils import timezone
from datetime import datetime
from django.db.models import F



@login_required(login_url='accounts:loginn')
def payments(request):
    body = json.loads(request.body)
    order = Order.objects.get(user=request.user, is_ordered = False, order_number=body['orderID'])

        # Store transaction details inside the Payment model
    payment = Payment(
            user=request.user,
            payment_id=body['transID'],
            payment_method=body['payment_method'],
            amount_paid=order.final_total,
            status=body['status'],
        )
    payment.save()

    
    order.payment = payment
    order.is_ordered = True
    order.status = 'Completed'
    order.save()

    # Move the cart items to the OrderProduct table
    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
                orderproduct = OrderProduct()
                orderproduct.order_id = order.id
                orderproduct.payment = payment
                orderproduct.user_id = request.user.id
                orderproduct.product_id = item.product_id
                orderproduct.quantity = item.quantity
                orderproduct.product_price = item.product.price
                orderproduct.ordered = True
                orderproduct.save()

                # Save product variations
                cart_item = CartItem.objects.get(id=item.id)
                product_variation = cart_item.variations.all()
                orderproduct = OrderProduct.objects.get(id=orderproduct.id)
                orderproduct.variations.set(product_variation)
                orderproduct.save()

                # Reduce the quantity of the sold products
                product = Product.objects.get(id=item.product_id)
                product.stock -= item.quantity
                product.save()

            # Clear cart
    CartItem.objects.filter(user=request.user).delete()

            # Send order number and transaction ID back to the sendData method via JsonResponse
    data = {
            'order_number': order.order_number,
            'transID': payment.payment_id,
            }
    return JsonResponse(data)

   
    
        

def place_order(request, total=0, quantity=0):
    if request.method == "POST":
        current_user = request.user
        current_datetime = timezone.now()
        selected_address_id = request.POST.get('selected_address')
        
        try:
            wallet = Wallet.objects.get(account=current_user)
            wallet_balance = wallet.wallet_balance
        except Wallet.DoesNotExist:
            wallet_balance = Decimal('0')  # Use Decimal

        cart_items = CartItem.objects.filter(user=current_user)
        cart_count = cart_items.count()
        if cart_count <= 0:
            return redirect('store')

        # Convert initial totals to Decimal
        grand_total = Decimal('0')
        tax = Decimal('0')
        final_total = Decimal('0')
        discount = Decimal('0')
        delivery_charge = Decimal('0')
    
        if selected_address_id:
            selected_address = get_object_or_404(Address, id=selected_address_id)
        
            for cart_item in cart_items:
                total += Decimal(cart_item.product.price_after_discount()) * cart_item.quantity
                quantity += cart_item.quantity
            
            tax = (Decimal('2') * total) / Decimal('100')
            grand_total = total + tax

            # Delivery charge logic
            if grand_total > Decimal('400'):
                delivery_charge = Decimal('0')
            else:
                delivery_charge = Decimal('60')

            final_total = grand_total + delivery_charge

        coupon_code = request.POST.get('coupon_code')
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                
                if coupon.valid_from <= current_datetime <= coupon.valid_to:
                    discount = Decimal(coupon.discount)  # Ensure discount is Decimal
                    final_total -= discount
                    final_total = max(Decimal('0'), final_total)
                else:
                    discount = Decimal('0')
                    
            except Coupon.DoesNotExist:
                discount = Decimal('0')
        else:
            final_total = grand_total

        if selected_address_id:
            order = Order.objects.create(
                user=current_user,
                first_name=current_user.first_name,
                last_name=current_user.last_name,
                coupon=coupon_code,
                email=current_user.email,
                street_address=selected_address.street_address,
                city=selected_address.city,
                state=selected_address.state,
                country=selected_address.country,
                phone_number=selected_address.phone_number,
                order_total=grand_total,
                final_total=final_total,
                tax=tax,
                delivery_charge=delivery_charge,
                ip=request.META.get('REMOTE_ADDR')
            )

            yr = current_datetime.year
            mt = current_datetime.month
            dt = current_datetime.day
            d = datetime(yr, mt, dt)
            current_date = d.strftime("%Y%d%m")
            order_number = current_date + str(order.id)
            order.order_number = order_number
            order.save()

            order = Order.objects.get(user=current_user, is_ordered=False, order_number=order_number)

            context = {
                'order': order,
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'discount': discount,
                'final_total': final_total,
                'delivery_charge': delivery_charge,
                'wallet_balance': wallet_balance,
                'error_message': None
            }
            
            return render(request, 'orders/payments.html', context)
        else:
            error_message = "Please select an address"
            addresses = Address.objects.filter(user=current_user)
            context = {
                'cart_items': cart_items,
                'total': total,
                'tax': tax,
                'grand_total': grand_total,
                'wallet_balance': wallet_balance,
                'addresses': addresses,
                'error_message': error_message
            }
            return render(request, 'store/checkout.html', context)
    else:
        return redirect('checkout')

@login_required(login_url='accounts:loginn')
def order_complete(request):
    order_number = request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        # Update the order status to 'Completed'
        order.status = 'Completed'  # 'Completed' instead of 'COMPLETED' for consistency with the model
        order.save()

        ordered_products = OrderProduct.objects.filter(order_id=order.id)

        subtotal = 0
        for i in ordered_products:
            subtotal += i.product_price * i.quantity

        # Debugging: Check if transID is correctly retrieved
        print(f"Transaction ID: {transID}")

        # Retrieve payment object
        try:
            payment = Payment.objects.get(payment_id=transID)
            # Debugging: Check if payment is correctly retrieved
            print(f"Payment Method: {payment.payment_method}")
        except Payment.DoesNotExist:
            payment = None
            print("Payment not found")

        # Retrieve coupon discount
        coupon_discount = 0
        if order.coupon:
            try:
                coupon = Coupon.objects.get(code=order.coupon)
                # Check if the coupon is valid
                if coupon.valid_from <= order.created_at <= coupon.valid_to:
                    coupon_discount = coupon.discount
            except Coupon.DoesNotExist:
                pass

        context = {
            'order': order,
            'ordered_products': ordered_products,
            'order_number': order.order_number,
            'transID': transID,
            'payment': payment,
            'subtotal': subtotal,
            'coupon_discount': coupon_discount,  # Pass coupon discount to the context
        }

        return render(request, 'orders/order_complete.html', context)
    except (Order.DoesNotExist, Exception) as e:
        print(f"Error: {e}")
        return redirect('store')
    
def add_to_wallet(request, order_number):
    try:
        # Retrieve the user's wallet
        wallet = get_object_or_404(Wallet, account=request.user)
        
        # Retrieve the order based on the order number
        order = get_object_or_404(Order, order_number=order_number)
        
        # Retrieve the final_total from the order
        final_total = order.final_total
        
        # Check if the user has enough balance in the wallet
        if wallet.wallet_balance < final_total:
            messages.error(request, "Insufficient balance in your wallet.")
            return redirect('cart')  # Redirect to the cart page or any relevant page
        
        # Reduce the final_total amount from the wallet_balance
        wallet.wallet_balance -= final_total
        wallet.save()

        # Update the order status to 'Completed' and is_ordered to True
        order.status = 'Completed'
        order.is_ordered = True
        order.save()

        # Create a new Payment instance for wallet payment method
        payment = Payment.objects.create(
            user=request.user,
            payment_id=f'WAL-{order.order_number}',
            payment_method='Wallet',
            amount_paid=order.final_total,
            status='Completed'  # Assuming payment is completed since it's deducted from the wallet
        )

        # Assign the Payment instance to the order
        order.payment = payment
        order.save()

        # Retrieve cart items and add them to the order
        cart_items = CartItem.objects.filter(user=request.user)
        for item in cart_items:
            orderproduct = OrderProduct()
            orderproduct.order_id = order.id
            orderproduct.user_id = request.user.id
            orderproduct.product_id = item.product_id
            orderproduct.quantity = item.quantity
            orderproduct.product_price = item.product.price
            orderproduct.ordered = True
            orderproduct.save()

            cart_item = CartItem.objects.get(id=item.id)
            product_variation = cart_item.variations.all()
            orderproduct = OrderProduct.objects.get(id=orderproduct.id)
            orderproduct.variations.set(product_variation)
            orderproduct.save()
        # Reduce the quantity of the sold products
        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()
    #clear cart

        # Delete all the current user's cart items
        CartItem.objects.filter(user=request.user).delete()

        # Render the confirm_payment.html template with the order details
        context = {
            'order_number': order_number,
            'order': order,
            'payment': payment  # Include the payment details in the context
        }

        messages.success(request, "Order placed successfully. Amount deducted from your wallet.")
        return render(request, 'orders/confirmpayment.html', context)
    except Exception as e:
        messages.error(request, "An error occurred while processing your order.")
        return redirect('cart')  # Redirect to the cart page or any relevant page

@login_required(login_url='accounts:loginn')
def cash_on_delivery(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if order.final_total > 1000:
        messages.error(request, "Orders above Rs 1000 are not eligible for Cash On Delivery (COD).")
        return redirect('order_summary', order_number=order.order_number)
    order.is_ordered = True
    order.status = 'Completed'
    order.save()

    payment = Payment.objects.create(
        user=request.user,
        payment_id=f'COD-{order.order_number}',
        payment_method='COD',
        amount_paid=order.final_total,
        status='Pending'
    )

    order.payment = payment
    order.save()

    cart_items = CartItem.objects.filter(user=request.user)
    for item in cart_items:
        order_product = OrderProduct(
            order=order,
            user=request.user,
            product=item.product,
            quantity=item.quantity,
            product_price=item.product.price,
            ordered=True,
        )
        order_product.save()

        product = Product.objects.get(id=item.product_id)
        product.stock -= item.quantity
        product.save()

    CartItem.objects.filter(user=request.user).delete()

    context = {
        'order_number': order_number,
        'order': order,
        'payment': payment,
    }
    return render(request, 'orders/confirmpayment.html', context)

@login_required(login_url='accounts:loginn')
def cancel_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    order.status = 'Cancelled'
    order.is_ordered = False
    order.save()

    order_items = OrderProduct.objects.filter(order=order)
    for order_item in order_items:
        product = order_item.product
        product.stock += order_item.quantity
        product.save()

    messages.success(request, "Order has been cancelled successfully.")
    return redirect('store')

@login_required(login_url='accounts:loginn')
def cancell_order(request, order_number):
    # Retrieve the order based on the order number
    order = get_object_or_404(Order, order_number=order_number)
    
    # Check if the order is already cancelled
    if order.status == 'Cancelled':
        messages.warning(request, "This order has already been cancelled.")
        return redirect('store')  # Redirect to a relevant page
    
    # Retrieve the final_total from the Order model
    final_total = order.final_total
    
    # Update order status to 'Cancelled' and set is_ordered to False
    order.status = 'Cancelled'
    order.is_ordered = False
    order.save()

    # Retrieve order items and update product stock
    order_items = OrderProduct.objects.filter(order=order)
    for order_item in order_items:
        product = order_item.product
        product.stock += order_item.quantity  # Increase product stock
        product.save()

    # Retrieve the user's wallet if it exists, or create a new wallet if it doesn't exist
    wallet, created = Wallet.objects.get_or_create(account=request.user)
    
    # If the wallet was just created, set the wallet balance to the final_total
    if created:
        wallet.wallet_balance = final_total
    else:
        # If the wallet already exists, add the final_total to the existing wallet balance
        wallet.wallet_balance += final_total

    wallet.save()
    
    messages.success(request, "Order has been cancelled successfully.")
    return redirect('accounts:my_orders')  # Redirect to a success page after cancellation


