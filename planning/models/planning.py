from django.db import models
import uuid



class Planning(models.Model):
    id = models.UUIDField(default=uuid.uuid4, unique=True, primary_key=True, editable=False)
    reference = models.CharField(max_length=255)
    id_task_type = models.UUIDField()
