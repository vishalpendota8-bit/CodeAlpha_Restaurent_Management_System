from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrManager, IsAdminOrManagerOrReadOnly

from . import services
from .models import Ingredient, InventoryLog, Recipe
from .serializers import (
    IngredientSerializer,
    InventoryLogSerializer,
    RecipeSerializer,
    RestockSerializer,
)


class IngredientViewSet(viewsets.ModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    search_fields = ["name"]
    ordering_fields = ["name", "quantity", "minimum_stock"]

    @action(detail=False, methods=["get"], url_path="low-stock")
    def low_stock(self, request):
        """GET /inventory/ingredients/low-stock — ingredients needing a restock."""
        queryset = services.low_stock_ingredients()
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["post"],
        url_path="restock",
        permission_classes=[IsAdminOrManager],
    )
    def restock(self, request, pk=None):
        """POST /inventory/ingredients/{id}/restock — add stock and log it."""
        ingredient = self.get_object()
        serializer = RestockSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        ingredient = services.restock(
            ingredient,
            serializer.validated_data["amount"],
            serializer.validated_data.get("note", ""),
        )
        return Response(
            IngredientSerializer(ingredient).data, status=status.HTTP_200_OK
        )


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.select_related("menu_item", "ingredient").all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAdminOrManager]
    filterset_fields = ["menu_item", "ingredient"]


class InventoryLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = InventoryLog.objects.select_related("ingredient").all()
    serializer_class = InventoryLogSerializer
    permission_classes = [IsAdminOrManager]
    filterset_fields = ["ingredient", "action"]
    ordering_fields = ["timestamp"]
