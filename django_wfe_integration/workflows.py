from django_wfe import workflows
from .steps import *


class MyWorkflow(workflows.Workflow):

    DIGRAPH = {
        steps.__start__: [StepA],
        StepA: [Decision],
        Decision: [StepB, StepC],
    }


class MyOther(workflows.Workflow):

    DIGRAPH = {
        steps.__start__: [StepA],
        StepA: [Decision],
        Decision: [StepB, StepC],
    }


class YetAnother(workflows.Workflow):

    DIGRAPH = {
        steps.__start__: [StepA],
        StepA: [Decision],
        Decision: [StepB, StepC],
    }


class YetAAnother(workflows.Workflow):

    DIGRAPH = {
        steps.__start__: [StepA],
        StepA: [Decision],
        Decision: [StepB, StepC],
    }


class CompletelyDifferent(workflows.Workflow):

    DIGRAPH = {
        steps.__start__: [StepA],
        StepA: [Decision],
        Decision: [StepB, StepC],
    }


class MyOtherModule4(workflows.Workflow):

    DIGRAPH = {
        steps.__start__: [StepA],
        StepA: [Decision],
        Decision: [StepB, StepC],
        StepB: [StepD],
    }
