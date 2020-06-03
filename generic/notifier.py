#!/usr/bin/etv python

"""
#########################
Notifier
#########################

:Purpose:
    Send a notification about a running script (notifier)
    Update the email frame (html_to_python)

:Usage:
    Called from other scripts (notifier)
    Called as needed (html_to_python)

:Dependencies:
    Python3

:Notes:
    Use notifier to send an email notification
    Use html_to_python to update the email frame

"""


def update_html(html_file='html_frame.py', script_name=__file__, status='Test'):
    """
    :Description:
    Updates the HTML code
    Adds variable (week number) to the HTML frame before the email is sent

    :Params:
    html_file: HTML frame of the email, written as a Python docstring
        type: str
        default: html_frame.py
    script_name: Name of the script that the notification is about
        type: str
        default: __file__
    status: Status of the script that the notification is about
        type: str
        default: Test
    returns: Nothing, updates the email HTML code

    :Dependencies:
    Python3

    :Example:
    update_html(html_file='html_frame.py', script_name='some_script.py', status='Error: doesn't work...')
    """

    # Loads the HTML frame from file
    with open(html_file) as infile:
         email_code = infile.read()

    # Add the script name to the HTML code
    email_code = email_code.replace('{{{SCRIPT}}}', script_name)

    # Add the script status to the HTML code
    email_code = email_code.replace('{{{STATUS}}}', status)

    # Save the updated HTML code
    with open('html_text.py', 'w') as outfile:
        outfile.write(email_code)


def send_email(recipients=[], subject='Test'):
    """
    :Description:
    Sends an email to the specified recipients

    :Params:
    recipients: Recipients of the email
        type: list
        default: []
    subject: Email subject
        type: str
        default: Test
    returns: Nothing, sends an email

    :Dependencies:
    Python3

    :Example:
    send_alert(recipients=['john.doe@example.com'], subject='TEST')
    """

    import smtplib

    # Default sender info
    user = 'sse.notifier@gmail.com'
    pwd = 'SSEnotifier322'
    mail_from = 'SSE Notifications'

    if type(recipients) != list:
        recipients = [recipients]

    mail_to = recipients

    # Generate the email message
    message = make_html(subject, recipients)

    try:
        # Send secure email (SSL)
        server_ssl = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server_ssl.ehlo()  # optional, called by login()
        server_ssl.login(user, pwd)
        # ssl server doesn't support or need tls, so don't call server_ssl.starttls()
        server_ssl.sendmail(mail_from, mail_to, message)
        server_ssl.quit()
        server_ssl.close()
        print('Successfully sent the mail using SSL.')
    except:
        print('Failed to send the mail using SSL.')
        try:
            # Send normal email
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.ehlo()
            server.starttls()
            server.login(user, pwd)
            server.sendmail(mail_from, mail_to, message)
            server.close()
            print('Successfully sent the mail.')
        except:
            print('Failed to send the mail.')


# Convert HTML to Python script
# Only use if changing the format of the email
def html_to_python(html_file='html_frame.html', python_file='html_frame.py'):
    """
    :Description:
    Converts the HTML code to a Python docstring

    :Params:
    html_file: HTML frame of the email, written as an HTML file
        type: str
        default: html_text.html
    python_file: Filename to save HTML frame to (as Python docstring)
        type: str
        default: html_frame.py
    returns: Nothing, generates the email HTML code as a Python docstring

    :Dependencies:
    Python3

    :Notes:
    Only run when frame (HTML layout) is changed

    :Example:
    html_to_python(html_file='html_text.html', python_file='html_frame.py')
    """

    # Load the HTML file
    # Prepend each line with 4 spaces
    with open(html_file) as infile:
        lines = ['    ' + line.replace('"', '\'') for line in infile.readlines()]

    # Add code to make the text a docstring
    lines.insert(0, 'def html_text():\n    """\n')
    lines.append('\n    """')

    # Save the updated code as a Python file
    with open(python_file, 'w') as outfile:
        outfile.writelines(lines)


def make_html(SUBJECT, TO):
    """
    :Description:
    Generates the email message

    :Params:
    SUBJECT: Email subject
        type: str
    TO: Recipients of the email
        type: list
    returns: The email message
        type: str

    :Dependencies:
    Python3
    html_text - email HTML code, written as Python docstring

    :Example:
    make_html(SUBJECT='TEST', TO=['john.doe@example.com'])
    """

    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from generic.html_text import html_text

    # If running multiple times in a row, it will fail if the old BODY isn't deleted
    try:
        del BODY
    except:
        pass

    # Load the docstring from the HTML file
    BODY = html_text.__doc__

    # BODY %= '0% 10%', '100%', SUBJECT  # old

    # Create message container - the correct MIME type is multipart
    MESSAGE = MIMEMultipart('alternative')
    MESSAGE['subject'] = 'SSE | ' + SUBJECT
    MESSAGE['To'] = ', '.join(TO)
    MESSAGE['From'] = 'SSE Notifications'

    # Record the MIME type text/html.
    HTML_BODY = MIMEText(BODY, 'html')

    # Attach parts into message container
    MESSAGE.attach(HTML_BODY)

    return MESSAGE.as_string()


def notifier(script_name=__file__, status='Test', recipients=['enowak@samschwartz.com'],
             subject='Script Status Update', html_file='html_frame.py'):

    import os

    cur_path = os.getcwd()

    os.chdir(__file__ + '/../')

    update_html(html_file, script_name, status)

    send_email(recipients, subject)

    os.chdir(cur_path)


if __name__ == '__main__':

    html_to_python()
    # notifier()
