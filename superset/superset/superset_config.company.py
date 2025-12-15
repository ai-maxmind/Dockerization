# superset_config.company8.py
# Sample Superset configuration for Company 8.
# Place this file in `superset/` and either rename to `superset_config.py`
# or set your container to load this file as the Superset config.

from flask_appbuilder.security.manager import AUTH_OID, AUTH_LDAP

# -------------------------
# Authentication selection
# -------------------------
# Choose one or enable both flows depending on your deployment strategy.
# For production pick the one used by your Identity Provider.
# AUTH_TYPE = AUTH_LDAP
# AUTH_TYPE = AUTH_OID

# -------------------------
# LDAP example config
# -------------------------
AUTH_TYPE = AUTH_LDAP
AUTH_LDAP_SERVER = "ldap://ldap.company8.local"
AUTH_LDAP_BIND_USER = "cn=bind,dc=company8,dc=local"
AUTH_LDAP_BIND_PASSWORD = "bind_password"
AUTH_LDAP_SEARCH = "ou=users,dc=company8,dc=local"
AUTH_LDAP_UID_FIELD = "uid"  # or sAMAccountName for AD
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"
AUTH_ROLES_SYNC_AT_FIRST_LOGIN = True

# -------------------------
# OIDC / Keycloak example
# -------------------------
# Uncomment and tune if using Keycloak
from flask_appbuilder.security.manager import AUTH_OID

AUTH_TYPE = AUTH_OID
OAUTH_PROVIDERS = [
    {
        'name': 'keycloak',
        'icon': 'fa-circle',
        'token_key': 'access_token',
        'remote_app': {
            'client_id': 'superset-client',
            'client_secret': 'CLIENT_SECRET',
            'api_base_url': 'http://localhost:8080/realms/company8-realm/protocol/openid-connect',
            'access_token_url': 'http://localhost:8080/realms/company8-realm/protocol/openid-connect/token',
            'authorize_url': 'http://localhost:8080/realms/company8-realm/protocol/openid-connect/auth',
            'client_kwargs': {
                'scope': 'openid email profile'
            }
        }
    }
]

# -------------------------
# Custom Security Manager
# -------------------------
# This class demonstrates an approach to auto-map claims coming from IdP
# (Keycloak/LDAP) to Superset roles. It is an illustrative example and
# may require small adjustments for the Superset/FAB version you run.

from superset.security import SupersetSecurityManager

class Company8SecurityManager(SupersetSecurityManager):
    """
    Example custom security manager that assigns a departmental role
    based on available claims (department, EMP_CODE, groups, email).

    NOTE: This implementation is intentionally defensive: it checks
    for the existence of users and roles before trying to modify them.
    Test carefully in staging before deploying to production.
    """

    def _get_claim(self, user_info, key_names):
        """Return first found claim from key_names list."""
        for k in key_names:
            val = user_info.get(k)
            if val:
                return val
        return None

    def oauth_user_info(self, user_info):
        """
        Called when OIDC/OAuth provider returns user info. Map claims -> roles here.
        """
        try:
            email = self._get_claim(user_info, ['email', 'preferred_username'])
            emp_code = self._get_claim(user_info, ['EMP_CODE', 'employeeNumber'])
            department = self._get_claim(user_info, ['department', 'dept'])
            groups = self._get_claim(user_info, ['groups']) or []

            # Normalize groups to list if comma separated
            if isinstance(groups, str):
                groups = [g.strip() for g in groups.split(',') if g.strip()]

            # Auto assign a Dept_<name> role if department claim exists
            if department and email:
                role_name = f"Dept_{department}"
                role = self.find_role(role_name)
                if not role:
                    # create role if missing
                    try:
                        role = self.add_role(role_name)
                    except Exception:
                        role = self.find_role(role_name)
                if role:
                    user = self.find_user(email)
                    # if user doesn't exist yet, don't crash; user may be created by registration flow
                    if user:
                        try:
                            self.add_role_to_user(user, role)
                        except Exception:
                            pass

            # Map IdP groups to Superset roles if role exists
            for grp in groups:
                role_name = grp if grp.startswith('Dept_') else f"Dept_{grp}"
                role = self.find_role(role_name)
                if role and email:
                    user = self.find_user(email)
                    if user:
                        try:
                            self.add_role_to_user(user, role)
                        except Exception:
                            pass

        except Exception:
            # Never raise here: fallback to default behaviour
            pass

        return user_info


# Activate custom manager
CUSTOM_SECURITY_MANAGER = Company8SecurityManager

# -------------------------
# Additional application-level settings
# -------------------------
# Example: show/hide SQL Lab or other toggles can be added here
# SUPERSET_WEBSERVER_TIMEOUT = 120
# MAPBOX_API_KEY = "..."

# End of sample config
