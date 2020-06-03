#!/usr/bin/env python3

"""
#########################
Get email attachments
#########################

:Description:
    Download email attachments from all new emails in specified folder
    ----------
    Check for new emails
    Grab attachments
    Save attachments

:Usage:
    Run daily

"""

import os
import json
from datetime import datetime, timedelta

from exchangelib import DELEGATE, Account, Credentials, EWSDateTime, EWSTimeZone, Configuration, Message, \
    FileAttachment, ItemAttachment


def read_param_file(param_file=None):

    with open(param_file) as infile:
        data = infile.read()

    d = json.loads(data)

    return d['email_address'], d['password'], d['email_folder'], d['output_folder'], d['file_types']


def check_folder(folder):

    if not os.path.isdir(folder):
        os.mkdir(folder)

    return folder


def get_attachments(email_address=None, password=None, email_folder=None, output_folder=None, file_types=''):

    if not isinstance(email_folder, list):
        email_folder = [email_folder]

    creds = Credentials(
        username='sam.local\\' + email_address,
        password=password
    )

    config = Configuration(server='imap-mail.outlook.com', credentials=creds)

    account = Account(
        primary_smtp_address=email_address,
        autodiscover=False,
        config=config,
        access_type=DELEGATE
    )

    tz = EWSTimeZone.timezone('America/New_York')

    today = datetime.today()
    tomorrow = today + timedelta(days=1)

    starttime = tz.localize(EWSDateTime(today.year, today.month, today.day, 0, 0, 0))

    endtime = tz.localize(EWSDateTime(tomorrow.year, tomorrow.month, tomorrow.day, 0, 0, 0))

    check_folder(output_folder)

    folder = account.root / 'Top of Information Store'

    for l in email_folder:
        folder = folder / l

    # Save attachments to specified folder
    for email in folder.all().order_by('-datetime_received').filter(datetime_received__range=(starttime, endtime)):

        print('  {0}'.format(email.datetime_received.astimezone(tz)))
        print('  {0}'.format(email.subject))

        if len(email.attachments) < 1:
            continue

        company_name = get_company_name(email.sender.email_address)

        for attachment in email.attachments:
            if isinstance(attachment, FileAttachment):

                print('    {0}'.format(attachment.name), end='')

                flag = True
                for f in file_types:
                    if attachment.name.endswith(f):
                        flag = False
                        break

                if flag:
                    print('  |  ignoring file')
                    continue

                print('  |  saving file')
                local_path = os.path.join(output_folder, '_'.join([company_name, attachment.name]))

                with open(local_path, 'wb') as f:
                    f.write(attachment.content)

            elif isinstance(attachment, ItemAttachment):
                if isinstance(attachment.item, Message):
                    print(attachment.item.subject, attachment.item.body)


def check_params(email_address=None, password=None, email_folder=None, output_folder=None, param_file=None,
                 file_types=''):

    if param_file is None:

        params = ['email_address', 'password', 'email_folder', 'output_folder']
        missing = [i for i, j in zip(params, [email_address, password, email_folder, output_folder]) if j is None]

        if len(missing) > 0:
            raise Exception('Parameters missing:\n  ' + '\n  '.join(missing))

        else:
            return email_address, password, email_folder, output_folder, file_types

    else:
        if not os.path.isfile(param_file):
            raise Exception('Parameter file does not exist:\n  {0}'.format(param_file))

        else:
            return read_param_file(param_file)


def get_email_attachments(email_address=None, password=None, email_folder=None, output_folder=None, param_file=None,
                          file_types=''):

    print('Checking parameters')
    u, p, l, o, f = check_params(email_address, password, email_folder, output_folder, param_file, file_types)

    print('Getting attachments')
    get_attachments(email_address=u, password=p, email_folder=l, output_folder=o, file_types=f)


if __name__ == '__main__':

    get_email_attachments(param_file='params.txt')
