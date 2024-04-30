from flask_wtf import FlaskForm
from wtforms import widgets, SelectMultipleField
from main import list


class MultiCheckboxField(SelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class SimpleForm(FlaskForm):
    list_of_files = list
    files = [(x, x) for x in list_of_files]
    example = MultiCheckboxField('Label', choices=files)
