#from django.shortcuts import render

# Create your views here.

from django.shortcuts import render, redirect
from django.core.mail import send_mail
from .forms import CreateTicketForm
from django.contrib.auth.decorators import login_required
from .models import Ticket, Message
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from django.db.models import Q
from django.conf import settings
from django.contrib import messages
#from django.contrib.auth.models import User
from user.models import User
# Create your views here.

UNASSIGNED_STATUS = 1
PENDING_STATUS = 2
RESOLVED_STATUS = 3

@login_required(login_url='/user/login/')
def create_ticket(request):
    if request.method == 'POST':
        
            form = CreateTicketForm(data=request.POST)

            print(request.FILES)
            if form.is_valid():
                ticket = form.save(commit=False)
                ticket.created_by = request.user.email
                ticket.status = UNASSIGNED_STATUS
                ticket.save()
                if request.FILES.get('image'):
                    message = Message(ticket=ticket, message=ticket.description, published_by='user', owner= request.user.get_full_name(), published_at=now(), image=request.FILES.get('image'))
                    message.save()
                else:
                    message = Message(ticket=ticket, message=ticket.description, published_by='user', owner= request.user.get_full_name(), published_at=now())
                    message.save()

                send_mail(subject="Ticket #00{0}: {1}".format(ticket.id,ticket.subject),message="".join(ticket.description),from_email=settings.EMAIL_HOST_USER,recipient_list=(ticket.created_by,))
                return redirect('list_tickets')          
            
    else:
        form = CreateTicketForm()
        args = {'form' : form}
        return render(request, 'tickets/create_ticket.html', args)

@login_required(login_url='/user/login/')
def list_tickets(request):

    tickets = Ticket.objects.order_by('-created_on')
    status = request.GET.get('status')
    staff_users = User.objects.filter(is_staff=True)

    if request.user.is_staff:
        # if request.user.department == 1:
        #     tickets = tickets.filter(department=1)
        # elif request.user.department == 2:
        #     tickets = tickets.filter(department=2)
        # elif request.user.department == 3:
        #     tickets = tickets.filter(department=3)
        # else:
        #     tickets = tickets.filter(department=4)

        if request.user.is_superuser:
            if status == 'unassigned':
                tickets = tickets.filter(status=1)
            elif status == 'pending':
                tickets = tickets.filter(status=2)
            elif status == 'resolved':
                tickets = tickets.filter(status=3)
            #else:
                #tickets = tickets.filter(Q(accepted_by__isnull=True) )
            return render(request, 'tickets/list_tickets_admin.html', {'tickets' : tickets, 'staff_users':staff_users})
        
        else:

            if status == 'unassigned':
                tickets = tickets.filter(status=1)
            elif status == 'pending':
                tickets = tickets.filter(status=2, accepted_by=request.user.email)
            elif status == 'resolved':
                tickets = tickets.filter(status=3, accepted_by=request.user.email)
            else:
                tickets = tickets.filter(Q(accepted_by__isnull=True) | Q(accepted_by=request.user.email))

            return render(request, 'tickets/list_tickets_agent.html', {'tickets' : tickets})
    
    else:
        if status == 'unassigned':
            tickets = tickets.filter(status=1)
        elif status == 'pending':
            tickets = tickets.filter(status=2)
        elif status == 'resolved':
            tickets = tickets.filter(status=3)
        tickets = tickets.filter(created_by=request.user.email)
        return render(request, 'tickets/list_tickets_user.html', {'tickets' : tickets})

@login_required(login_url='/user/login/')
def accept_ticket(request, id):
    ticket = Ticket.objects.get(id=id)
    ticket.accepted_by = request.user.email
    ticket.status = PENDING_STATUS
    ticket.save()
    send_mail(subject="Ticket #00{0}: {1}".format(ticket.id, ticket.subject), message="Ticket has been received and assigned to {0}".format(ticket.accepted_by),
              from_email=settings.EMAIL_HOST_USER, recipient_list=(ticket.created_by,))
    messages.add_message(request, messages.SUCCESS, 'Ticket is accepted')
    return redirect('list_tickets')

