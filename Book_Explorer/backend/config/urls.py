from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/v1/', include(('backend.books.urls', 'books'), namespace='v1')),

    path('api/v1/users/', include(('backend.users.urls', 'users'), namespace='users')),
]
