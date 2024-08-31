from django.shortcuts import render,redirect
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login,logout
from django.contrib import messages,auth
from accounts.models import Account,Wallet
from category.models import Category
from store.models import Product, ProductImage
from .forms import ProductForm, ProductImageForm,CategoryForm,VariationForm,DeliveryUpdateForm, CouponForm
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import TemplateView,View,ListView, CreateView, UpdateView, DeleteView
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import Q
from orders.models import Order,OrderProduct, Coupon
from django.urls import reverse
from django.http import HttpResponse
from django.utils import timezone
from datetime import timedelta
import pandas as pd
from django.db.models import Sum, Q, F, DecimalField, ExpressionWrapper
from django.template.loader import render_to_string
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from django.http import JsonResponse
import json 
from django.views.decorators.csrf import csrf_exempt
from store.models import ProductImage








# Create your views here.

class SuperuserRequiredMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superadmin

    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect('accounts:loginn')
        else:
            return redirect('home')

class AdminLoginView(View):
    def get(self, request):
        return render(request, 'admin/login.html')

    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(username=username, password=password)

        if user is not None:
            if user.is_superadmin:
                login(request, user)
                return redirect('AdminApp:adminhome')
            else:
                messages.error(request, "You are not authorized to access this area.")
                return redirect('admin_login')
        else:
            messages.error(request, "Invalid login credentials.")
            return redirect('admin_login')
        
class AdminHomeView(SuperuserRequiredMixin, TemplateView):
    template_name = 'admin/custom_admin_homepage.html'

class SignoutView(SuperuserRequiredMixin, View):
    def get(self, request):
        logout(request)
        messages.success(request, "You are logged out.")
        return redirect('accounts:loginn')
    


class UsersView(SuperuserRequiredMixin,View):
    def get(self, request):
        # Fetch account objects from the database
        accounts = Account.objects.all()  # You can filter or order the queryset as needed
        
        # Pass the accounts queryset to the template context
        context = {'accounts': accounts}
        
        # Render the template with the context
        return render(request, 'admin/displayuser.html', context)
    
    def post(self, request):

        # Get the user ID from the form data
            user_id = request.POST.get('user_id')
            # Retrieve the user object
            user = Account.objects.get(id=user_id)
            # Toggle the block/unblock status
            user.is_blocked = not user.is_blocked
            # Save the changes
            user.save()
            # Redirect back to the same page after the update
            return redirect('AdminApp:users')
    
class BlockedUsersView(SuperuserRequiredMixin,View):
    def get(self, request):
        # Fetch blocked accounts
        blocked_accounts = Account.objects.filter(is_blocked=True)

        # Pass the blocked accounts queryset to the template context
        context = {'blocked_accounts': blocked_accounts}

        # Render the template with the context
        return render(request, 'admin/blocked_users.html', context)
    
class DeleteUserView(SuperuserRequiredMixin,View):
    def post(self, request):
        user_id = request.POST.get('user_id')
        user = get_object_or_404(Account, id=user_id)
        user.delete()
        return redirect('AdminApp:users')

class ProductCreateView(SuperuserRequiredMixin,CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'admin/addproduct.html'
    success_url = '/AdminApp/productlist/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form_image'] = ProductImageForm()
        return context

    def form_valid(self, form):
        form.instance.save()
        files = self.request.FILES.getlist('images')
        for file in files:
            ProductImage.objects.create(product=form.instance, image=file)
        messages.success(self.request, "Product created successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error creating product. Please check the form.")
        return super().form_invalid(form)

class ProductListView(SuperuserRequiredMixin,ListView):
    model = Product
    template_name = 'admin/productlist.html'
    context_object_name = 'products'
    paginate_by = 6

