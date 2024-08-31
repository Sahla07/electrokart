from django.urls import path
from . import views
app_name = 'AdminApp'  # Namespace for admin URLs
urlpatterns = [
   
    #path('adminhome/',views.AdminHomeView.as_view(), name='adminhome'),
    path('signout/',views.SignoutView.as_view(), name='signout'),
    
    #users urls
    path('users/', views.UsersView.as_view(), name='users'),
    path('block_users/', views.BlockedUsersView.as_view(), name='block_users'),
    path('delete_user/', views.DeleteUserView.as_view(), name='delete_user'),
    
    #category urls
    path('categorylist/', views.CategoryListView.as_view(), name='categorylist'),
    path('addcategory/', views.CategoryCreateView.as_view(), name='addcategory'),
    path('editcategory/<int:pk>/', views.CategoryUpdateView.as_view(), name='editcategory'),
    path('deletecategory/<int:category_id>/', views.CategoryDeleteView.as_view(), name='deletecategory'),
    path('deletedcategories/', views.DeletedCategoryListView.as_view(), name='deleted_category_list'),
    
    #product urls
    path('addproduct/', views.ProductCreateView.as_view(), name='addproduct'),
    path('productlist/', views.ProductListView.as_view(), name='productlist'),
    path('deleteproduct/<int:product_id>/', views.ProductDeleteView.as_view(), name='deleteproduct'),
    path('editproduct/<int:pk>/', views.ProductUpdateView.as_view(), name='editproduct'),
    path('product/add-variation/', views.AdminAddVariationView.as_view(), name='admin_add_variation'),
    path('delete-image/', views.delete_image, name='delete_image'),


    #order urls
    path('orderlist/', views.OrderListView.as_view(), name='orderlist'),
    path('order_detaill/<int:order_id>/', views.OrderDetailView.as_view(), name='order_detaill'),
    path('cancelorder/<int:order_id>/', views.CancelOrderView.as_view(), name='cancelorder'),
    path('approve-return/<int:order_id>/', views.ApproveReturnView.as_view(), name='approve_return'),

    #coupon

    path('coupon/', views.CouponListView.as_view(), name='coupon'),
    path('add_coupon/', views.CouponCreateView.as_view(), name='add_coupon'),
    path('coupon/<int:coupon_id>/delete/', views.CouponDeleteView.as_view(), name='delete_coupon'),

    path('sales_report/', views.SalesReportView.as_view(), name='sales_report'),
    path('sales/daily/', views.DailySalesReportView.as_view(), name='daily_sales_report'),
    path('sales/weekly/', views.WeeklySalesReportView.as_view(), name='weekly_sales_report'),
    path('sales/monthly/', views.MonthlySalesReportView.as_view(), name='monthly_sales_report'),
    path('sales/yearly/', views.YearlySalesReportView.as_view(), name='yearly_sales_report'),
    path('sales/custom/', views.CustomSalesReportView.as_view(), name='custom_sales_report'),
    path('custom_admin_homepage/', views.CustomAdminHomepageView.as_view(), name='custom_admin_homepage'),
    path('sales_report/pdf/', views.DownloadSalesReportPDF.as_view(), name='download_sales_reportpdf'),
    path('sales_report/excel/', views.DownloadSalesReportExcel.as_view(), name='download_sales_reportexcel'),
    ]