import logging
from django.http import JsonResponse
from rest_framework_simplejwt.authentication import JWTAuthentication
from workspaces.models import Membership, Workspace

logger = logging.getLogger(__name__)


class WorkspaceMiddleware:
    """
    Extracts active workspace from X-Workspace-ID header.
    Authenticates JWT tokens manually in middleware if request.user is Anonymous.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Initialize context
        request.workspace = None
        request.workspace_role = None

        # 2. Route bypasses
        if (
            request.path.startswith('/admin/')
            or request.path.startswith('/api/auth/')
            or request.path.startswith('/accounts/')
            or request.path.startswith('/api/schema/')
            or request.path.startswith('/api/docs/')
        ):
            return self.get_response(request)

        # 3. 🟢 THE JWT FIX: Authenticate Bearer token early so middleware knows who request.user is
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            try:
                jwt_auth = JWTAuthentication()
                auth_result = jwt_auth.authenticate(request)
                if auth_result is not None:
                    user, _ = auth_result
                    request.user = user
            except Exception:
                pass  # Fall through to unauthenticated handler if token is invalid/expired

        # 4. If still unauthenticated after JWT check, pass through
        if not getattr(request, 'user', None) or not request.user.is_authenticated:
            return self.get_response(request)

        # 5. Read and sanitize X-Workspace-ID header
        workspace_id = request.headers.get('X-Workspace-ID')
        if workspace_id in ["null", "undefined", "", None]:
            workspace_id = None

        # 6. Look up membership by explicit header
        if workspace_id:
            try:
                membership = Membership.objects.select_related('workspace').get(
                    workspace_id=workspace_id,
                    user=request.user,
                    is_active=True
                )
                request.workspace = membership.workspace
                request.workspace_role = membership.role

            except Membership.DoesNotExist:
                return JsonResponse(
                    {"detail": "You do not have access to this workspace or it does not exist."},
                    status=403
                )
            except (ValueError, TypeError):
                return JsonResponse({"detail": "Invalid Workspace ID format."}, status=400)

        # 7. Default Fallback: Auto-select personal workspace if no header sent
        if not request.workspace:
            membership = Membership.objects.select_related('workspace').filter(
                user=request.user,
                is_active=True,
                workspace__workspace_type=Workspace.PERSONAL
            ).first()

            if not membership:
                membership = Membership.objects.select_related('workspace').filter(
                    user=request.user,
                    is_active=True
                ).first()

            if membership:
                request.workspace = membership.workspace
                request.workspace_role = membership.role

        return self.get_response(request)