from rest_framework import serializers

from .models import (
    Agent,
    ChatInquiry,
    ContactMessage,
    CounterPayRequest,
    LiveChatMessage,
    LiveChatThread,
    PartialHome,
    Property,
)


class AgentSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)

    class Meta:
        model = Agent
        fields = ["id", "name", "phone", "email", "image"]


class AgentAdminSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id")

    class Meta:
        model = Agent
        fields = ["id", "name", "phone", "email", "image", "agent_code"]
        extra_kwargs = {"agent_code": {"required": False}}


class PropertySerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)
    type = serializers.CharField(source="property_type", read_only=True)
    yearBuilt = serializers.IntegerField(source="year_built", read_only=True)
    agent = AgentSerializer(read_only=True)
    images = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "address",
            "city",
            "state",
            "price",
            "bedrooms",
            "bathrooms",
            "sqft",
            "image",
            "images",
            "type",
            "status",
            "yearBuilt",
            "description",
            "features",
            "agent",
        ]

    def get_images(self, obj: Property):
        return [img.image for img in obj.images.all()] or [obj.image]

    def get_features(self, obj: Property):
        return [feature.name for feature in obj.features.all()]


class PropertyAdminSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id")
    type = serializers.CharField(source="property_type")
    yearBuilt = serializers.IntegerField(source="year_built")
    agent = AgentSerializer(read_only=True)
    agentId = serializers.SlugRelatedField(
        source="agent",
        slug_field="public_id",
        queryset=Agent.objects.all(),
        write_only=True,
    )
    imageUrls = serializers.ListField(child=serializers.URLField(), write_only=True, required=False)
    featureNames = serializers.ListField(child=serializers.CharField(max_length=120), write_only=True, required=False)
    images = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = Property
        fields = [
            "id",
            "title",
            "address",
            "city",
            "state",
            "price",
            "bedrooms",
            "bathrooms",
            "sqft",
            "image",
            "images",
            "imageUrls",
            "type",
            "status",
            "yearBuilt",
            "description",
            "features",
            "featureNames",
            "agent",
            "agentId",
            "is_featured",
        ]

    def get_images(self, obj: Property):
        return [img.image for img in obj.images.all()] or [obj.image]

    def get_features(self, obj: Property):
        return [feature.name for feature in obj.features.all()]

    def _sync_related(self, instance, image_urls, feature_names):
        if image_urls is not None:
            instance.images.all().delete()
            for index, image in enumerate(image_urls):
                instance.images.create(image=image, sort_order=index)
        if feature_names is not None:
            instance.features.all().delete()
            for feature_name in feature_names:
                instance.features.create(name=feature_name)

    def create(self, validated_data):
        image_urls = validated_data.pop("imageUrls", [])
        feature_names = validated_data.pop("featureNames", [])
        instance = super().create(validated_data)
        self._sync_related(instance, image_urls, feature_names)
        return instance

    def update(self, instance, validated_data):
        image_urls = validated_data.pop("imageUrls", None)
        feature_names = validated_data.pop("featureNames", None)
        instance = super().update(instance, validated_data)
        self._sync_related(instance, image_urls, feature_names)
        return instance


class PartialHomeListSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id", read_only=True)
    fullPrice = serializers.DecimalField(source="full_price", max_digits=12, decimal_places=2, read_only=True)
    amountPaid = serializers.DecimalField(source="amount_paid", max_digits=12, decimal_places=2, read_only=True)
    remainingAmount = serializers.DecimalField(source="remaining_amount", max_digits=12, decimal_places=2, read_only=True)
    percentagePaid = serializers.IntegerField(source="percentage_paid", read_only=True)
    type = serializers.CharField(source="property_type", read_only=True)
    yearBuilt = serializers.IntegerField(source="year_built", read_only=True)
    agent = AgentSerializer(read_only=True)
    images = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = PartialHome
        fields = [
            "id",
            "title",
            "address",
            "city",
            "state",
            "fullPrice",
            "amountPaid",
            "remainingAmount",
            "percentagePaid",
            "bedrooms",
            "bathrooms",
            "sqft",
            "image",
            "images",
            "type",
            "yearBuilt",
            "description",
            "features",
            "agent",
        ]

    def get_images(self, obj: PartialHome):
        return [img.image for img in obj.images.all()] or [obj.image]

    def get_features(self, obj: PartialHome):
        return [feature.name for feature in obj.features.all()]


