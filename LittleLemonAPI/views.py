
from django.contrib.auth.models import User, Group
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from .models import Category, MenuItem, Cart, Order, OrderItem
from .serializers import (
    CategorySerializer,
    MenuItemSerializer,
    UserSerializer,
    CartSerializer,
    OrderSerializer,
)
class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

class MenuItemView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer
    filter_backends = [OrderingFilter, SearchFilter]
    ordering_fields = ['price']
    search_fields = ['category__title']

    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]

class ManagerUsersView(generics.GenericAPIView):
    permission_classes=[IsAdminUser]

    def get(self, request):
        users=User.objects.filter(groups__name='Manager')
        serializer=UserSerializer(users,many=True)
        return Response(serializer.data)

    def post(self, request):
        username = request.data.get('username')

        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        group = Group.objects.get(name='Manager')
        group.user_set.add(user)

        return Response(
            {'message': 'User added to Manager group'},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request):
        username = request.data.get('username')

        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        group = Group.objects.get(name='Manager')
        group.user_set.remove(user)

        return Response(
            {'message': 'User removed from Manager group'},
            status=status.HTTP_200_OK
        )
class DeliveryCrewUsersView(generics.GenericAPIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        users = User.objects.filter(groups__name='Delivery crew')
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        username = request.data.get('username')

        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        group = Group.objects.get(name='Delivery crew')
        group.user_set.add(user)

        return Response(
            {'message': 'User added to Delivery crew'},
            status=status.HTTP_201_CREATED
        )

    def delete(self, request):
        username = request.data.get('username')

        if not username:
            return Response(
                {'error': 'Username is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        group = Group.objects.get(name='Delivery crew')
        group.user_set.remove(user)

        return Response(
            {'message': 'User removed from Delivery crew'},
            status=status.HTTP_200_OK
        )
class CartView(generics.ListCreateAPIView):
    serializer_class = CartSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
class OrderView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.groups.filter(name='Manager').exists():
            orders = Order.objects.all()
        elif request.user.groups.filter(name='Delivery crew').exists():
            orders = Order.objects.filter(delivery_crew=request.user)
        else:
            orders = Order.objects.filter(user=request.user)

        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data)

    def post(self, request):
        cart_items = Cart.objects.filter(user=request.user)

        if not cart_items.exists():
            return Response(
                {"error": "Cart is empty"},
                status=status.HTTP_400_BAD_REQUEST
            )

        total = sum(item.price for item in cart_items)

        order = Order.objects.create(
            user=request.user,
            total=total,
            status=False
        )

        for item in cart_items:
            OrderItem.objects.create(
                order=order,
                menuitem=item.menuitem,
                quantity=item.quantity,
                unit_price=item.unit_price,
                price=item.price
            )

        cart_items.delete()

        serializer = OrderSerializer(order)
        return Response(serializer.data, status=status.HTTP_201_CREATED)        
class OrderDetailView(generics.GenericAPIView):
    permission_classes = [IsAuthenticated]

    def put(self, request, pk):
        try:
            order = Order.objects.get(id=pk)
        except Order.DoesNotExist:
            return Response(
                {"error": "Order not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        # Manager assigns delivery crew
        if request.user.groups.filter(name='Manager').exists():
            delivery_id = request.data.get('delivery_crew')

            if delivery_id:
                try:
                    crew = User.objects.get(id=delivery_id)
                    order.delivery_crew = crew
                except User.DoesNotExist:
                    return Response(
                        {"error": "Delivery crew not found"},
                        status=status.HTTP_404_NOT_FOUND
                    )

            status_value = request.data.get('status')
            if status_value is not None:
                order.status = status_value

            order.save()
            return Response({"message": "Order updated"})

        # Delivery crew marks delivered
        if request.user.groups.filter(name='Delivery crew').exists():
            order.status = True
            order.save()
            return Response({"message": "Order delivered"})

        return Response(
            {"error": "Permission denied"},
            status=status.HTTP_403_FORBIDDEN
        )    