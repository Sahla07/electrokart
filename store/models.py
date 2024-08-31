from django.db import models
from category.models import Category
from accounts.models import Account
from django.urls import reverse
from django.core.validators import MinLengthValidator,MinValueValidator, MaxValueValidator

# Create your models here.

    
class Product(models.Model):
    product_name = models.CharField(max_length=255,blank=True)
    slug = models.SlugField(max_length=200, unique=True,blank=True)
    description = models.TextField(blank=True)
    price = models.IntegerField()
    stock = models.IntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    brand = models.CharField(max_length=255, blank=True, null=True)  
    created_date = models.DateField(auto_now_add = True)
    modified_date = models.DateField(auto_now = True)
    is_active = models.BooleanField(default=True)# Soft delete flag
    
    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])

    def __str__(self):
        return self.product_name
    
    def price_after_discount(self):
        
        if self.discount > 0 and self.discount < 100:
            print("Discount product")
            return round(self.price - (self.price * self.discount / 100),)
        else:
            print("No discount")
            return self.price

class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.FileField(upload_to='photos/products', blank=True, null=True)
    

    def __str__(self):
        return f"Image for {self.product.product_name}"



class VariationManager(models.Manager):
    def colors(self):
        return super(VariationManager, self).filter(variation_category='color', is_active=True)
    
variation_category_choice = (
    ('color', 'color'),
   
)

class Variation(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variation_category = models.CharField(max_length=200, choices=variation_category_choice)
    variation_value = models.CharField(max_length=100)
    is_active = models.BooleanField(default= True)
    created_at = models.DateTimeField(auto_now=True)

    objects = VariationManager()

    def __str__(self):
        return self.variation_value

class Wishlist(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_date = models.DateTimeField(auto_now_add=True)

    def get_url(self):
        return reverse('product_detaill', args=[self.product.slug])


    def __str__(self):
        return f'{self.user.username} - {self.product.product_name}'
    
class ReviewRating(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100, blank=True)
    review = models.TextField(max_length=500, blank=True)
    rating = models.FloatField()
    ip = models.CharField(max_length=20, blank=True)
    status = models.BooleanField(default=True)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.subject