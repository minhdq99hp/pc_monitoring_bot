from rest_framework.viewsets import GenericViewSet
from rest_framework.decorators import action

class PCViewSet(GenericViewSet):



    @action(detail=False, methods=['post'], url_path='import-from-articles')
    def turnoff(self, request):
        pass
