from django.db.backends.signals import connection_created
from django.db.backends.postgresql.base import DatabaseWrapper
from django.dispatch import receiver
from .models import RecordingSource
from .tasks import continuous_rebroadcast

@receiver(connection_created, sender=DatabaseWrapper)
def initial_connection_to_db(sender, **kwargs):
    streams = RecordingSource.objects.filter(rebroadcast_active=True)
    for stream in streams:
        # Quick check if there's already a pending/running task for this stream
        #existing_tasks = RecordingSource.objects.filter(task_name='streams.tasks.continuous_rebroadcast',
        #                                    kwargs__stream_id=stream.id,
        #                                    status__in=['QUEUED', 'RUNNING'])
        #if existing_tasks.exists():
            # Already queued or running
        #    continue
        print("Starting rebroadcast for stream", stream.title)
        continuous_rebroadcast.enqueue(stream_id=stream.pk)