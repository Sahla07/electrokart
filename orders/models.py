from django.db import models
from accounts.models import Account
from store.models import Product
from carts.models import Variation
# Create your models here.

class Payment(models.Model):
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method = models.CharField(max_length=100)
    amount_paid = models.CharField(max_length=100)  # this is the total amount paid
    status = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.payment_id
    
class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.FloatField()
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    def __str__(self):
        return self.code

class Order(models.Model):
    STATUS = (
        ('New', 'New'),
        ('Accepted', 'Accepted'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
        ('Shipped', 'Shipped'),
        ('Out for delivery', 'Out for delivery'),
        ('Delivered', 'Delivered'),
        ('Delivered', 'Delivered'),
        ('Returned', 'Returned'),
        ('Payment Failed', 'Payment Failed'),
       
    )
    # PAYMENT_STATUS=(
    #      ('Payment_Pending','Payment_Pending')
    # )
    
    PAYMENT = (
        ('COD', 'COD'),
        ('Wallet', 'Wallet'),
        ('PayPal', 'Paypal'),
    )
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    coupon = models.CharField(max_length=100, null=True)
    final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    order_number = models.CharField(max_length=100)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(max_length=50)
    street_address = models.CharField(max_length=255, null=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)  # Add this line for state field
    country = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=50)
    tax = models.FloatField(null=True)
    order_total = models.DecimalField(max_digits=10, decimal_places=2, null=True)
    status = models.CharField(max_length=20, choices=STATUS, default='New')
    delivery_charge = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ip = models.CharField(blank=True, max_length=20)
    is_ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    return_requested = models.BooleanField(default=False)
    return_approved = models.BooleanField(default=False)

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.first_name
    
  
        

class OrderProduct(models.Model):
    order = models.ForeignKey(Order,related_name='order_items', on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment, on_delete=models.SET_NULL, blank=True, null=True)
    user = models.ForeignKey(Account, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    variations = models.ManyToManyField(Variation, blank=True)
    ordered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def subtotal(self):
        return self.product_price * self.quantity

    def __str__(self):
        return self.product.product_name
    
class DeliveryUpdate(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.order.order_number} - {self.status}"
