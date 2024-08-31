from django.urls import path
from .import views



urlpatterns = [
    
    path('', views.store,name="store"),
    path('category/<slug:category_slug>/', views.store, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.product_detail, name='product_detail'),
    path('search/', views.search, name='search'),
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('add_wishlist/<slug:product_slug>/', views.add_wishlist, name='add_wishlist'),
    path('wishlist/', views.wishlist, name='wishlist'),
     path('get-counts/', views.get_counts, name='get_counts'),
    path('remove_from_wishlist/<int:wishlist_item_id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('product_detaill/<slug:product_slug>/', views.product_detail, name='product_detaill'),

]
