"""
The module implementing functions used among others in the AppConfig, before Django imports work properly.
As long as this module is imported in django_wfe.__init__, all functions should define imports within themselves.
"""
import typing
import importlib


class JobState:
    PENDING = 'PENDING'
    ONGOING = 'ONGOING'
    INPUT_REQUIRED = 'INPUT_REQUIRED'
    INPUT_RECEIVED = 'INPUT_RECEIVED'
    FAILED = 'FAILED'
    FINISHED = 'FINISHED'


def order_workflow_execution(workflow_id: typing.Union[int, str]) -> int:
    """
    A function handling Django WFE Workflow execution order.

    :param workflow_id: django_wfe.models.Workflow record's ID
    :return: Ordered workflow's execution ID (django_wfe.models.Job instance's ID)
    """
    from .models import Workflow, Job
    from .tasks import process_job

    job = Job(workflow=Workflow.objects.get(id=int(workflow_id)))
    job.save()
    process_job.send(job_id=job.id)

    return job.id


def provide_external_input(job_id: typing.Union[int, str], external_data: typing.Dict) -> None:
    """
    A function handling Django WFE external input's and resuming the execution of the Workflow.

    :param job_id: django_wfe.models.Job record's ID
    :param external_data: a dictionary containing external data required by the current django_wfe.models.Step
    :return: None
    """
    from .models import Job
    from .tasks import process_job

    job = Job.objects.get(id=job_id)
    job.provide_external_input(external_data)
    process_job.send(job.id)


def update_wdk_models():
    """
    A function iterating over user defined WDK classes (Steps, Decisions, and Workflows),
    updating the database with their representation for the proper Job serialization.

    :return: None
    """
    from django.conf import settings

    from .steps import StepType
    from .workflows import WorkflowType
    from .models import Step, Workflow

    # update Steps with the starting step
    if not Step.objects.filter(path=f'{__package__}.steps.__start__'):
        Step(name='__start__', path=f'{__package__}.steps.__start__').save()

    # update user created steps
    update_wdk_model(settings.WFE_STEPS, Step, StepType)
    # update user created decisions, if not present in steps module
    if settings.WFE_STEPS != settings.WFE_DECISIONS:
        update_wdk_model(settings.WFE_DECISIONS, Step, StepType)
    # update user created workflows
    update_wdk_model(settings.WFE_WORKFLOWS, Workflow, WorkflowType)


def update_wdk_model(module_path: str, model: type, model_type: type) -> None:
    """
    A function updating the database with a certain user defined WDK class

    :param module_path: python path (dot notation) to the WKD classes definition module
    :param model: database model of WDK class representation
    :param model_type: WDK class's type (metaclass)
    :return: None
    """
    from django.db.models import ObjectDoesNotExist

    # import the module
    model_definitions_module = importlib.import_module(module_path)
    # refresh the module to attach all the newest changes
    importlib.reload(model_definitions_module)

    models = [name for name, cls in model_definitions_module.__dict__.items() if isinstance(cls, model_type)]

    for name in models:
        model_path = f'{module_path}.{name}'

        try:
            model.objects.get(path=model_path)
        except ObjectDoesNotExist:
            try:
                model(name=name, path=model_path).save()
            except Exception as e:
                print(f"SKIPPING Automatic mapping {module_path}: failed due to the exception:\n{type(e).__name__}: {e}")


def deregister_watchdog():
    """
    A function setting Watchdog running flag False.
    Should be executed on the main process exit.

    :return: None
    """
    from .models import Watchdog

    w = Watchdog.load()
    w.running = False
    w.save()
