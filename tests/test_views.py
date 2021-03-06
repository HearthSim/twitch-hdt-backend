from django.core.cache import caches
from django.test import override_settings

from twitch_hdt_ebs.twitch import TwitchClient


def test_config_view(client):
	response = client.post("/config/")

	assert response.status_code == 403


def test_setup_view(client):
	response = client.post("/setup/")

	assert response.status_code == 403


def test_send_view(client):
	response = client.post("/send/")

	assert response.status_code == 401


@override_settings(
	EBS_APPLICATIONS={
		"1a": {
			"secret": "eA==",
			"owner_id": "1",
			"ebs_client_id": "y",
		}
	},
	CACHES={
		"default": {
			"BACKEND": "django.core.cache.backends.locmem.LocMemCache"
		}
	},
	CACHE_READONLY=False,
)
def test_game_start(requests_mock, mocker, client):
	TWITCH_USER_ID = 1

	DECK_LIST = [
		[268, 2, 2], [306, 1, 1], [459, 2, 2], [559, 1, 1], [667, 1, 1], [724, 2, 2],
		[757, 2, 2], [1117, 2, 2], [41217, 2, 2], [41247, 1, 1], [41323, 2, 2], [41418, 1, 1],
		[42442, 2, 2], [45265, 2, 2], [45707, 2, 2], [46461, 1, 1], [47014, 2, 2],
		[48158, 1, 1], [48487, 1, 1],
	]

	DECK_LIST_FLAT = [
		268, 268, 306, 459, 459, 559, 667, 724, 724, 757, 757, 1117, 1117, 41217, 41217, 41247,
		41323, 41323, 41418, 42442, 42442, 45265, 45265, 45707, 45707, 46461, 47014, 47014,
		48158, 48487
	]

	requests_mock.post(TwitchClient.EBS_SEND_MESSAGE.format(channel_id=1), status_code=204)

	def set_user_id(request, view):
		request.twitch_user_id = "1"
		return True
	mocker.patch(
		"twitch_hdt_ebs.views.CanPublishToTwitchChannel.has_permission",
		side_effect=set_user_id
	)

	def set_client_id(request, view):
		request.twitch_client_id = "1a"
		return True
	mocker.patch(
		"twitch_hdt_ebs.views.HasValidTwitchClientId.has_permission",
		side_effect=set_client_id
	)

	class MockUser:
		is_authenticated = True
		settings = {}
		id = 1
		username = "MockUser"
	mocker.patch(
		"oauth2_provider.contrib.rest_framework.authentication.OAuth2Authentication.authenticate",
		side_effect=lambda x: (MockUser, "xxx")
	)

	response = client.post(
		"/send/",
		{
			"type": "game_start",
			"data": {
				"deck": {
					"hero": 930,
					"format": 1,
					"cards": DECK_LIST,
				},
				"game_type": 2,
				"rank": None,
				"legend_rank": 1337,
			},
			"version": 3
		},
		content_type="application/json",
		HTTP_CONTENT_TYPE="application/json",
		HTTP_AUTHORIZATION="Bearer xxx",
		HTTP_X_TWITCH_USER_ID=TWITCH_USER_ID,
		HTTP_X_TWITCH_CLIENT_ID=1,
	)

	assert response.status_code == 200

	body = response.json()
	assert body["status"] == 204

	stored = caches["default"].get(f"twitch_{TWITCH_USER_ID}")
	assert stored
	assert stored["hero"] == 930
	assert stored["format"] == 1
	assert stored["game_type"] == 2
	assert stored["rank"] is None
	assert stored["legend_rank"] == 1337
	assert stored["deck"] == DECK_LIST_FLAT


def test_ping_view(client):
	response = client.get("/ping/")

	assert response.status_code == 200
	assert response.content == b"OK"
