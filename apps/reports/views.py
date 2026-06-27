from datetime import datetime

from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import IsAdminOrManager

from . import services


class DailySalesReport(APIView):
    """GET /reports/daily?date=YYYY-MM-DD (defaults to today)."""

    permission_classes = [IsAdminOrManager]

    def get(self, request):
        raw_date = request.query_params.get("date")
        report_date = None
        if raw_date:
            try:
                report_date = datetime.strptime(raw_date, "%Y-%m-%d").date()
            except ValueError:
                return Response(
                    {"detail": "Invalid date format, expected YYYY-MM-DD."},
                    status=400,
                )
        return Response(services.daily_sales(report_date))


class MonthlySalesReport(APIView):
    """GET /reports/monthly?year=YYYY&month=MM (defaults to current month)."""

    permission_classes = [IsAdminOrManager]

    def get(self, request):
        now = timezone.localdate()
        try:
            year = int(request.query_params.get("year", now.year))
            month = int(request.query_params.get("month", now.month))
        except ValueError:
            return Response(
                {"detail": "year and month must be integers."}, status=400
            )
        if not 1 <= month <= 12:
            return Response({"detail": "month must be between 1 and 12."}, status=400)
        return Response(services.monthly_sales(year, month))


class TopItemsReport(APIView):
    """GET /reports/top-items?limit=N (default 10)."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = int(request.query_params.get("limit", 10))
        except ValueError:
            limit = 10
        limit = max(1, min(limit, 100))
        return Response(services.top_selling_items(limit))


class LowStockReport(APIView):
    """GET /reports/low-stock — ingredients needing replenishment."""

    permission_classes = [IsAdminOrManager]

    def get(self, request):
        return Response(services.low_stock_report())
