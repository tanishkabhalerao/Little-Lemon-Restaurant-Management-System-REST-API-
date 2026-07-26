from django.urls import path
from .views import (
    CategoryView,
    MenuItemView,
    ManagerUsersView,
    DeliveryCrewUsersView,
    CartView,
    OrderView,
    OrderDetailView,
)

urlpatterns = [
    path('categories/', CategoryView.as_view()),
    path('menu-items/', MenuItemView.as_view()),
    path('groups/manager/users/', ManagerUsersView.as_view()),
    path('groups/delivery-crew/users/', DeliveryCrewUsersView.as_view()),
    path('cart/menu-items/', CartView.as_view()),
    path('orders/', OrderView.as_view()),
    path('orders/<int:pk>/', OrderDetailView.as_view()),
]