class ProductDeleteView(SuperuserRequiredMixin,View):
    def get(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        product.is_active = False
        product.save()
        messages.success(request, "Product deleted successfully")
        return redirect('AdminApp:productlist')

class ProductUpdateView(SuperuserRequiredMixin,UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'admin/editproduct.html'
    success_url = '/AdminApp/productlist/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['image_form'] = ProductImageForm(initial={'images': self.object.images.all()})
        context['existing_images'] = self.object.images.all()
        return context

    def form_valid(self, form):
        form.save()
        files = self.request.FILES.getlist('images')
        for image in files:
            ProductImage.objects.create(product=form.instance, image=image)
        messages.success(self.request, "Product edited successfully")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error editing product. Please check the form.")
        return super().form_invalid(form)



class CategoryListView(SuperuserRequiredMixin,ListView):
    model = Category
    template_name = 'admin/categorylist.html'
    context_object_name = 'categories'
    paginate_by = 7

    def get_queryset(self):
        return Category.objects.filter(is_active=True)
    
    



class CategoryCreateView(SuperuserRequiredMixin,CreateView):
    model = Category
    form_class = CategoryForm
    template_name = 'admin/addcategory.html'
    success_url = reverse_lazy('AdminApp:categorylist')

    def form_valid(self, form):
        response = super().form_valid(form)
        return response

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

class CategoryUpdateView(SuperuserRequiredMixin,UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'admin/editcategory.html'
    success_url = reverse_lazy('AdminApp:categorylist')

class CategoryDeleteView(SuperuserRequiredMixin,View):
    def get(self, request, category_id):
        category = get_object_or_404(Category, id=category_id)
        # Soft delete all products associated with the category
        products_to_delete = Product.objects.filter(category=category)
        products_to_delete.update(is_active=False)

        # Deactivate the category
        category.is_active = False
        category.save()  # Update the 'is_active' field to False instead of deleting
        return redirect('AdminApp:categorylist')

class DeletedCategoryListView(SuperuserRequiredMixin,ListView):
    model = Category
    template_name = 'admin/deleted_category_list.html'
    context_object_name = 'categories'

    def get_queryset(self):
        return Category.objects.filter(is_active=False)
    
class OrderListView(SuperuserRequiredMixin,ListView):
    model = Order
    template_name = 'admin/orderlist.html'
    context_object_name = 'orders'
    ordering = ['-created_at']
    paginate_by = 5

    def get_queryset(self):
        queryset = super().get_queryset()
        search_query = self.request.GET.get('search', '')
        status_filter = self.request.GET.get('status', None)

        # Apply search filter
        if search_query:
            queryset = queryset.filter(
                Q(order_number__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        
        # Apply status filter
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset

class CancelOrderView(SuperuserRequiredMixin,View):
    def get(self, request, order_id):
        print("Cancel Order ID: ", order_id)  # Debug print
        order = get_object_or_404(Order, id=order_id)
        order.is_ordered = False
        order.status = 'Cancelled'
        order.save()
        return redirect('AdminApp:orderlist')

class OrderDetailView(SuperuserRequiredMixin,TemplateView):
    template_name = 'admin/order_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, order_number=order_id)
        order_detail = OrderProduct.objects.filter(order__order_number=order_id)
        
        subtotal = 0
        for i in order_detail:
            product = Product.objects.get(id=i.product_id)  # Retrieve the product
            subtotal += product.price_after_discount() * i.quantity  # Calculate subtotal using price_after_discount

        # Get the payment method from the associated Payment object
       
        if order.payment:
            payment_method = order.payment.payment_method

        context.update({
            'order_detail': order_detail,
            'order': order,
            'subtotal': subtotal,
            'payment_method': payment_method,  # Use the actual payment method
            'delivery_update_form': DeliveryUpdateForm(instance=order),
        })
        
        return context

    def post(self, request, *args, **kwargs):
        order_id = self.kwargs.get('order_id')
        order = get_object_or_404(Order, order_number=order_id)
        form = DeliveryUpdateForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            return redirect(reverse('AdminApp:order_detaill', kwargs={'order_id': order_id}))
        return self.get(request, *args, **kwargs)
    

class AdminAddVariationView(SuperuserRequiredMixin,FormView):
    template_name = 'admin/add_variation.html'
    form_class = VariationForm

    def form_valid(self, form):
        product_id = form.cleaned_data['product'].id  # Get selected product ID from the form
        variation = form.save(commit=False)
        variation.product_id = product_id
        variation.save()
        return redirect('AdminApp:admin_add_variation')

class CouponListView(SuperuserRequiredMixin,ListView):
    model = Coupon
    template_name = 'admin/coupon.html'
    context_object_name = 'coupons'

class CouponCreateView(SuperuserRequiredMixin, CreateView):
    model = Coupon
    form_class = CouponForm
    template_name = 'admin/add_coupon.html'
    success_url = reverse_lazy('AdminApp:coupon')

class CouponDeleteView(SuperuserRequiredMixin, DeleteView):
    model = Coupon
    success_url = reverse_lazy('AdminApp:coupon')

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        coupon = get_object_or_404(Coupon, pk=kwargs['coupon_id'])
        coupon.delete()
        return redirect(self.success_url)


class ApproveReturnView(View):
    def get(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)

        if order.return_requested and not order.return_approved:
            for item in order.order_items.all():
                item.product.stock += item.quantity
                item.product.save()

            order.status = 'Returned'
            order.return_approved = True
            order.save()

            final_total = order.final_total
            wallet, created = Wallet.objects.get_or_create(account=order.user)
            if created:
                wallet.wallet_balance = final_total
            else:
                wallet.wallet_balance += final_total
            wallet.save()

            messages.success(request, "Return approved and refund processed.")
        else:
            messages.error(request, "Return request not found or already approved.")

        return redirect('AdminApp:orderlist')  # Replace with your admin order list view
    
class GenerateSalesReportData:
    @staticmethod
    def generate_sales_report_data(start_date=None, end_date=None):
        orders = Order.objects.none()
        droporders = Order.objects.none()

        if start_date and end_date:
            if isinstance(start_date, str):
                start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
            if isinstance(end_date, str):
                end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()

            orders = Order.objects.filter(status='Delivered', created_at__date__range=[start_date, end_date])
            droporders = Order.objects.filter(Q(status='Returned') | Q(status='Cancelled'), created_at__date__range=[start_date, end_date])

        total_sales = round(orders.aggregate(total_sales=Sum('final_total'))['total_sales'] or 0, 2)
        total_drop_sales = round(droporders.aggregate(total_drop_sales=Sum('final_total'))['total_drop_sales'] or 0, 2)

        total_discount = round(orders.annotate(
            discount_per_product=ExpressionWrapper(
                F('order_items__product__price') * F('order_items__product__discount') / 100,
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        ).aggregate(total_discount=Sum('discount_per_product'))['total_discount'] or 0, 2)

        total_coupons = orders.filter(~Q(coupon=None)).values('coupon').distinct().count()

        net_sales = round(total_sales - total_discount, 2)

        return {
            'start_date': start_date,
            'end_date': end_date,
            'total_sales': total_sales,
            'total_discount': total_discount,
            'total_coupons': total_coupons,
            'net_sales': net_sales,
            'orders': orders,
            'total_drop_sales': total_drop_sales
        }

class SalesReportView(SuperuserRequiredMixin,TemplateView):
   
    template_name = 'admin/sales_report.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        date_range = self.request.GET.get('date_range')
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')

        # Handle predefined ranges
        if date_range:
            today = timezone.now().date()
            if date_range == '1day':
                start_date = end_date = today
            elif date_range == '1week':
                start_date = today - timedelta(days=7)
                end_date = today
            elif date_range == '1month':
                start_date = today.replace(day=1)  # Start of the month
                end_date = today

        context.update(GenerateSalesReportData.generate_sales_report_data(start_date, end_date))
        return context

class DailySalesReportView(SalesReportView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        end_date = timezone.now().date()
        start_date = end_date
        context.update(GenerateSalesReportData.generate_sales_report_data(start_date, end_date))
        return context

class WeeklySalesReportView(SalesReportView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=7)
        context.update(GenerateSalesReportData.generate_sales_report_data(start_date, end_date))
        return context

class MonthlySalesReportView(SalesReportView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        end_date = timezone.now().date()
        start_date = end_date.replace(day=1)
        context.update(GenerateSalesReportData.generate_sales_report_data(start_date, end_date))
        return context

class YearlySalesReportView(SalesReportView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        end_date = timezone.now().date()
        start_date = end_date.replace(day=1, month=1)
        context.update(GenerateSalesReportData.generate_sales_report_data(start_date, end_date))
        return context

class CustomSalesReportView(SalesReportView):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        start_date = self.request.GET.get('start_date')
        end_date = self.request.GET.get('end_date')
        context.update(GenerateSalesReportData.generate_sales_report_data(start_date, end_date))
        return context
    
class DownloadSalesReportPDF(View):
    def get(self, request, *args, **kwargs):
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        start_date = timezone.datetime.strptime(start_date, "%Y-%m-%d").date()
        end_date = timezone.datetime.strptime(end_date, "%Y-%m-%d").date()

        report_data = GenerateSalesReportData.generate_sales_report_data(start_date=start_date, end_date=end_date)
        
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{start_date}_{end_date}.pdf"'

        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter

        # Draw some content
        p.drawString(100, height - 100, f"Sales Report from {start_date} to {end_date}")
        p.drawString(100, height - 120, f"Total Sales: {report_data['total_sales']}")
        p.drawString(100, height - 140, f"Total Discount: {report_data['total_discount']}")
        p.drawString(100, height - 160, f"Total Coupons: {report_data['total_coupons']}")
        p.drawString(100, height - 180, f"Net Sales: {report_data['net_sales']}")
        p.drawString(100, height - 200, f"Total Drop Sales: {report_data['total_drop_sales']}")
        
        # Draw a table or more detailed content as needed

        p.showPage()
        p.save()

        return response

class DownloadSalesReportExcel(View):
    def get(self, request, *args, **kwargs):
        report_data = GenerateSalesReportData.generate_sales_report_data(request.GET.get('start_date'), request.GET.get('end_date'))
        excel_file_path = render_sales_report_excel(report_data)

        with open(excel_file_path, 'rb') as excel_file:
            file_content = excel_file.read()

        response = HttpResponse(file_content, content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="sales_report_{report_data["start_date"]}_{report_data["end_date"]}.xlsx"'
        return response



class CustomAdminHomepageView(SuperuserRequiredMixin,TemplateView):
    template_name = 'admin/custom_admin_homepage.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        filter_period = self.request.GET.get('period', 'yearly')
        today = timezone.now().date()
        start_date, end_date = calculate_date_range(filter_period, today)
        sales_report_data = GenerateSalesReportData.generate_sales_report_data(start_date, end_date)
        
        if sales_report_data:
            context.update(sales_report_data)
            context['filter_period'] = filter_period
            context['top_products'] = list(OrderProduct.objects.filter(order__created_at__date__range=[start_date, end_date]).values('product__product_name').annotate(total_sales=Sum('product_price')).order_by('-total_sales')[:10])
            context['top_categories'] = list(OrderProduct.objects.filter(order__created_at__date__range=[start_date, end_date]).values('product__category__category_name').annotate(total_sales=Sum('product_price')).order_by('-total_sales')[:10])
             # Calculate top brands
            context['top_brands'] = list(OrderProduct.objects
                                         .filter(order__created_at__date__range=[start_date, end_date])
                                         .values('product__brand')
                                         .annotate(total_sales=Sum('product_price'))
                                         .order_by('-total_sales')[:10])
        return context

def calculate_date_range(filter_period, today):
    start_date = end_date = today

    if filter_period == 'weekly':
        start_date = today - timedelta(days=7)
    elif filter_period == 'monthly':
        start_date = today.replace(day=1)
    elif filter_period == 'yearly':
        start_date = today.replace(day=1, month=1)
    else:
        raise ValueError("Invalid filter period")

    return start_date, end_date

def render_sales_report_excel(report_data):
    start_date = report_data['start_date']
    end_date = report_data['end_date']
    total_sales = report_data['total_sales']
    total_discount = report_data['total_discount']
    total_coupons = report_data['total_coupons']
    net_sales = report_data['net_sales']
    orders = report_data['orders']
    total_drop_sales = report_data['total_drop_sales']

    # Make sure to use the correct related name 'order_items'
    order_data = []
    for order in orders:
        order_items = order.order_items.all()  # Use the related name here
        quantity = sum(item.quantity for item in order_items)
        order_data.append({
            'Order ID': order.id,
            'Customer Name': order.user.full_name(),
            'Total Amount': order.final_total,
            'Quantity': quantity,
            'Coupon': order.coupon,
            'Status': order.status,
        })

    sales_df = pd.DataFrame(order_data)

    excel_file_path = f'sales_report_{start_date}_{end_date}.xlsx'
    with pd.ExcelWriter(excel_file_path, engine='openpyxl') as writer:
        sales_df.to_excel(writer, sheet_name='Sales Report', index=False)

        summary_df = pd.DataFrame({
            'Total Sales': [total_sales],
            'Total Discount': [total_discount],
            'Total Coupons': [total_coupons],
            'Net Sales': [net_sales],
            'Total Drop Sales': [total_drop_sales]
        })
        summary_df.to_excel(writer, sheet_name='Summary', index=False)

    return excel_file_path

@csrf_exempt
def delete_image(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            image_id = data.get('image_id')
            image = get_object_or_404(ProductImage, id=image_id)
            image.delete()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method.'})