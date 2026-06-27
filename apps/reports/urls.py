from django.urls import path

from .views import (
    DailySalesReport,
    LowStockReport,
    MonthlySalesReport,
    TopItemsReport,
)

app_name = "reports"

urlpatterns = [
    path("daily", DailySalesReport.as_view(), name="daily"),
    path("monthly", MonthlySalesReport.as_view(), name="monthly"),
    path("top-items", TopItemsReport.as_view(), name="top-items"),
    path("low-stock", LowStockReport.as_view(), name="low-stock"),
]
