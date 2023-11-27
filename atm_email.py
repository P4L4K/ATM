import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def send_email(receiver_email, subject, message):
    sender_email = "projectdevhelpid@gmail.com"
    password = "wquu nnar yfga xayc"
    # Set up the MIME
    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    # Attach the message body
    msg.attach(MIMEText(message, 'plain'))

    # Establish a secure connection with the SMTP server
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as server:
        # Log in to the email account
        server.login(sender_email, password)

        # Send the email
        server.sendmail(sender_email, receiver_email, msg.as_string())

# Example usage:
  # Replace with your Gmail email address
receiver_email = "palak03102003@gmail.com"  # Replace with the recipient's email address
subject = "Test Email"
message = "This is a test email sent from Python!"

  # Replace with your generated app password

send_email(receiver_email, subject, message)
