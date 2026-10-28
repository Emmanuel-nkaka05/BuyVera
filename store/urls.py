from django.urls import path
from . import views

urlpatterns = [
    path('', views.store, name='store'),
    path('add_product/', views.add_product, name='add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'), # <-- MUST BE HERE
    path('submit_review/<int:product_id>/', views.submit_review, name='submit_review'),
    
    # These dynamic paths MUST come last
    path('<slug:category_slug>/', views.store, name='products_by_category'),
    path('<slug:category_slug>/<slug:product_slug>/', views.products_detail, name='product_detail'),
]