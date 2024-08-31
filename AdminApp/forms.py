from django import forms
from store.models import Product, ProductImage,Variation
from django.forms import modelformset_factory
from django.core.validators import MinValueValidator, MaxValueValidator
from category.models import Category
from django.utils.text import slugify
from orders.models import Order,Coupon


class ProductForm(forms.ModelForm):
    discount = forms.DecimalField(
        label='Discount',
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
   
    class Meta:
        model = Product
        fields = ['product_name', 'slug', 'description', 'price', 'discount', 'stock', 'is_available', 'category','brand']
        widgets = {
            'product_name': forms.TextInput(attrs={'class': 'form-control'}),
            'slug': forms.TextInput(attrs={'class': 'form-control'}),
            'brand': forms.TextInput(attrs={'class': 'form-control'}), 
            'description': forms.TextInput(attrs={'class': 'form-control'}),
            'price': forms.NumberInput(attrs={'class': 'form-control'}),
            'stock': forms.NumberInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.filter(is_active=True)
        
        
    def clean_product_name(self):
            product_name = self.cleaned_data.get('product_name')
            if product_name:
                return product_name
            return None

    def save(self, commit=True):
            instance = super().save(commit=False)
            instance.slug = slugify(self.cleaned_data['product_name'])
            if commit:
                instance.save()
            return instance

class ProductImageForm(forms.ModelForm):
    images = forms.FileField(widget = forms.TextInput(attrs={
            "name": "images",
            "type": "File",
            "class": "form-control",
            "multiple": "True",
        }), label = "")
    class Meta:
        model = ProductImage
        fields = ['images']

    
# class CategoryForm(forms.ModelForm):
#     category_discount = forms.DecimalField(
#         label='Category_Discount',
#         max_digits=10,
#         decimal_places=2,
#         validators=[MinValueValidator(0), MaxValueValidator(100)],
#         widget=forms.NumberInput(attrs={'class': 'form-control'})
#     )
#     class Meta:
#         model = Category
#         fields = ['category_name', 'slug', 'description', 'category_image', 'category_discount']

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['category_name', 'slug', 'description', 'category_image']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category_image'].widget.attrs.update({'class': 'form-control-file'})

class VariationForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.all(), empty_label="Select a product")

    class Meta:
        model = Variation
        fields = ['product', 'variation_category', 'variation_value', 'is_active']

class DeliveryUpdateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status']

class CouponForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})
    class Meta:
        model = Coupon
        fields = ['code', 'discount', 'valid_from', 'valid_to']
        widgets = {
            'valid_from': forms.DateTimeInput(attrs={'type': 'datetime-local' , 'class': 'form-control'}),
            'valid_to': forms.DateTimeInput(attrs={'type': 'datetime-local' , 'class': 'form-control'}),
        }