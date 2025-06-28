from django.db.backends.signals import connection_created
from django.db.backends.postgresql.base import DatabaseWrapper
from django.utils import timezone
from django.dispatch import receiver
from django_tasks.backends.database.models import DBTaskResult
from django_tasks import ResultStatus
from .models import RecordingSource
from .tasks import continuous_rebroadcast, record_source
from functools import partial
from django.core.management import call_command

@receiver(connection_created, sender=DatabaseWrapper)
def initial_connection_to_db(sender, **kwargs):
    print('hello!')
    prune_task_results = partial(call_command, "prune_db_task_results", verbosity=0)
    existing_tasks = DBTaskResult.objects.all()
    print(existing_tasks)
    #print(DBTaskResult.objects.complete().count())
    existing_tasks.update(
        status=ResultStatus.SUCCEEDED, finished_at=timezone.now()
    )
    prune_task_results(min_age_days=0, verbosity=3)
    
    streams = RecordingSource.objects.filter(recording_enabled=True)
    for stream in streams:
        print('Should start recording for stream', stream.title)
        worker_id = record_source.enqueue(stream_id=stream.pk)
        stream.recording_worker_id = worker_id
        stream.save()
        #print("Starting rebroadcast for stream", stream.title)
        #continuous_rebroadcast.enqueue(stream_id=stream.pk)