@login_required(login_url='/user/login/')
def assign_ticket(request, id, userId):
    try:
        ticket = Ticket.objects.get(id=id)
        # Check if the provided userId is valid (you might want to add more validation here)
        user = User.objects.get(id=userId)

        # Assign the ticket to the selected user
        ticket.accepted_by = user.email
        ticket.status = 2  # Assign the appropriate status here
        ticket.save()

        # Send an email and display a success message
        send_mail(
            subject="Ticket #00{0}: {1}".format(ticket.id, ticket.subject),
            message="Ticket has been received and assigned to {0}".format(ticket.accepted_by),
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=(ticket.created_by,)
        )
        messages.add_message(request, messages.SUCCESS, 'Ticket is assigned')
    except Ticket.DoesNotExist:
        messages.add_message(request, messages.ERROR, 'Ticket not found')
    except User.DoesNotExist:
        messages.add_message(request, messages.ERROR, 'User not found')
    return redirect('list_tickets')

@login_required(login_url='/user/login/')
def ticket_resolved(request, id):
    ticket = Ticket.objects.get(id=id)
    ticket.status = RESOLVED_STATUS
    ticket.save()
    send_mail(subject="Ticket #00{0}: {1}".format(ticket.id, ticket.subject),
              message="Ticket has been resolved", from_email=settings.EMAIL_HOST_USER, recipient_list=(ticket.created_by,))
    messages.add_message(request, messages.SUCCESS, 'Ticket is resolved')
    return redirect('list_tickets')

@login_required(login_url='/user/login/')
def ticket_close(request, id):
    ticket = Ticket.objects.get(id=id)
    ticket.delete()
    send_mail(subject="Ticket #00{0}: {1}".format(id, ticket.subject),
              message="Ticket has been closed", from_email=settings.EMAIL_HOST_USER, recipient_list=(ticket.created_by,))
    messages.add_message(request, messages.SUCCESS, 'Ticket is closed')
    return redirect('list_tickets')

@login_required(login_url='/user/login/')
def ticket_details(request, id):
    ticket= Ticket.objects.get(id=id)
    if request.method == 'POST':
        print(request.FILES.get('image2'))
        ticket_messages = request.POST.get('message')
        if request.user.is_staff:
            if request.FILES.get('image2'):
                ticket_msgs = Message.objects.create(ticket=ticket, message=ticket_messages, published_by='agent', owner= request.user.get_full_name(), published_at=now(), image=request.FILES.get('image2'))
                ticket_msgs.save()
            else:
                ticket_msgs = Message.objects.create(ticket=ticket, message=ticket_messages, published_by='agent',owner= request.user.get_full_name(), published_at=now())
                ticket_msgs.save()
            send_mail(subject="Ticket #00{0}: {1}".format(ticket.id, ticket.subject),
                      message="{0}\n\n\nThank you\n{1}".format(ticket_messages, ticket.accepted_by),
                      from_email=settings.EMAIL_HOST_USER, recipient_list=(ticket.created_by,))
        else:
            if request.FILES.get('image2'):
                ticket_msgs = Message.objects.create(ticket=ticket, message=ticket_messages, published_by='user',owner= request.user.get_full_name() , published_at=now(), image=request.FILES.get('image2'))
                ticket_msgs.save()
            else:
                ticket_msgs = Message.objects.create(ticket=ticket, message=ticket_messages, published_by='user',owner= request.user.get_full_name() , published_at=now())
                ticket_msgs.save()
            #ticket_msgs = Message.objects.create(ticket=ticket, message=ticket_messages, published_by='user', published_at=now())
            send_mail(subject="Ticket #00{0}: {1}".format(ticket.id, ticket.subject),
                      message="{0}\n\n\nThank you\n{1}".format(ticket_messages, ticket.created_by),
                      from_email=settings.EMAIL_HOST_USER, recipient_list=(ticket.accepted_by,))
        #ticket_msgs.save()
    ticket_msgs = Message.objects.filter(ticket=ticket)
    ticket_msgs = ticket_msgs.order_by('published_at')

    user = get_user_model().objects.get(email=ticket.created_by)
    if ticket.accepted_by:
        agent = get_user_model().objects.get(email =ticket.accepted_by)
    else:
        agent = None
    return render(request, 'tickets/ticket_details.html', {'ticket_msgs' : ticket_msgs, 'created_by':user, 'accepted_by':agent})
