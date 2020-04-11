from rest_framework import serializers


class PubSubMessageSerializer(serializers.Serializer):
	type = serializers.CharField()
	data = serializers.DictField()
	version = serializers.IntegerField(default=0)


class ConfigSerializer(serializers.Serializer):
	deck_position = serializers.CharField(default="topright")
	hidden = serializers.CharField(default="0")
	game_offset_horizontal = serializers.CharField(default="0")
	promote_on_hsreplaynet = serializers.BooleanField(default=True)
