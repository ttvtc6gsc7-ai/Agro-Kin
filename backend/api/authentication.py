from rest_framework import authentication, exceptions

from missions.models import Robot


class RobotPrincipal:
    """Principal DRF minimal : un robot n'est jamais un utilisateur Django."""
    is_authenticated = True
    is_anonymous = False

    def __init__(self, robot):
        self.robot = robot
        self.pk = f"robot:{robot.pk}"

    def __str__(self):
        return f"Robot {self.robot.identifiant}"


class RobotTokenAuthentication(authentication.BaseAuthentication):
    """Authentifie X-Robot-Id / X-Robot-Token sans jamais journaliser le jeton."""
    keyword_id = "HTTP_X_ROBOT_ID"
    keyword_token = "HTTP_X_ROBOT_TOKEN"

    def authenticate(self, request):
        robot_id = request.META.get(self.keyword_id)
        token = request.META.get(self.keyword_token)
        if not robot_id and not token:
            return None
        if not robot_id or not token:
            raise exceptions.AuthenticationFailed("Identifiant et jeton robot requis.")
        try:
            robot = Robot.objects.get(identifiant=robot_id)
        except (Robot.DoesNotExist, ValueError):
            raise exceptions.AuthenticationFailed("Robot inconnu.")
        if not robot.verifier_jeton(token):
            raise exceptions.AuthenticationFailed("Authentification robot invalide.")
        return RobotPrincipal(robot), robot
