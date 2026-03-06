from academiaserver.scheduler.reminders_scheduler import get_due_reminders

reminders = get_due_reminders()

print("Recordatorios vencidos:")
print(reminders)