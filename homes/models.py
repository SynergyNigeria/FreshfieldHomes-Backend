import random
import string
import uuid

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


def _generate_agent_code() -> str:
    """Generate a unique ABC-123 style agent login code."""
    letters = "".join(random.choices(string.ascii_uppercase, k=3))
    digits = "".join(random.choices(string.digits, k=3))
    return f"{letters}-{digits}"


def _unique_agent_code() -> str:
    code = _generate_agent_code()
    while Agent.objects.filter(agent_code=code).exists():
        code = _generate_agent_code()
    return code


def _new_public_id() -> str:
    return uuid.uuid4().hex[:24]


class PropertyType(models.TextChoices):
    HOUSE = "house", "House"
    APARTMENT = "apartment", "Apartment"
    CONDO = "condo", "Condo"
    TOWNHOUSE = "townhouse", "Townhouse"


class PropertyStatus(models.TextChoices):
    FOR_SALE = "for-sale", "For Sale"
    PENDING = "pending", "Pending"
    SOLD = "sold", "Sold"


class RequestStatus(models.TextChoices):
    NEW = "new", "New"
    CONTACTED = "contacted", "Contacted"
    CLOSED = "closed", "Closed"


class ContactStatus(models.TextChoices):
    NEW = "new", "New"
    READ = "read", "Read"
    REPLIED = "replied", "Replied"


class ContactSubject(models.TextChoices):
    BUYING = "buying", "Buying a Home"
    SELLING = "selling", "Selling a Home"
    VIEWING = "viewing", "Schedule a Viewing"
    GENERAL = "general", "General Inquiry"


class Agent(models.Model):
    public_id = models.CharField(max_length=24, unique=True)
    name = models.CharField(max_length=120)
    phone = models.CharField(max_length=40)
    email = models.EmailField(unique=True)
    image = models.URLField(blank=True)
    agent_code = models.CharField(max_length=7, unique=True, blank=True)

    class Meta:
        ordering = ["name"]

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = _new_public_id()
        if not self.agent_code:
            self.agent_code = _unique_agent_code()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.name


class Property(models.Model):
    public_id = models.CharField(max_length=24, unique=True)
    title = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    bedrooms = models.PositiveSmallIntegerField()
    bathrooms = models.PositiveSmallIntegerField()
    sqft = models.PositiveIntegerField()
    image = models.URLField(help_text="Main image URL")
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    status = models.CharField(max_length=20, choices=PropertyStatus.choices, default=PropertyStatus.FOR_SALE)
    year_built = models.PositiveIntegerField()
    description = models.TextField()
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name="properties")
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def save(self, *args, **kwargs):
        if not self.public_id:
            self.public_id = _new_public_id()
        super().save(*args, **kwargs)

    def __str__(self) -> str:
        return self.title


class PropertyImage(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="images")
    image = models.URLField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]


class PropertyFeature(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="features")
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name


class PartialHome(models.Model):
    public_id = models.CharField(max_length=24, unique=True)
    title = models.CharField(max_length=200)
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)

    full_price = models.DecimalField(max_digits=12, decimal_places=2)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    remaining_amount = models.DecimalField(max_digits=12, decimal_places=2)
    percentage_paid = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    bedrooms = models.PositiveSmallIntegerField()
    bathrooms = models.PositiveSmallIntegerField()
    sqft = models.PositiveIntegerField()
    image = models.URLField(help_text="Main image URL")
    property_type = models.CharField(max_length=20, choices=PropertyType.choices)
    year_built = models.PositiveIntegerField()
    description = models.TextField()

    payer_name = models.CharField(max_length=150)
    payer_amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    payer_date_paid = models.DateField()
    payer_percentage_paid = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )

    secure_code = models.CharField(max_length=64, default="1998runs")
    agent = models.ForeignKey(Agent, on_delete=models.PROTECT, related_name="partial_homes")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.title


class PartialHomeImage(models.Model):
    partial_home = models.ForeignKey(PartialHome, on_delete=models.CASCADE, related_name="images")
    image = models.URLField()
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "id"]


class PartialHomeFeature(models.Model):
    partial_home = models.ForeignKey(PartialHome, on_delete=models.CASCADE, related_name="features")
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["id"]

    def __str__(self) -> str:
        return self.name


class CounterPayRequest(models.Model):
    partial_home = models.ForeignKey(PartialHome, on_delete=models.CASCADE, related_name="counter_requests")
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.NEW)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ContactMessage(models.Model):
    first_name = models.CharField(max_length=80)
    last_name = models.CharField(max_length=80)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=20, choices=ContactSubject.choices, default=ContactSubject.GENERAL)
    message = models.TextField()
    status = models.CharField(max_length=20, choices=ContactStatus.choices, default=ContactStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class ChatInquiry(models.Model):
    email = models.EmailField(blank=True)
    message = models.TextField()
    source = models.CharField(max_length=80, default="website-chat")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class LiveChatThread(models.Model):
    property = models.ForeignKey(Property, on_delete=models.CASCADE, related_name="live_chat_threads")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="live_chat_threads")
    user_ip = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["property", "user_ip"],
                name="unique_live_thread_per_property_user_ip",
            )
        ]


class LiveChatMessage(models.Model):
    SENDER_USER = "user"
    SENDER_AGENT = "agent"
    SENDER_CHOICES = [
        (SENDER_USER, "User"),
        (SENDER_AGENT, "Agent"),
    ]

    thread = models.ForeignKey(LiveChatThread, on_delete=models.CASCADE, related_name="messages")
    sender = models.CharField(max_length=10, choices=SENDER_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
