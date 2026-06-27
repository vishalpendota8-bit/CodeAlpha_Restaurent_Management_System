from rest_framework.routers import DefaultRouter

from .views import RestaurantTableViewSet

app_name = "tables"

router = DefaultRouter()
router.register("", RestaurantTableViewSet, basename="table")

urlpatterns = router.urls
