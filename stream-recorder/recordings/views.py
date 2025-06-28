from django.shortcuts import render, redirect, get_object_or_404
from .models import RecordingSource
from .tasks import continuous_rebroadcast
from django.views.decorators.cache import never_cache

@never_cache
def index(request):
    # get all RecordingSource objects
    sources = RecordingSource.objects.all()
    return render(request, 'recordings/index.html', {'sources': sources})

def start_rebroadcast_view(request, pk):
    source = get_object_or_404(RecordingSource, pk=pk)
    #if not source.rebroadcast_active:
        # Fire off the background task
        # continuous_rebroadcast.delay(stream_id=pk)
    return redirect('stream_detail', pk=pk)

def stop_rebroadcast_view(request, pk):
    source = get_object_or_404(RecordingSource, pk=pk)
    if source.rebroadcast_active:
        # For django-tasks, there's no "built-in" kill, 
        # so we rely on the task to notice or we manually track the subprocess. 
        # Easiest hack: Mark the stream as inactive, let the task break out, or send a signal.
        source.rebroadcast_active = False
        source.save()
        # The task’s next loop iteration sees .poll() or the DB flag 
        # and kills the process. 
    return redirect('stream_detail', pk=pk)
