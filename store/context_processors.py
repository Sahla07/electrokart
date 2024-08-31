from .models import Wishlist

def wishlist_count(request):
    wishlist_items = []

    # Check if the user is authenticated before accessing their wishlist items
    if request.user.is_authenticated:
        wishlist_items = Wishlist.objects.filter(user=request.user)

    return {'wishlist_count': len(wishlist_items)}