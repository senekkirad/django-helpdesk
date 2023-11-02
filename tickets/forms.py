
from .models import Ticket
from django import forms
from django.utils.timezone import now

class CreateTicketForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = ['product', 'subject', 'description', 'priority']

    def clean(self):
        cleaned_data = super(CreateTicketForm, self).clean()
        subject = cleaned_data.get('subject')
        description = cleaned_data.get('description')
        #department = cleaned_data.get('department')
        product = cleaned_data.get('product')
        priority = cleaned_data.get('priority')
        image=cleaned_data.get('image')
        ticket = super().save(commit=False)
        ticket.subject = subject
        ticket.description = description
        #ticket.department = department
        ticket.product = product
        ticket.priority = priority
        ticket.created_on = now()
        
        ticket = super().save(commit=False)

    def save(self, commit=True):
        ticket = super().save(commit=False)
        if commit:
            ticket.save()
        return ticket
