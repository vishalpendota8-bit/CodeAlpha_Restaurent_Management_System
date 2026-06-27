from rest_framework import viewsets

from apps.accounts.permissions import IsAdminOrManagerOrReadOnly

from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    search_fields = ["name"]
    ordering_fields = ["name", "created_at"]


class MenuItemViewSet(viewsets.ModelViewSet):
    queryset = MenuItem.objects.select_related("category").all()
    serializer_class = MenuItemSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filterset_fields = ["category", "available"]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "created_at"]
