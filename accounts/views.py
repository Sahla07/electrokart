from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegistrationForm,AddressForm
from . models import Account,UserProfile, Address,Wallet
from django.contrib import messages,auth
from django.contrib.auth import authenticate, login,logout
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from orders.models import Order,OrderProduct,DeliveryUpdate,Payment,Coupon
from store.models import Product
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from datetime import timedelta
from xhtml2pdf import pisa
import logging
from django.core.paginator import Paginator
#verification email
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            phone_number = form.cleaned_data['phone_number']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            username = email.split("@")[0]
            user = Account.objects.create_user(
                first_name=first_name,
                last_name=last_name,
                email=email,
                username=username,
                password=password
            )
            user.phone_number = phone_number
            user.save()

            # User Activation
            current_site = get_current_site(request)
            mail_subject = 'Please Activate your Account'
            message = render_to_string('accounts/account_verification_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            to_email = user.email
            send_mail = EmailMessage(mail_subject, message, to=[to_email])
            send_mail.send()

            messages.info(request, 'An email with the verification link has been sent to your email address.')
            return redirect('accounts:register')
    else:
        form = RegistrationForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def loginn(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(email=email, password=password)

        if user is not None:
            if user.is_superadmin:
                login(request, user)
                return redirect('AdminApp:custom_admin_homepage')
            else:
                login(request, user)
                # messages.success(request, 'Logged in successfully.')
                return redirect('home')
        else:
            messages.error(request, "Invalid Login Credentials")
            return redirect('accounts:loginn')

    return render(request, 'accounts/login.html')

@login_required(login_url='accounts:loginn')
def logout(request):
    auth.logout(request,)
    messages.success(request, 'You are logged out.')  # Set logout message
    return redirect('accounts:loginn')  # Redirect to the login view

def activate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request, 'Congratulations! Your account is activated')
        return redirect('accounts:loginn')
    else:
        messages.error(request, 'Invalid activation link')
        return redirect('accounts:register')
    
@login_required(login_url='accounts:loginn')
def dashboard(request):
    return render(request, 'accounts/dashboard.html')


def forgotpassword(request):
    if request.method == "POST":
        email = request.POST['email']
        if Account.objects.filter(email=email).exists():
            user = Account.objects.get(email__exact=email)

            # reset password email
            current_site = get_current_site(request)
            mail_subject = 'Please reset your Password'
            message = render_to_string('accounts/reset_password_email.html', {
                'user' : user,
                'domain' : current_site,
                'uid' : urlsafe_base64_encode(force_bytes(user.pk)),
                'token': default_token_generator.make_token(user)
            })
            to_email = email 
            send_email = EmailMessage(mail_subject, message, to=[to_email])
            send_email.send()

            messages.success(request, 'Password reset email has been sent to your email address')
            return redirect('accounts:loginn')

        else:
            messages.error(request, 'Account does not exist')
            return redirect('accounts:forgotpassword')
    return render(request,'accounts/forgotpassword.html')

def resetpassword_validate(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = Account._default_manager.get(pk=uid)
    except(TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.success(request, 'Please reset your Password')
        return redirect('accounts:resetpassword')
    else:
        messages.error(request, "This link has been expired!")
        return redirect('accounts:loginn')

def resetpassword(request):
    if request.method == "POST":
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']
        if password == confirm_password:
            uid = request.session.get('uid')
            user = Account.objects.get(pk=uid)
            user.set_password(password)
            user.save()
            messages.success(request, 'Password reset Successfull')
            return redirect('accounts:loginn')
        else:
            messages.error(request, 'Password do not match')
            return redirect('accounts:resetpassword')
    else:
        return render(request, 'accounts/resetpassword.html')
    
@login_required(login_url = 'accounts:loginn')  
def dashboard(request):
    orders = Order.objects.order_by('-created_at').filter(user_id=request.user.id).exclude(status='New')
    orders_count = orders.count()
    user_full_name = request.user.full_name()  # Corrected this line

    context = {
        'orders_count' : orders_count,
        'user_full_name': user_full_name,
        'user': request.user,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required(login_url='accounts:loginn')
def my_orders(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(orders, 7)  # Show 7 orders per page

    page_number = request.GET.get('page')
    
    # Get the orders for the current page
    orders = paginator.get_page(page_number)
    context = {
        'orders' : orders,
        

    }
    return render(request, 'accounts/my_orders.html', context)
@login_required(login_url='accounts:loginn')
def order_detail(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id)
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        product = Product.objects.get(id=i.product_id)  # Retrieve the product
        subtotal += product.price_after_discount() * i.quantity  # Calculate subtotal using price_after_discount

    # Access payment through the order object
    payment_method = order.payment.payment_method if order.payment else None

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
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
        'payment': order.payment, 
        'payment_method': payment_method,
        'coupon_discount': coupon_discount, 
     
    }

    return render(request, 'accounts/order_detail.html', context)

@login_required(login_url = 'accounts:loginn')
def edit_profile(request):
    user = request.user
    profile = UserProfile.objects.get_or_create(user=user)[0]
    addresses = Address.objects.filter(user=user)

    if request.method == 'POST':
        address_form = AddressForm(request.POST)
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = user
            address.save()
            profile.addresses.add(address)
            messages.success(request, 'Address added successfully')
            return redirect('edit_profile')
    else:
        address_form = AddressForm()

    context = {
        'address_form': address_form,
        'addresses': addresses
    }
    return render(request, 'accounts/edit_profile.html', context)

@login_required(login_url='accounts:loginn')
def track_order(request, order_id):
    order = get_object_or_404(Order, order_number=order_id)
    delivery_updates = DeliveryUpdate.objects.filter(order=order).order_by('timestamp')  # Adjust as per your model

    context = {
        'order': order,
        'delivery_updates': delivery_updates,
    }

    return render(request, 'accounts/track_order.html', context)

@login_required(login_url = 'accounts:loginn')
def add_address(request):
    if request.method == 'POST':
        address_form = AddressForm(request.POST)
        if address_form.is_valid():
            address = address_form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, 'Address added successfully')
            return redirect('edit_profile')
    else:
        address_form = AddressForm()

    context = {
        'address_form': address_form,
    }
    return render(request, 'accounts/add_address.html', context)

@login_required(login_url = 'accounts:loginn')
def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id)
    if request.method == 'POST':
        address_form = AddressForm(request.POST, instance=address)
        if address_form.is_valid():
            address_form.save()
            messages.success(request, 'Address updated successfully')
            return redirect('edit_profile')
    else:
        address_form = AddressForm(instance=address)

    context = {
        'address_form': address_form
    }
    return render(request, 'accounts/edit_address.html', context)

@login_required(login_url = 'accounts:loginn')
def delete_address(request, address_id):
    address = Address.objects.get(pk=address_id)
    if request.method == 'POST':
        address.delete()
        messages.success(request, 'Address deleted successfully')
    return redirect('edit_profile')


@login_required(login_url='accounts:loginn')   
def change_password(request):
    if request.method == 'POST':
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        user = Account.objects.get(username__exact = request.user.username)

        if new_password == confirm_password:
            success = user.check_password(current_password)
            if success:
                user.set_password(new_password)
                user.save()
                # auth.logout(request)
                messages.success(request, 'Password Updated Successfully')
                return redirect('accounts:change_password')
            else:
                messages.error(request, 'Please enter valid current password')
                return redirect('change_password')
        else:
            messages.error(request, 'Password does not match')
            return redirect('accounts:change_password')
            
    return render(request, 'accounts/change_password.html')

@login_required(login_url='accounts:loginn')
def user_wallet(request):
    try:
        wallet = Wallet.objects.get(account=request.user)
    except ObjectDoesNotExist:
        # If wallet doesn't exist, create a new one for the user
        wallet = Wallet.objects.create(account=request.user, wallet_balance=0.00)
    
    # Fetching orders with payment method 'Wallet'
    orders_wallet = Order.objects.filter(user=request.user, payment__payment_method='Wallet').order_by('-created_at')
    
    return render(request, 'accounts/user_wallet.html', {'wallet': wallet, 'orders_wallet': orders_wallet})


logger = logging.getLogger(__name__)

@login_required(login_url='accounts:loginn')
def return_order(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    
    logger.debug(f"Initial Order Status: {order.status}")

    if order.status == 'Returned':
        messages.error(request, "Order has already been returned.")
    elif order.status == 'Delivered':
        if order.created_at + timedelta(days=3) < timezone.now():
            messages.error(request, "Cannot return order after 3 days.")
        else:
            order.return_requested = True
            order.save()
            messages.success(request, "Return request has been submitted. Awaiting admin approval.")
    else:
        messages.error(request, "Order cannot be returned.")

    return redirect("accounts:my_orders")

@login_required(login_url='accounts:loginn')
def invoice(request, order_id):
    order_detail = OrderProduct.objects.filter(order__order_number=order_id).prefetch_related('product')
    order = Order.objects.get(order_number=order_id)
    subtotal = 0
    for i in order_detail:
        
        subtotal += i.product.price_after_discount() * i.quantity  # Calculate subtotal using price_after_discount
        print("subtotal is ", subtotal)
    # Fetching payment method from the related Payment object
    payment_method = order.payment.payment_method if order.payment else None

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

    print("Order Detail:", order_detail)
    print("Order:", order)
    print("Subtotal:", subtotal)
    print("Payment Method:", payment_method)
    print("Coupon Discount:", coupon_discount)

    context = {
        'order_detail': order_detail,
        'order': order,
        'subtotal': subtotal,
        'payment_method': payment_method,
        'coupon_discount': coupon_discount,
    }

    return render(request, 'accounts/invoice.html', context)

@login_required(login_url='loginn') 
def generate_invoice_pdf(request, order_number):
    # Fetch the order details and other necessary data
    order = Order.objects.get(order_number=order_number)
    order_detail = OrderProduct.objects.filter(order__order_number=order_number)

    subtotal = 0
    for i in order_detail:
        
        subtotal += i.product.price_after_discount() * i.quantity  # Calculate subtotal using price_after_discount
        print("subtotal is ", subtotal)

    # Fetching payment method from the related Payment object
    payment_method = order.payment.payment_method if order.payment else None

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

    # Render the invoice HTML template with the order data
    rendered_html = render_to_string('accounts/invoice.html', {
        'order_detail': order_detail,
        'order': order,
        'payment': order.payment,
        'subtotal': subtotal,
        'payment_method': payment_method,
        'coupon_discount': coupon_discount,
    })

    # Create an HttpResponse object with PDF content type
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="invoice.pdf"'

    # Convert the rendered HTML to PDF and write to the response
    pisa.CreatePDF(rendered_html, dest=response)
    
    return response
