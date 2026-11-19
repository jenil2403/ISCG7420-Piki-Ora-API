def confirmation_text(user, slot):
    who = user.first_name or user.username
    when = slot.date.strftime("%d %b %Y")
    clock = slot.start_time.strftime("%H:%M")
    return (
        f"Confirmed: {who}, your visit with {slot.doctor.full_name} "
        f"on {when} at {clock} is booked."
    )
