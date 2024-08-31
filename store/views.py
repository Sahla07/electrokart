from django.shortcuts import render, get_object_or_404, redirect
from .models import Product, Wishlist, ReviewRating,Variation
from category.models import Category
from orders.models import OrderProduct
from django.contrib import messages
from django.db.models import  Q
from django.http import HttpResponseRedirect
from carts.views import _cart_id
from carts.models import CartItem
from django.core.paginator import  Paginator
from django.contrib.auth.decorators import login_required
from .forms import ReviewForm
from django.http import JsonResponse


def store(request, category_slug=None):
    categories = None
    products = None

    if category_slug:
        category = get_object_or_404(Category, slug=category_slug, is_active=True)
        products = Product.objects.filter(category=category, is_available=True, is_active=True)
    else:
        products = Product.objects.filter(is_available=True, is_active=True).order_by('id')

    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    product_count = products.count()

    context = {
        'products': paged_products,
        'product_count': product_count,
        'category': category if category_slug else None,
    }
    return render(request, 'store/store.html', context)

def product_detail(request, product_slug, category_slug=None):
    if category_slug:
        single_product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug)
    else:
        single_product = get_object_or_404(Product, slug=product_slug)
    in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=single_product).exists()
    in_wishlist = Wishlist.objects.filter(user=request.user, product=single_product).exists() if request.user.is_authenticated else None
    orderproduct = OrderProduct.objects.filter(user=request.user, product_id=single_product.id).exists() if request.user.is_authenticated else None
    reviews = ReviewRating.objects.filter(product_id=single_product.id, status=True)

    cart_count = CartItem.objects.filter(user=request.user).count() if request.user.is_authenticated else 0
    wishlist_count = Wishlist.objects.filter(user=request.user).count() if request.user.is_authenticated else 0

    context = {
        'single_product': single_product,
        'in_cart': in_cart,
        'orderproduct': orderproduct,
        'in_wishlist': in_wishlist,
        'reviews': reviews,
        'cart_count': cart_count,
        'wishlist_count': wishlist_count,
    }
    return render(request, 'store/product_detail.html', context)

def search(request):
    keyword = request.GET.get('keyword', '')
    sort_by = request.GET.get('sort_by', '')
    
    products = Product.objects.filter(is_active=True, is_available=True)
    
    if keyword:
        products = products.filter(Q(description__icontains=keyword) | Q(product_name__icontains=keyword))
    
    if sort_by == 'price_low_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_low':
        products = products.order_by('-price')
    elif sort_by == 'name_a_to_z':
        products = products.order_by('product_name')
    elif sort_by == 'name_z_to_a':
        products = products.order_by('-product_name')
    
    product_count = products.count()
    
    paginator = Paginator(products, 6)  # 6 products per page
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    
    context = {
        'products': paged_products,
        'product_count': product_count,
        'keyword': keyword,
        'sort_by': sort_by,
    }
    
    return render(request, 'store/store.html', context)



@login_required(login_url='accounts:loginn')
def add_wishlist(request, product_slug):
    try:
        product = Product.objects.get(slug=product_slug)
        variations = []

        if request.method == "POST":
            for item in request.POST:
                if 'variation_id' in item:
                    variation_id = request.POST.get(item)
                    try:
                        variation = Variation.objects.get(id=variation_id)
                        variations.append(variation)
                    except Variation.DoesNotExist:
                        pass

        is_in_cart = CartItem.objects.filter(product=product, user=request.user).exists()

        if is_in_cart:
            messages.error(request, 'Product is already in the cart')
        else:
            wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
            if variations:
                wishlist_item.variations.set(variations)
            if created:
                messages.success(request, 'Product added to wishlist')
            else:
                wishlist_item.delete()
                messages.info(request, 'Product removed from wishlist')

    except Product.DoesNotExist:
        messages.error(request, 'Product does not exist')
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required(login_url='accounts:loginn')
def remove_from_wishlist(request, wishlist_item_id):
    wishlist_item = get_object_or_404(Wishlist, id=wishlist_item_id)
    wishlist_item.delete()
    return redirect('wishlist')

@login_required(login_url='accounts:loginn')
def wishlist(request):
    if request.method == 'POST':
        wishlist_item_id = request.POST.get('wishlist_item_id')
        if wishlist_item_id:
            wishlist_item = get_object_or_404(Wishlist, id=wishlist_item_id)
            wishlist_item.delete()
            return redirect('wishlist')


    wishlist_items = Wishlist.objects.filter(user=request.user)


    # Get the slug of the current product from the request or session
    current_product_slug = request.GET.get('product_slug', None)




    

# Check if any product in the wishlist matches the current product
    in_wishlist = wishlist_items.filter(product__slug=current_product_slug).exists()


    context = {
        'wishlist_items': wishlist_items,
        'in_wishlist': in_wishlist,  # Pass the in_wishlist variable to the template
        }
    return render(request, 'store/wishlist.html', context)

@login_required(login_url='accounts:loginn')
def get_counts(request):
    cart_count = CartItem.objects.filter(user=request.user).count()
    wishlist_count = Wishlist.objects.filter(user=request.user).count()
    return JsonResponse({'cart_count': cart_count, 'wishlist_count': wishlist_count})

@login_required(login_url='accounts:loginn')
def submit_review(request, product_id):
    url = request.META.get('HTTP_REFERER')
    if request.method == "POST":
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
                messages.success(request, 'Thank you! Your review has been Submitted.')
                return redirect(url)
