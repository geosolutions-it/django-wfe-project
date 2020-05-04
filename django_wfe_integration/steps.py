from time import sleep
from random import randint
from django_wfe import steps
from pydantic import BaseModel


class StepA(steps.Step):

    class UserInputSchema(BaseModel):
        some_data: int

    def execute(self, _input=None, external_input=None, *args, **kwargs):
        print(external_input['some_data'])
        sleep(3)
        return randint(0, 1)


class Decision(steps.Decision):

    def transition(self, _input=None, *args, **kwargs):
        sleep(3)
        return _input


class StepB(steps.Step):

    def execute(self, _input=None, *args, **kwargs):
        sleep(3)


class StepC(steps.Step):

    def execute(self, _input=None, *args, **kwargs):
        sleep(3)
