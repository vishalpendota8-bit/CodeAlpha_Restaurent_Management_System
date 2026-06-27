from rest_framework.routers import DefaultRouter

from .views import IngredientViewSet, InventoryLogViewSet, RecipeViewSet

app_name = "inventory"

router = DefaultRouter()
router.register("ingredients", IngredientViewSet, basename="ingredient")
router.register("recipes", RecipeViewSet, basename="recipe")
router.register("logs", InventoryLogViewSet, basename="inventorylog")

urlpatterns = router.urls
