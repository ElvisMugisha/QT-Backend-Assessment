from django.urls import path
from apps.accounts.views import ClientUpdateView

urlpatterns = [
    path('api/client', ClientUpdateView.as_view(), name='client_update'),
]
