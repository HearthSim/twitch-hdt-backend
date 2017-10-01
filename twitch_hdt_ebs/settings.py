"""
Django configuration

https://docs.djangoproject.com/en/1.11/topics/settings/
"""

import os


if os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
	DEBUG = False
	ALLOWED_HOSTS = [
		".twitch-ebs.hearthsim.net",
		".execute-api.{region}.amazonaws.com".format(
			region=os.environ.get("AWS_REGION", "us-east-1")
		),
	]
else:
	DEBUG = True
	ALLOWED_HOSTS = ["*"]


def get_secure_parameters(namespace="twitch_ebs"):
	if DEBUG:
		return {}

	import boto3

	parameters = [
		"DJANGO_DB_HOST", "DJANGO_DB_NAME", "DJANGO_DB_USER",
		"DJANGO_DB_PASSWORD", "DJANGO_SECRET_KEY", "HDT_EBS_CLIENT_ID",
		"HDT_TWITCH_CLIENT_ID", "HDT_TWITCH_SECRET_KEY", "HDT_TWITCH_OWNER_ID",
	]
	ssm_parameters = {
		"{}.{}".format(namespace, param.lower()): param for param in parameters
	}

	ssm = boto3.client("ssm")
	response = ssm.get_parameters(Names=list(ssm_parameters.keys()), WithDecryption=True)
	invalid_parameters = response.get("InvalidParameters", [])
	if invalid_parameters:
		raise ValueError("Invalid parameters: {}".format(str(invalid_parameters)))

	ret = {}
	for p in response["Parameters"]:
		ret[ssm_parameters[p["Name"]]] = p["Value"]

	return ret


params = get_secure_parameters()

SECRET_KEY = params.get("DJANGO_SECRET_KEY", "<local>")

WSGI_APPLICATION = "twitch_hdt_ebs.wsgi.application"
ROOT_URLCONF = "twitch_hdt_ebs.urls"
AUTH_USER_MODEL = "accounts.User"

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = False
USE_L10N = False
USE_TZ = True

INSTALLED_APPS = [
	"django.contrib.auth",
	"django.contrib.contenttypes",
	"django.contrib.sessions",
	"django.contrib.sites",
	"allauth.account",
	"allauth.socialaccount",
	"oauth2_provider",
	"rest_framework",
	"corsheaders",
	"hearthsim_identity.accounts",
	"hearthsim_identity.api",
	"hearthsim_identity.oauth2",
]

MIDDLEWARE = [
	"django.middleware.security.SecurityMiddleware",
	"django.contrib.sessions.middleware.SessionMiddleware",
	"corsheaders.middleware.CorsMiddleware",
	"django.middleware.common.CommonMiddleware",
	"django.middleware.csrf.CsrfViewMiddleware",
	"django.contrib.auth.middleware.AuthenticationMiddleware",
	"django.contrib.messages.middleware.MessageMiddleware",
	"django.middleware.clickjacking.XFrameOptionsMiddleware",
]

DATABASES = {
	"default": {
		"ENGINE": "django.db.backends.postgresql",
		"NAME": params.get("DJANGO_DB_NAME", "hsreplaynet"),
		"USER": params.get("DJANGO_DB_USER", "postgres"),
		"PASSWORD": params.get("DJANGO_DB_PASSWORD", ""),
		"HOST": params.get("DJANGO_DB_HOST", "localhost"),
		"PORT": 5432,
	},
}

TEMPLATES = []
AUTH_PASSWORD_VALIDATORS = []


# Disable DRF browsable API (it requires templates to be setup)
REST_FRAMEWORK = {
	"DEFAULT_RENDERER_CLASSES": ("rest_framework.renderers.JSONRenderer", ),
}

# DRF CORS handling
CORS_ALLOW_METHODS = ("OPTIONS", "POST",)
CORS_ORIGIN_REGEX_WHITELIST = (r"^https://(\w+)\.ext-twitch.tv/", )
CORS_ALLOW_HEADERS = (
	"accept",
	"accept-encoding",
	"authorization",
	"content-type",
	"dnt",
	"origin",
	"user-agent",
	"x-requested-with",
	"x-twitch-client-id",
	"x-twitch-extension-version",
	"x-twitch-user-id",
)

OAUTH2_PROVIDER_APPLICATION_MODEL = "oauth2.Application"


# Should this be moved to the db?
EBS_APPLICATIONS = {
	params.get("HDT_TWITCH_CLIENT_ID", ""): {
		"secret": params.get("HDT_TWITCH_SECRET_KEY", ""),
		"owner_id": params.get("HDT_TWITCH_OWNER_ID", ""),
		"ebs_client_id": params.get("HDT_EBS_CLIENT_ID", ""),
	}
}
EBS_JWT_TTL_SECONDS = 120