class PartialHomeAdminSerializer(serializers.ModelSerializer):
    id = serializers.CharField(source="public_id")
    fullPrice = serializers.DecimalField(source="full_price", max_digits=12, decimal_places=2)
    amountPaid = serializers.DecimalField(source="amount_paid", max_digits=12, decimal_places=2)
    remainingAmount = serializers.DecimalField(source="remaining_amount", max_digits=12, decimal_places=2)
    percentagePaid = serializers.IntegerField(source="percentage_paid")
    type = serializers.CharField(source="property_type")
    yearBuilt = serializers.IntegerField(source="year_built")
    secureCode = serializers.CharField(source="secure_code")
    payerName = serializers.CharField(source="payer_name")
    payerAmountPaid = serializers.DecimalField(source="payer_amount_paid", max_digits=12, decimal_places=2)
    payerDatePaid = serializers.DateField(source="payer_date_paid")
    payerPercentagePaid = serializers.IntegerField(source="payer_percentage_paid")
    agent = AgentSerializer(read_only=True)
    agentId = serializers.SlugRelatedField(
        source="agent",
        slug_field="public_id",
        queryset=Agent.objects.all(),
        write_only=True,
    )
    imageUrls = serializers.ListField(child=serializers.URLField(), write_only=True, required=False)
    featureNames = serializers.ListField(child=serializers.CharField(max_length=120), write_only=True, required=False)
    images = serializers.SerializerMethodField()
    features = serializers.SerializerMethodField()

    class Meta:
        model = PartialHome
        fields = [
            "id",
            "title",
            "address",
            "city",
            "state",
            "fullPrice",
            "amountPaid",
            "remainingAmount",
            "percentagePaid",
            "bedrooms",
            "bathrooms",
            "sqft",
            "image",
            "images",
            "imageUrls",
            "type",
            "yearBuilt",
            "description",
            "features",
            "featureNames",
            "payerName",
            "payerAmountPaid",
            "payerDatePaid",
            "payerPercentagePaid",
            "secureCode",
            "agent",
            "agentId",
            "is_active",
        ]

    def get_images(self, obj: PartialHome):
        return [img.image for img in obj.images.all()] or [obj.image]

    def get_features(self, obj: PartialHome):
        return [feature.name for feature in obj.features.all()]

    def _sync_related(self, instance, image_urls, feature_names):
        if image_urls is not None:
            instance.images.all().delete()
            for index, image in enumerate(image_urls):
                instance.images.create(image=image, sort_order=index)
        if feature_names is not None:
            instance.features.all().delete()
            for feature_name in feature_names:
                instance.features.create(name=feature_name)

    def create(self, validated_data):
        image_urls = validated_data.pop("imageUrls", [])
        feature_names = validated_data.pop("featureNames", [])
        instance = super().create(validated_data)
        self._sync_related(instance, image_urls, feature_names)
        return instance

    def update(self, instance, validated_data):
        image_urls = validated_data.pop("imageUrls", None)
        feature_names = validated_data.pop("featureNames", None)
        instance = super().update(instance, validated_data)
        self._sync_related(instance, image_urls, feature_names)
        return instance


class UnlockPartialHomeSerializer(serializers.Serializer):
    secure_code = serializers.CharField(max_length=64)


class PartialPayerSerializer(serializers.Serializer):
    name = serializers.CharField()
    amountPaid = serializers.DecimalField(max_digits=12, decimal_places=2)
    datePaid = serializers.DateField()
    percentagePaid = serializers.IntegerField()


class PartialHomeUnlockedSerializer(PartialHomeListSerializer):
    payer = serializers.SerializerMethodField()

    class Meta(PartialHomeListSerializer.Meta):
        fields = PartialHomeListSerializer.Meta.fields + ["payer"]

    def get_payer(self, obj: PartialHome):
        return {
            "name": obj.payer_name,
            "amountPaid": obj.payer_amount_paid,
            "datePaid": obj.payer_date_paid,
            "percentagePaid": obj.payer_percentage_paid,
        }


class CounterPayRequestCreateSerializer(serializers.ModelSerializer):
    partialHomeId = serializers.CharField(write_only=True)

    class Meta:
        model = CounterPayRequest
        fields = ["partialHomeId", "email"]

    def create(self, validated_data):
        public_id = validated_data.pop("partialHomeId")
        partial_home = PartialHome.objects.get(public_id=public_id, is_active=True)
        return CounterPayRequest.objects.create(partial_home=partial_home, **validated_data)


class CounterPayRequestAdminSerializer(serializers.ModelSerializer):
    partialHomeId = serializers.CharField(source="partial_home.public_id", read_only=True)
    partialHomeTitle = serializers.CharField(source="partial_home.title", read_only=True)

    class Meta:
        model = CounterPayRequest
        fields = ["id", "partialHomeId", "partialHomeTitle", "email", "status", "notes", "created_at"]


class ContactMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = ["first_name", "last_name", "email", "phone", "subject", "message"]


class ContactMessageAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactMessage
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "subject",
            "message",
            "status",
            "created_at",
        ]


class ChatInquiryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInquiry
        fields = ["email", "message", "source"]


class ChatInquiryAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatInquiry
        fields = ["id", "email", "message", "source", "created_at"]


class LiveChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = LiveChatMessage
        fields = ["id", "sender", "text", "created_at"]


class LiveChatThreadSerializer(serializers.ModelSerializer):
    propertyId = serializers.CharField(source="property.public_id", read_only=True)
    propertyTitle = serializers.CharField(source="property.title", read_only=True)
    userIp = serializers.CharField(source="user_ip", read_only=True)
    lastMessage = serializers.SerializerMethodField()

    class Meta:
        model = LiveChatThread
        fields = ["id", "propertyId", "propertyTitle", "userIp", "created_at", "updated_at", "lastMessage"]

    def get_lastMessage(self, obj: LiveChatThread):
        message = obj.messages.order_by("-created_at", "-id").first()
        if not message:
            return None
        return LiveChatMessageSerializer(message).data
