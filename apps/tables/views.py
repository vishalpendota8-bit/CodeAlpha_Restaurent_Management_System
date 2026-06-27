from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.accounts.permissions import IsAdminOrManagerOrReadOnly

from .models import RestaurantTable
from .serializers import RestaurantTableSerializer


class RestaurantTableViewSet(viewsets.ModelViewSet):
    queryset = RestaurantTable.objects.all()
    serializer_class = RestaurantTableSerializer
    permission_classes = [IsAdminOrManagerOrReadOnly]
    filterset_fields = ["status", "capacity"]
    search_fields = ["table_number"]
    ordering_fields = ["table_number", "capacity"]

    @action(detail=False, methods=["get"], url_path="available")
    def available(self, request):
        """GET /tables/available — list tables ready to seat guests.

        Optional ``?guests=N`` filters to tables that can seat the party.
        """
        queryset = self.get_queryset().filter(
            status=RestaurantTable.Status.AVAILABLE
        )
        guests = request.query_params.get("guests")
        if guests:
            try:
                queryset = queryset.filter(capacity__gte=int(guests))
            except ValueError:
                pass
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(page or queryset, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)
