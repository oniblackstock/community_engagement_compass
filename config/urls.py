from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from django.views import defaults as default_views
from django.views.generic import TemplateView

def root_redirect(request):
    """Redirect base URL depending on authentication state.

    - If authenticated: go to chat home
    - If not authenticated: go to login page
    """
    if request.user.is_authenticated:
        return redirect("chatbot:chat_home")
    return redirect("account_login")

urlpatterns = [
    # Chat application URLs
    path("chat/", include("chat.urls", namespace="chatbot")),

    # Core pages
    path("", root_redirect, name="home"),
    path("about/", TemplateView.as_view(template_name="pages/about.html"), name="about"),

    # Django Admin
    path(settings.ADMIN_URL, admin.site.urls),

    # User management
    path("users/", include("knowledgeassistant.users.urls", namespace="users")),
    path("accounts/", include("allauth.urls")),

    # Media files
    *static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT),
]

if settings.DEBUG:
    # Debug toolbar
    import debug_toolbar
    urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns

    # This allows the error pages to be debugged during development
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]

    # Serve media and static files in development
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
