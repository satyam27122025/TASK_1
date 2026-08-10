from django.db import models


class Notification(models.Model):
    event_id = models.CharField(
        max_length=255,
        unique=True,
        null=True,
        blank=True,
        db_index=True,
    )
    user_id = models.IntegerField()
    email = models.EmailField()
    message = models.TextField()
    status = models.CharField(
        max_length=20,
        default="pending"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"User {self.user_id} ({self.status}) - Event {self.event_id}"