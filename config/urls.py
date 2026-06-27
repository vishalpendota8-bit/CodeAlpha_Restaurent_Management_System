"""Root URL configuration for the Restaurant Management System."""
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(url="/menu/"), name="home"),
    path("admin/", admin.site.urls),
    path("auth/", include("apps.accounts.urls")),
    path("menu/", include("apps.menu.urls")),
    path("tables/", include("apps.tables.urls")),
    path("reservations/", include("apps.reservations.urls")),
    path("inventory/", include("apps.inventory.urls")),
    path("orders/", include("apps.orders.urls")),
    path("reports/", include("apps.reports.urls")),
]
